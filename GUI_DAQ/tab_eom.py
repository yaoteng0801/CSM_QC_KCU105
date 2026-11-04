from __future__ import annotations

import csv
import os
import time
from datetime import datetime

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from TDC_config_low_level_function import (
    lpgbt_config_read,
    lpgbt_config_write,
)
from lpgbt_register_map_v1 import LpgbtRegisterMapV1


class EOMScanWorker(QtCore.QObject):
    point = QtCore.pyqtSignal(int, int, int, int, float)
    progress = QtCore.pyqtSignal(int, int)
    message = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(object)

    def __init__(
        self,
        eth,
        which_csm,
        lpgbt_addr,
        uplink_index,
        lpgbt_role,
        phase_values,
        vof_values,
        end_count_sel,
        normalize_mode,
        bias_delay_ms,
        settle_delay_ms,
        poll_interval_ms,
        timeout_ms,
        bypass_phase_interpolator=False,
        start_point_index=0,
    ):
        super().__init__()
        self.eth = eth
        self.which_csm = int(which_csm)
        self.lpgbt_addr = int(lpgbt_addr)
        self.uplink_index = int(uplink_index)
        self.lpgbt_role = str(lpgbt_role)
        self.phase_values = list(phase_values)
        self.vof_values = list(vof_values)
        self.end_count_sel = int(end_count_sel)
        self.normalize_mode = str(normalize_mode)
        self.bias_delay_s = max(float(bias_delay_ms), 0.0) / 1000.0
        self.settle_delay_s = max(float(settle_delay_ms), 0.0) / 1000.0
        self.poll_interval_s = max(float(poll_interval_ms), 0.1) / 1000.0
        self.timeout_s = max(float(timeout_ms), 1.0) / 1000.0
        self.bypass_phase_interpolator = bool(bypass_phase_interpolator)
        self.start_point_index = max(int(start_point_index), 0)
        self.response_timeout_s = 1.0
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    @QtCore.pyqtSlot()
    def run(self):
        rows = []
        cancelled = False
        timed_out = False
        error_text = None
        total = len(self.phase_values) * len(self.vof_values)
        start_point_index = min(self.start_point_index, total)
        done = start_point_index
        current_vof = None
        current_phase = None

        config_base = (
            ((self.end_count_sel & 0xF) << LpgbtRegisterMapV1.EOMCONFIGH.EOMENDOFCOUNTSEL.offset)
            | (0x04 if self.bypass_phase_interpolator else 0x00)
            | LpgbtRegisterMapV1.EOMCONFIGH.EOMENABLE.bit_mask
        )

        try:
            self.message.emit(
                f"Selecting CSM {self.which_csm}, {self.lpgbt_role} lpGBT "
                f"(addr 0x{self.lpgbt_addr:02X}, uplink {self.uplink_index})"
            )
            # Ethernet lpGBT commands carry the uplink in their target field.
            # _read_regs() and _write_reg() pass which_csm/lpgbt_addr so the
            # low-level helper selects this uplink for every transaction.

            self.message.emit("Enabling EOM bias")
            self._write_reg(LpgbtRegisterMapV1.EOMCONFIGH.address, config_base)
            time.sleep(self.bias_delay_s)
            self.progress.emit(done, total)

            phase_count = len(self.phase_values)
            for vof_index, vof in enumerate(self.vof_values):
                if self._cancel_requested:
                    cancelled = True
                    break

                row_start = vof_index * phase_count
                if row_start + phase_count <= start_point_index:
                    continue

                current_vof = vof
                current_phase = None
                self._write_reg(LpgbtRegisterMapV1.EOMVOFSEL.address, vof)

                for phase_index, phase in enumerate(self.phase_values):
                    if self._cancel_requested:
                        cancelled = True
                        break

                    point_index = row_start + phase_index
                    if point_index < start_point_index:
                        continue

                    current_phase = phase
                    self._write_reg(LpgbtRegisterMapV1.EOMCONFIGL.address, phase)
                    time.sleep(self.settle_delay_s)

                    self._write_reg(
                        LpgbtRegisterMapV1.EOMCONFIGH.address,
                        config_base | LpgbtRegisterMapV1.EOMCONFIGH.EOMSTART.bit_mask,
                    )
                    status, counter, counter40 = self._wait_for_eom_done()
                    normalized = self._normalize(counter, counter40)

                    rows.append(
                        {
                            "csm": self.which_csm,
                            "lpgbt_role": self.lpgbt_role,
                            "lpgbt_addr": self.lpgbt_addr,
                            "uplink_index": self.uplink_index,
                            "phase": phase,
                            "vof": vof,
                            "counter": counter,
                            "counter40": counter40,
                            "normalized": normalized,
                            "status": status,
                            "end_count_sel": self.end_count_sel,
                            "normalize_mode": self.normalize_mode,
                        }
                    )

                    self.point.emit(phase, vof, counter, counter40, normalized)
                    done = point_index + 1
                    self.progress.emit(done, total)

                    self._write_reg(LpgbtRegisterMapV1.EOMCONFIGH.address, config_base)

            if cancelled:
                self.message.emit("EOM scan cancelled")
            else:
                self.message.emit("EOM scan finished")
        except TimeoutError as exc:
            timed_out = True
            if current_phase is not None:
                location = f"phase={current_phase}, VOF={current_vof}"
            elif current_vof is not None:
                location = f"VOF={current_vof} setup"
            else:
                location = "scan setup"
            error_text = f"EOM timeout at {location}: {exc}"
            self.error.emit(error_text)
        except Exception as exc:
            error_text = str(exc)
            self.error.emit(error_text)
        finally:
            try:
                self._write_reg(LpgbtRegisterMapV1.EOMCONFIGH.address, 0)
            except Exception as exc:
                disable_error = f"Failed to disable EOM: {exc}"
                if error_text is None:
                    error_text = disable_error
                self.error.emit(disable_error)

            self.finished.emit(
                {
                    "rows": rows,
                    "cancelled": cancelled,
                    "timed_out": timed_out,
                    "error": error_text,
                    "next_point_index": done,
                    "total_points": total,
                    "failed_phase": current_phase,
                    "failed_vof": current_vof,
                    "phase_values": self.phase_values,
                    "vof_values": self.vof_values,
                    "which_csm": self.which_csm,
                    "lpgbt_addr": self.lpgbt_addr,
                    "lpgbt_role": self.lpgbt_role,
                    "uplink_index": self.uplink_index,
                    "end_count_sel": self.end_count_sel,
                    "normalize_mode": self.normalize_mode,
                }
            )

    def _read_reg(self, reg_addr):
        return self._read_regs(reg_addr, 1)[0]

    def _read_regs(self, reg_addr, count):
        reg_addr = int(reg_addr)
        count = int(count)

        data = lpgbt_config_read(
            self.eth,
            lpgbt_addr=self.lpgbt_addr,
            reg_addr=reg_addr,
            nb_read=count,
            verbose=False,
            response_timeout_s=self.response_timeout_s,
            which_csm=self.which_csm,
        )

        if not isinstance(data, (list, tuple, bytes, bytearray)) or len(data) != count:
            raise RuntimeError(
                f"lpGBT read failed at register 0x{reg_addr:03X}: "
                f"expected {count} byte(s), received {data}"
            )
        return [int(value) & 0xFF for value in data]

    def _write_reg(self, reg_addr, value):
        value = int(value) & 0xFF
        data = lpgbt_config_write(
            self.eth,
            reg_addr=int(reg_addr),
            value_list=[value],
            which_csm=self.which_csm,
            lpgbt_addr=self.lpgbt_addr,
            verbose=False,
            response_timeout_s=self.response_timeout_s,
        )
        if not isinstance(data, list) or data != [value]:
            raise RuntimeError(
                f"lpGBT write failed at register 0x{int(reg_addr):03X}: "
                f"expected reply {[value]}, received {data}"
            )

    def _wait_for_eom_done(self):
        deadline = time.monotonic() + self.timeout_s
        last_status = None

        while time.monotonic() < deadline:
            # Status and both 16-bit counters occupy five contiguous registers.
            # Reading them together replaces five lpGBT transactions with one.
            measurement = self._read_regs(LpgbtRegisterMapV1.EOMSTATUS.address, 5)
            status = measurement[0]
            ended = bool(status & LpgbtRegisterMapV1.EOMSTATUS.EOMEND.bit_mask)
            if ended:
                counter = (measurement[1] << 8) | measurement[2]
                counter40 = (measurement[3] << 8) | measurement[4]
                return status, counter, counter40
            last_status = status
            time.sleep(self.poll_interval_s)

        status_detail = "no status received"
        if last_status is not None:
            busy = int(bool(last_status & LpgbtRegisterMapV1.EOMSTATUS.EOMBUSY.bit_mask))
            state = (
                last_status & LpgbtRegisterMapV1.EOMSTATUS.EOMSMSTATE.bit_mask
            ) >> LpgbtRegisterMapV1.EOMSTATUS.EOMSMSTATE.offset
            status_detail = (
                f"last status=0x{last_status:02X} "
                f"(EOMEND=0, EOMBUSY={busy}, EOMSMSTATE={state})"
            )
        raise TimeoutError(
            f"EOMEND did not assert within {self.timeout_s:.3f} s; {status_detail}"
        )

    def _normalize(self, counter, counter40):
        if self.normalize_mode == "counter40":
            return float(counter) / float(counter40) if counter40 else 0.0
        if self.normalize_mode == "max32767":
            return float(counter) / 32767.0
        return float(counter)


