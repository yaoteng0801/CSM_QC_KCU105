# noise_scan_controller.py
from PyQt5 import QtWidgets, QtCore
import csv
import datetime
import os
import time

import numpy as np

from pop_noise_scan import (
    NOISE_SCAN_TRIGGERED,
    NOISE_SCAN_TRIGGERLESS_COUNT,
    NOISE_SCAN_TRIGGERLESS_RAW,
    NoiseScanDialog,
    NoiseScanResultDialog,
)


CH_HIT_TIME_WINDOW_S = 60.0 * 25.0e-9
NOISE_SCAN_MODES = {
    NOISE_SCAN_TRIGGERED,
    NOISE_SCAN_TRIGGERLESS_RAW,
    NOISE_SCAN_TRIGGERLESS_COUNT,
}


class NoiseScanController(QtCore.QObject):
    def __init__(self, tab_capture):
        super().__init__(tab_capture)
        self.tab = tab_capture

        self._configure_threshold_callback = None
        self._configure_hyst_callback = None
        self._selected_mezz_callback = None
        self._active_channels_callback = None
        self._disabled_channels_callback = None
        self._minidaq_setup_callback = None

        self._scan_active = False
        self._cancel_requested = False
        self._values = []
        self._index = 0
        self._event_count = 20000
        self._scan_type = "threshold"
        self._noise_acquisition_mode = NOISE_SCAN_TRIGGERED
        self._selected_mezz = []
        self._active_channels = {}
        self._disabled_channels = []
        self._results = []
        self._summary_path = ""
        self._current_out_path = ""
        self._output_dir = ""
        self._stamp = ""
        self._current_threshold = None
        self._current_hyst = None
        self._start_threshold = 40
        self._end_threshold = 100
        self._step = 5
        self._hyst_values = [7]
        self._fixed_threshold = 40
        self._fixed_hyst = 7
        self._last_summary_path = ""
        self._last_decode = None
        self._result_dialog = None
        self._point_started_monotonic = 0.0
        self._point_duration_s = 0.0

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._poll_events)

    def __getattr__(self, name):
        tab = object.__getattribute__(self, "tab")
        return getattr(tab, name)

    def add_button_row(self, layout):
        noise_btns = QtWidgets.QHBoxLayout()
        layout.addLayout(noise_btns)

        self.tab.btn_noise_scan = QtWidgets.QPushButton("Noise Scan")
        self.tab.btn_noise_scan.clicked.connect(self._on_scan_button)
        noise_btns.addWidget(self.tab.btn_noise_scan, 1)

        self.tab.btn_noise_result = QtWidgets.QPushButton("Noise Result")
        self.tab.btn_noise_result.clicked.connect(self.show_results)
        noise_btns.addWidget(self.tab.btn_noise_result, 1)
        noise_btns.addStretch(1)

    def set_control(
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
        self._active_channels_callback = active_channels_callback
        self._disabled_channels_callback = disabled_channels_callback
        self._configure_threshold_callback = configure_threshold_callback
        self._configure_hyst_callback = configure_hyst_callback
        self._minidaq_setup_callback = minidaq_setup_callback

    def load_settings(self):
        self._scan_type = self.settings.value("noise_scan/scan_type", self._scan_type, type=str)
        if self._scan_type not in ("threshold", "hyst"):
            self._scan_type = "threshold"
        self._start_threshold = self.settings.value(
            "noise_scan/start_threshold", self._start_threshold, type=int
        )
        self._end_threshold = self.settings.value(
            "noise_scan/end_threshold", self._end_threshold, type=int
        )
        self._step = self.settings.value("noise_scan/step", self._step, type=int)
        self._event_count = self.settings.value(
            "noise_scan/event_count", self._event_count, type=int
        )
        self._noise_acquisition_mode = self.settings.value(
            "noise_scan/acquisition_mode",
            self._noise_acquisition_mode,
            type=str,
        )
        if self._noise_acquisition_mode not in NOISE_SCAN_MODES:
            self._noise_acquisition_mode = NOISE_SCAN_TRIGGERED
        self._hyst_values = self._parse_hyst_settings(
            self.settings.value("noise_scan/hyst_values", "7", type=str)
        )
        self._fixed_threshold = self.settings.value(
            "noise_scan/fixed_threshold", self._fixed_threshold, type=int
        )
        self._fixed_hyst = self.settings.value(
            "noise_scan/fixed_hyst", self._fixed_hyst, type=int
        )
        self._last_summary_path = self.settings.value("noise_scan/last_summary", "", type=str)
        self.btn_noise_result.setEnabled(True)

    def is_active(self) -> bool:
        return bool(self._scan_active)

    def _set_analysis_emit_suppressed(self, suppressed: bool) -> None:
        backend = self.backend
        if backend is None:
            return
        setter = getattr(backend, "set_analysis_emit_suppressed", None)
        try:
            if callable(setter):
                setter(bool(suppressed))
            else:
                setattr(backend, "_analysis_emit_suppressed", bool(suppressed))
        except Exception:
            pass

    def on_decode_snapshot(self, snap):
        self._last_decode = snap

    def on_run_finished(self) -> bool:
        if not self._scan_active:
            return False
        self.btn_start.setEnabled(False)
        self.btn_process.setEnabled(False)
        self.btn_stop.setEnabled(False)
        return True

    def _save_scan_settings(
        self,
        scan_type,
        start_threshold,
        end_threshold,
        step,
        event_count,
        hyst_values,
        fixed_threshold,
        fixed_hyst,
        acquisition_mode,
    ):
        self._scan_type = str(scan_type or "threshold")
        if self._scan_type not in ("threshold", "hyst"):
            self._scan_type = "threshold"
        self._start_threshold = int(start_threshold)
        self._end_threshold = int(end_threshold)
        self._step = max(1, int(step))
        self._event_count = max(1, int(event_count))
        self._noise_acquisition_mode = str(acquisition_mode or NOISE_SCAN_TRIGGERED)
        if self._noise_acquisition_mode not in NOISE_SCAN_MODES:
            self._noise_acquisition_mode = NOISE_SCAN_TRIGGERED
        self._hyst_values = [int(v) for v in (hyst_values or [])]
        self._fixed_threshold = self._bounded_int(fixed_threshold, 0, 255, 40)
        self._fixed_hyst = self._bounded_int(fixed_hyst, 0, 15, 7)
        self.settings.setValue("noise_scan/scan_type", self._scan_type)
        self.settings.setValue("noise_scan/start_threshold", self._start_threshold)
        self.settings.setValue("noise_scan/end_threshold", self._end_threshold)
        self.settings.setValue("noise_scan/step", self._step)
        self.settings.setValue("noise_scan/event_count", self._event_count)
        self.settings.setValue("noise_scan/acquisition_mode", self._noise_acquisition_mode)
        self.settings.setValue(
            "noise_scan/hyst_values",
            ",".join(str(v) for v in self._hyst_values),
        )
        self.settings.setValue("noise_scan/fixed_threshold", self._fixed_threshold)
        self.settings.setValue("noise_scan/fixed_hyst", self._fixed_hyst)
        self.settings.sync()

    @staticmethod
    def _parse_hyst_settings(raw):
        values = []
        for part in str(raw or "").split(","):
            try:
                value = int(part.strip())
            except Exception:
                continue
            if 0 <= value <= 15 and value not in values:
                values.append(value)
        return values or [7]

    @staticmethod
    def _bounded_int(value, lo: int, hi: int, default: int) -> int:
        try:
            value = int(value)
        except Exception:
            value = int(default)
        return max(int(lo), min(int(hi), value))

    def _on_scan_button(self):
        if self._scan_active:
            self.cancel()
            return

        dlg = NoiseScanDialog(
            self.tab.parent,
            start_threshold=self._start_threshold,
            end_threshold=self._end_threshold,
            step=self._step,
            event_count=self._event_count,
            scan_type=self._scan_type,
            acquisition_mode=self._noise_acquisition_mode,
            hyst_values=self._hyst_values,
            fixed_threshold=self._fixed_threshold,
            fixed_hyst=self._fixed_hyst,
        )
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        self._save_scan_settings(
            dlg.scan_type(),
            dlg.start_threshold(),
            dlg.end_threshold(),
            dlg.step(),
            dlg.event_count(),
            dlg.hyst_values(),
            dlg.fixed_threshold(),
            dlg.fixed_hyst(),
            dlg.acquisition_mode(),
        )

        if not self._confirm_ready():
            return

        self._start_scan(
            scan_type=dlg.scan_type(),
            values=dlg.scan_values(),
            event_count=dlg.event_count(),
            fixed_threshold=dlg.fixed_threshold(),
            fixed_hyst=dlg.fixed_hyst(),
            acquisition_mode=dlg.acquisition_mode(),
        )

    def _confirm_ready(self) -> bool:
        selected_count = len(self._selected_mezz_list())
        reply = QtWidgets.QMessageBox.question(
            self.tab.parent,
            "Noise Scan Reminder",
            f"{selected_count} mezz currently selected.\nDid you perform a mezz scan first?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        return reply == QtWidgets.QMessageBox.Yes

    def _selected_mezz_list(self):
        if self._selected_mezz_callback is None:
            return []
        try:
            selected = self._selected_mezz_callback()
        except Exception as e:
            print(f"[NoiseScan] Failed to read selected mezz list: {e}")
            return []

        out = []
        for item in selected or []:
            try:
                which_csm, mezz = item
                out.append((int(which_csm), int(mezz)))
            except Exception:
                continue
        return out

    def _set_controls(self, scanning: bool):
        self.btn_noise_scan.setText("Cancel Noise Scan" if scanning else "Noise Scan")
        self.btn_start.setEnabled(not scanning)
        self.btn_process.setEnabled(not scanning)
        acquisition_combo = getattr(self.tab, "combo_acquisition_mode", None)
        if acquisition_combo is not None:
            acquisition_combo.setEnabled(not scanning)
        self.btn_stop.setEnabled(False if scanning else bool(self.backend and self.backend.is_running()))
        self.btn_noise_result.setEnabled(True)

    def _start_scan(
        self,
        *,
        scan_type: str,
        values,
        event_count: int,
        fixed_threshold: int,
        fixed_hyst: int,
        acquisition_mode: str,
    ):
        if self.backend is None:
            print("[ERROR] Backend is not initialized.")
            return
        if self.backend.is_running():
            print("[ERROR] Stop the current run before starting a noise scan.")
            return

        scan_type = str(scan_type or "threshold")
        if scan_type not in ("threshold", "hyst"):
            print(f"[ERROR] Unsupported noise scan type: {scan_type}")
            return
        if self._configure_threshold_callback is None or self._configure_hyst_callback is None:
            print("[ERROR] Noise scan ASD configuration callbacks are not configured.")
            return
        acquisition_mode = str(acquisition_mode or NOISE_SCAN_TRIGGERED)
        if acquisition_mode not in NOISE_SCAN_MODES:
            print(f"[ERROR] Unsupported noise scan acquisition mode: {acquisition_mode}")
            return

        dev = self.current_device()
        if not dev or "ERROR" in dev:
            print("[ERROR] No valid Ethernet device selected.")
            return
        if not self._apply_rt_selection():
            return

        selected_mezz = self._selected_mezz_list()
        if not selected_mezz:
            print("[ERROR] Select at least one mezz in the Mezz Config tab before noise scan.")
            return

        values = sorted({int(v) for v in (values or [])}, reverse=True)
        if not values:
            print("[ERROR] Noise scan value list is empty.")
            return

        active_channels = self._active_channel_map(selected_mezz)
        if self._active_channel_count(active_channels) <= 0:
            print("[ERROR] No active ASD/TDC channels found for the selected mezz.")
            return
        disabled_channels = self._disabled_channel_list(selected_mezz)

        self._noise_acquisition_mode = acquisition_mode
        if not self._apply_minidaq_noise_scan_setup():
            return

        self._scan_type = scan_type
        self._values = values
        self._index = 0
        self._event_count = max(1, int(event_count))
        self._selected_mezz = selected_mezz
        self._active_channels = active_channels
        self._disabled_channels = disabled_channels
        self._results = []
        self._summary_path = ""
        self._current_out_path = ""
        self._current_threshold = None
        self._current_hyst = None
        self._cancel_requested = False
        self._point_started_monotonic = 0.0
        self._point_duration_s = 0.0

        if scan_type == "hyst":
            self._current_threshold = self._bounded_int(fixed_threshold, 0, 255, 40)
            print(f"[NoiseScan] Setting fixed ASD main_thr {self._current_threshold} for hyst scan")
            if not self._configure_asd_setting("threshold", self._current_threshold):
                return
        else:
            self._current_hyst = self._bounded_int(fixed_hyst, 0, 15, 7)
            print(f"[NoiseScan] Setting fixed ASD hyst {self._current_hyst} for main_thr scan")
            if not self._configure_asd_setting("hyst", self._current_hyst):
                return

        base_dir = self.edit_outdir.text().strip() or os.getcwd()
        self._stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tag = self._directory_tag()
        prefix = self._filename_prefix()
        scan_dir = os.path.join(base_dir, f"{prefix}noise_scan_{tag}_{self._stamp}")
        try:
            os.makedirs(scan_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Failed to create noise scan folder: {e}")
            return

        self._output_dir = scan_dir
        self._summary_path = os.path.join(
            scan_dir,
            f"{prefix}noise_scan_summary_{tag}_{self._stamp}.csv",
        )
        self._scan_active = True
        self._set_controls(True)
        self._save_settings()

        selected_text = ", ".join(f"CSM{csm}/Mezz{mezz}" for csm, mezz in selected_mezz)
        print(
            f"[NoiseScan] Starting {self._setting_label()} scan values={values}, "
            f"mode={self._mode_label()}, {self._target_description()}, mezz={selected_text}, "
            f"active channels={self._active_channel_count(active_channels)}, "
            f"disabled channels={len(disabled_channels)}"
        )
        print(f"[NoiseScan] Result folder: {scan_dir}")
        QtCore.QTimer.singleShot(0, self._start_next_point)

    def _mode_register_values(self):
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_RAW:
            return 1, 1
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_COUNT:
            return 1, 2
        return 0, 0

    def _apply_minidaq_noise_scan_setup(self, *, clear_noise_counters=False) -> bool:
        if self._minidaq_setup_callback is None:
            print("[ERROR] Noise scan MiniDAQ setup callback is not configured.")
            return False
        acquisition_mode, noise_test_mode = self._mode_register_values()
        try:
            ok = self._minidaq_setup_callback(
                acquisition_mode=acquisition_mode,
                noise_test_mode=noise_test_mode,
                en_int_trigger=1,
                enable_hit=1,
                hit_interval=40000,
                clear_noise_counters=bool(clear_noise_counters),
            )
        except Exception as e:
            print(f"[ERROR] MiniDAQ setup for noise scan failed: {e}")
            return False
        if ok is False:
            print("[ERROR] MiniDAQ setup for noise scan failed.")
            return False
        try:
            if hasattr(self.backend, "set_acquisition_mode"):
                self.backend.set_acquisition_mode(acquisition_mode)
            if hasattr(self.backend, "set_noise_test_mode"):
                self.backend.set_noise_test_mode(noise_test_mode)
        except Exception as e:
            print(f"[ERROR] Failed to set decoder noise scan mode: {e}")
            return False
        return True

    def _mode_label(self) -> str:
        labels = {
            NOISE_SCAN_TRIGGERED: "triggered",
            NOISE_SCAN_TRIGGERLESS_RAW: "triggerless raw hits",
            NOISE_SCAN_TRIGGERLESS_COUNT: "triggerless hit counters",
        }
        return labels.get(self._noise_acquisition_mode, self._noise_acquisition_mode)

    def _target_description(self) -> str:
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED:
            return f"events/point={self._event_count}"
        return f"seconds/point={self._event_count}"

    def _target_unit(self) -> str:
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED:
            return "events"
        return "seconds"

    def _directory_tag(self) -> str:
        if self._scan_type == "hyst":
            threshold = self._filename_value(self._current_threshold, 3)
            return f"{self._mode_file_tag()}_hyst_main_thr_{threshold}"
        hyst = self._filename_value(self._current_hyst, 2)
        return f"{self._mode_file_tag()}_main_thr_hyst_{hyst}"

    def _mode_file_tag(self) -> str:
        tags = {
            NOISE_SCAN_TRIGGERED: "triggered",
            NOISE_SCAN_TRIGGERLESS_RAW: "triggerless_raw",
            NOISE_SCAN_TRIGGERLESS_COUNT: "triggerless_count",
        }
        return tags.get(self._noise_acquisition_mode, "triggered")

    def _file_stem(self) -> str:
        threshold = self._filename_value(self._current_threshold, 3)
        hyst = self._filename_value(self._current_hyst, 2)
        stamp = self._stamp or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self._filename_prefix()
        if self._scan_type == "hyst":
            return f"{prefix}noise_hyst_{hyst}_main_thr_{threshold}_{stamp}"
        return f"{prefix}noise_main_thr_{threshold}_hyst_{hyst}_{stamp}"

    def _filename_prefix(self) -> str:
        prefix = ""
        getter = getattr(self.tab, "csm_filename_prefix", None)
        if callable(getter):
            try:
                prefix = str(getter() or "")
            except Exception:
                prefix = ""
        return os.path.basename(prefix)

    def _csm_number_text(self) -> str:
        getter = getattr(self.tab, "csm_number_text", None)
        if callable(getter):
            try:
                return str(getter() or "")
            except Exception:
                return ""
        return ""

    def _asd_main_thr_text(self) -> str:
        getter = getattr(self.tab, "asd_main_thr_text", None)
        if callable(getter):
            try:
                return str(getter() or "")
            except Exception:
                return ""
        return ""

    @staticmethod
    def _filename_value(value, width: int) -> str:
        try:
            value = int(value)
        except Exception:
            value = -1
        if value < 0:
            return "x" * int(width)
        return str(value).zfill(int(width))

    def _setting_label(self) -> str:
        if self._scan_type == "hyst":
            return "hyst"
        return "main_thr"

    def _configure_asd_setting(self, setting: str, value: int) -> bool:
        if setting == "hyst":
            callback = self._configure_hyst_callback
            response_key = "hyst"
        else:
            callback = self._configure_threshold_callback
            response_key = "threshold"

        if callback is None:
            return False
        try:
            response = callback(int(value), selected_mezz=list(self._selected_mezz))
        except TypeError:
            try:
                response = callback(int(value))
            except Exception as e:
                print(f"[ERROR] ASD {setting} configuration failed: {e}")
                return False
        except Exception as e:
            print(f"[ERROR] ASD {setting} configuration failed: {e}")
            return False
        if not response:
            print(f"[ERROR] SCA/ASD {setting} configuration failed at value {value}. Noise scan stopped.")
            return False

        confirmed = self._response_int(response, response_key, int(value))
        if setting == "hyst":
            self._current_hyst = confirmed
            other = self._response_int(response, "threshold", self._current_threshold)
            if other is not None:
                self._current_threshold = other
        else:
            self._current_threshold = confirmed
            other = self._response_int(response, "hyst", self._current_hyst)
            if other is not None:
                self._current_hyst = other
        return True

    @staticmethod
    def _response_int(response, key: str, default):
        try:
            value = response.get(key, default)
        except Exception:
            value = default
        try:
            return int(value)
        except Exception:
            return default

    def _start_next_point(self):
        if not self._scan_active:
            return
        if self._cancel_requested:
            self._finish(cancelled=True)
            return
        if self._index >= len(self._values):
            self._finish(cancelled=False)
            return

        self._set_analysis_emit_suppressed(True)

        value = int(self._values[self._index])
        setting_label = self._setting_label()
        print(f"[NoiseScan] Configuring ASD {setting_label} {value}")
        if self._scan_type == "hyst":
            if not self._configure_asd_setting("hyst", value):
                self._finish(cancelled=True)
                return
        else:
            if not self._configure_asd_setting("threshold", value):
                self._finish(cancelled=True)
                return

        if not self._apply_minidaq_noise_scan_setup(
            clear_noise_counters=self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_COUNT
        ):
            self._finish(cancelled=True)
            return

        stem = self._file_stem()
        if hasattr(self.backend, "make_data_path"):
            out_path = self.backend.make_data_path(self._output_dir, stem)
        else:
            run_dir = os.path.join(self._output_dir, stem)
            out_path = os.path.join(run_dir, f"{stem}.dat")
        self._current_out_path = out_path
        dev = self.current_device()
        bpf = self.edit_filter.text().strip()

        run = self._allocate_run_number()
        log_path = None
        if hasattr(self.backend, "prepare_run_log"):
            log_path = self.backend.prepare_run_log(
                out_path,
                context={
                    "mode": "noise_scan_capture",
                    "run_number": int(run),
                    "csm_number": self._csm_number_text(),
                    "asd_main_thr": self._asd_main_thr_text(),
                    "filename_prefix": self._filename_prefix(),
                    "ethernet_device": dev,
                    "bpf_filter": bpf,
                    "output_dir": self._output_dir,
                    "data_file": out_path,
                    "rt_file": self.edit_rtfile.text().strip(),
                    "settings_file": os.path.join(os.getcwd(), "capture_settings.ini"),
                    "noise_scan_type": self._scan_type,
                    "noise_scan_setting": setting_label,
                    "noise_scan_value": int(value),
                    "noise_scan_threshold": int(self._current_threshold),
                    "noise_scan_hyst": int(self._current_hyst),
                    "noise_scan_acquisition_mode": self._noise_acquisition_mode,
                    "acquisition_mode": self._mode_register_values()[0],
                    "noise_test_mode": self._mode_register_values()[1],
                    "noise_scan_target_value": int(self._event_count),
                    "noise_scan_target_unit": self._target_unit(),
                    "noise_scan_selected_mezz": list(self._selected_mezz),
                    "noise_scan_active_channels": dict(self._active_channels),
                    "noise_scan_disabled_channels": list(self._disabled_channels),
                    "disabled_channels": list(self._disabled_channels),
                },
            )
        print(
            f"[NoiseScan] Starting {setting_label} {value} run "
            f"for {self._target_description()} (run {run})"
        )
        print(f"[NoiseScan] Output DAT: {out_path}")
        print(f"[NoiseScan] Run folder: {os.path.dirname(out_path)}")
        if log_path:
            print(f"[NoiseScan] Output log: {log_path}")

        self._last_decode = None
        try:
            self.backend.start_capture(dev, bpf, out_path)
        except Exception as e:
            print(f"[ERROR] Failed to start noise scan capture: {e}")
            self._finish(cancelled=True)
            return

        if not self._start_hardware_run():
            print("[ERROR] Failed to start MiniDAQ hardware for noise scan.")
            self.backend.stop_capture()
            self._finish(cancelled=True)
            return

        self._point_started_monotonic = time.monotonic()
        self._point_duration_s = 0.0
        self._set_current_dat_name(out_path)
        self.btn_start.setEnabled(False)
        self.btn_process.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self._timer.start()

    def _poll_events(self):
        if not self._scan_active:
            self._timer.stop()
            return
        if self._cancel_requested:
            self._timer.stop()
            self._stop_hardware_run()
            if self.backend and self.backend.is_running():
                self.backend.stop_capture()
            self._finish(cancelled=True)
            return

        snap = self._current_decode_snapshot()
        if self._point_progress(snap) < self._event_count:
            return

        self._timer.stop()
        self._finish_point(snap)

    def _point_progress(self, snap) -> float:
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED:
            return float(self._event_windows(snap))
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_COUNT:
            try:
                return float(max(0, int(getattr(snap, "noise_last_seconds", 0) or 0)))
            except Exception:
                return 0.0
        return self._point_elapsed_s()

    def _point_elapsed_s(self) -> float:
        if self._point_started_monotonic <= 0.0:
            return 0.0
        return max(0.0, time.monotonic() - self._point_started_monotonic)

    def _measurement_duration_s(self, snap) -> float:
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED:
            return float(self._event_windows(snap)) * CH_HIT_TIME_WINDOW_S
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_COUNT:
            try:
                return float(max(0, int(getattr(snap, "noise_last_seconds", 0) or 0)))
            except Exception:
                return 0.0
        if self._point_duration_s > 0.0:
            return self._point_duration_s
        return self._point_elapsed_s()

    def _start_hardware_run(self) -> bool:
        callback = getattr(self.tab, "_start_daq_hardware", None)
        if not callable(callback):
            return True
        try:
            return callback() is not False
        except Exception as e:
            print(f"[ERROR] MiniDAQ hardware start failed: {e}")
            return False

    def _stop_hardware_run(self) -> bool:
        callback = getattr(self.tab, "_stop_daq_hardware", None)
        if not callable(callback):
            return True
        try:
            return callback() is not False
        except Exception as e:
            print(f"[ERROR] MiniDAQ hardware stop failed: {e}")
            return False

    def _current_decode_snapshot(self, *, include_channel_hits: bool = False):
        if self.backend is not None and hasattr(self.backend, "current_decode_snapshot"):
            fields = {"ch_hits"} if include_channel_hits else set()
            snap = self.backend.current_decode_snapshot(
                snapshot_fields=fields,
            )
            if snap is not None:
                return snap
        return self._last_decode

    def _finish_point(self, snap):
        if not self._scan_active:
            return

        final_snap = self._current_decode_snapshot(include_channel_hits=True) or snap
        self._point_duration_s = self._measurement_duration_s(final_snap)
        self._stop_hardware_run()
        if self.backend and self.backend.is_running():
            self.backend.stop_capture()
            final_snap = getattr(self.backend, "_last_decode_snapshot", None) or final_snap
        self._set_analysis_emit_suppressed(False)

        value = int(self._values[self._index])
        result = self._result_from_snapshot(value, final_snap)
        if result is not None:
            self._results.append(result)
            self._write_summary()
            self._refresh_result_dialog()
            avg_rate = float(result.get("avg_rate_hz", float("nan")))
            rate_text = "nan" if not np.isfinite(avg_rate) else f"{avg_rate:.6g}"
            print(
                f"[NoiseScan] {self._setting_label()} {value}: "
                f"average noise rate/channel = {rate_text} Hz over "
                f"{int(result.get('n_channels', 0) or 0)} channels"
            )
        else:
            print(f"[NoiseScan] No result recorded for {self._setting_label()} {value}")

        self._index += 1
        QtCore.QTimer.singleShot(250, self._start_next_point)

    def _event_windows(self, snap) -> int:
        if snap is None:
            return 0
        try:
            headers = int(getattr(snap, "headers", getattr(snap, "header_cnt", 0)) or 0)
        except Exception:
            headers = 0
        if headers > 0:
            return headers

        try:
            fifo_windows = int(getattr(snap, "events_fifoA", 0) or 0) + int(getattr(snap, "events_fifoB", 0) or 0)
        except Exception:
            fifo_windows = 0
        if fifo_windows > 0:
            return fifo_windows

        try:
            return max(0, int(getattr(snap, "trailers", getattr(snap, "trailer_cnt", 0)) or 0))
        except Exception:
            return 0

    def _result_from_snapshot(self, value: int, snap):
        if snap is None:
            print("[NoiseScan] Missing decode snapshot; cannot calculate noise rate.")
            return None
        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERLESS_COUNT:
            channel_hits = getattr(snap, "noise_counter_total", None)
            missing_name = "noise_counter_total"
        else:
            channel_hits = getattr(snap, "raw_hit_ch_count", None)
            missing_name = "raw_hit_ch_count"
        if channel_hits is None:
            print(f"[NoiseScan] Decode snapshot has no {missing_name}; cannot calculate noise rate.")
            return None

        events = self._event_windows(snap)
        duration_s = self._measurement_duration_s(snap)
        if duration_s <= 0.0:
            print("[NoiseScan] Scan point has no valid measurement duration.")
            return None

        arr = np.asarray(channel_hits)
        if arr.ndim != 2:
            print(f"[NoiseScan] Decode snapshot {missing_name} has invalid dimensions.")
            return None
        decode_error_counts = np.asarray(
            getattr(snap, "noise_decode_error_count", np.zeros((0,), dtype=np.uint64))
        )
        invalid_channel_counts = np.asarray(
            getattr(snap, "noise_invalid_channel_count", np.zeros((0,), dtype=np.uint64))
        )
        rows = []
        total_hits = 0
        total_decode_errors = 0
        total_invalid_channels = 0
        tdc_to_mezz = {
            int(csm) * 20 + int(mezz): (int(csm), int(mezz))
            for csm, mezz in self._selected_mezz
        }
        for tdc, channels in sorted(self._active_channels.items()):
            if tdc < 0 or tdc >= arr.shape[0]:
                continue
            decode_error_count = (
                int(decode_error_counts[tdc])
                if decode_error_counts.ndim == 1 and tdc < decode_error_counts.shape[0]
                else 0
            )
            invalid_channel_count = (
                int(invalid_channel_counts[tdc])
                if invalid_channel_counts.ndim == 1 and tdc < invalid_channel_counts.shape[0]
                else 0
            )
            total_decode_errors += decode_error_count
            total_invalid_channels += invalid_channel_count
            csm, mezz = tdc_to_mezz.get(tdc, (tdc // 20, tdc % 20))
            for ch in sorted(channels):
                if ch < 0 or ch >= arr.shape[1]:
                    continue
                hit_count = int(arr[tdc, ch])
                total_hits += hit_count
                rate_hz = float(hit_count) / duration_s
                rows.append(
                    {
                        "tdc_global": int(tdc),
                        "csm_id": int(csm),
                        "mezz": int(mezz),
                        "channel_id": int(ch),
                        "hit_count": hit_count,
                        "rate_hz": rate_hz,
                        "tdc_kerr_derr_count": decode_error_count,
                        "tdc_invalid_channel_count": invalid_channel_count,
                    }
                )

        if not rows:
            print("[NoiseScan] No active selected channels to write.")
            return None

        n_channels = len(rows)
        avg_rate_hz = float(total_hits) / (duration_s * float(n_channels))
        detail_dir = os.path.dirname(self._current_out_path) if self._current_out_path else self._output_dir
        csv_path = os.path.join(detail_dir, f"{self._file_stem()}_hits.csv")
        self._write_detail_csv(csv_path, rows, events, duration_s)

        return {
            "scan_type": self._scan_type,
            "acquisition_mode": self._noise_acquisition_mode,
            "scan_value": int(value),
            "threshold": int(self._current_threshold),
            "hyst": int(self._current_hyst),
            "events": int(events),
            "target_events": int(self._event_count)
            if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED
            else 0,
            "target_value": int(self._event_count),
            "target_unit": self._target_unit(),
            "duration_s": float(duration_s),
            "avg_rate_hz": avg_rate_hz,
            "n_channels": n_channels,
            "total_hits": int(total_hits),
            "total_kerr_derr": int(total_decode_errors),
            "total_invalid_channels": int(total_invalid_channels),
            "disabled_channel_count": int(len(self._disabled_channels)),
            "disabled_channels": self._disabled_channel_text(self._disabled_channels),
            "csv_path": csv_path,
            "dat_path": self._current_out_path,
        }

    def _write_detail_csv(self, path: str, rows, events: int, duration_s: float):
        try:
            with open(path, "w", newline="") as f:
                fieldnames = [
                    "scan_type",
                    "acquisition_mode",
                    "scan_value",
                    "threshold",
                    "main_thr",
                    "hyst",
                    "target_events",
                    "target_value",
                    "target_unit",
                    "events",
                    "time_window_s",
                    "duration_s",
                    "tdc_global",
                    "csm_id",
                    "mezz",
                    "channel_id",
                    "active",
                    "hit_count",
                    "rate_hz",
                    "tdc_kerr_derr_count",
                    "tdc_invalid_channel_count",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                scan_value = self._current_hyst if self._scan_type == "hyst" else self._current_threshold
                for row in rows:
                    out = {
                        "scan_type": self._scan_type,
                        "acquisition_mode": self._noise_acquisition_mode,
                        "scan_value": int(scan_value),
                        "threshold": int(self._current_threshold),
                        "main_thr": int(self._current_threshold),
                        "hyst": int(self._current_hyst),
                        "target_events": int(self._event_count)
                        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED
                        else 0,
                        "target_value": int(self._event_count),
                        "target_unit": self._target_unit(),
                        "events": int(events),
                        "time_window_s": CH_HIT_TIME_WINDOW_S
                        if self._noise_acquisition_mode == NOISE_SCAN_TRIGGERED
                        else 0.0,
                        "duration_s": float(duration_s),
                        "active": 1,
                    }
                    out.update(row)
                    writer.writerow(out)
            print(f"[NoiseScan] Detail CSV: {path}")
        except Exception as e:
            print(f"[ERROR] Failed to write noise scan detail CSV: {e}")

    def _write_summary(self):
        if not self._summary_path:
            return
        try:
            with open(self._summary_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "scan_type",
                        "acquisition_mode",
                        "scan_value",
                        "threshold",
                        "main_thr",
                        "hyst",
                        "average_noise_rate_per_channel_hz",
                        "avg_rate_hz",
                        "n_channels",
                        "target_events",
                        "target_value",
                        "target_unit",
                        "events",
                        "duration_s",
                        "total_hits",
                        "total_kerr_derr",
                        "total_invalid_channels",
                        "disabled_channel_count",
                        "disabled_channels",
                        "selected_mezz",
                        "detail_csv",
                        "dat_file",
                    ]
                )
                selected = ";".join(f"CSM{csm}/Mezz{mezz}" for csm, mezz in self._selected_mezz)
                for result in self._results:
                    writer.writerow(
                        [
                            str(result.get("scan_type", self._scan_type) or self._scan_type),
                            str(
                                result.get("acquisition_mode", self._noise_acquisition_mode)
                                or self._noise_acquisition_mode
                            ),
                            int(result.get("scan_value", result.get("threshold", 0))),
                            int(result.get("threshold", -1)),
                            int(result.get("threshold", -1)),
                            int(result.get("hyst", -1)),
                            float(result.get("avg_rate_hz", float("nan"))),
                            float(result.get("avg_rate_hz", float("nan"))),
                            int(result.get("n_channels", 0) or 0),
                            int(result.get("target_events", self._event_count) or 0),
                            int(result.get("target_value", self._event_count) or 0),
                            str(result.get("target_unit", self._target_unit()) or self._target_unit()),
                            int(result.get("events", 0) or 0),
                            float(result.get("duration_s", 0.0) or 0.0),
                            int(result.get("total_hits", 0) or 0),
                            int(result.get("total_kerr_derr", 0) or 0),
                            int(result.get("total_invalid_channels", 0) or 0),
                            int(result.get("disabled_channel_count", 0) or 0),
                            str(result.get("disabled_channels", "") or ""),
                            selected,
                            str(result.get("csv_path", "") or ""),
                            str(result.get("dat_path", "") or ""),
                        ]
                    )
        except Exception as e:
            print(f"[ERROR] Failed to write noise scan summary CSV: {e}")

    def _remember_summary(self):
        if not self._summary_path or not os.path.isfile(self._summary_path):
            return
        self._last_summary_path = self._summary_path
        self.settings.setValue("noise_scan/last_summary", self._last_summary_path)
        self.settings.sync()

    def cancel(self):
        if not self._scan_active:
            return
        print("[NoiseScan] Cancel requested.")
        self._cancel_requested = True
        if self._timer.isActive():
            self._timer.stop()
        self._stop_hardware_run()
        if self.backend and self.backend.is_running():
            self.backend.stop_capture()
        self._finish(cancelled=True)

    def _finish(self, *, cancelled: bool):
        if not self._scan_active:
            return
        if self._timer.isActive():
            self._timer.stop()

        self._stop_hardware_run()
        if self.backend and self.backend.is_running():
            self.backend.stop_capture()
        self._scan_active = False
        self._cancel_requested = False
        self._set_analysis_emit_suppressed(False)
        self._set_controls(False)
        self.btn_start.setEnabled(True)
        self.btn_process.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if self._results:
            self._write_summary()
            self._remember_summary()
            print(f"[NoiseScan] Summary CSV: {self._summary_path}")
            self.show_results()

        if cancelled:
            print("[NoiseScan] Cancelled.")
        else:
            print("[NoiseScan] Complete.")

    def show_results(self):
        results, source_label = self._result_payload()
        start_dir = self.edit_outdir.text().strip() or os.getcwd()
        summary_hint = self._summary_path or self._last_summary_path
        if summary_hint:
            start_dir = os.path.dirname(summary_hint)

        if self._result_dialog is None:
            self._result_dialog = NoiseScanResultDialog(self.tab.parent, start_dir=start_dir)
            self._result_dialog.set_results(results, label=source_label)
        else:
            self._result_dialog.replace_results(results, label=source_label)

        self._result_dialog.show()
        self._result_dialog.raise_()
        self._result_dialog.activateWindow()

    def _refresh_result_dialog(self):
        if self._result_dialog is None:
            return
        if not self._result_dialog.isVisible():
            return
        results, source_label = self._result_payload()
        self._result_dialog.replace_results(results, label=source_label)

    def _result_payload(self):
        results = list(self._results)
        source_label = "Current scan"
        if not results and (not self._scan_active) and self._last_summary_path:
            results = NoiseScanResultDialog._load_summary_results(self._last_summary_path)
            if results:
                self._results = results
                source_label = os.path.basename(self._last_summary_path)
        return results, source_label

    def _active_channel_map(self, selected_mezz=None):
        selected_mezz = list(selected_mezz if selected_mezz is not None else self._selected_mezz)
        fallback = {
            int(which_csm) * 20 + int(mezz): list(range(24))
            for which_csm, mezz in selected_mezz
        }
        if self._active_channels_callback is None:
            return fallback

        try:
            raw_map = self._active_channels_callback(selected_mezz)
        except TypeError:
            raw_map = self._active_channels_callback()
        except Exception as e:
            print(f"[NoiseScan] Failed to read active channel mask; using all channels: {e}")
            return fallback

        if not isinstance(raw_map, dict):
            print("[NoiseScan] Invalid active channel mask; using all channels.")
            return fallback

        normalized = {}
        for tdc, channels in raw_map.items():
            try:
                tdc = int(tdc)
            except Exception:
                continue
            clean_channels = []
            for ch in channels or []:
                try:
                    ch = int(ch)
                except Exception:
                    continue
                if 0 <= ch < 24 and ch not in clean_channels:
                    clean_channels.append(ch)
            normalized[tdc] = clean_channels

        for tdc in fallback:
            normalized.setdefault(tdc, fallback[tdc])
        return normalized

    def _disabled_channel_list(self, selected_mezz=None):
        if self._disabled_channels_callback is None:
            return []
        selected_mezz = list(selected_mezz if selected_mezz is not None else self._selected_mezz)
        try:
            disabled = self._disabled_channels_callback(selected_mezz) or []
        except TypeError:
            try:
                disabled = self._disabled_channels_callback() or []
            except Exception as e:
                print(f"[NoiseScan] Failed to read disabled channel mask: {e}")
                return []
        except Exception as e:
            print(f"[NoiseScan] Failed to read disabled channel mask: {e}")
            return []

        try:
            return list(disabled)
        except Exception:
            return []

    @staticmethod
    def _active_channel_count(active_channels) -> int:
        return sum(len(channels) for channels in (active_channels or {}).values())

    @staticmethod
    def _disabled_channel_text(disabled_channels) -> str:
        parts = []
        for item in disabled_channels or []:
            if not isinstance(item, dict):
                continue
            location = str(item.get("location", "") or "").strip()
            if not location:
                try:
                    location = (
                        f"CSM{int(item.get('csm_id', -1))}/Mezz{int(item.get('mezz', -1))}/"
                        f"TDC{int(item.get('tdc_global', item.get('tdc_id', -1))):02d}/"
                        f"CH{int(item.get('channel_id', -1)):02d}"
                    )
                except Exception:
                    location = "unknown"
            source = str(item.get("disabled_in", "") or "").strip()
            reason = str(item.get("disabled_reason", "") or "").strip()
            text = location
            if source:
                text += f" disabled_in={source}"
            if reason:
                text += f" reason={reason}"
            parts.append(text)
        return " | ".join(parts)
