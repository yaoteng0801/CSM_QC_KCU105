# tab_capture.py
from PyQt5 import QtWidgets, QtCore
import json
import os
import sys
import time
try:
    import pcapy  # pcapy-ng (Linux)
except ImportError:
    if sys.platform != "win32":
        raise

    class pcapy:  # noqa: N801 - Windows: Npcap device names behind pcapy's interface
        @staticmethod
        def findalldevs():
            import win_pcap
            entries = win_pcap.list_devices()
            # Physical adapters with link first.
            entries.sort(key=lambda d: (d["loopback"], not d["up"], not d["mac"]))
            return [d["name"] for d in entries]

from noise_scan_controller import NoiseScanController
from pop_run_plot_saving import pop_run_plot_saving
from dataclasses import asdict
from triggerless_filters import TubeFilterSettings
from tube_filter_widget import TubeFilterWidget
from fpga_diagnostics_widget import DiagnosticWidget, SnapshotWorker
from fpga_diagnostics import DiagnosticContinuityError
from external_trigger import DEFAULT_EDITOR_CONFIG, UnsupportedTriggerFirmwareError
from external_trigger_widget import ExternalTriggerWidget
from acquisition_settings import MODE_FIELDS, TIMING, MATCHING, GENERATOR, PULSE_FIELDS
from MiniDAQ_reg import MiniDAQ_reg
from acquisition_register_widget import AcquisitionRegisterWidget

SETTINGS_FILE = "capture_settings.ini"
HIT_SOURCE_MAC = "02:00:00:c7:05:01"
DEFAULT_HIT_CAPTURE_FILTER = (
    f"ether src {HIT_SOURCE_MAC} and ether[12:2] = 0x0068"
)

RUN_PROFILE_TRIGGERED_EXTERNAL = 0
RUN_PROFILE_TRIGGERLESS = 1
RUN_PROFILE_TRIGGERLESS_NOISE_RAW = 2
RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER = 3
RUN_PROFILE_TRIGGERED_INTERNAL = 4

MIN_TRIGGERLESS_WINDOW_CYCLES = 1
MAX_TRIGGERLESS_WINDOW_CYCLES = (1 << 16) - 1
PERSISTENT_TRIGGER_REGISTERS = (set(TIMING + MATCHING + GENERATOR) - PULSE_FIELDS) | {"sma_trigger_enable"}

RUN_PROFILE_SETTINGS = {
    RUN_PROFILE_TRIGGERED_EXTERNAL: (0, 0, 0, 0),
    RUN_PROFILE_TRIGGERED_INTERNAL: (0, 0, 1, 1),
    RUN_PROFILE_TRIGGERLESS: (1, 0, None, None),
    RUN_PROFILE_TRIGGERLESS_NOISE_RAW: (1, 1, None, None),
    RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER: (1, 2, None, None),
}


class FourDigitSpinBox(QtWidgets.QSpinBox):
    def textFromValue(self, value):
        return f"{int(value):04d}"

    def valueFromText(self, text):
        text = str(text or "").strip()
        return int(text) if text else 0