class tab_eom(object):
    def __init__(self, MainWindow, eth):
        self.MainWindow = MainWindow
        self.eth = eth
        self.thread = None
        self.worker = None
        self._matrix = None
        self._phase_index = {}
        self._vof_index = {}
        self._last_result = None
        self._last_rows = []
        self._active_selection = None
        self._active_scan_signature = None
        self._resume_scan_signature = None
        self._resume_point_index = None
        self._run_start_row_count = 0
        self.setup_UI(MainWindow)

    def set_ethernet_client(self, eth):
        self.eth = eth

    def setup_UI(self, MainWindow):
        self.main_layout = QtWidgets.QVBoxLayout(MainWindow)

        controls_group = QtWidgets.QGroupBox("Eye Opening Monitor Scan")
        controls = QtWidgets.QGridLayout(controls_group)

        self.spin_csm = QtWidgets.QSpinBox()
        self.spin_csm.setRange(0, 1)
        self.spin_csm.setValue(0)
        self.spin_csm.setToolTip("CSM number used to select the lpGBT uplink.")

        self.combo_lpgbt = QtWidgets.QComboBox()
        self.combo_lpgbt.addItem("Master (0x75)", {"role": "Master", "addr": 117, "uplink_offset": 0})
        self.combo_lpgbt.addItem("Slave (0x73)", {"role": "Slave", "addr": 115, "uplink_offset": 1})

        self.spin_end_count = QtWidgets.QSpinBox()
        self.spin_end_count.setRange(0, 10)
        self.spin_end_count.setValue(7)
        self.spin_end_count.setToolTip(
            "EOMendOfCountSel. The lpGBT manual limits this field to 10 to avoid counter overflow."
        )

        self.spin_phase_start = QtWidgets.QSpinBox()
        self.spin_phase_start.setRange(0, 63)
        self.spin_phase_start.setValue(0)

        self.spin_phase_end = QtWidgets.QSpinBox()
        self.spin_phase_end.setRange(0, 63)
        self.spin_phase_end.setValue(63)

        self.spin_vof_start = QtWidgets.QSpinBox()
        self.spin_vof_start.setRange(0, 30)
        self.spin_vof_start.setValue(0)

        self.spin_vof_end = QtWidgets.QSpinBox()
        self.spin_vof_end.setRange(0, 30)
        self.spin_vof_end.setValue(30)

        self.combo_normalize = QtWidgets.QComboBox()
        self.combo_normalize.addItem("Counter / EOMCounter40M", "counter40")
        self.combo_normalize.addItem("Counter / 32767", "max32767")
        self.combo_normalize.addItem("Raw counter", "raw")

        self.spin_bias_delay = QtWidgets.QSpinBox()
        self.spin_bias_delay.setRange(0, 1000)
        self.spin_bias_delay.setValue(5)
        self.spin_bias_delay.setSuffix(" ms")
        self.spin_bias_delay.setToolTip("Delay after EOMEnable before starting the first measurement.")

        self.spin_settle_delay = QtWidgets.QSpinBox()
        self.spin_settle_delay.setRange(0, 1000)
        self.spin_settle_delay.setValue(5)
        self.spin_settle_delay.setSuffix(" ms")
        self.spin_settle_delay.setToolTip("Delay after each phase/voltage-offset update before EOMStart.")

        self.spin_timeout = QtWidgets.QSpinBox()
        self.spin_timeout.setRange(1, 5000)
        self.spin_timeout.setValue(500)
        self.spin_timeout.setSuffix(" ms")
        self.spin_timeout.setToolTip("Maximum wait per EOM point before reporting a timeout.")

        self.check_bypass_phase = QtWidgets.QCheckBox("Bypass phase interpolator")
        self.check_bypass_phase.setToolTip(
            "Sets EOMBypassPhaseInterpolator. Leave unchecked for the normal 64-step phase scan."
        )

        self.button_start = QtWidgets.QPushButton("Start EOM Scan")
        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_cancel.setEnabled(False)
        self.button_save = QtWidgets.QPushButton("Save CSV")
        self.button_save.setEnabled(False)

        controls.addWidget(QtWidgets.QLabel("CSM#"), 0, 0)
        controls.addWidget(self.spin_csm, 0, 1)
        controls.addWidget(QtWidgets.QLabel("lpGBT"), 0, 2)
        controls.addWidget(self.combo_lpgbt, 0, 3)
        controls.addWidget(QtWidgets.QLabel("EOMendOfCountSel"), 0, 4)
        controls.addWidget(self.spin_end_count, 0, 5)

        controls.addWidget(QtWidgets.QLabel("Phase start"), 1, 0)
        controls.addWidget(self.spin_phase_start, 1, 1)
        controls.addWidget(QtWidgets.QLabel("Phase end"), 1, 2)
        controls.addWidget(self.spin_phase_end, 1, 3)
        controls.addWidget(QtWidgets.QLabel("VOF start"), 1, 4)
        controls.addWidget(self.spin_vof_start, 1, 5)
        controls.addWidget(QtWidgets.QLabel("VOF end"), 1, 6)
        controls.addWidget(self.spin_vof_end, 1, 7)

        controls.addWidget(QtWidgets.QLabel("Display"), 2, 0)
        controls.addWidget(self.combo_normalize, 2, 1, 1, 2)
        controls.addWidget(QtWidgets.QLabel("Bias delay"), 2, 3)
        controls.addWidget(self.spin_bias_delay, 2, 4)
        controls.addWidget(QtWidgets.QLabel("Point delay"), 2, 5)
        controls.addWidget(self.spin_settle_delay, 2, 6)
        controls.addWidget(QtWidgets.QLabel("Timeout"), 2, 7)
        controls.addWidget(self.spin_timeout, 2, 8)

        controls.addWidget(self.check_bypass_phase, 3, 0, 1, 3)
        controls.addWidget(self.button_start, 3, 5)
        controls.addWidget(self.button_cancel, 3, 6)
        controls.addWidget(self.button_save, 3, 7)

        self.main_layout.addWidget(controls_group)

        note = QtWidgets.QLabel(
            "Manual page 127, section 14.4: scan EOMphaseSel 0..63 and EOMvofSel 0..30, "
            "poll EOMStatus, then plot EOMcounterValue normalized by EOMCounter40M. "
            "Use after the high-speed receiver/CDR is locked; the tab disables EOM when the scan ends."
        )
        note.setWordWrap(True)
        self.main_layout.addWidget(note)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.main_layout.addWidget(self.progress)

        self.status_label = QtWidgets.QLabel("Idle")
        self.main_layout.addWidget(self.status_label)

        self.plot = pg.PlotWidget()
        self.plot.setLabel("bottom", "EOMphaseSel")
        self.plot.setLabel("left", "EOMvofSel")
        self.plot.setTitle("lpGBT Eye Opening Monitor")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMaximumHeight(320)
        self.plot.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred,
        )
        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)
        try:
            colormap = pg.colormap.get("viridis")
            self.image_item.setLookupTable(colormap.getLookupTable(0.0, 1.0, 256))
        except Exception:
            pass
        self.main_layout.addWidget(self.plot)

        self.button_start.clicked.connect(self.start_scan)
        self.button_cancel.clicked.connect(self.cancel_scan)
        self.button_save.clicked.connect(self.save_csv)

    def _lpgbt_selection(self):
        csm = self.spin_csm.value()
        data = self.combo_lpgbt.currentData()
        return {
            "which_csm": csm,
            "lpgbt_role": data["role"],
            "lpgbt_addr": data["addr"],
            "uplink_index": csm * 2 + data["uplink_offset"],
        }

    def _range_values(self, start_widget, end_widget):
        start = start_widget.value()
        end = end_widget.value()
        low = min(start, end)
        high = max(start, end)
        return list(range(low, high + 1))

    def _scan_signature(self, selection, phase_values, vof_values):
        return (
            selection["which_csm"],
            selection["lpgbt_addr"],
            selection["uplink_index"],
            tuple(phase_values),
            tuple(vof_values),
            self.spin_end_count.value(),
            self.combo_normalize.currentData(),
            self.spin_bias_delay.value(),
            self.spin_settle_delay.value(),
            self.spin_timeout.value(),
            self.check_bypass_phase.isChecked(),
        )

    def start_scan(self):
        if self.thread is not None:
            return

        phase_values = self._range_values(self.spin_phase_start, self.spin_phase_end)
        vof_values = self._range_values(self.spin_vof_start, self.spin_vof_end)
        if not phase_values or not vof_values:
            QtWidgets.QMessageBox.warning(self.MainWindow, "EOM scan", "Phase and VOF ranges must not be empty.")
            return

        selection = self._lpgbt_selection()
        scan_signature = self._scan_signature(selection, phase_values, vof_values)
        total = len(phase_values) * len(vof_values)
        resume_scan = (
            scan_signature == self._resume_scan_signature
            and self._resume_point_index is not None
            and 0 <= self._resume_point_index < total
        )
        start_point_index = self._resume_point_index if resume_scan else 0

        self._active_selection = dict(selection)
        self._active_scan_signature = scan_signature
        self._phase_index = {value: index for index, value in enumerate(phase_values)}
        self._vof_index = {value: index for index, value in enumerate(vof_values)}
        if not resume_scan:
            self._matrix = np.full((len(vof_values), len(phase_values)), np.nan, dtype=float)
            self._last_rows = []
            self._resume_scan_signature = None
            self._resume_point_index = None
        self._run_start_row_count = len(self._last_rows)
        self._last_result = None
        self._refresh_image(auto_levels=True)
        self._set_controls_running(True)

        self.progress.setRange(0, total)
        self.progress.setValue(start_point_index)
        if resume_scan:
            phase = phase_values[start_point_index % len(phase_values)]
            vof = vof_values[start_point_index // len(phase_values)]
            self.status_label.setText(
                f"Resuming EOM scan at phase={phase}, VOF={vof} "
                f"({start_point_index}/{total} points complete)"
            )
        else:
            self.button_start.setText("Start EOM Scan")
            self.status_label.setText(f"Starting EOM scan with {total} points")

        self.thread = QtCore.QThread()
        self.worker = EOMScanWorker(
            eth=self.eth,
            which_csm=selection["which_csm"],
            lpgbt_addr=selection["lpgbt_addr"],
            uplink_index=selection["uplink_index"],
            lpgbt_role=selection["lpgbt_role"],
            phase_values=phase_values,
            vof_values=vof_values,
            end_count_sel=self.spin_end_count.value(),
            normalize_mode=self.combo_normalize.currentData(),
            bias_delay_ms=self.spin_bias_delay.value(),
            settle_delay_ms=self.spin_settle_delay.value(),
            poll_interval_ms=1,
            timeout_ms=self.spin_timeout.value(),
            bypass_phase_interpolator=self.check_bypass_phase.isChecked(),
            start_point_index=start_point_index,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.point.connect(self._on_point)
        self.worker.progress.connect(self._on_progress)
        self.worker.message.connect(self._on_message)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._thread_finished)
        self.thread.start()

    def cancel_scan(self):
        if self.worker is not None:
            self.status_label.setText("Cancelling EOM scan...")
            self.worker.cancel()

    def save_csv(self):
        if not self._last_rows:
            QtWidgets.QMessageBox.information(self.MainWindow, "EOM scan", "No EOM scan data to save yet.")
            return

        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"eom_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        fieldnames = [
            "csm",
            "lpgbt_role",
            "lpgbt_addr",
            "uplink_index",
            "phase",
            "vof",
            "counter",
            "counter40",
            "normalized",
            "status",
            "end_count_sel",
            "normalize_mode",
        ]
        with open(path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._last_rows)

        self.status_label.setText(f"Saved EOM CSV: {path}")

    def _on_point(self, phase, vof, counter, counter40, normalized):
        selection = self._active_selection or self._lpgbt_selection()
        self._last_rows.append(
            {
                "csm": selection["which_csm"],
                "lpgbt_role": selection["lpgbt_role"],
                "lpgbt_addr": selection["lpgbt_addr"],
                "uplink_index": selection["uplink_index"],
                "phase": phase,
                "vof": vof,
                "counter": counter,
                "counter40": counter40,
                "normalized": normalized,
                "status": "",
                "end_count_sel": self.spin_end_count.value(),
                "normalize_mode": self.combo_normalize.currentData(),
            }
        )

        phase_index = self._phase_index.get(phase)
        vof_index = self._vof_index.get(vof)
        if self._matrix is not None and phase_index is not None and vof_index is not None:
            self._matrix[vof_index, phase_index] = normalized
            self._refresh_image(auto_levels=True)

        self.status_label.setText(
            f"phase={phase}, vof={vof}, counter={counter}, counter40={counter40}, value={normalized:.6g}"
        )

    def _on_progress(self, done, total):
        self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _on_message(self, text):
        self.status_label.setText(text)
        print(f"[EOM] {text}")

    def _on_error(self, text):
        self.status_label.setText(f"EOM scan error: {text}")
        print(f"[EOM ERROR] {text}")

    def _on_finished(self, result):
        self._last_result = result
        if isinstance(result, dict):
            self._last_rows = (
                self._last_rows[:self._run_start_row_count]
                + list(result.get("rows") or [])
            )
        if self._last_rows:
            self.button_save.setEnabled(True)

        if isinstance(result, dict) and result.get("cancelled"):
            self._resume_scan_signature = None
            self._resume_point_index = None
            self.button_start.setText("Start EOM Scan")
            self.status_label.setText(f"EOM scan cancelled after {len(self._last_rows)} points")
        elif (
            isinstance(result, dict)
            and result.get("error")
            and int(result.get("next_point_index", 0)) < int(result.get("total_points", 0))
        ):
            self._resume_scan_signature = self._active_scan_signature
            self._resume_point_index = int(result.get("next_point_index", 0))
            phase_values = list(result.get("phase_values") or [])
            vof_values = list(result.get("vof_values") or [])
            phase = phase_values[self._resume_point_index % len(phase_values)]
            vof = vof_values[self._resume_point_index // len(phase_values)]
            self.button_start.setText("Resume EOM Scan")
            failure_kind = "timed out" if result.get("timed_out") else "failed"
            self.status_label.setText(
                f"EOM scan {failure_kind} after {self._resume_point_index}/"
                f"{result.get('total_points')} points; next Start resumes at "
                f"phase={phase}, VOF={vof}. {result.get('error')}"
            )
        elif isinstance(result, dict) and result.get("error"):
            self._resume_scan_signature = None
            self._resume_point_index = None
            self.button_start.setText("Start EOM Scan")
            self.status_label.setText(
                f"EOM scan stopped after {len(self._last_rows)} points: {result.get('error')}"
            )
        else:
            self._resume_scan_signature = None
            self._resume_point_index = None
            self.button_start.setText("Start EOM Scan")
            self.status_label.setText(f"EOM scan complete: {len(self._last_rows)} points")

        # Keep Start disabled until QThread.finished clears self.thread.  If it
        # is enabled here, an immediate Resume click reaches start_scan while
        # the old thread is still present and is silently ignored.
        self.button_cancel.setEnabled(False)

    def _thread_finished(self):
        self.thread = None
        self.worker = None
        self._set_controls_running(False)

    def _set_controls_running(self, running):
        self.button_start.setEnabled(not running)
        self.button_cancel.setEnabled(running)
        self.button_save.setEnabled((not running) and bool(self._last_rows))
        for widget in (
            self.spin_csm,
            self.combo_lpgbt,
            self.spin_end_count,
            self.spin_phase_start,
            self.spin_phase_end,
            self.spin_vof_start,
            self.spin_vof_end,
            self.combo_normalize,
            self.spin_bias_delay,
            self.spin_settle_delay,
            self.spin_timeout,
            self.check_bypass_phase,
        ):
            widget.setEnabled(not running)

    def _refresh_image(self, auto_levels=False):
        if self._matrix is None:
            return

        display_matrix = np.nan_to_num(self._matrix, nan=0.0)
        self.image_item.setImage(display_matrix.T, autoLevels=auto_levels)

        phase_values = list(self._phase_index.keys())
        vof_values = list(self._vof_index.keys())
        if phase_values and vof_values:
            rect = QtCore.QRectF(
                min(phase_values) - 0.5,
                min(vof_values) - 0.5,
                max(1, len(phase_values)),
                max(1, len(vof_values)),
            )
            self.image_item.setRect(rect)
