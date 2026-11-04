from PyQt5 import QtCore, QtGui, QtWidgets

from TDC_config_low_level_function import *
from lpgbt_register_map_v1 import LpgbtRegisterMapV1
from pop_miniDAQ_setup import pop_miniDAQ_setup
from pop_prbs import pop_prbs
from pop_link_setup import pop_link_setup
from GUI_lowlevel import *
from MiniDAQ_reg import *
from triggerless_filters import SIGNATURE, ERRORS
from fpga_diagnostics import read_snapshot
from external_trigger import apply_config as apply_trigger_config, read_config as read_trigger_config
from pop_BER import pop_BER

import os
import sys
import time
import datetime
import pandas as pd

from Worker_lpGBT import *
from Worker_load_CSM_bit_ethernet import Worker_load_CSM_bit_ethernet
from Worker_read_CSM_idcode_ethernet import (
    Worker_read_CSM_idcode_ethernet,
)


class tab_lpgbt(object):
    """docstring for rad_tab"""

    def __init__(
        self,
        MainWindow,
        eth,
        ethernet_device_callback=None,
    ):
        self.eth = eth
        self._ethernet_device_callback = ethernet_device_callback
        self._ethernet_device = ""
        self.worker_lpGBT = Worker_lpGBT(eth)
        self.lpgbt_master_addr = 117
        self.lpgbt_slave_addr = 115
        self.rxprbssel = [0]
        self._link_ready_timer = QtCore.QTimer(MainWindow)
        self._link_ready_timer.setInterval(100)
        self._link_ready_timer.setTimerType(QtCore.Qt.PreciseTimer)
        self._link_ready_timer.timeout.connect(self._poll_loaded_uplink_ready)
        self._link_ready_poll = None
        self.miniDAQ_reg = MiniDAQ_reg()
        self.default_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'bitstreams', 'lpgbtcsm_fpga_top.bit',
        )
        self.thread_load_CSM_bit = None
        self.worker_load_CSM_bit = None
        self.thread_read_CSM_idcode = None
        self.worker_read_CSM_idcode = None
        self._fpga_idcode_buttons = []
        self.setup_UI(MainWindow)

    def set_ethernet_client(self, eth):
        self.eth = eth
        if hasattr(self, "worker_lpGBT"):
            self.worker_lpGBT.eth = eth

    def setup_UI(self, MainWindow):
        sectionLayout = QtWidgets.QVBoxLayout(MainWindow)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)
        self.gridLayout.setHorizontalSpacing(12)
        self.gridLayout.setVerticalSpacing(10)
        self.uplink_status_component = []
        self.fpga_status_component = []

        def action_button(text, slot, tooltip=None):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(slot)
            if tooltip:
                button.setToolTip(tooltip)
            return button

        # ---------------- lpGBT configuration ----------------
        config_group = QtWidgets.QGroupBox("lpGBT Configuration")
        config_layout = QtWidgets.QHBoxLayout(config_group)
        config_layout.setSpacing(12)

        for which_csm in range(2):
            csm_group = QtWidgets.QGroupBox(f"CSM{which_csm}")
            csm_layout = QtWidgets.QGridLayout(csm_group)
            csm_layout.setColumnStretch(1, 1)

            master_label = QtWidgets.QLabel("Master lpGBT")
            master_load = action_button(
                "Load configuration",
                partial(self.load_lpgbt, which_csm, 1),
                f"Load the CSM{which_csm} master lpGBT configuration file.",
            )
            slave_checkbox = QtWidgets.QCheckBox("Enable slave link")
            slave_checkbox.stateChanged.connect(partial(self.slave_control, which_csm))
            slave_load = action_button(
                "Load configuration",
                partial(self.load_lpgbt, which_csm, 0),
                f"Load the CSM{which_csm} slave lpGBT configuration file.",
            )

            csm_layout.addWidget(master_label, 0, 0)
            csm_layout.addWidget(master_load, 0, 1)
            csm_layout.addWidget(slave_checkbox, 1, 0)
            csm_layout.addWidget(slave_load, 1, 1)
            config_layout.addWidget(csm_group, 1)

            self.uplink_status_component.extend((master_label, slave_checkbox))

        self.gridLayout.addWidget(config_group, 0, 0, 1, 2)

        # ---------------- link diagnostics ----------------
        diagnostics_group = QtWidgets.QGroupBox("Link Diagnostics")
        diagnostics_layout = QtWidgets.QHBoxLayout(diagnostics_group)
        update_status_button = action_button(
            "Update link status",
            self.update_status,
            "Read uplink-ready and downlink-ready status and print it in the output log.",
        )
        self.pushButton_prbs = action_button("PRBS test", self.prbs_test_dialog)
        ber_button = action_button("BER monitor", self.BER_dialog_setup)
        link_setup_button = action_button(
            "Uplink/downlink controls",
            self.link_setup_dialog,
            "Configure and read back the FPGA uplink and downlink controls.",
        )
        diagnostics_layout.addWidget(update_status_button)
        diagnostics_layout.addWidget(self.pushButton_prbs)
        diagnostics_layout.addWidget(ber_button)
        diagnostics_layout.addWidget(link_setup_button)
        self.gridLayout.addWidget(diagnostics_group, 1, 0, 1, 2)

        # ---------------- FPGA programming ----------------
        fpga_group = QtWidgets.QGroupBox("FPGA Programming")
        fpga_layout = QtWidgets.QGridLayout(fpga_group)
        fpga_layout.setColumnStretch(1, 1)
        fpga_layout.setColumnStretch(2, 1)

        self.file_path_box = QtWidgets.QLineEdit()
        self.file_path_box.setText(self.default_file)
        self.file_path_box.setPlaceholderText("Select a Xilinx .bit file")
        browse_button = action_button("Browse…", self.open_file_dialog)
        fpga_layout.addWidget(QtWidgets.QLabel("Bitstream file"), 0, 0)
        fpga_layout.addWidget(self.file_path_box, 0, 1, 1, 3)
        fpga_layout.addWidget(browse_button, 0, 4)

        idcode_tooltip = (
            "Read the CSM FPGA IDCODE through Ethernet and the selected "
            "SCA0 JTAG path to confirm that the FPGA is present."
        )
        ethernet_program_tooltip = (
            "Send 1408-byte CRC-protected chunks through the Ethernet interface "
            "selected on the Ethernet Capture tab. The FPGA performs the SCA "
            "JTAG sequence and acknowledges each completed chunk."
        )
        for which_csm, row in ((0, 1), (1, 2)):
            csm_status_label = QtWidgets.QLabel(f"CSM{which_csm}")
            fpga_layout.addWidget(csm_status_label, row, 0)
            self.fpga_status_component.append(csm_status_label)
            read_button = action_button(
                "Read IDCODE",
                partial(self.read_fpga_id, which_csm),
                idcode_tooltip,
            )
            self._fpga_idcode_buttons.append(read_button)
            ethernet_program_button = action_button(
                "Program via Ethernet",
                partial(self.load_fpga_bit_ethernet, which_csm),
                ethernet_program_tooltip,
            )
            fpga_layout.addWidget(read_button, row, 1)
            fpga_layout.addWidget(ethernet_program_button, row, 2, 1, 3)
            if which_csm == 0:
                self.pushButton_load_CSM0_bit_ethernet = ethernet_program_button
            else:
                self.pushButton_load_CSM1_bit_ethernet = ethernet_program_button

        self.ethernet_interface_label = QtWidgets.QLabel()
        self.ethernet_interface_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )
        fpga_layout.addWidget(QtWidgets.QLabel("Ethernet interface"), 3, 0)
        fpga_layout.addWidget(self.ethernet_interface_label, 3, 1, 1, 4)
        self.refresh_ethernet_device_label()

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.pushButton_cancel_CSM_bit = action_button(
            "Cancel programming",
            self.cancel_load_CSM_bit,
        )
        self.pushButton_cancel_CSM_bit.setEnabled(False)
        fpga_layout.addWidget(QtWidgets.QLabel("Progress"), 4, 0)
        fpga_layout.addWidget(self.progress_bar, 4, 1, 1, 3)
        fpga_layout.addWidget(self.pushButton_cancel_CSM_bit, 4, 4)
        self.gridLayout.addWidget(fpga_group, 2, 0, 1, 2)

        # ---------------- reset and MiniDAQ controls ----------------
        reset_group = QtWidgets.QGroupBox("Resets")
        reset_layout = QtWidgets.QGridLayout(reset_group)
        reset_layout.addWidget(
            action_button(
                "Physical uplink reset (all)",
                self.fpga_physical_rx_reset,
                "Run the shared GT Wizard physical RX-datapath reset on all uplinks.",
            ),
            0,
            0,
            1,
            2,
        )
        reset_layout.addWidget(action_button("Downlink reset", self.fpga_downlink_reset), 1, 0)
        reset_layout.addWidget(action_button("SCA reset", self.fpga_sca_reset), 1, 1)
        reset_layout.addWidget(action_button("Global reset", self.fpga_global_reset), 2, 0, 1, 2)
        self.gridLayout.addWidget(reset_group, 3, 0)

        minidaq_group = QtWidgets.QGroupBox("MiniDAQ Controls")
        minidaq_layout = QtWidgets.QVBoxLayout(minidaq_group)
        minidaq_layout.addWidget(action_button("Open MiniDAQ setup", self.miniDAQ_setup_dialog))
        minidaq_layout.addWidget(action_button("Reset MiniDAQ registers", self.MiniDAQ_reg_reset))
        self.gridLayout.addWidget(minidaq_group, 3, 1)

        self.gridLayout.setRowStretch(4, 1)
        sectionLayout.addWidget(buttonWindow)

    def _set_uplink_text_ready(self, link_index, ready):
        if 0 <= link_index < len(self.uplink_status_component):
            self.uplink_status_component[link_index].setStyleSheet(
                "background-color: cyan;" if ready else ""
            )

    def _set_fpga_status_ready(self, which_csm, ready):
        if 0 <= which_csm < len(self.fpga_status_component):
            self.fpga_status_component[which_csm].setStyleSheet(
                "background-color: cyan;" if ready else ""
            )

    def set_ethernet_device(self, device):
        self._ethernet_device = str(device or "").strip()
        self.refresh_ethernet_device_label()

    def current_ethernet_device(self):
        if self._ethernet_device_callback is not None:
            try:
                device = str(self._ethernet_device_callback() or "").strip()
            except Exception:
                device = ""
            if device:
                self._ethernet_device = device
        return self._ethernet_device

    def refresh_ethernet_device_label(self):
        if not hasattr(self, "ethernet_interface_label"):
            return
        device = self.current_ethernet_device()
        text = device
        if sys.platform == "win32" and device.startswith("\\Device\\"):
            try:
                import win_pcap
                text = win_pcap.describe_device(device)
            except Exception:
                pass
        self.ethernet_interface_label.setText(
            text if text else "No interface selected"
        )

    def BER_dialog_setup(self):
        # Create and show the TDC configuration popup window
        self.BER_popup = pop_BER(self.eth,self.miniDAQ_reg)
        self.BER_popup.exec_()  # exec_() for modal behavior, show() for non-modal

    def MiniDAQ_reg_reset(self):
        fpga_reg_reset(self.eth)
        self.miniDAQ_reg.reset()
        print("MiniDAQ registers reset to default.")

    def _set_minidaq_register(self, name, value):
        for pos, (index, reg_name, _bit_width, _old_value) in enumerate(self.miniDAQ_reg.register_table):
            if reg_name != name:
                continue
            value = self.miniDAQ_reg.sanitize_value(reg_name, value, _bit_width)
            fpga_config(self.eth, index, value_to_list(value))
            self.miniDAQ_reg.set_register_value(pos, value)
            return value
        raise KeyError(f"Unknown MiniDAQ register: {name}")

    def DAQ_start(self):
        self._set_minidaq_register("run_enable", 1)
        try:
            running = (self._read_fpga_value(1) >> 25) & 1
            if not running:
                raise RuntimeError("FPGA refused run_enable; verify geometry and filter configuration")
        except Exception:
            self.DAQ_stop()
            raise
        print("run_enable verified as 1")

    @ethernet_locked_method
    def DAQ_stop(self):
        value = self._set_minidaq_register("run_enable", 0)
        if (self._read_fpga_value(1) >> 25) & 1:
            raise RuntimeError("FPGA did not acknowledge DAQ stop")
        print(f"run_enable set to {value}")

    def read_diagnostic_snapshot(self, cancelled=None):
        # Polling must be cancellable even while another hardware operation
        # holds the shared transport. Never interleave a multi-page snapshot.
        lock = get_ethernet_lock(self.eth)
        deadline = time.monotonic() + 2.0
        while not lock.acquire(timeout=0.05):
            if cancelled is not None and cancelled():
                raise RuntimeError("FPGA diagnostic read cancelled")
            if time.monotonic() >= deadline:
                raise RuntimeError("FPGA diagnostic read deferred: control link is busy")
        try:
            return read_snapshot(
                self._read_fpga_value,
                lambda address, value: fpga_config(self.eth, address, value_to_list(value)),
                cancelled=cancelled,
            )
        finally:
            lock.release()

    def configure_tdc_chamber_map(self, enabled_mask, chamber1_mask):
        """Atomically program and verify the triggerless TDC-to-chamber map."""
        if any(
            name == "run_enable" and int(value) != 0
            for _index, name, _bit_width, value in self.miniDAQ_reg.register_table
        ):
            raise RuntimeError("Stop the DAQ before changing the TDC chamber map")

        mask40 = (1 << 40) - 1
        enabled_mask = int(enabled_mask) & mask40
        chamber1_mask = int(chamber1_mask) & enabled_mask
        packed = enabled_mask | (chamber1_mask << 40)
        packed = self._set_minidaq_register("tdc_chamber_map", packed)

        bin_str = fpga_readback(self.eth, 61)
        if not isinstance(bin_str, str) or len(bin_str) < 160:
            raise RuntimeError("Invalid TDC chamber-map readback")
        readback = int(bin_str[-80:], 2)
        if readback != packed:
            raise RuntimeError(
                "TDC chamber-map readback mismatch: "
                f"wrote=0x{packed:020x}, read=0x{readback:020x}"
            )
        print(
            "TDC chamber map set: "
            f"enabled=0x{enabled_mask:010x}, chamber1=0x{chamber1_mask:010x}"
        )
        return enabled_mask, chamber1_mask

    def _current_minidaq_register(self, register_name, default=0):
        for _index, name, _bit_width, value in self.miniDAQ_reg.register_table:
            if name == register_name:
                return int(value)
        return int(default)

    def current_acquisition_mode(self):
        return self._current_minidaq_register("acquisition_mode")

    def set_acquisition_mode(self, mode):
        return self.set_run_modes(mode, self.current_noise_test_mode())[0]

    def set_run_modes(
        self,
        acquisition_mode,
        noise_test_mode,
        *,
        en_int_trigger=None,
        enable_hit=None,
    ):
        if any(
            name == "run_enable" and int(value) != 0
            for _index, name, _bit_width, value in self.miniDAQ_reg.register_table
        ):
            raise RuntimeError("Stop the DAQ before changing run modes")

        acquisition_mode = 1 if int(acquisition_mode) == 1 else 0
        noise_test_mode = max(0, min(2, int(noise_test_mode)))
        if acquisition_mode == 0:
            noise_test_mode = 0

        register_values = []
        if en_int_trigger is not None and enable_hit is not None:
            trigger_values = (
                1 if int(en_int_trigger) else 0,
                1 if int(enable_hit) else 0,
            )
            if trigger_values == (0, 0):
                # Stop a running periodic generator before selecting the
                # external-trigger input.
                register_values.extend(
                    (("enable_hit", 0), ("en_int_trigger", 0))
                )
            else:
                # Select the internal source before enabling its generator.
                register_values.extend(
                    (
                        ("en_int_trigger", trigger_values[0]),
                        ("enable_hit", trigger_values[1]),
                    )
                )
        else:
            if en_int_trigger is not None:
                register_values.append(
                    ("en_int_trigger", 1 if int(en_int_trigger) else 0)
                )
            if enable_hit is not None:
                register_values.append(("enable_hit", 1 if int(enable_hit) else 0))
        register_values.extend(
            (
                ("acquisition_mode", acquisition_mode),
                ("noise_test_mode", noise_test_mode),
            )
        )

        previous_values = {
            name: self._current_minidaq_register(name)
            for name, _value in register_values
        }
        applied_values = {}
        try:
            for name, value in register_values:
                applied_values[name] = self._set_minidaq_register(name, value)
        except Exception:
            for name, _value in reversed(register_values):
                try:
                    self._set_minidaq_register(name, previous_values[name])
                except Exception:
                    pass
            raise
        acquisition_mode = applied_values["acquisition_mode"]
        noise_test_mode = applied_values["noise_test_mode"]
        print(
            f"run modes set: acquisition_mode={acquisition_mode}, "
            f"noise_test_mode={noise_test_mode}, "
            f"en_int_trigger={self.current_en_int_trigger()}, "
            f"enable_hit={self.current_enable_hit()}"
        )
        return acquisition_mode, noise_test_mode

    def current_noise_test_mode(self):
        return self._current_minidaq_register("noise_test_mode")

    def current_en_int_trigger(self):
        return self._current_minidaq_register("en_int_trigger")

    def current_enable_hit(self):
        return self._current_minidaq_register("enable_hit")

    def current_triggerless_event_settings(self):
        return (
            self._current_minidaq_register("window_cycles", 20),
            self.miniDAQ_reg.tube_filter_settings(),
        )

    @ethernet_locked_method
    def set_acquisition_register(self, name, value):
        from acquisition_settings import READBACK, PULSE_FIELDS, MODE_FIELDS
        if name not in {field for fields in MODE_FIELDS.values() for field in fields}:
            raise ValueError("Unsupported acquisition register")
        address, _, width, _ = next(r for r in self.miniDAQ_reg.register_table if r[1] == name)
        minimum, maximum = self.miniDAQ_reg.value_limits(name, width)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            raise ValueError(f"{name} must be {minimum}..{maximum}")
        if name not in PULSE_FIELDS and (self._current_minidaq_register("run_enable") or
                                       ((self._read_fpga_value(1) >> 25) & 1)):
            raise RuntimeError("Stop the DAQ before changing acquisition settings")
        fpga_config(self.eth, address, value_to_list(value))
        if name in PULSE_FIELDS:
            fpga_config(self.eth, address, [0])
            return
        page, shift, bits = READBACK[name]
        actual = (self._read_fpga_value(page) >> shift) & ((1 << bits) - 1)
        if actual != value:
            raise RuntimeError(f"{name} readback mismatch: requested {value}, got {actual}")
        self.miniDAQ_reg.set_named_value(name, actual)
        return actual

    @ethernet_locked_method
    def read_acquisition_registers(self, names):
        from acquisition_settings import READBACK
        fields = {name: READBACK[name] for name in names}
        if any(name.startswith("tube_filters_chamber") for name in names):
            self._require_tube_firmware()
        pages = {page: self._read_fpga_value(page) for page in sorted({f[0] for f in fields.values()})}
        values = {name: (pages[page] >> shift) & ((1 << width) - 1)
                  for name, (page, shift, width) in fields.items()}
        for name, value in values.items():
            if name.startswith("tube_filters_chamber"):
                TubeFilterSettings.unpack(value)
        for name, value in values.items():
            self.miniDAQ_reg.set_named_value(name, value)

    @ethernet_locked_method
    def configure_external_trigger(self, config, deadtime=None):
        if deadtime is not None and (not isinstance(deadtime, int) or not 0 <= deadtime <= 65535):
            raise ValueError("Dead time must be a 16-bit value (0..65535)")
        applied = apply_trigger_config(
            self._read_fpga_value,
            lambda address, value: fpga_config(self.eth, address, value_to_list(value)),
            config)
        if deadtime is not None:
            fpga_config(self.eth, 19, value_to_list(deadtime))
            if (self._read_fpga_value(1) >> 32) & 0xFFFF != deadtime:
                raise RuntimeError("Trigger dead-time readback mismatch")
            self.miniDAQ_reg.set_named_value("trigger_deadtime", deadtime)
        self.miniDAQ_reg.set_named_value("external_trigger_config", applied)
        return applied

    @ethernet_locked_method
    def read_external_trigger_settings(self):
        config, busy = read_trigger_config(self._read_fpga_value)
        if busy:
            raise RuntimeError("External trigger LUT is still being programmed")
        mask = self._read_fpga_value(72) & 0xF
        deadtime = (self._read_fpga_value(1) >> 32) & 0xFFFF
        self.miniDAQ_reg.set_named_value("trigger_deadtime", deadtime)
        self.miniDAQ_reg.set_named_value("external_trigger_config", config)
        self.miniDAQ_reg.set_named_value("sma_trigger_enable", mask)
        return config

    @ethernet_locked_method
    def set_sma_trigger_output(self, bit, enabled):
        if bit not in range(4):
            raise ValueError("SMA output index must be 0..3")
        mask = self._read_fpga_value(72) & 0xF
        mask = (mask | (1 << bit)) if enabled else (mask & ~(1 << bit))
        fpga_config(self.eth, 72, [mask])
        if self._read_fpga_value(72) & 0xF != mask:
            raise RuntimeError("SMA output gate readback mismatch")
        self.miniDAQ_reg.set_named_value("sma_trigger_enable", mask)
        return mask

    def _read_fpga_value(self, address, selector=0):
        bits = (fpga_readback(self.eth, address, selector) if selector else
                fpga_readback(self.eth, address))
        if not isinstance(bits, str) or len(bits) != 160 or set(bits) - {"0", "1"}:
            raise RuntimeError(f"Invalid FPGA register {address} readback")
        return int(bits, 2)

    def _require_tube_firmware(self):
        status = self._read_fpga_value(64)
        if (status >> 64) & 0xffffffff != SIGNATURE:
            raise RuntimeError("FPGA does not support TFB v1 tube filters. Load the updated MiniDAQ firmware.")
        if (status >> 96) & 0x7ff != 1280 or (status >> 112) & 0x3ff != 960:
            raise RuntimeError("Unsupported FPGA geometry table capacity")
        return status

    def set_triggerless_event_settings(self, window_cycles, filters):
        if any(
            name == "run_enable" and int(value) != 0
            for _index, name, _bit_width, value in self.miniDAQ_reg.register_table
        ):
            raise RuntimeError(
                "Stop the DAQ before changing triggerless event settings"
            )

        if len(filters) != 2:
            raise ValueError("Two chamber filter settings are required")
        self._require_tube_firmware()
        if (self._read_fpga_value(1) >> 25) & 1:
            raise RuntimeError("Stop the DAQ before changing triggerless event settings")
        register_values = (("window_cycles", window_cycles),
                           ("tube_filters_chamber0", filters[0].pack()),
                           ("tube_filters_chamber1", filters[1].pack()))
        previous_values = {
            name: self._current_minidaq_register(name)
            for name, _value in register_values
        }
        applied_values = {}
        try:
            for name, value in register_values:
                applied_values[name] = self._set_minidaq_register(name, value)
            for chamber in range(2):
                if self._read_fpga_value(66+chamber) != filters[chamber].pack():
                    raise RuntimeError(f"Chamber {chamber} tube-filter readback mismatch")
            if (self._read_fpga_value(4) >> 56) & 0xffff != applied_values["window_cycles"]:
                raise RuntimeError("Triggerless window readback mismatch")
        except Exception:
            for name, _value in reversed(register_values):
                try:
                    self._set_minidaq_register(name, previous_values[name])
                except Exception:
                    pass
            raise

        values = (applied_values["window_cycles"], tuple(filters))
        print(
            "triggerless event settings set: "
            f"window_cycles={values[0]}, tube_filters={values[1]}"
        )
        return values

    @ethernet_locked_method
    def configure_triggerless_geometry(self, image, progress=None):
        """Upload and verify a full snapshot while holding the transport lock."""
        filters = self.miniDAQ_reg.tube_filter_settings()
        status = self._require_tube_firmware()
        if (self._read_fpga_value(1) >> 25) & 1:
            raise RuntimeError("Stop the DAQ before uploading geometry")
        if status & 2:
            raise RuntimeError("FPGA geometry validation is already busy; wait before retrying")
        raw_limit = (self._read_fpga_value(4) >> 24) & 1023
        image.validate_filters(filters, raw_limit)
        old_generation = (status >> 32) & 0xffffffff
        try:
            self.configure_tdc_chamber_map(image.enabled_mask, image.chamber1_mask)
            fpga_config(self.eth, 64, [1])  # BEGIN invalidates the previous image
            for chamber, cfg in enumerate(filters):
                self._set_minidaq_register(f"tube_filters_chamber{chamber}", cfg.pack())
            for done, (index, entry) in enumerate(image.entries, 1):
                fpga_config(self.eth, 62, value_to_list(index))
                # Verify the indirect address too: a lost index write must not
                # silently write/read the previous channel and escape detection.
                if self._read_fpga_value(62) != index:
                    raise RuntimeError(f"Geometry index readback mismatch at {index}")
                fpga_config(self.eth, 63, value_to_list(entry))
                if self._read_fpga_value(63) != entry:
                    raise RuntimeError(f"Geometry entry readback mismatch at {index}")
                if progress:
                    progress(done, len(image.entries), f"Verified channel {done}/{len(image.entries)}")
            fpga_config(self.eth, 64, [2])
            deadline = time.monotonic() + 2.0
            while True:
                status = self._require_tube_firmware()
                if not status & 2:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("FPGA geometry validation timed out")
                time.sleep(0.005)
            error, index = (status >> 8) & 255, (status >> 16) & 0x7ff
            if error or not status & 1:
                raise RuntimeError(f"FPGA geometry rejected: {ERRORS.get(error, 'not ready')} "
                                   f"(error {error}, index {index})")
            if (status >> 32) & 0xffffffff != (old_generation + 1) & 0xffffffff:
                raise RuntimeError("FPGA did not validate a new geometry generation")
            for chamber, cfg in enumerate(filters):
                if self._read_fpga_value(66+chamber) != cfg.pack():
                    raise RuntimeError(f"Chamber {chamber} filter verification failed")
                ml = self._read_fpga_value(65, chamber*4)
                low = self._read_fpga_value(65, chamber*4+1)
                high = self._read_fpga_value(65, chamber*4+2)
                if ml != image.ml_masks[chamber] or (low | (high << 128)) != image.layer_masks[chamber]:
                    raise RuntimeError(f"Chamber {chamber} geometry-mask verification failed")
            print(f"Geometry validated: {len(image.entries)} channels, {len(image.positions)} distinct tubes")
        except Exception:
            # Leave a failed upload unusable even if APPLY succeeded but a later
            # readback failed. Never assert run_enable from this transaction.
            try:
                fpga_config(self.eth, 64, [1])
            except Exception:
                pass
            raise

    def inquire_acquisition_mode(self):
        try:
            bin_str = fpga_readback(self.eth, 1)
            if not isinstance(bin_str, str) or len(bin_str) < 160:
                raise ValueError(f"invalid FPGA readback length: {len(bin_str) if bin_str else 0}")
            mode = int(bin_str[-29], 2)
            stream_hits_only = int(bin_str[-27], 2)
            noise_counter_stream = int(bin_str[-28], 2)
            en_int_trigger = int(bin_str[-25], 2)
            enable_hit = int(bin_str[-24], 2)
            noise_test_mode = stream_hits_only | (noise_counter_stream << 1)
            for pos, (_index, name, _bit_width, _value) in enumerate(self.miniDAQ_reg.register_table):
                if name == "acquisition_mode":
                    self.miniDAQ_reg.set_register_value(pos, mode)
                elif name == "noise_test_mode":
                    self.miniDAQ_reg.set_register_value(pos, noise_test_mode)
                elif name == "en_int_trigger":
                    self.miniDAQ_reg.set_register_value(pos, en_int_trigger)
                elif name == "enable_hit":
                    self.miniDAQ_reg.set_register_value(pos, enable_hit)
            print(
                "[MiniDAQ] run-mode readback: "
                f"acquisition_mode={mode}, noise_test_mode={noise_test_mode}, "
                f"en_int_trigger={en_int_trigger}, enable_hit={enable_hit}"
            )
        except Exception as e:
            print(
                "[WARN] Failed to read run modes from FPGA; "
                f"using cached acquisition_mode={self.current_acquisition_mode()}, "
                f"noise_test_mode={self.current_noise_test_mode()}: {e}"
            )
        return self.current_acquisition_mode()

    def configure_noise_scan_minidaq(
        self,
        *,
        acquisition_mode=0,
        noise_test_mode=0,
        en_int_trigger=1,
        enable_hit=1,
        hit_interval=40000,
        clear_noise_counters=False,
    ):
        settings = {
            "acquisition_mode": int(acquisition_mode),
            "noise_test_mode": int(noise_test_mode),
            "en_int_trigger": int(en_int_trigger),
            "enable_hit": int(enable_hit),
            "hit_interval": int(hit_interval),
        }
        try:
            self._set_minidaq_register("run_enable", 0)
            for name in (
                "acquisition_mode",
                "noise_test_mode",
                "en_int_trigger",
                "enable_hit",
                "hit_interval",
            ):
                settings[name] = self._set_minidaq_register(name, settings[name])
            if clear_noise_counters:
                self._set_minidaq_register("noise_counter_clear", 1)
                self._set_minidaq_register("noise_counter_clear", 0)
        except Exception as e:
            print(f"[NoiseScan] Failed to configure MiniDAQ setup: {e}")
            return False

        print(
            "[NoiseScan] MiniDAQ setup: "
            f"acquisition_mode={settings['acquisition_mode']}, "
            f"noise_test_mode={settings['noise_test_mode']}, "
            f"en_int_trigger={settings['en_int_trigger']}, "
            f"enable_hit={settings['enable_hit']}, "
            f"hit_interval={settings['hit_interval']}, "
            f"clear_noise_counters={int(bool(clear_noise_counters))}"
        )
        return True




    def update_status(self):
        bin_str = None
        try:
            bin_str = fpga_readback(self.eth, 3)
            if not isinstance(bin_str, str) or len(bin_str) < 24:
                raise ValueError(
                    "invalid FPGA link-status readback length: %s"
                    % (len(bin_str) if isinstance(bin_str, str) else 0)
                )
            uplink_ready_bits = bin_str[-16:-8]
            downlink_ready_bits = bin_str[-8:]
            uplink_ready = int(uplink_ready_bits, 2)
            print('Uplink ready = '+uplink_ready_bits)
            print('Downlink ready = '+downlink_ready_bits)
            for link_index in range(len(self.uplink_status_component)):
                ready = bool(uplink_ready & (1 << link_index))
                if self._link_ready_poll is not None and link_index == self._link_ready_poll["link"]:
                    ready = False  # Confirm only after three consecutive samples.
                self._set_uplink_text_ready(
                    link_index,
                    ready,
                )
            return uplink_ready
        except Exception as e:
            print(e)
            print(bin_str)
            return None

    def _start_uplink_ready_poll(self, link_index):
        self._link_ready_timer.stop()
        self._link_ready_poll = {
            "link": link_index,
            "deadline": time.monotonic() + 1.0,
            "successes": 0,
        }
        self._set_uplink_text_ready(link_index, False)
        self._link_ready_timer.start()

    def _poll_loaded_uplink_ready(self):
        poll = self._link_ready_poll
        if poll is None:
            self._link_ready_timer.stop()
            return
        link_index = poll["link"]
        if time.monotonic() <= poll["deadline"]:
            ready_mask = self.update_status()
            if ready_mask is not None and ready_mask & (1 << link_index):
                poll["successes"] += 1
            else:
                poll["successes"] = 0
            if time.monotonic() <= poll["deadline"]:
                if poll["successes"] < 3:
                    return
                self._link_ready_timer.stop()
                self._link_ready_poll = None
                self._set_uplink_text_ready(link_index, True)
                print(f"Uplink {link_index} ready confirmed after 3 consecutive reads.")
                return
        self._link_ready_timer.stop()
        self._link_ready_poll = None
        self._set_uplink_text_ready(link_index, False)
        print(f"Uplink {link_index} ready not confirmed within 1 second (3 consecutive reads required).")


    def load_lpgbt(self,which_csm,is_master):
        self._link_ready_timer.stop()
        self._link_ready_poll = None
        self.worker_lpGBT.load_lpgbt_config(
            which_csm=which_csm,
            is_master=is_master,
        )
        link_index = which_csm * 2 + (0 if is_master else 1)
        self.fpga_physical_rx_reset()
        self._start_uplink_ready_poll(link_index)

    # def slave_control0(self):
    #     self.slave_control(which_csm=self.comboBox_ICselect.currentIndex() // 2, set_enable=self.checkBox_enable_vtrx_slave0.isChecked())

    # def set_prbs(self):
    #     lpgbt_addr = self.lpgbt_master_addr if (self.comboBox_ICselect.currentIndex()%2)==0 else self.lpgbt_slave_addr
    #     self.set_uplink_prbs(which_csm=self.comboBox_ICselect.currentIndex() // 2, lpgbt_addr=lpgbt_addr, set_enable=self.checkBox_enable_master_prbs0.isChecked())

    
    def slave_control(self, which_csm, state):
        set_enable = 1 if state == Qt.Checked else 0
        action = "enable" if set_enable else "disable"

        def report_failure(step, errors):
            print(
                "FAILED to %s CSM%s slave link at step: %s"
                % (action, which_csm, step)
            )
            for error in errors:
                print("  - " + error)

        def checked_read(step, reg_addr):
            verification = {}
            try:
                result = lpgbt_read(
                    self.eth,
                    lpgbt_addr=self.lpgbt_master_addr,
                    reg_addr=reg_addr,
                    nb_to_be_read=1,
                    verbose=False,
                    verification=verification,
                    which_csm=which_csm,
                )
            except Exception as error:
                result = -1
                verification.setdefault("errors", []).append(
                    "%s: %s" % (type(error).__name__, error)
                )
            if not isinstance(result, list):
                verification.setdefault("errors", []).append(
                    "No valid register-data reply was returned."
                )
            errors = verification.get("errors", [])
            if errors:
                report_failure(step, errors)
                return None
            return result

        def checked_write(step, reg_addr, value):
            verification = {}
            try:
                result = lpgbt_config_write(
                    self.eth,
                    reg_addr=reg_addr,
                    value_list=[value],
                    which_csm=which_csm,
                    lpgbt_addr=self.lpgbt_master_addr,
                    verbose=False,
                    verification=verification,
                )
            except Exception as error:
                result = -1
                verification.setdefault("errors", []).append(
                    "%s: %s" % (type(error).__name__, error)
                )
            if not isinstance(result, list):
                verification.setdefault("errors", []).append(
                    "No valid register-data reply was returned."
                )
            errors = verification.get("errors", [])
            if errors:
                report_failure(
                    "%s: lpGBT%s register 0x%03X = 0x%02X"
                    % (step, self.lpgbt_master_addr, reg_addr, value),
                    errors,
                )
                return False
            return True

        transaction_count_reg = LpgbtRegisterMapV1.I2CM1TRANCNT.address
        if checked_read("read initial I2CM1 transaction count", transaction_count_reg) is None:
            return

        write_steps = (
            ("set VTRX+ I2C address", LpgbtRegisterMapV1.I2CM1ADDRESS.address, 0x50),
            ("set two-byte, 400-kHz control", LpgbtRegisterMapV1.I2CM1DATA0.address, 0x0A),
            ("apply I2CM1 control", LpgbtRegisterMapV1.I2CM1CMD.address, 0x00),
            ("set VTRX+ register address", LpgbtRegisterMapV1.I2CM1DATA0.address, 0x00),
            ("set VTRX+ slave-link value", LpgbtRegisterMapV1.I2CM1DATA1.address, 0x03 if set_enable else 0x01),
            ("stage I2C data", LpgbtRegisterMapV1.I2CM1CMD.address, 0x08),
            ("execute I2C write", LpgbtRegisterMapV1.I2CM1CMD.address, 0x0C),
        )
        for step, reg_addr, value in write_steps:
            if not checked_write(step, reg_addr, value):
                return

        if checked_read("read final I2CM1 transaction count", transaction_count_reg) is None:
            return
        print(
            "CSM%s slave-link %s transaction succeeded."
            % (which_csm, action)
        )

    def set_ic_enable(self):
        # Target selection is encoded in each lpGBT Ethernet request.
        pass

    def fpga_physical_rx_reset(self):
        fpga_config(self.eth, 2, [0x0F])
        fpga_config(self.eth, 2, [0x00])
        print("Physical RX reset sent to all uplinks")

    def fpga_downlink_reset(self):
        fpga_config(self.eth, 3, [1])
        fpga_config(self.eth, 3, [0])
        print("Downlink reset sent")

    def fpga_sca_reset(self):
        fpga_config(self.eth, 4, [1])
        fpga_config(self.eth, 4, [0])
        print("SCA reset sent")

    def fpga_global_reset(self):
        fpga_config(self.eth, 5, [1])
        fpga_config(self.eth, 5, [0])
        print("Global reset sent")


    def print_message(self,str):
        print(str)

    def read_fpga_id(self, which_csm=0, _checked=False, on_result=None):
        """Start the read and return True; on_result receives (csm, idcode, configured)."""
        if (
            self.worker_load_CSM_bit is not None
            or self.worker_read_CSM_idcode is not None
        ):
            print("An Ethernet SCA/JTAG operation is already running.")
            return False

        device = self.current_ethernet_device()
        self.refresh_ethernet_device_label()
        if not device or "ERROR" in device:
            print(
                "No valid Ethernet interface is selected in the "
                "Ethernet Capture tab."
            )
            return False

        self._set_fpga_status_ready(which_csm, False)
        self._set_load_CSM_bit_busy(True)
        self.pushButton_cancel_CSM_bit.setEnabled(False)

        self.thread_read_CSM_idcode = QThread()
        self.worker_read_CSM_idcode = Worker_read_CSM_idcode_ethernet(
            which_csm=which_csm,
            ethernet_device=device,
            target_sca=0,
        )
        self.worker_read_CSM_idcode.moveToThread(
            self.thread_read_CSM_idcode
        )
        self.thread_read_CSM_idcode.started.connect(
            self.worker_read_CSM_idcode.run
        )
        self.thread_read_CSM_idcode.finished.connect(
            self.thread_read_CSM_idcode.deleteLater
        )
        self.thread_read_CSM_idcode.finished.connect(
            self._finish_read_CSM_idcode
        )
        self.worker_read_CSM_idcode.message_out.connect(self.print_message)
        self.worker_read_CSM_idcode.idcode_signal.connect(
            self._on_fpga_idcode_result
        )
        self.worker_read_CSM_idcode.finished.connect(
            self.thread_read_CSM_idcode.quit
        )
        self.worker_read_CSM_idcode.finished.connect(
            self.worker_read_CSM_idcode.deleteLater
        )
        if on_result is not None:
            self.worker_read_CSM_idcode.idcode_signal.connect(on_result)
        self.thread_read_CSM_idcode.start()
        return True

    def _on_fpga_idcode_result(self, csm, _idcode, configured):
        configured = bool(configured)
        self._set_fpga_status_ready(csm, configured)
        if not configured:
            self.progress_bar.setValue(0)

    def _finish_read_CSM_idcode(self):
        self.worker_read_CSM_idcode = None
        self.thread_read_CSM_idcode = None
        self._set_load_CSM_bit_busy(False)

    def _set_load_CSM_bit_busy(self, busy):
        self.pushButton_load_CSM0_bit_ethernet.setEnabled(not busy)
        self.pushButton_load_CSM1_bit_ethernet.setEnabled(not busy)
        for button in self._fpga_idcode_buttons:
            button.setEnabled(not busy)
        self.pushButton_cancel_CSM_bit.setEnabled(busy)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def load_fpga_bit_ethernet(self, which_csm=0, on_programmed=None):
        """Start programming and return True; on_programmed receives the CSM on success."""
        if (
            self.worker_load_CSM_bit is not None
            or self.worker_read_CSM_idcode is not None
        ):
            print("An Ethernet SCA/JTAG operation is already running.")
            return False

        device = self.current_ethernet_device()
        self.refresh_ethernet_device_label()
        if not device or "ERROR" in device:
            print(
                "No valid Ethernet interface is selected in the "
                "Ethernet Capture tab."
            )
            return False

        self._set_load_CSM_bit_busy(True)
        self.progress_bar.setValue(0)
        self.thread_load_CSM_bit = QThread()
        self.worker_load_CSM_bit = Worker_load_CSM_bit_ethernet(
            which_csm=which_csm,
            file_name=self.file_path_box.text(),
            ethernet_device=device,
            target_sca=0,
        )
        self.worker_load_CSM_bit.moveToThread(self.thread_load_CSM_bit)
        self.thread_load_CSM_bit.started.connect(
            self.worker_load_CSM_bit.run
        )
        self.thread_load_CSM_bit.finished.connect(
            self.thread_load_CSM_bit.deleteLater
        )
        self.thread_load_CSM_bit.finished.connect(
            self._finish_load_CSM_bit
        )
        self.worker_load_CSM_bit.message_out.connect(self.print_message)
        self.worker_load_CSM_bit.progress_signal.connect(self.update_progress)
        self.worker_load_CSM_bit.programmed_signal.connect(
            lambda csm: self._set_fpga_status_ready(csm, True)
        )
        self.worker_load_CSM_bit.finished.connect(
            self.thread_load_CSM_bit.quit
        )
        self.worker_load_CSM_bit.finished.connect(
            self.worker_load_CSM_bit.deleteLater
        )
        if on_programmed is not None:
            self.worker_load_CSM_bit.programmed_signal.connect(on_programmed)
        self.thread_load_CSM_bit.start()
        return True

    def cancel_load_CSM_bit(self):
        if self.worker_load_CSM_bit is None:
            return
        self.pushButton_cancel_CSM_bit.setEnabled(False)
        self.worker_load_CSM_bit.request_cancel()
        print("Cancel requested for CSM bit load.")

    def _finish_load_CSM_bit(self):
        self.worker_load_CSM_bit = None
        self.thread_load_CSM_bit = None
        self._set_load_CSM_bit_busy(False)

    def miniDAQ_setup_dialog(self):
        # Create and show the TDC configuration popup window
        self.miniDAQ_setup_popup = pop_miniDAQ_setup(
            self.eth, self.miniDAQ_reg,
            start_callback=getattr(self, "_manual_daq_start_callback", None),
            stop_callback=self.DAQ_stop,
        )
        self.miniDAQ_setup_popup.exec_()  # exec_() for modal behavior, show() for non-modal

    def link_setup_dialog(self):
        self.link_setup_popup = pop_link_setup(self.eth)
        self.link_setup_popup.exec_()

    def prbs_test_dialog(self):
        # Create and show the TDC configuration popup window
        self.prbs_test_popup = pop_prbs(self.eth,self.rxprbssel)
        self.prbs_test_popup.exec_()  # exec_() for modal behavior, show() for non-modal

    def handle_checkbox(self, index, name, state):
        value = 1 if state == Qt.Checked else 0
        print(f"{name} changed to {value}")
        fpga_config(self.eth, index, [value])

    def open_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select a File",
            self.default_file,  # Start with default file
            "Bitstream Files (*.bit);;All Files (*)",  # Filter to show only .bit files
            options=options
        )

        if file_path:  # If a file was selected
            self.file_path_box.setText(file_path)