class tab_capture(QtCore.QObject):
    def __init__(
        self,
        parent_widget,
        backend=None,
        *,
        status_parent_widget=None,
        initial_rt_file: str = "",
        rt_apply_callback=None,
    ):
        super().__init__(parent_widget)
        self.parent = parent_widget
        self._status_parent_widget = status_parent_widget
        self.backend = backend
        self._initial_rt_file = str(initial_rt_file or "")
        self._rt_apply_callback = rt_apply_callback
        self._plot_save_labels = set()
        self._plot_live_labels = None
        self._plot_labels_callback = None
        self._plot_selection_callback = None
        self._plot_save_previous_callback = None
        self._plot_can_save_previous_callback = None
        self._asd_main_thr_callback = None
        self._selected_mezz_callback = None
        self._disabled_channels_callback = None
        self._daq_preflight_callback = None
        self._daq_start_callback = None
        self._daq_stop_callback = None
        self._daq_set_modes_callback = None
        self._daq_set_mode_callback = None
        self._daq_mode_callback = None
        self._daq_cached_mode_callback = None
        self._daq_noise_test_mode_callback = None
        self._daq_set_triggerless_settings_callback = None
        self._daq_triggerless_settings_callback = None
        self._configure_external_trigger_callback = None
        self._read_external_trigger_callback = None
        self._set_sma_output_callback = None
        self._applying_external_trigger = False
        self._unsupported_trigger_warning_shown = False
        self._restored_external_trigger_state = None
        self._saved_trigger_registers = {}
        self._set_acquisition_register_callback = None
        self._read_acquisition_registers_callback = None
        self._diagnostic_snapshot_callback = None
        self._diagnostic_baseline = None
        self._diagnostic_latest = None
        self._diagnostic_worker = None
        self._diagnostic_active = False
        self._diagnostic_last_error = None
        self._diagnostic_last_good_time = None
        self._diagnostic_continuity_error = None
        self._ethernet_device_name = ""
        self._diagnostic_timer = QtCore.QTimer(self)
        self._diagnostic_timer.setInterval(1000)
        self._diagnostic_timer.timeout.connect(self._poll_diagnostics)
        self._updating_triggerless_settings = False
        self._minidaq_registers = None
        self._hardware_run_active = False
        self._applied_run_profile = RUN_PROFILE_TRIGGERED_EXTERNAL

        settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
        self.settings = QtCore.QSettings(settings_path, QtCore.QSettings.IniFormat)
        self.noise_scan = NoiseScanController(self)

        self._build_ui()
        self._load_settings()
        for editor in self.external_editors:
            editor.settings_changed.connect(lambda editor=editor: self._save_external_trigger_settings(editor))
        self.refresh_devices()

        if self.backend is not None:
            self.backend.stats.connect(self.update_stats)
            if hasattr(self.backend, "isolation_stats"):
                self.backend.isolation_stats.connect(self.update_isolation_stats)
                self.backend.capture_started.connect(
                    lambda: self.update_isolation_stats((0, 0, 0, 0)))
            if hasattr(self.backend, "decode_status"):
                self.backend.decode_status.connect(self._on_decode_1hz)
            else:
                self.backend.analysis_1hz.connect(self._on_decode_1hz)
            if hasattr(self.backend, "run_finished"):
                self.backend.run_finished.connect(self._on_run_finished)
            if hasattr(self.backend, "run_stopping"):
                self.backend.run_stopping.connect(self._stop_daq_hardware)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self.parent)
        layout.setSpacing(10)

        # ---------------- hardware connections ----------------
        connections_group = QtWidgets.QGroupBox("Hardware Connections")
        connections = QtWidgets.QGridLayout(connections_group)
        connections.setColumnStretch(1, 1)

        connections.addWidget(QtWidgets.QLabel("Ethernet"), 0, 0)
        self.combo_iface = QtWidgets.QComboBox()
        self.combo_iface.setMinimumWidth(190)
        self.combo_iface.currentIndexChanged.connect(self._on_device_changed)
        connections.addWidget(self.combo_iface, 0, 1, 1, 2)
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_devices)
        connections.addWidget(self.btn_refresh, 0, 3)

        rt_group = QtWidgets.QGroupBox("RT Calibration")
        rt_layout = QtWidgets.QGridLayout(rt_group)
        rt_layout.setContentsMargins(6, 6, 6, 6)
        rt_layout.setColumnStretch(1, 1)
        self.edit_rtfile = QtWidgets.QLineEdit()
        self.edit_rtfile.setPlaceholderText("Chamber .root or coefficients .txt")
        self.edit_rtfile.editingFinished.connect(self._save_settings)
        self.btn_browse_rt = QtWidgets.QPushButton("Browse...")
        self.btn_browse_rt.clicked.connect(self._browse_rt_file)
        rt_layout.addWidget(QtWidgets.QLabel("RT file"), 0, 0)
        rt_layout.addWidget(self.edit_rtfile, 0, 1)
        rt_layout.addWidget(self.btn_browse_rt, 0, 2)

        self.combo_nrt = QtWidgets.QComboBox()
        self.combo_nrt.addItem("Auto", 0)
        self.combo_nrt.addItem("1 (shared)", 1)
        self.combo_nrt.addItem("2 (ML1 / ML2)", 2)
        self.combo_nrt.setToolTip("NRT=2 uses RTParam0 for ML1 and RTParam1 for ML2.")
        self.check_rt_catalogue_ranges = QtWidgets.QCheckBox("Catalogue times")
        self.check_rt_catalogue_ranges.setChecked(True)
        self.check_rt_catalogue_ranges.setToolTip(
            "Read time limits from matching _ML1.txt / _ML2.txt tables beside the ROOT file. "
            "Coefficient TXT files default to 0–200 ns. Uncheck to enter manual ranges."
        )
        self.btn_apply_rt = QtWidgets.QPushButton("Apply RT")
        self.btn_apply_rt.clicked.connect(self._apply_rt_selection)
        rt_layout.addWidget(QtWidgets.QLabel("NRT"), 1, 0)
        rt_layout.addWidget(self.combo_nrt, 1, 1, alignment=QtCore.Qt.AlignLeft)
        rt_layout.addWidget(self.btn_apply_rt, 1, 2)
        rt_layout.addWidget(self.check_rt_catalogue_ranges, 2, 0, 1, 3)

        self.rt_ranges_widget = QtWidgets.QWidget()
        rt_ranges = QtWidgets.QGridLayout(self.rt_ranges_widget)
        rt_ranges.setContentsMargins(0, 0, 0, 0)
        rt_ranges.setHorizontalSpacing(3)
        rt_ranges.addWidget(QtWidgets.QLabel("Tmin (ns)"), 0, 1)
        rt_ranges.addWidget(QtWidgets.QLabel("Tmax (ns)"), 0, 2)
        self.rt_range_spins = []
        for ml in (1, 2):
            rt_ranges.addWidget(QtWidgets.QLabel(f"ML{ml}"), ml, 0)
            pair = []
            for col, value in enumerate((0.0, 200.0), start=1):
                spin = QtWidgets.QDoubleSpinBox()
                spin.setRange(-100000.0, 100000.0)
                spin.setDecimals(4)
                spin.setValue(value)
                spin.valueChanged.connect(self._save_settings)
                rt_ranges.addWidget(spin, ml, col)
                pair.append(spin)
            self.rt_range_spins.append(pair)
        rt_layout.addWidget(self.rt_ranges_widget, 3, 0, 1, 3)
        self.lab_rt_status = QtWidgets.QLabel("Select a calibration and click Apply RT.")
        self.lab_rt_status.setWordWrap(True)
        rt_layout.addWidget(self.lab_rt_status, 4, 0, 1, 3)
        self.combo_nrt.currentIndexChanged.connect(self._rt_options_changed)
        self.check_rt_catalogue_ranges.toggled.connect(self._rt_options_changed)
        self._update_rt_range_controls()
        rt_group.setParent(self.parent)
        self._legacy_rt_group = rt_group
        rt_group.hide()  # Legacy settings; calibration controls now live in each Geometry tab.

        # ---------------- online capture setup ----------------
        online_group = QtWidgets.QGroupBox("Online Capture Setup")
        online = QtWidgets.QGridLayout(online_group)
        online.setColumnStretch(1, 1)
        online.setColumnStretch(3, 1)

        self.edit_filter = QtWidgets.QLineEdit(self.parent)
        self.edit_filter.setText(DEFAULT_HIT_CAPTURE_FILTER)
        self.edit_filter.editingFinished.connect(self._save_settings)
        self.edit_filter.hide()
        # Keep the saved/default capture filter active internally without
        # exposing a low-level BPF editor in the normal GUI workflow.

        self.edit_outdir = QtWidgets.QLineEdit()
        self.edit_outdir.setText(os.getcwd())
        self.edit_outdir.editingFinished.connect(self._save_settings)
        self.btn_browse_outdir = QtWidgets.QPushButton("Browse...")
        self.btn_browse_outdir.clicked.connect(self._browse_output_dir)
        online.addWidget(QtWidgets.QLabel("Output directory"), 0, 0)
        online.addWidget(self.edit_outdir, 0, 1, 1, 3)
        online.addWidget(self.btn_browse_outdir, 0, 4)

        online.addWidget(QtWidgets.QLabel("Next run #"), 1, 0)
        self.spin_run = QtWidgets.QSpinBox()
        self.spin_run.setRange(1, 99999999)
        self.spin_run.setValue(1)
        self.spin_run.setFixedWidth(100)
        self.spin_run.valueChanged.connect(self._on_run_changed)
        online.addWidget(self.spin_run, 1, 1, alignment=QtCore.Qt.AlignLeft)

        online.addWidget(QtWidgets.QLabel("CSM #"), 1, 2)
        self.spin_csm_number = FourDigitSpinBox()
        self.spin_csm_number.setRange(0, 9999)
        self.spin_csm_number.setValue(0)
        self.spin_csm_number.setFixedWidth(70)
        self.spin_csm_number.valueChanged.connect(self._save_settings)
        online.addWidget(self.spin_csm_number, 1, 3)
        self.check_include_csm_filename = QtWidgets.QCheckBox("In filename")
        self.check_include_csm_filename.setChecked(True)
        self.check_include_csm_filename.setToolTip(
            "Include the CSM number in generated run file and folder names."
        )
        self.check_include_csm_filename.toggled.connect(self._save_settings)
        online.addWidget(self.check_include_csm_filename, 1, 4)

        online.addWidget(QtWidgets.QLabel("Mode"), 2, 0)
        self.combo_acquisition_mode = QtWidgets.QComboBox()
        self.combo_acquisition_mode.addItem(
            "Triggered_external", RUN_PROFILE_TRIGGERED_EXTERNAL
        )
        self.combo_acquisition_mode.addItem(
            "Triggered_internal", RUN_PROFILE_TRIGGERED_INTERNAL
        )
        self.combo_acquisition_mode.addItem(
            "Triggerless", RUN_PROFILE_TRIGGERLESS
        )
        self.combo_acquisition_mode.addItem(
            "Triggerless Noise Raw", RUN_PROFILE_TRIGGERLESS_NOISE_RAW
        )
        self.combo_acquisition_mode.addItem(
            "Triggerless Noise Counter", RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER
        )
        self.combo_acquisition_mode.setMinimumWidth(250)
        self.combo_acquisition_mode.setToolTip(
            "Immediately set the MiniDAQ acquisition, noise-test, and trigger-source modes"
        )
        self.combo_acquisition_mode.currentIndexChanged.connect(
            self._on_acquisition_mode_changed
        )
        online.addWidget(self.combo_acquisition_mode, 2, 1)

        online.addWidget(QtWidgets.QLabel("Error limit"), 2, 2)
        self.spin_decode_err_stop = QtWidgets.QSpinBox()
        self.spin_decode_err_stop.setRange(0, 100000000)
        self.spin_decode_err_stop.setValue(1000)
        self.spin_decode_err_stop.setSingleStep(100)
        self.spin_decode_err_stop.setToolTip("Stop DAQ when decode errors exceed this value. Set 0 to disable.")
        self.spin_decode_err_stop.valueChanged.connect(self._on_decode_error_stop_changed)
        online.addWidget(self.spin_decode_err_stop, 2, 3)
        self.btn_run_plot_saving = QtWidgets.QPushButton("Plot display / saving...")
        self.btn_run_plot_saving.setMinimumSize(230, 32)
        self.btn_run_plot_saving.clicked.connect(self._open_run_plot_saving_dialog)
        online.addWidget(self.btn_run_plot_saving, 2, 4)

        online.addWidget(QtWidgets.QLabel("Display min hits"), 3, 0)
        self.spin_event_buffer_min_hits = QtWidgets.QSpinBox()
        self.spin_event_buffer_min_hits.setRange(0, 1023)
        self.spin_event_buffer_min_hits.setValue(1)
        self.spin_event_buffer_min_hits.setToolTip(
            "Only put decoded events with at least this many hits into the "
            "Geometry event-display buffer. This does not change any MiniDAQ "
            "hardware hit limit. Set 0 to include empty events."
        )
        self.spin_event_buffer_min_hits.valueChanged.connect(self._save_settings)
        online.addWidget(
            self.spin_event_buffer_min_hits,
            3,
            1,
            alignment=QtCore.Qt.AlignLeft,
        )

        self.check_remove_isolated_hits = QtWidgets.QCheckBox("Remove isolated hits from .dat")
        self.check_remove_isolated_hits.setChecked(False)
        self.check_remove_isolated_hits.setToolTip(
            "Triggerless events only. Check to discard hits with no immediately adjacent "
            "hit tube in the same multilayer, using the loaded geometry. "
            "Live plots use the saved stream. Damaged events are preserved unchanged."
            " After removal, enabled tube filters are reapplied; failing events are not saved."
        )
        self.check_remove_isolated_hits.toggled.connect(self._save_settings)
        online.addWidget(self.check_remove_isolated_hits, 3, 2, 1, 3)

        self.triggerless_settings_group = QtWidgets.QGroupBox(
            "Triggerless Settings (MiniDAQ)"
        )
        triggerless_settings = QtWidgets.QGridLayout(
            self.triggerless_settings_group
        )
        triggerless_settings.setColumnStretch(1, 1)
        triggerless_settings.setColumnStretch(3, 1)

        triggerless_settings.addWidget(
            QtWidgets.QLabel("Window cycles (25 ns)"), 0, 0
        )
        self.spin_triggerless_window_cycles = QtWidgets.QSpinBox()
        self.spin_triggerless_window_cycles.setRange(
            MIN_TRIGGERLESS_WINDOW_CYCLES,
            MAX_TRIGGERLESS_WINDOW_CYCLES,
        )
        self.spin_triggerless_window_cycles.setValue(20)
        self.spin_triggerless_window_cycles.setToolTip(
            "MiniDAQ register window_cycles. The triggerless event window is "
            "this value multiplied by 25 ns."
        )
        self.spin_triggerless_window_cycles.valueChanged.connect(
            self._on_triggerless_settings_changed
        )
        triggerless_settings.addWidget(
            self.spin_triggerless_window_cycles, 0, 1
        )

        self.tube_filters = TubeFilterWidget()
        self.tube_filters.settingsChanged.connect(self._on_triggerless_settings_changed)
        triggerless_settings.addWidget(self.tube_filters, 1, 0, 1, 4)
        self.read_filters_button = QtWidgets.QPushButton("Read FPGA filters/window (replace staged values)")
        self.read_filters_button.clicked.connect(lambda: self._read_acquisition_registers((
            "window_cycles", "tube_filters_chamber0", "tube_filters_chamber1")))
        triggerless_settings.addWidget(self.read_filters_button, 4, 0, 1, 4)
        self.trigger_settings_group = QtWidgets.QGroupBox("Trigger Settings (MiniDAQ)")
        trigger_settings = QtWidgets.QVBoxLayout(self.trigger_settings_group)
        self.external_triggers = ExternalTriggerWidget(
            DEFAULT_EDITOR_CONFIG, self._apply_external_triggers, self._read_external_triggers)
        trigger_settings.addWidget(self.external_triggers)
        deadtime_row = QtWidgets.QHBoxLayout()
        deadtime_row.addWidget(QtWidgets.QLabel("Dead time (25 ns)"))
        self.spin_trigger_deadtime = QtWidgets.QSpinBox()
        self.spin_trigger_deadtime.setRange(0, 65535)
        self.spin_trigger_deadtime.setValue(10)
        self.spin_trigger_deadtime.setToolTip("16-bit holdoff before timestamping. 0 bypasses dead time. Changes apply immediately while stopped.")
        self.spin_trigger_deadtime.valueChanged.connect(self._on_trigger_deadtime_changed)
        deadtime_row.addWidget(self.spin_trigger_deadtime)
        deadtime_row.addStretch()
        trigger_settings.addLayout(deadtime_row)
        self.sma_outputs_group = sma_group = QtWidgets.QGroupBox("SMA trigger outputs")
        sma_layout = QtWidgets.QHBoxLayout(sma_group)
        self.sma_output_checks = []
        for bit, label in enumerate(("GPIO P (J36)", "GPIO N (J37)",
                                     "CLOCK P (J34)", "CLOCK N (J35)")):
            checkbox = QtWidgets.QCheckBox(label)
            checkbox.setChecked(True)
            checkbox.setToolTip("Gate this output independently; usable during acquisition.")
            checkbox.toggled.connect(lambda enabled, bit=bit: self._set_sma_output(bit, enabled))
            self.sma_output_checks.append(checkbox)
            sma_layout.addWidget(checkbox)
        self.mode_settings_stack = QtWidgets.QStackedWidget()
        self.mode_settings_stack.addWidget(self.triggerless_settings_group)
        self.mode_settings_stack.addWidget(self.trigger_settings_group)
        self.mode_pages = {0: self.trigger_settings_group, 1: self.triggerless_settings_group}
        self.register_editors = {}
        self.external_editors = [self.external_triggers]
        for profile, names in MODE_FIELDS.items():
            if profile not in self.mode_pages:
                title = {4: "Internal Trigger Settings (MiniDAQ)",
                         2: "Raw Noise Settings (MiniDAQ)",
                         3: "Noise Counter Settings (MiniDAQ)"}[profile]
                page = QtWidgets.QGroupBox(title)
                QtWidgets.QVBoxLayout(page)
                self.mode_pages[profile] = page
                self.mode_settings_stack.addWidget(page)
            page = self.mode_pages[profile]
            editor = AcquisitionRegisterWidget(
                tuple(n for n in names if not (profile == 0 and n == "trigger_deadtime")),
                self._write_acquisition_register, self._read_acquisition_registers)
            self.register_editors[profile] = editor
            if profile == 1:
                page.layout().addWidget(editor, 2, 0, 1, 4)
            else:
                page.layout().addWidget(editor)
            if profile == RUN_PROFILE_TRIGGERLESS:
                trigger_editor = ExternalTriggerWidget(DEFAULT_EDITOR_CONFIG, lambda: None, lambda: None)
                trigger_editor.read_button.clicked.disconnect()
                trigger_editor.apply_callback = lambda widget=trigger_editor: self._apply_external_editor(widget)
                trigger_editor.read_button.clicked.connect(self._read_external_triggers)
                self.external_editors.append(trigger_editor)
                page.layout().addWidget(trigger_editor, 3, 0, 1, 4)
        settings_scroll = QtWidgets.QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(self.mode_settings_stack)
        settings_scroll.setMinimumHeight(320)
        settings_scroll.setMaximumHeight(560)
        online.addWidget(settings_scroll, 4, 0, 1, 5)

        setup_row = QtWidgets.QHBoxLayout()
        setup_row.setSpacing(10)
        left_column = QtWidgets.QVBoxLayout()
        left_column.setSpacing(6)
        left_column.addWidget(connections_group)
        setup_row.addLayout(left_column, 2)
        setup_row.addWidget(online_group, 3, alignment=QtCore.Qt.AlignTop)
        layout.addLayout(setup_row)

        # ---------------- online capture controls ----------------
        controls_group = QtWidgets.QGroupBox("Capture Controls")
        controls = QtWidgets.QHBoxLayout(controls_group)
        self.btn_start = QtWidgets.QPushButton("Start capture")
        self.btn_start.clicked.connect(self.start)
        controls.addWidget(self.btn_start, 1)
        self.btn_stop = QtWidgets.QPushButton("Stop capture")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        controls.addWidget(self.btn_stop, 1)
        layout.insertWidget(0, controls_group)

        # ---------------- offline DAT processing ----------------
        offline_group = QtWidgets.QGroupBox("Offline DAT Processing")
        offline = QtWidgets.QGridLayout(offline_group)
        offline.setContentsMargins(6, 6, 6, 6)
        offline.setSpacing(4)
        offline.setColumnStretch(1, 1)

        self.edit_datfile = QtWidgets.QLineEdit()
        self.edit_datfile.setPlaceholderText("Select a local .dat file to replay")
        self.edit_datfile.editingFinished.connect(self._save_settings)
        self.btn_browse_dat = QtWidgets.QPushButton("Browse...")
        self.btn_browse_dat.clicked.connect(self._browse_dat_file)
        offline.addWidget(QtWidgets.QLabel("DAT file"), 0, 0)
        offline.addWidget(self.edit_datfile, 0, 1)
        offline.addWidget(self.btn_browse_dat, 0, 2)

        # Keep this compatibility label for the existing filename update path,
        # but show the active filename only once in Live Status.
        self.lab_current_dat = QtWidgets.QLabel("-", self.parent)
        self.lab_current_dat.hide()
        self.btn_process = QtWidgets.QPushButton("Process DAT")
        self.btn_process.clicked.connect(self.process_dat)
        offline.addWidget(self.btn_process, 1, 1, 1, 2)
        left_column.addWidget(offline_group)

        # ---------------- noise scan ----------------
        noise_group = QtWidgets.QGroupBox("Noise Scan")
        noise_layout = QtWidgets.QVBoxLayout(noise_group)
        noise_layout.setContentsMargins(6, 6, 6, 6)
        noise_layout.setSpacing(4)
        self.noise_scan.add_button_row(noise_layout)
        left_column.addWidget(noise_group)
        left_column.addWidget(self.sma_outputs_group)
        self._build_live_status_ui(left_column)
        left_column.addStretch(1)

        status_layout = layout
        if self._status_parent_widget is not None:
            layout.addStretch(1)
            status_layout = QtWidgets.QVBoxLayout(self._status_parent_widget)
            status_layout.setSpacing(10)
        self.fpga_diagnostics = DiagnosticWidget(status_layout.parentWidget())
        status_layout.addWidget(self.fpga_diagnostics)
        status_layout.addStretch(1)

    def _build_live_status_ui(self, layout):
        # ---------------- live status ----------------
        self.live_status_group = live_group = QtWidgets.QGroupBox("Live Status")
        live_layout = QtWidgets.QVBoxLayout(live_group)

        capture_status_group = QtWidgets.QGroupBox("Capture and Throughput")
        stats = QtWidgets.QGridLayout()
        stats.setHorizontalSpacing(12)
        capture_status_group.setLayout(stats)

        self.lab_total = QtWidgets.QLabel("0")
        self.lab_lost = QtWidgets.QLabel("0")
        self.lab_bytes = QtWidgets.QLabel("0")
        self.lab_file = QtWidgets.QLabel("-")
        self.lab_file.setWordWrap(True)
        self.lab_capture_rate = QtWidgets.QLabel("0.00 MB/s | 0 packets/s")
        self.lab_decode_rate = QtWidgets.QLabel("0.00 MB/s | 0 words/s")
        self.lab_queue_backlog = QtWidgets.QLabel("0 / 0 chunks")
        self.lab_isolated_dropped = QtWidgets.QLabel("0")
        self.lab_filtered_events = QtWidgets.QLabel("0")
        self.lab_filtered_events.setToolTip("Complete events examined, including events rejected by the tube cuts.")
        self.lab_preserved_events = QtWidgets.QLabel("0")
        self.lab_filter_rejected_events = QtWidgets.QLabel("0")

        stats.addWidget(QtWidgets.QLabel("Total packets:"), 0, 0)
        stats.addWidget(self.lab_total, 0, 1)
        stats.addWidget(QtWidgets.QLabel("Lost packets:"), 1, 0)
        stats.addWidget(self.lab_lost, 1, 1)
        stats.addWidget(QtWidgets.QLabel("Buffered bytes:"), 2, 0)
        stats.addWidget(self.lab_bytes, 2, 1)
        stats.addWidget(QtWidgets.QLabel("Current file:"), 3, 0)
        stats.addWidget(self.lab_file, 3, 1)
        stats.addWidget(QtWidgets.QLabel("Capture rate:"), 6, 0)
        stats.addWidget(self.lab_capture_rate, 6, 1)
        stats.addWidget(QtWidgets.QLabel("Decode rate:"), 7, 0)
        stats.addWidget(self.lab_decode_rate, 7, 1)
        stats.addWidget(QtWidgets.QLabel("Analysis queue:"), 8, 0)
        stats.addWidget(self.lab_queue_backlog, 8, 1)
        stats.addWidget(QtWidgets.QLabel("Isolated hits removed:"), 4, 0)
        stats.addWidget(self.lab_isolated_dropped, 4, 1)
        stats.addWidget(QtWidgets.QLabel("Events filtered:"), 9, 0)
        stats.addWidget(self.lab_filtered_events, 9, 1)
        preserved_label = QtWidgets.QLabel("Damaged/incomplete events kept:")
        preserved_label.setToolTip("Events saved unchanged because filtering could not safely classify all hits.")
        stats.addWidget(preserved_label, 10, 0)
        stats.addWidget(self.lab_preserved_events, 10, 1)
        stats.addWidget(QtWidgets.QLabel("Events rejected after isolation:"), 5, 0)
        stats.addWidget(self.lab_filter_rejected_events, 5, 1)
        stats.setColumnStretch(1, 1)
        live_layout.addWidget(capture_status_group, 2)

        decoder_status_group = QtWidgets.QGroupBox("Decoder")
        dec = QtWidgets.QGridLayout()
        decoder_status_group.setLayout(dec)

        self.lab_hdr = QtWidgets.QLabel("0")
        self.lab_trl = QtWidgets.QLabel("0")
        self.lab_trg = QtWidgets.QLabel("0")
        self.lab_hit = QtWidgets.QLabel("0")
        self.lab_evbuf = QtWidgets.QLabel("0")

        self.lab_err_eid = QtWidgets.QLabel("0")
        self.lab_err_hit = QtWidgets.QLabel("0")
        self.lab_err_mtrl = QtWidgets.QLabel("0")
        self.lab_err_mhdr = QtWidgets.QLabel("0")
        self.lab_err_decode = QtWidgets.QLabel("0")
        self.lab_abort_burst = QtWidgets.QLabel("0")

        counts_form = QtWidgets.QFormLayout()
        counts_form.addRow("Headers:", self.lab_hdr)
        counts_form.addRow("Trailers:", self.lab_trl)
        counts_form.addRow("Hits:", self.lab_hit)
        counts_form.addRow("Triggers:", self.lab_trg)
        counts_form.addRow("Events buffered:", self.lab_evbuf)

        errors_form = QtWidgets.QFormLayout()
        errors_form.addRow("Err: event_id mismatch:", self.lab_err_eid)
        errors_form.addRow("Err: hit_count mismatch:", self.lab_err_hit)
        errors_form.addRow("Err: missing trailer:", self.lab_err_mtrl)
        errors_form.addRow("Err: missing header:", self.lab_err_mhdr)
        errors_form.addRow("Err: decode error:", self.lab_err_decode)

        aborts_form = QtWidgets.QFormLayout()
        aborts_form.addRow("Abort: burst:", self.lab_abort_burst)

        dec.addWidget(QtWidgets.QLabel("<b>Counts</b>"), 0, 0)
        dec.addWidget(QtWidgets.QLabel("<b>Err / Mismatch</b>"), 0, 1)
        dec.addWidget(QtWidgets.QLabel("<b>Aborts</b>"), 2, 0)
        dec.addLayout(counts_form, 1, 0)
        dec.addLayout(errors_form, 1, 1)
        dec.addLayout(aborts_form, 3, 0, 1, 2)
        dec.setColumnStretch(0, 1)
        dec.setColumnStretch(1, 1)
        live_layout.addWidget(decoder_status_group, 3)

        layout.addWidget(live_group)

    # ------------------------------------------------------------------
    # settings

    def _load_settings(self):
        self.check_remove_isolated_hits.blockSignals(True)
        self.check_remove_isolated_hits.setChecked(
            not self.settings.value("run/save_isolated_hits", True, type=bool))
        self.check_remove_isolated_hits.blockSignals(False)
        self._last_device = self.settings.value("last/last_device", "", type=str)
        # The capture filter is firmware-defined, not a user preference.
        self.settings.remove("last/last_filter")
        last_outdir = self.settings.value("last/out_dir", "", type=str)
        last_dat = self.settings.value("last/dat_file", "", type=str)
        last_rt = self.settings.value("last/rt_file", self._initial_rt_file, type=str)
        csm_number = self.settings.value("run/csm_number", "0", type=str)
        include_csm_in_filename = self.settings.value(
            "run/include_csm_in_filename",
            True,
            type=bool,
        )
        self.edit_filter.setText(DEFAULT_HIT_CAPTURE_FILTER)
        if last_outdir:
            self.edit_outdir.setText(last_outdir)
        if last_dat:
            self.edit_datfile.setText(last_dat)
        if last_rt:
            self.edit_rtfile.setText(last_rt)
        self.combo_nrt.blockSignals(True)
        nrt = self.settings.value("last/nrt", 0, type=int)
        self.combo_nrt.setCurrentIndex(max(0, self.combo_nrt.findData(nrt)))
        self.combo_nrt.blockSignals(False)
        self.check_rt_catalogue_ranges.blockSignals(True)
        self.check_rt_catalogue_ranges.setChecked(
            self.settings.value("last/rt_catalogue_ranges", True, type=bool)
        )
        self.check_rt_catalogue_ranges.blockSignals(False)
        for ml, pair in enumerate(self.rt_range_spins):
            for name, spin, default in zip(("min", "max"), pair, (0.0, 200.0)):
                spin.blockSignals(True)
                spin.setValue(self.settings.value(f"last/rt_ml{ml + 1}_{name}", default, type=float))
                spin.blockSignals(False)
        self._update_rt_range_controls()
        try:
            csm_number = max(0, min(9999, int(csm_number)))
        except Exception:
            csm_number = 0
        self.spin_csm_number.blockSignals(True)
        self.spin_csm_number.setValue(csm_number)
        self.spin_csm_number.blockSignals(False)
        self.check_include_csm_filename.blockSignals(True)
        self.check_include_csm_filename.setChecked(bool(include_csm_in_filename))
        self.check_include_csm_filename.blockSignals(False)

        self._plot_save_labels = set(self._parse_plot_save_labels(
            self.settings.value("run/plot_save_labels", "[]", type=str)
        ))
        if self.settings.contains("run/plot_live_labels"):
            self._plot_live_labels = set(self._parse_plot_save_labels(
                self.settings.value("run/plot_live_labels", "[]", type=str)
            ))

        decode_err_stop = self.settings.value("run/decode_error_stop_threshold", 1000, type=int)
        if decode_err_stop < 0:
            decode_err_stop = 1000
        self.spin_decode_err_stop.blockSignals(True)
        self.spin_decode_err_stop.setValue(int(decode_err_stop))
        self.spin_decode_err_stop.blockSignals(False)
        self._sync_decode_error_stop_threshold()

        event_buffer_min_hits = self.settings.value(
            "run/event_buffer_min_hits",
            1,
            type=int,
        )
        self.spin_event_buffer_min_hits.blockSignals(True)
        self.spin_event_buffer_min_hits.setValue(
            max(0, min(1023, int(event_buffer_min_hits)))
        )
        self.spin_event_buffer_min_hits.blockSignals(False)

        window_cycles = self.settings.value(
            "run/triggerless_window_cycles",
            20,
            type=int,
        )
        hit_threshold = self.settings.value(
            "run/triggerless_hit_threshold",
            4,
            type=int,
        )
        # Migrate the former shared hit threshold to both total-tube minima.
        fallback = TubeFilterSettings(min_tubes=max(0, min(256, hit_threshold)))
        filters = []
        for chamber in range(2):
            try:
                filters.append(TubeFilterSettings.unpack(int(self.settings.value(
                    f"run/tube_filters_chamber{chamber}", str(fallback.pack())))))
            except (ValueError, TypeError):
                print(f"[WARN] Invalid saved chamber {chamber} tube filters; using defaults")
                filters.append(fallback)
        self._set_triggerless_setting_widgets(window_cycles, tuple(filters))

        acquisition_mode = self.settings.value("run/acquisition_mode", 0, type=int)
        noise_test_mode = self.settings.value("run/noise_test_mode", 0, type=int)
        saved_profile = self.settings.value("run/mode_profile", -1, type=int)
        self._set_acquisition_mode_combo(
            acquisition_mode,
            noise_test_mode,
            preferred_profile=saved_profile,
        )

        next_run = self.settings.value("run/next_run", 1, type=int)
        if next_run < 1:
            next_run = 1
        self.spin_run.setValue(int(next_run))
        self.noise_scan.load_settings()
        self._load_trigger_settings()

    def _save_external_trigger_settings(self, editor):
        state = editor.settings_state()
        self.settings.setValue("trigger/external_editor", json.dumps(state))
        self.settings.sync()
        self._restored_external_trigger_state = state

    def _save_trigger_register(self, name, value):
        self._saved_trigger_registers[name] = int(value)
        self.settings.setValue(f"trigger/{name}", str(int(value)))
        self.settings.sync()

    def _load_trigger_settings(self):
        defaults = MiniDAQ_reg()
        for _, name, width, _ in defaults.register_table:
            if name not in PERSISTENT_TRIGGER_REGISTERS or not self.settings.contains(f"trigger/{name}"):
                continue
            try:
                value = int(self.settings.value(f"trigger/{name}"))
                low, high = defaults.value_limits(name, width)
                if not low <= value <= high:
                    raise ValueError("value out of range")
                self._saved_trigger_registers[name] = value
                for editor in self.register_editors.values():
                    editor.refresh(name, value)
                if name == "trigger_deadtime":
                    self.spin_trigger_deadtime.blockSignals(True)
                    self.spin_trigger_deadtime.setValue(value)
                    self.spin_trigger_deadtime.blockSignals(False)
                elif name == "sma_trigger_enable":
                    for bit, checkbox in enumerate(self.sma_output_checks):
                        checkbox.blockSignals(True)
                        checkbox.setChecked(bool(value & (1 << bit)))
                        checkbox.blockSignals(False)
            except (ValueError, TypeError) as exc:
                print(f"[WARN] Invalid saved {name}; using default: {exc}")
        if self.settings.contains("trigger/external_editor"):
            try:
                state = json.loads(self.settings.value("trigger/external_editor", type=str))
                for editor in self.external_editors:
                    editor.restore_settings(state)
                    editor.set_hardware_status("Restored local settings; not read from FPGA.")
                self._restored_external_trigger_state = state
            except (ValueError, TypeError, KeyError) as exc:
                print(f"[WARN] Invalid saved external trigger settings; using defaults: {exc}")
        if self._restored_external_trigger_state is None:
            for editor in self.external_editors:
                editor.set_config(DEFAULT_EDITOR_CONFIG)
                editor.set_hardware_status("Default local settings; not read from FPGA.")
            # Preserve these local defaults when the register model is bound;
            # loading the GUI does not program the FPGA.
            self._restored_external_trigger_state = self.external_triggers.settings_state()

    def _save_settings(self):
        self.settings.setValue("run/save_isolated_hits", not self.check_remove_isolated_hits.isChecked())
        device = self.current_device()
        if device and "ERROR" not in device:
            self._last_device = device
            self.settings.setValue("last/last_device", device)

        self.settings.setValue("last/out_dir", self.edit_outdir.text().strip())
        self.settings.setValue("last/dat_file", self.edit_datfile.text().strip())
        self.settings.setValue("last/rt_file", self.edit_rtfile.text().strip())
        self.settings.setValue("last/nrt", self.combo_nrt.currentData())
        self.settings.setValue("last/rt_catalogue_ranges", self.check_rt_catalogue_ranges.isChecked())
        for ml, pair in enumerate(self.rt_range_spins):
            for name, spin in zip(("min", "max"), pair):
                self.settings.setValue(f"last/rt_ml{ml + 1}_{name}", spin.value())
        self.settings.setValue("run/next_run", int(self.spin_run.value()))
        self.settings.setValue("run/csm_number", int(self.spin_csm_number.value()))
        self.settings.setValue(
            "run/include_csm_in_filename",
            bool(self.include_csm_in_filename()),
        )
        self.settings.setValue("run/plot_save_labels", json.dumps(sorted(self._plot_save_labels)))
        if self._plot_live_labels is not None:
            self.settings.setValue(
                "run/plot_live_labels",
                json.dumps(sorted(self._plot_live_labels)),
            )
        self.settings.setValue("run/acquisition_mode", int(self.selected_acquisition_mode()))
        self.settings.setValue("run/noise_test_mode", int(self.selected_noise_test_mode()))
        self.settings.setValue("run/mode_profile", int(self.selected_run_profile()))
        self.settings.setValue("run/decode_error_stop_threshold", int(self.decode_error_stop_threshold()))
        self.settings.setValue(
            "run/event_buffer_min_hits",
            int(self.event_buffer_min_hits()),
        )
        self.settings.setValue(
            "run/triggerless_window_cycles",
            int(self.triggerless_window_cycles()),
        )
        for chamber, cfg in enumerate(self.triggerless_filter_settings()):
            self.settings.setValue(f"run/tube_filters_chamber{chamber}", str(cfg.pack()))
        self.settings.sync()

    def _on_run_changed(self, _val: int):
        self._save_settings()

    @staticmethod
    def _parse_plot_save_labels(raw):
        if raw is None:
            return []
        if isinstance(raw, (list, tuple, set)):
            return [str(v) for v in raw if str(v)]
        text = str(raw or "").strip()
        if not text:
            return []
        try:
            values = json.loads(text)
            if isinstance(values, list):
                return [str(v) for v in values if str(v)]
        except Exception:
            pass
        return [part for part in text.split("|") if part]

    def run_plot_save_labels(self):
        return set(self._plot_save_labels)

    def run_plot_live_labels(self):
        if self._plot_live_labels is None:
            return set(self._available_run_plot_labels())
        return set(self._plot_live_labels)

    def should_save_all_plots(self) -> bool:
        return bool(self._plot_save_labels)

    def set_run_plot_saving_control(
        self,
        *,
        plot_labels_callback=None,
        selection_callback=None,
        save_previous_callback=None,
        can_save_previous_callback=None,
    ):
        self._plot_labels_callback = plot_labels_callback
        self._plot_selection_callback = selection_callback
        self._plot_save_previous_callback = save_previous_callback
        self._plot_can_save_previous_callback = can_save_previous_callback
        if self._plot_live_labels is None:
            self._plot_live_labels = set(self._available_run_plot_labels())
        self._apply_plot_selection()

    def _apply_plot_selection(self):
        callback = self._plot_selection_callback
        if not callable(callback):
            return
        try:
            callback(
                set(self.run_plot_live_labels()),
                set(self.run_plot_save_labels()),
            )
        except Exception as error:
            print(f"[WARN] Failed to apply plot display/save selection: {error}")

    def _available_run_plot_labels(self):
        callback = self._plot_labels_callback
        if not callable(callback):
            return []
        try:
            labels = list(callback() or [])
        except Exception as e:
            print(f"[WARN] Failed to collect plot-save labels: {e}")
            return []
        return [str(label) for label in labels if str(label)]

    def _open_run_plot_saving_dialog(self):
        labels = self._available_run_plot_labels()
        if not labels:
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Run Plot Saving",
                "No plot tabs are available for saving.",
            )
            return

        dialog = pop_run_plot_saving(
            labels,
            selected_live_labels=self.run_plot_live_labels(),
            selected_save_labels=self._plot_save_labels,
            save_previous_callback=self._save_previous_run_plots,
            can_save_previous_callback=self._can_save_previous_run_plots,
            parent=self.parent,
        )
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self._plot_live_labels = set(dialog.live_labels())
            self._plot_save_labels = set(dialog.save_labels())
            self._apply_plot_selection()
            self._save_settings()

    def _can_save_previous_run_plots(self):
        callback = self._plot_can_save_previous_callback
        if not callable(callback):
            return False
        try:
            return bool(callback())
        except Exception:
            return False

    def _save_previous_run_plots(self, labels):
        selected = set(str(label) for label in (labels or []) if str(label))
        self._plot_save_labels = selected
        self._apply_plot_selection()
        self._save_settings()
        callback = self._plot_save_previous_callback
        if not callable(callback):
            print("[WARN] Previous run plot saving is not connected.")
            return False
        return bool(callback(sorted(selected)))

    def decode_error_stop_threshold(self) -> int:
        spin = getattr(self, "spin_decode_err_stop", None)
        return int(spin.value()) if spin is not None else 1000

    def event_buffer_min_hits(self) -> int:
        spin = getattr(self, "spin_event_buffer_min_hits", None)
        return int(spin.value()) if spin is not None else 0

    def triggerless_window_cycles(self) -> int:
        spin = getattr(self, "spin_triggerless_window_cycles", None)
        value = int(spin.value()) if spin is not None else 20
        return max(
            MIN_TRIGGERLESS_WINDOW_CYCLES,
            min(MAX_TRIGGERLESS_WINDOW_CYCLES, value),
        )

    def triggerless_filter_settings(self):
        return self.tube_filters.values()

    def _set_triggerless_setting_widgets(
        self,
        window_cycles: int,
        filters,
    ) -> None:
        window_cycles = max(
            MIN_TRIGGERLESS_WINDOW_CYCLES,
            min(MAX_TRIGGERLESS_WINDOW_CYCLES, int(window_cycles)),
        )
        self._updating_triggerless_settings = True
        try:
            spin = self.spin_triggerless_window_cycles
            spin.blockSignals(True)
            spin.setValue(window_cycles)
            spin.blockSignals(False)
            self.tube_filters.set_values(filters)
        finally:
            self._updating_triggerless_settings = False

    def _set_minidaq_triggerless_settings(
        self,
        window_cycles: int,
        filters,
    ):
        callback = self._daq_set_triggerless_settings_callback
        if not callable(callback):
            return int(window_cycles), tuple(filters)
        values = callback(int(window_cycles), tuple(filters))
        try:
            window_cycles, filters = values
            if len(filters) != 2 or not all(isinstance(cfg, TubeFilterSettings) for cfg in filters):
                raise ValueError("Expected two chamber settings")
        except Exception as exc:
            raise RuntimeError(
                "MiniDAQ triggerless-settings callback returned invalid values"
            ) from exc
        return int(window_cycles), tuple(filters)

    def _restore_triggerless_settings_from_hardware_cache(self) -> None:
        callback = self._daq_triggerless_settings_callback
        if not callable(callback):
            return
        try:
            window_cycles, filters = callback()
            self._set_triggerless_setting_widgets(
                window_cycles,
                filters,
            )
        except Exception as exc:
            print(
                "[WARN] Failed to restore cached MiniDAQ triggerless settings: "
                f"{exc}"
            )

    def _apply_triggerless_settings(self):
        try:
            values = self._set_minidaq_triggerless_settings(
                self.triggerless_window_cycles(),
                self.triggerless_filter_settings(),
            )
        except Exception as exc:
            print(f"[ERROR] Failed to set MiniDAQ triggerless settings: {exc}")
            self._restore_triggerless_settings_from_hardware_cache()
            return None
        self._set_triggerless_setting_widgets(*values)
        return values

    def bind_minidaq_registers(self, registers):
        """Bind all mode panels to one model; saved filter/window drafts win at startup."""
        self._minidaq_registers = registers
        for name, value in self._saved_trigger_registers.items():
            registers.set_named_value(name, value)
        registers.set_named_value("window_cycles", self.triggerless_window_cycles())
        registers.set_tube_filter_settings(self.triggerless_filter_settings())
        registers.register_changed.connect(self._on_minidaq_register_changed)
        self.external_triggers.set_config(next(reg[3] for reg in registers.register_table
                                               if reg[1] == "external_trigger_config"))
        self.spin_trigger_deadtime.blockSignals(True)
        self.spin_trigger_deadtime.setValue(next(reg[3] for reg in registers.register_table
                                                if reg[1] == "trigger_deadtime"))
        self.spin_trigger_deadtime.blockSignals(False)
        for _, name, _, value in registers.register_table:
            for editor in self.register_editors.values():
                editor.refresh(name, value)
            if name == "external_trigger_config":
                for editor in self.external_editors:
                    editor.set_config(value)
        if self._restored_external_trigger_state is not None:
            for editor in self.external_editors:
                editor.restore_settings(self._restored_external_trigger_state)
                editor.set_hardware_status("Restored local settings; not read from FPGA.")
        self._refresh_sma_output_checks()
        self._update_mode_settings()

    def _refresh_sma_output_checks(self):
        registers = self._minidaq_registers
        mask = next((reg[3] for reg in registers.register_table
                     if reg[1] == "sma_trigger_enable"), 15) if registers is not None else 15
        for bit, checkbox in enumerate(self.sma_output_checks):
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(mask & (1 << bit)))
            checkbox.blockSignals(False)

    def _update_mode_settings(self):
        selected = self.mode_pages[self.selected_run_profile()]
        for page in self.mode_pages.values():
            page.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                               QtWidgets.QSizePolicy.Preferred if page is selected
                               else QtWidgets.QSizePolicy.Ignored)
        self.mode_settings_stack.setCurrentWidget(selected)
        self.mode_settings_stack.updateGeometry()
        running = self._hardware_run_active or (self._minidaq_registers is not None and any(
            reg[1] == "run_enable" and reg[3] for reg in self._minidaq_registers.register_table))
        self.spin_triggerless_window_cycles.setEnabled(not running)
        self.tube_filters.setEnabled(not running)
        self.read_filters_button.setEnabled(not running and callable(self._read_acquisition_registers_callback))
        for editor in self.external_editors:
            editor.setEnabled(not running and callable(self._configure_external_trigger_callback))
        for editor in self.register_editors.values():
            editor.set_available(callable(self._set_acquisition_register_callback), running)
        self.spin_trigger_deadtime.setEnabled(not running and callable(self._configure_external_trigger_callback))
        for checkbox in self.sma_output_checks:
            checkbox.setEnabled(callable(self._set_sma_output_callback))

    def _on_trigger_deadtime_changed(self, value):
        if callable(self._set_acquisition_register_callback):
            self._write_acquisition_register("trigger_deadtime", value)
        elif callable(self._configure_external_trigger_callback):
            self._apply_external_triggers()
        self._save_trigger_register("trigger_deadtime", self.spin_trigger_deadtime.value())

    def _apply_external_triggers(self):
        return self._apply_external_editor(self.external_triggers)

    def _apply_external_editor(self, editor):
        try:
            if not callable(self._configure_external_trigger_callback):
                raise RuntimeError("External trigger controls are not connected")
            self._applying_external_trigger = True
            self._configure_external_trigger_callback(
                editor.config(), deadtime=self.spin_trigger_deadtime.value() if editor is self.external_triggers else None)
            config = editor.config()
            for other in self.external_editors:
                other.set_hardware_status("")
                if other is not editor:
                    other.set_config(config)
            self._unsupported_trigger_warning_shown = False
            return True
        except UnsupportedTriggerFirmwareError as exc:
            # Keep local drafts separate from the last verified register cache.
            config = editor.config()
            for other in self.external_editors:
                if other is not editor:
                    other.set_config(config)
                other.set_hardware_status("Local settings only: FPGA firmware lacks programmable trigger support.")
            if not self._unsupported_trigger_warning_shown:
                self._unsupported_trigger_warning_shown = True
                QtWidgets.QMessageBox.warning(self.parent, "External trigger configuration unavailable", str(exc))
            return True  # Accept the GUI edit without claiming a hardware update.
        except Exception as exc:
            if self._minidaq_registers is not None:
                cached = next(r[3] for r in self._minidaq_registers.register_table
                              if r[1] == "external_trigger_config")
                editor.set_config(cached)
            QtWidgets.QMessageBox.warning(self.parent, "External trigger configuration failed", str(exc))
            return False
        finally:
            self._applying_external_trigger = False

    def _read_external_triggers(self):
        try:
            if not callable(self._read_external_trigger_callback):
                raise RuntimeError("External trigger controls are not connected")
            config = self._read_external_trigger_callback()
            for editor in self.external_editors:
                editor.set_config(config)
                editor.set_hardware_status("")
            self._unsupported_trigger_warning_shown = False
            self._save_external_trigger_settings(self.external_triggers)
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S %Z')}] Trigger settings updated from FPGA: "
                f"enabled=0x{config & 0xF:X}, active-low=0x{(config >> 4) & 0xF:X}, "
                f"LUT=0x{config >> 8:04X}, dead time={self.spin_trigger_deadtime.value()} x 25 ns, "
                f"SMA enables=0x{sum(int(w.isChecked()) << bit for bit, w in enumerate(self.sma_output_checks)):X}"
            )
        except Exception as exc:
            print(f"[ERROR] Trigger settings read from FPGA failed: {exc}")
            QtWidgets.QMessageBox.warning(self.parent, "External trigger readback failed", str(exc))

    def _set_sma_output(self, bit, enabled):
        try:
            if not callable(self._set_sma_output_callback):
                raise RuntimeError("SMA output controls are not connected")
            self._set_sma_output_callback(bit, enabled)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.parent, "SMA output gate failed", str(exc))
        finally:
            self._refresh_sma_output_checks()

    def _on_minidaq_register_changed(self, name, _value):
        if name in PERSISTENT_TRIGGER_REGISTERS:
            self._save_trigger_register(name, _value)
        for editor in self.register_editors.values():
            editor.refresh(name, _value)
        if name == "trigger_deadtime":
            self.spin_trigger_deadtime.blockSignals(True)
            self.spin_trigger_deadtime.setValue(_value)
            self.spin_trigger_deadtime.blockSignals(False)
        if name == "external_trigger_config" and not self._applying_external_trigger:
            for editor in self.external_editors:
                editor.set_config(_value)
            self._save_external_trigger_settings(self.external_triggers)
        elif name == "sma_trigger_enable":
            self._refresh_sma_output_checks()
        elif name == "run_enable":
            self._update_mode_settings()
        if self._updating_triggerless_settings:
            return
        if name in ("window_cycles", "run_enable") or name.startswith("tube_filters_chamber"):
            registers = self._minidaq_registers
            window = next(reg[3] for reg in registers.register_table if reg[1] == "window_cycles")
            self._set_triggerless_setting_widgets(window, registers.tube_filter_settings())
            self._update_mode_settings()
            self._save_settings()

    def _write_acquisition_register(self, name, value):
        try:
            if not callable(self._set_acquisition_register_callback):
                raise RuntimeError("Acquisition controls are not connected")
            self._set_acquisition_register_callback(name, value)
        except Exception as exc:
            if self._minidaq_registers is not None:
                cached = next(r[3] for r in self._minidaq_registers.register_table if r[1] == name)
                for editor in self.register_editors.values():
                    editor.refresh(name, cached)
                if name == "trigger_deadtime":
                    self.spin_trigger_deadtime.blockSignals(True)
                    self.spin_trigger_deadtime.setValue(cached)
                    self.spin_trigger_deadtime.blockSignals(False)
            QtWidgets.QMessageBox.warning(self.parent, "Acquisition setting failed", str(exc))

    def _read_acquisition_registers(self, names):
        try:
            if not callable(self._read_acquisition_registers_callback):
                raise RuntimeError("Acquisition readback is not connected")
            self._read_acquisition_registers_callback(names)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.parent, "Acquisition readback failed", str(exc))

    def _on_triggerless_settings_changed(self, *_args) -> None:
        if self._updating_triggerless_settings:
            return
        registers = self._minidaq_registers
        if registers is not None:
            if self._hardware_run_active or any(
                reg[1] == "run_enable" and reg[3] for reg in registers.register_table
            ):
                self._on_minidaq_register_changed("run_enable", 1)
                return
            self._updating_triggerless_settings = True
            try:
                registers.set_named_value("window_cycles", self.triggerless_window_cycles())
                registers.set_tube_filter_settings(self.triggerless_filter_settings())
            finally:
                self._updating_triggerless_settings = False
        self._save_settings()

    def _sync_decode_error_stop_threshold(self) -> int:
        threshold = int(self.decode_error_stop_threshold())
        if self.backend is not None:
            if hasattr(self.backend, "decode_error_stop_threshold"):
                self.backend.decode_error_stop_threshold = threshold
            dec_thread = getattr(self.backend, "_dec_thread", None)
            if dec_thread is not None and hasattr(dec_thread, "decode_error_stop_threshold"):
                dec_thread.decode_error_stop_threshold = threshold
        return threshold

    def _on_decode_error_stop_changed(self, _val: int):
        self._sync_decode_error_stop_threshold()
        self._save_settings()

    def selected_acquisition_mode(self) -> int:
        return self.selected_run_modes()[0]

    def selected_noise_test_mode(self) -> int:
        return self.selected_run_modes()[1]

    def selected_run_profile(self) -> int:
        combo = getattr(self, "combo_acquisition_mode", None)
        try:
            profile = int(combo.currentData()) if combo is not None else 0
        except Exception:
            profile = RUN_PROFILE_TRIGGERED_EXTERNAL
        if profile not in RUN_PROFILE_SETTINGS:
            return RUN_PROFILE_TRIGGERED_EXTERNAL
        return profile

    def selected_run_modes(self):
        acquisition_mode, noise_test_mode, _en_int_trigger, _enable_hit = (
            RUN_PROFILE_SETTINGS[self.selected_run_profile()]
        )
        return acquisition_mode, noise_test_mode

    def selected_trigger_controls(self):
        _acquisition_mode, _noise_test_mode, en_int_trigger, enable_hit = (
            RUN_PROFILE_SETTINGS[self.selected_run_profile()]
        )
        return en_int_trigger, enable_hit

    @staticmethod
    def _run_mode_profile(
        acquisition_mode: int,
        noise_test_mode: int,
        en_int_trigger=None,
        enable_hit=None,
    ) -> int:
        acquisition_mode = 1 if int(acquisition_mode) == 1 else 0
        noise_test_mode = max(0, min(2, int(noise_test_mode)))
        if acquisition_mode == 0:
            if int(en_int_trigger or 0) == 1 and int(enable_hit or 0) == 1:
                return RUN_PROFILE_TRIGGERED_INTERNAL
            return RUN_PROFILE_TRIGGERED_EXTERNAL
        return {
            0: RUN_PROFILE_TRIGGERLESS,
            1: RUN_PROFILE_TRIGGERLESS_NOISE_RAW,
            2: RUN_PROFILE_TRIGGERLESS_NOISE_COUNTER,
        }[noise_test_mode]

    def _set_acquisition_mode_combo(
        self,
        acquisition_mode: int,
        noise_test_mode: int = 0,
        *,
        preferred_profile=None,
    ) -> None:
        combo = getattr(self, "combo_acquisition_mode", None)
        if combo is None:
            return
        profile = None
        try:
            candidate = int(preferred_profile)
        except Exception:
            candidate = -1
        if candidate in RUN_PROFILE_SETTINGS:
            candidate_modes = RUN_PROFILE_SETTINGS[candidate][:2]
            requested_modes = (
                1 if int(acquisition_mode) == 1 else 0,
                max(0, min(2, int(noise_test_mode))),
            )
            if requested_modes[0] == 0:
                requested_modes = (0, 0)
            if candidate_modes == requested_modes:
                profile = candidate
        if profile is None:
            profile = self._run_mode_profile(acquisition_mode, noise_test_mode)
        index = combo.findData(profile)
        if index < 0:
            return
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)
        self._applied_run_profile = profile
        self._update_mode_settings()
        self._update_isolated_hit_control()

    def _update_isolated_hit_control(self):
        self.check_remove_isolated_hits.setEnabled(
            self.selected_run_modes() == (1, 0) and not self._hardware_run_active
            and self.btn_start.isEnabled())

    def save_isolated_hits(self):
        return self.selected_run_modes() != (1, 0) or not self.check_remove_isolated_hits.isChecked()

    def _on_acquisition_mode_changed(self, _index: int) -> None:
        selected_profile = self.selected_run_profile()
        acquisition_mode, noise_test_mode = self.selected_run_modes()
        en_int_trigger, enable_hit = self.selected_trigger_controls()
        previous_profile = self._applied_run_profile
        try:
            applied_modes = self._set_minidaq_run_modes(
                acquisition_mode,
                noise_test_mode,
                en_int_trigger=en_int_trigger,
                enable_hit=enable_hit,
            )
        except Exception as e:
            print(
                "[ERROR] Failed to set run modes "
                f"acquisition_mode={acquisition_mode}, noise_test_mode={noise_test_mode}, "
                f"en_int_trigger={en_int_trigger}, enable_hit={enable_hit}: {e}"
            )
            previous = RUN_PROFILE_SETTINGS.get(
                previous_profile,
                RUN_PROFILE_SETTINGS[RUN_PROFILE_TRIGGERED_EXTERNAL],
            )
            self._set_acquisition_mode_combo(
                previous[0],
                previous[1],
                preferred_profile=previous_profile,
            )
            self._save_settings()
            return

        self._set_acquisition_mode_combo(
            *applied_modes,
            preferred_profile=selected_profile,
        )
        if self.backend is not None:
            try:
                if hasattr(self.backend, "set_acquisition_mode"):
                    self.backend.set_acquisition_mode(applied_modes[0])
                if hasattr(self.backend, "set_noise_test_mode"):
                    self.backend.set_noise_test_mode(applied_modes[1])
            except Exception as e:
                print(f"[WARN] Failed to update decoder run modes {applied_modes}: {e}")
        self._save_settings()

    # ------------------------------------------------------------------
    # devices

    def refresh_devices(self):
        self.refresh_ethernet_devices()

    def refresh_ethernet_devices(self):
        self.combo_iface.blockSignals(True)
        self.combo_iface.clear()

        try:
            devs = pcapy.findalldevs()
            labels = list(devs)
            if sys.platform == "win32":
                # Show "Ethernet 3 - adapter (MAC)"; the item data stays the NPF name.
                import win_pcap
                labels = [win_pcap.describe_device(d) for d in devs]
        except Exception as e:
            self.combo_iface.addItem("ERROR listing devices")
            self._ethernet_device_name = "ERROR listing devices"
            self.combo_iface.blockSignals(False)
            print(f"[ERROR] listing capture devices failed: {repr(e)}")
            return

        for label, d in zip(labels, devs):
            self.combo_iface.addItem(label, d)

        if devs:
            if self._last_device and self._last_device in devs:
                self.combo_iface.setCurrentIndex(devs.index(self._last_device))
            else:
                pick = next((d for d in devs if d != "lo"), devs[0])
                self.combo_iface.setCurrentIndex(devs.index(pick))

        self.combo_iface.blockSignals(False)
        self._ethernet_device_name = self._combo_device()

    def _combo_device(self) -> str:
        data = self.combo_iface.currentData()
        return str(data if data else self.combo_iface.currentText()).strip()

    def current_device(self) -> str:
        # Hardware workers must not read a QWidget from a background thread.
        return self._ethernet_device_name

    def _on_device_changed(self, _idx: int):
        self._ethernet_device_name = self._combo_device()
        dev = self.current_device()
        if dev and "ERROR" not in dev:
            self._last_device = dev
            self._save_settings()


    def _dialog_start_dir(self, path_text: str = "") -> str:
        path = os.path.expanduser((path_text or "").strip())
        if path and os.path.isdir(path):
            return path
        if path:
            parent = os.path.dirname(path)
            if parent and os.path.isdir(parent):
                return parent
        return os.getcwd()

    def _browse_output_dir(self):
        start_dir = self._dialog_start_dir(self.edit_outdir.text())
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent,
            "Select output directory",
            start_dir,
        )
        if not path:
            return
        self.edit_outdir.setText(path)
        self._save_settings()

    def _browse_dat_file(self):
        start_dir = self._dialog_start_dir(self.edit_datfile.text() or self.edit_outdir.text())
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.parent,
            "Select DAT file",
            start_dir,
            "DAT files (*.dat);;All files (*)",
        )
        if not path:
            return
        self.edit_datfile.setText(path)
        self._save_settings()

    def _browse_rt_file(self):
        start_dir = self._dialog_start_dir(self.edit_rtfile.text() or self.edit_outdir.text())
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.parent,
            "Select RT file",
            start_dir,
            "RT calibrations (*.root *.txt);;ROOT files (*.root);;Coefficient TXT files (*.txt);;All files (*)",
        )
        if not path:
            return
        self.edit_rtfile.setText(path)
        self._save_settings()

    def _set_current_dat_name(self, filename: str):
        name = os.path.basename((filename or "").strip()) or "-"
        self.lab_current_dat.setText(name)
        self.lab_file.setText(name)

    def _apply_rt_selection(self) -> bool:
        if getattr(self, "_geometry_rt_managed", False):
            return True
        if self._rt_apply_callback is None:
            return True
        rt_path = self.edit_rtfile.text().strip()
        time_ranges = None if self.check_rt_catalogue_ranges.isChecked() else [
            [spin.value() for spin in pair] for pair in self.rt_range_spins
        ]
        ok = bool(self._rt_apply_callback(
            rt_path, nrt=self.combo_nrt.currentData() or None, time_ranges=time_ranges,
        ))
        if not ok:
            print("[ERROR] Failed to apply RT file selection.")
            self.lab_rt_status.setText("RT selection failed; previous calibration retained. See the log for details.")
        return ok

    def set_rt_summary(self, rt):
        if rt is None:
            self.lab_rt_status.setText("RT disabled.")
            return
        ranges = "; ".join(
            f"ML{ml + 1}: {lo:g}–{hi:g} ns" for ml, (lo, hi) in enumerate(rt.time_ranges)
        )
        self.lab_rt_status.setText(f"Loaded {os.path.basename(rt.file_path)} — NRT={rt.nrt}; {ranges}")
        for pair, values in zip(self.rt_range_spins, rt.time_ranges):
            for spin, value in zip(pair, values):
                spin.blockSignals(True)
                spin.setValue(float(value))
                spin.blockSignals(False)
        self._save_settings()

    def _update_rt_range_controls(self):
        manual = not self.check_rt_catalogue_ranges.isChecked()
        self.rt_ranges_widget.setVisible(manual)
        for ml, pair in enumerate(self.rt_range_spins):
            for spin in pair:
                spin.setEnabled(manual and (ml == 0 or self.combo_nrt.currentData() != 1))

    def _rt_options_changed(self):
        self._update_rt_range_controls()
        self._save_settings()

    # ------------------------------------------------------------------
    # noise scan

    def set_noise_scan_control(
        self,
        *,
        selected_mezz_callback=None,
        active_channels_callback=None,
        disabled_channels_callback=None,
        configure_threshold_callback=None,
        configure_hyst_callback=None,
        minidaq_setup_callback=None,
    ):
        self._selected_mezz_callback = selected_mezz_callback
        self._disabled_channels_callback = disabled_channels_callback
        self.noise_scan.set_control(
            selected_mezz_callback=selected_mezz_callback,
            active_channels_callback=active_channels_callback,
            disabled_channels_callback=disabled_channels_callback,
            configure_threshold_callback=configure_threshold_callback,
            configure_hyst_callback=configure_hyst_callback,
            minidaq_setup_callback=minidaq_setup_callback,
        )

    def _selected_mezz_for_run(self):
        callback = self._selected_mezz_callback
        if not callable(callback):
            return []
        try:
            selected = callback() or []
        except Exception as e:
            print(f"[WARN] Failed to read selected mezz for run artifacts: {e}")
            return []

        out = []
        for item in selected:
            try:
                which_csm, mezz = item
                out.append((int(which_csm), int(mezz)))
            except Exception:
                continue
        return out

    def _disabled_channels_for_run(self, selected_mezz=None):
        callback = self._disabled_channels_callback
        if not callable(callback):
            return []
        if selected_mezz is None:
            selected_mezz = self._selected_mezz_for_run()
        try:
            disabled = callback(selected_mezz) or []
        except TypeError:
            try:
                disabled = callback() or []
            except Exception as e:
                print(f"[WARN] Failed to read disabled channels for run artifacts: {e}")
                return []
        except Exception as e:
            print(f"[WARN] Failed to read disabled channels for run artifacts: {e}")
            return []

        try:
            return list(disabled)
        except Exception:
            return []

    def set_filename_prefix_control(self, *, asd_main_thr_callback=None):
        self._asd_main_thr_callback = asd_main_thr_callback

    def set_daq_run_control(
        self,
        preflight_callback=None,
        start_callback=None,
        stop_callback=None,
        set_modes_callback=None,
        set_mode_callback=None,
        mode_callback=None,
        cached_mode_callback=None,
        noise_test_mode_callback=None,
        set_triggerless_settings_callback=None,
        triggerless_settings_callback=None,
        diagnostic_snapshot_callback=None,
        configure_external_trigger_callback=None,
        read_external_trigger_callback=None,
        set_sma_output_callback=None,
        set_acquisition_register_callback=None,
        read_acquisition_registers_callback=None,
    ):
        self._daq_preflight_callback = preflight_callback
        self._daq_start_callback = start_callback
        self._daq_stop_callback = stop_callback
        self._daq_set_modes_callback = set_modes_callback
        self._daq_set_mode_callback = set_mode_callback
        self._daq_mode_callback = mode_callback
        self._daq_cached_mode_callback = cached_mode_callback
        self._daq_noise_test_mode_callback = noise_test_mode_callback
        self._daq_set_triggerless_settings_callback = (
            set_triggerless_settings_callback
        )
        self._daq_triggerless_settings_callback = triggerless_settings_callback
        self._diagnostic_snapshot_callback = diagnostic_snapshot_callback
        self._configure_external_trigger_callback = configure_external_trigger_callback
        self._read_external_trigger_callback = read_external_trigger_callback
        self._set_sma_output_callback = set_sma_output_callback
        self._set_acquisition_register_callback = set_acquisition_register_callback
        self._read_acquisition_registers_callback = read_acquisition_registers_callback
        self._update_mode_settings()

    @staticmethod
    def _read_acquisition_mode(callback, source: str) -> int:
        if not callable(callback):
            return 0
        try:
            return 1 if int(callback()) == 1 else 0
        except Exception as e:
            print(f"[WARN] Failed to read acquisition_mode from {source}; using triggered mode: {e}")
            return 0

    def _current_acquisition_mode(self) -> int:
        return self._read_acquisition_mode(self._daq_cached_mode_callback, "cache")

    def _inquire_acquisition_mode(self) -> int:
        return self._read_acquisition_mode(self._daq_mode_callback, "FPGA")

    def _set_minidaq_run_modes(
        self,
        acquisition_mode: int,
        noise_test_mode: int,
        *,
        en_int_trigger=None,
        enable_hit=None,
    ):
        acquisition_mode = 1 if int(acquisition_mode) == 1 else 0
        noise_test_mode = max(0, min(2, int(noise_test_mode)))
        if acquisition_mode == 0:
            noise_test_mode = 0

        if callable(self._daq_set_modes_callback):
            values = self._daq_set_modes_callback(
                acquisition_mode,
                noise_test_mode,
                en_int_trigger=en_int_trigger,
                enable_hit=enable_hit,
            )
            try:
                acquisition_mode, noise_test_mode = values
            except Exception:
                pass
        elif callable(self._daq_set_mode_callback):
            acquisition_mode = 1 if int(self._daq_set_mode_callback(acquisition_mode)) == 1 else 0
        return acquisition_mode, noise_test_mode

    def _run_daq_preflight(self) -> bool:
        if not callable(self._daq_preflight_callback):
            return True
        try:
            return self._daq_preflight_callback() is not False
        except Exception as e:
            print(f"[ERROR] MiniDAQ DAQ-start validation failed: {e}")
            return False

    def _apply_selected_run_modes(self):
        selected_profile = self.selected_run_profile()
        selected_modes = self.selected_run_modes()
        en_int_trigger, enable_hit = self.selected_trigger_controls()
        try:
            self._set_minidaq_run_modes(
                *selected_modes,
                en_int_trigger=en_int_trigger,
                enable_hit=enable_hit,
            )
        except Exception as e:
            print(
                "[ERROR] Failed to set run modes "
                f"acquisition_mode={selected_modes[0]}, noise_test_mode={selected_modes[1]}, "
                f"en_int_trigger={en_int_trigger}, enable_hit={enable_hit}: {e}"
            )
            return None

        confirmed_acquisition_mode = selected_modes[0]
        if callable(self._daq_mode_callback):
            confirmed_acquisition_mode = self._inquire_acquisition_mode()
        confirmed_modes = (confirmed_acquisition_mode, self._current_noise_test_mode())
        self._set_acquisition_mode_combo(
            *confirmed_modes,
            preferred_profile=selected_profile,
        )

        if confirmed_modes != selected_modes:
            print(
                "[WARN] Run-mode readback differs from selection: "
                f"selected={selected_modes}, readback={confirmed_modes}"
            )
        return confirmed_modes

    def _current_noise_test_mode(self) -> int:
        callback = self._daq_noise_test_mode_callback
        if not callable(callback):
            return 0
        try:
            return max(0, min(2, int(callback())))
        except Exception as e:
            print(f"[WARN] Failed to read noise_test_mode from cache; using off: {e}")
            return 0

    def _start_daq_hardware(self) -> bool:
        if not callable(self._daq_start_callback):
            return True
        try:
            self._daq_start_callback()
        except Exception as e:
            print(f"[ERROR] MiniDAQ DAQ_start failed: {e}")
            return False
        self._hardware_run_active = True
        self._update_mode_settings()
        return True

    def _stop_daq_hardware(self) -> bool:
        self._pause_diagnostic_polling()
        if not self._hardware_run_active or not callable(self._daq_stop_callback):
            self._hardware_run_active = False
            self._update_mode_settings()
            self._finish_diagnostics()
            return True
        try:
            self._daq_stop_callback()
        except Exception as e:
            print(f"[ERROR] MiniDAQ DAQ_stop failed: {e}")
            self._finish_diagnostics(stop_error=str(e))
            return False
        self._hardware_run_active = False
        self._update_mode_settings()
        self._finish_diagnostics()
        return True

    def _record_diagnostics(self, phase, snapshot=None, error=None):
        recorder = getattr(self.backend, "record_fpga_diagnostics", None)
        if callable(recorder):
            recorder(phase, snapshot, self._diagnostic_baseline, error=error)

    def _begin_diagnostics(self, acquisition_mode, noise_test_mode):
        self._pause_diagnostic_polling()
        self._diagnostic_active = False
        self._diagnostic_baseline = self._diagnostic_latest = None
        self._diagnostic_last_error = None
        self._diagnostic_last_good_time = None
        self._diagnostic_continuity_error = None
        self.fpga_diagnostics.reset("Not applicable to this run mode")
        if acquisition_mode != 1 or noise_test_mode != 0:
            return
        try:
            if not callable(self._diagnostic_snapshot_callback):
                raise RuntimeError("FPGA diagnostic readback is not connected")
            snapshot = self._diagnostic_snapshot_callback()
            if snapshot.running:
                raise RuntimeError("Cannot establish diagnostic baseline while FPGA is already running")
            self._diagnostic_baseline = self._diagnostic_latest = snapshot
            self._diagnostic_active = True
            self._diagnostic_last_good_time = time.monotonic()
            self.fpga_diagnostics.show_snapshot(snapshot, snapshot)
            self._record_diagnostics("start", snapshot)
        except Exception as exc:
            self.fpga_diagnostics.reset(f"Unavailable: {exc}")
            self._record_diagnostics("start", error=str(exc))

    def _poll_diagnostics(self):
        if not self._diagnostic_active or self._diagnostic_worker is not None:
            return
        worker = SnapshotWorker(self._diagnostic_snapshot_callback, self)
        self._diagnostic_worker = worker
        worker.finished.connect(lambda: self._diagnostic_poll_finished(worker))
        worker.start()

    def _diagnostic_poll_finished(self, worker):
        if worker is not self._diagnostic_worker:
            worker.deleteLater()
            return
        self._diagnostic_worker = None
        if self._diagnostic_active:
            try:
                if worker.error:
                    raise RuntimeError(worker.error)
                snapshot = worker.snapshot
                if self._diagnostic_continuity_error:
                    raise DiagnosticContinuityError(self._diagnostic_continuity_error)
                if not snapshot.running:
                    raise RuntimeError("FPGA is no longer running")
                self.fpga_diagnostics.show_snapshot(
                    snapshot, self._diagnostic_baseline, self._diagnostic_latest)
                self._diagnostic_latest = snapshot
                self._diagnostic_last_good_time = time.monotonic()
                self._diagnostic_last_error = None
                self._record_diagnostics("latest", snapshot)
            except Exception as exc:
                if isinstance(exc, DiagnosticContinuityError):
                    self._diagnostic_continuity_error = str(exc)
                age = time.monotonic() - self._diagnostic_last_good_time
                self.fpga_diagnostics.status.setText(f"STALE ({age:.1f} s since last good snapshot): {exc}")
                if str(exc) != self._diagnostic_last_error:
                    self._record_diagnostics("latest", error=str(exc))
                    self._diagnostic_last_error = str(exc)
        worker.deleteLater()

    def _pause_diagnostic_polling(self):
        self._diagnostic_timer.stop()
        worker = self._diagnostic_worker
        self._diagnostic_worker = None
        if worker is not None:
            worker.requestInterruption()
            # The reader checks cancellation between Ethernet requests. Keep the
            # QThread parent alive if an unrelated control operation holds its lock.
            worker.wait(2000)

    def _finish_diagnostics(self, stop_error=None):
        if not self._diagnostic_active:
            return
        self._diagnostic_active = False
        try:
            if stop_error:
                raise RuntimeError(f"DAQ stop failed: {stop_error}")
            if self._diagnostic_continuity_error:
                raise DiagnosticContinuityError(self._diagnostic_continuity_error)
            snapshot = self._diagnostic_snapshot_callback()
            if snapshot.running:
                raise RuntimeError("FPGA still running; no final stopped snapshot")
            self.fpga_diagnostics.show_snapshot(
                snapshot, self._diagnostic_baseline, self._diagnostic_latest, final=True)
            self._diagnostic_latest = snapshot
            self._record_diagnostics("final", snapshot)
        except Exception as exc:
            self.fpga_diagnostics.status.setText(f"Final snapshot unavailable; displayed totals are STALE: {exc}")
            self._record_diagnostics("final", error=str(exc))

    # ------------------------------------------------------------------
    # run control

    def _allocate_run_number(self) -> int:
        run = int(self.spin_run.value())
        self.spin_run.setValue(run + 1)
        return run

    def csm_number_text(self) -> str:
        return f"{int(self.spin_csm_number.value()):04d}"

    def include_csm_in_filename(self) -> bool:
        return bool(self.check_include_csm_filename.isChecked())

    def asd_main_thr_text(self) -> str:
        value = 0
        callback = self._asd_main_thr_callback
        if callable(callback):
            try:
                value = int(callback())
            except Exception:
                value = 0
        value = max(0, min(999, int(value)))
        return f"{value:03d}"

    def filename_prefix(self) -> str:
        return f"{self.csm_filename_prefix()}vth{self.asd_main_thr_text()}_"

    def csm_filename_prefix(self) -> str:
        if not self.include_csm_in_filename():
            return ""
        return f"CSM{self.csm_number_text()}_"

    def _artifact_context(self, *, mode: str, dat_path: str, run_number=None, output_dir: str = ""):
        selected_mezz = self._selected_mezz_for_run()
        disabled_channels = self._disabled_channels_for_run(selected_mezz)
        return {
            "mode": str(mode or ""),
            "run_number": "" if run_number is None else int(run_number),
            "csm_number": self.csm_number_text(),
            "include_csm_in_filename": bool(self.include_csm_in_filename()),
            "asd_main_thr": self.asd_main_thr_text(),
            "filename_prefix": self.filename_prefix(),
            "ethernet_device": self.current_device(),
            "bpf_filter": self.edit_filter.text().strip(),
            "output_dir": str(output_dir or ""),
            "data_file": str(dat_path or ""),
            "rt_file": "" if getattr(self, "_geometry_rt_managed", False) else self.edit_rtfile.text().strip(),
            "nrt": "per geometry" if getattr(self, "_geometry_rt_managed", False) else (self.combo_nrt.currentData() or "auto"),
            "rt_catalogue_ranges": "per geometry" if getattr(self, "_geometry_rt_managed", False) else self.check_rt_catalogue_ranges.isChecked(),
            "rt_time_ranges_ns": "per geometry" if getattr(self, "_geometry_rt_managed", False) else (
                [[spin.value() for spin in pair] for pair in self.rt_range_spins]
                if not self.check_rt_catalogue_ranges.isChecked() else "catalogue"),
            "settings_file": os.path.join(os.getcwd(), SETTINGS_FILE),
            "decode_error_stop_threshold": int(self.decode_error_stop_threshold()),
            "event_buffer_min_hits": int(self.event_buffer_min_hits()),
            "save_isolated_hits": self.save_isolated_hits() if mode == "capture" else "as recorded",
            "triggerless_window_cycles": int(self.triggerless_window_cycles()),
            "tube_filters": [asdict(cfg) for cfg in self.triggerless_filter_settings()],
            "acquisition_mode": int(self.selected_acquisition_mode()),
            "noise_test_mode": int(self.selected_noise_test_mode()),
            "run_mode_profile": int(self.selected_run_profile()),
            "run_mode_label": str(self.combo_acquisition_mode.currentText()),
            "en_int_trigger": self.selected_trigger_controls()[0],
            "enable_hit": self.selected_trigger_controls()[1],
            "selected_mezz": selected_mezz,
            "selected_tdc_ids": sorted(
                int(which_csm) * 20 + int(mezz)
                for which_csm, mezz in selected_mezz
            ),
            "disabled_channels": disabled_channels,
        }

    def start(self):
        if self.backend is None:
            print("[ERROR] Backend is not initialized.")
            return

        dev = self.current_device()
        bpf = self.edit_filter.text().strip()
        out_dir = self.edit_outdir.text().strip() or os.getcwd()

        if not dev or "ERROR" in dev:
            print("[ERROR] No valid device selected.")
            return

        if not self._apply_rt_selection():
            return

        self._save_settings()
        decode_err_threshold = self._sync_decode_error_stop_threshold()
        if (
            self.selected_acquisition_mode() == 1
            and self.selected_noise_test_mode() == 0
            and self._apply_triggerless_settings() is None
        ):
            return
        run_modes = self._apply_selected_run_modes()
        if run_modes is None:
            return
        acquisition_mode, noise_test_mode = run_modes
        if hasattr(self.backend, "set_acquisition_mode"):
            self.backend.set_acquisition_mode(acquisition_mode)
        if hasattr(self.backend, "set_noise_test_mode"):
            self.backend.set_noise_test_mode(noise_test_mode)

        if not self._run_daq_preflight():
            print("[INFO] DAQ start cancelled before capture began.")
            return

        if not self.save_isolated_hits():
            try:
                from isolated_hits import neighbor_map_text
                neighbor_map_text(self.backend.geometries().values(), self.triggerless_filter_settings())
            except Exception as exc:
                print(f"[ERROR] Cannot configure isolated-hit DAT filter: {exc}")
                return

        run = self._allocate_run_number()
        out_path = self.backend.make_out_path(out_dir, run, prefix=self.filename_prefix())
        log_path = None
        if hasattr(self.backend, "prepare_run_log"):
            log_path = self.backend.prepare_run_log(
                out_path,
                context=self._artifact_context(
                    mode="capture",
                    dat_path=out_path,
                    run_number=run,
                    output_dir=out_dir,
                ),
            )

        print(f"Starting capture on {dev}")
        print(f"Filter: {bpf}")
        print(f"Output: {out_path}")
        print(f"Run folder: {os.path.dirname(out_path)}")
        if decode_err_threshold > 0:
            print(f"Decode-error stop threshold: {decode_err_threshold}")
        else:
            print("Decode-error stop threshold: disabled")
        if log_path:
            print(f"Log: {log_path}")
        print(f"Acquisition mode: {acquisition_mode}")
        print(f"Noise test mode: {noise_test_mode}")
        print(f"Run mode profile: {self.combo_acquisition_mode.currentText()}")
        en_int_trigger, enable_hit = self.selected_trigger_controls()
        if en_int_trigger is not None and enable_hit is not None:
            print(f"Internal trigger enable: {en_int_trigger}")
            print(f"Periodic trigger enable: {enable_hit}")
        print(f"Event display buffer minimum hits: {self.event_buffer_min_hits()}")
        if acquisition_mode == 1:
            print(
                "Triggerless settings: "
                f"window_cycles={self.triggerless_window_cycles()}, "
                f"tube_filters={[asdict(cfg) for cfg in self.triggerless_filter_settings()]}"
            )
        print(f"Save isolated hits in DAT: {self.save_isolated_hits()}")
        try:
            self.backend.start_capture(
                dev,
                bpf,
                out_path,
                min_event_hits=self.event_buffer_min_hits(),
                save_isolated_hits=self.save_isolated_hits(),
                tube_filters=self.triggerless_filter_settings(),
            )
        except Exception as exc:
            print(f"[ERROR] Cannot start capture: {exc}")
            return
        self._begin_diagnostics(acquisition_mode, noise_test_mode)
        if not self._start_daq_hardware():
            print("[ERROR] Stopping capture because MiniDAQ hardware start failed.")
            self.backend.stop_capture()
            return

        if self._diagnostic_active:
            self._diagnostic_timer.start()

        self._set_current_dat_name(out_path)
        self.btn_start.setEnabled(False)
        self.check_remove_isolated_hits.setEnabled(False)
        self.combo_iface.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.combo_acquisition_mode.setEnabled(False)
        self.spin_event_buffer_min_hits.setEnabled(False)
        self._update_mode_settings()
        self.btn_stop.setEnabled(True)

    def stop(self):
        self._stop_daq_hardware()

        if self.backend:
            self.backend.stop_capture()

        self.btn_start.setEnabled(True)
        self.combo_iface.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.btn_process.setEnabled(True)
        self.combo_acquisition_mode.setEnabled(True)
        self.spin_event_buffer_min_hits.setEnabled(True)
        self._update_mode_settings()
        self.btn_stop.setEnabled(False)

        self._update_isolated_hit_control()

    def process_dat(self):
        if self.backend is None:
            print("[ERROR] Backend is not initialized.")
            return

        dat_path = self.edit_datfile.text().strip()
        if not dat_path:
            print("[ERROR] Please select a .dat file first.")
            return
        if not os.path.isfile(dat_path):
            print(f"[ERROR] DAT file not found: {dat_path}")
            return

        from replay_format import replay_modes
        try:
            replay_mode, replay_noise, mode_source = replay_modes(dat_path, self.selected_run_modes())
            self.backend.set_acquisition_mode(replay_mode)
            self.backend.set_noise_test_mode(replay_noise)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"[ERROR] Cannot prepare DAT replay: {exc}")
            return

        if not self._apply_rt_selection():
            return

        self._save_settings()
        decode_err_threshold = self._sync_decode_error_stop_threshold()
        log_path = None
        if hasattr(self.backend, "prepare_replay_log"):
            log_path = self.backend.prepare_replay_log(
                dat_path,
                context=self._artifact_context(
                    mode="replay",
                    dat_path=dat_path,
                    output_dir=os.path.dirname(dat_path),
                ),
            )
        print(f"Processing DAT: {dat_path}")
        if decode_err_threshold > 0:
            print(f"Decode-error stop threshold: {decode_err_threshold}")
        else:
            print("Decode-error stop threshold: disabled")
        if log_path:
            print(f"Log: {log_path}")
        print(f"Replay decoder mode: {replay_mode}, noise mode: {replay_noise} ({mode_source})")
        print(f"Event display buffer minimum hits: {self.event_buffer_min_hits()}")
        self.backend.start_replay(
            dat_path,
            min_event_hits=self.event_buffer_min_hits(),
        )
        self.fpga_diagnostics.reset("Not sampled during DAT replay; consult the original run log")
        self._hardware_run_active = False

        self._set_current_dat_name(dat_path)
        self.btn_start.setEnabled(False)
        self.btn_process.setEnabled(False)
        self.combo_acquisition_mode.setEnabled(False)
        self.spin_event_buffer_min_hits.setEnabled(False)
        self.btn_stop.setEnabled(True)

    # ------------------------------------------------------------------
    # slots

    @QtCore.pyqtSlot(object)
    def update_isolation_stats(self, counts):
        dropped, filtered, preserved, rejected = counts
        self.lab_isolated_dropped.setText(str(dropped))
        self.lab_filtered_events.setText(str(filtered))
        self.lab_preserved_events.setText(str(preserved))
        self.lab_filter_rejected_events.setText(str(rejected))

    @QtCore.pyqtSlot(int, int, int, str)
    def update_stats(self, total_packets, lost_total, bytes_total, filename):
        self.lab_total.setText(str(total_packets))
        self.lab_lost.setText(str(lost_total))
        self.lab_bytes.setText(str(bytes_total))
        self._set_current_dat_name(filename)

    @QtCore.pyqtSlot(object)
    def _on_decode_1hz(self, snap):
        self.noise_scan.on_decode_snapshot(snap)
        capture_bytes_s = float(getattr(snap, "capture_rate_bytes_s", 0.0))
        capture_packets_s = float(getattr(snap, "capture_rate_packets_s", 0.0))
        decode_bytes_s = float(getattr(snap, "decode_rate_bytes_s", 0.0))
        decode_words_s = float(getattr(snap, "decode_rate_words_s", 0.0))
        queue_chunks = int(getattr(snap, "queue_backlog_chunks", 0))
        queue_peak = int(getattr(snap, "queue_backlog_peak_chunks", queue_chunks))
        queue_capacity = int(getattr(snap, "queue_capacity_chunks", 0))
        queue_percent = (
            100.0 * float(queue_chunks) / float(queue_capacity)
            if queue_capacity > 0
            else 0.0
        )
        self.lab_capture_rate.setText(
            f"{capture_bytes_s / 1_000_000.0:.2f} MB/s | "
            f"{capture_packets_s:,.0f} packets/s"
        )
        self.lab_decode_rate.setText(
            f"{getattr(snap, 'decode_backend', 'Python')} | "
            f"{decode_bytes_s / 1_000_000.0:.2f} MB/s | "
            f"{decode_words_s:,.0f} words/s"
        )
        self.lab_queue_backlog.setText(
            f"{queue_chunks} / {queue_capacity} chunks ({queue_percent:.1f}%) | "
            f"peak {queue_peak}"
        )
        self.lab_hdr.setText(str(int(snap.headers)))
        self.lab_trl.setText(str(int(snap.trailers)))
        self.lab_trg.setText(str(int(snap.triggers)))
        self.lab_hit.setText(str(int(snap.hits_total)))
        self.lab_evbuf.setText(str(int(snap.events_buffered)))
        self.lab_abort_burst.setText(str(int(getattr(snap, "abort_burst", 0))))

        self.lab_err_eid.setText(str(int(snap.err_event_id)))
        self.lab_err_hit.setText(str(int(snap.err_hit_count)))
        self.lab_err_mtrl.setText(str(int(snap.err_missing_trailer)))
        self.lab_err_mhdr.setText(str(int(snap.err_missing_header)))
        self.lab_err_decode.setText(
            str(int(getattr(snap, "decode_error_total", self._counter_total(getattr(snap, "decode_err_cnt", None)))))
        )

    @staticmethod
    def _counter_total(values) -> int:
        if values is None:
            return 0
        try:
            return int(values.sum())
        except Exception:
            try:
                return int(sum(int(v) for v in values))
            except Exception:
                return 0

    @QtCore.pyqtSlot()
    def _on_run_finished(self):
        if self.noise_scan.on_run_finished():
            return
        self._stop_daq_hardware()
        self.btn_start.setEnabled(True)
        self.combo_iface.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.btn_process.setEnabled(True)
        self.combo_acquisition_mode.setEnabled(True)
        self.spin_event_buffer_min_hits.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._update_isolated_hit_control()
