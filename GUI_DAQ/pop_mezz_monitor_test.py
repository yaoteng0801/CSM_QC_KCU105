"""Continuous ADC communication tests for the Mezz Monitor selection."""

import csv
from datetime import datetime
from pathlib import Path
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS, MonitorLimitsWidget, ALARM_STYLE, range_error

from pop_jtag_debug import JTAGDebugDialog
from SCA_share import SCA_share
from TDC_config_low_level_function import (
    SCA_connect, SCA_config, SCA_enable_adc, ethernet_exclusive_session, sca_reply_retry_reporting,
)


MUX_NAMES = ("AVDD", "AVDD_GND", "DVDD", "DVDD_GND", "TEMP", "TEMP_GND")


class MezzMonitorTestWorker(QtCore.QThread):
    result = QtCore.pyqtSignal(int, int, object, bool, str)
    message_out = QtCore.pyqtSignal(str)

    def __init__(self, controller, selected, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.selected = tuple(selected)
        self.stop_requested = threading.Event()
        self.target_index = 0
        self.initialized = set()
        self.limits = (controller.get_monitor_limits() if hasattr(controller, "get_monitor_limits")
                       else dict(DEFAULT_MONITOR_LIMITS))
        with Path(__file__).with_name("sca_mapping.csv").open(newline="") as source:
            self.mapping = {row[""]: row for row in csv.DictReader(source)}

    def stop(self):
        self.stop_requested.set()

    def _test(self, csm, mezz):
        controller = self.controller
        column = str(mezz)
        sca = int(self.mapping["SCA"][column])
        target = (csm, sca)
        raw = {}
        errors = []
        values = {"AVDD": None, "DVDD": None, "Temp": None}
        # Keep mux selection and conversion together, including all six reads.
        with ethernet_exclusive_session(controller.eth):
            def config(channel, command, data):
                return SCA_config(
                    controller.eth, sca_enable=1 << sca, which_csm=csm,
                    sca_address=0, transID=controller.get_transID(), channel=channel,
                    datalen=4, command=command, data=data,
                )

            if target not in self.initialized:
                SCA_connect(controller.eth, sca_enable=1 << sca, which_csm=csm,
                            sca_address=0, verbose=0)
                SCA_enable_adc(controller.eth, controller.get_transID,
                               sca_enable=1 << sca, which_csm=csm)
                self.initialized.add(target)

            for name in MUX_NAMES:
                try:
                    config(SCA_share.ADC_CHANNEL, SCA_share.ADC_W_MUX,
                           int(self.mapping[name][column]))
                    channel, error, adc = config(
                        SCA_share.ADC_CHANNEL, SCA_share.ADC_GO, SCA_share.ADC_GO_DATA)
                    if channel != SCA_share.ADC_CHANNEL or error or not 0 <= adc < 4096:
                        raise RuntimeError(f"Invalid ADC reply: channel={channel}, error={error}, value={adc}")
                    raw[name] = adc / 4096.0
                except Exception as exc:
                    errors.append(f"{name}: {exc}")

            for label, positive, ground, scale in (
                ("AVDD", "AVDD", "AVDD_GND", 6.7),
                ("DVDD", "DVDD", "DVDD_GND", 6.7),
                ("Temp", "TEMP", "TEMP_GND", 3.0),
            ):
                if positive in raw and ground in raw:
                    value = raw[positive] * scale - raw[ground]
                    values[label] = (value - 0.5) * 100 if label == "Temp" else value
            if errors:
                self.initialized.discard(target)
        errors.extend(message for label, value in values.items()
                      if value is not None and (message := range_error(label, value, self.limits)))
        return values, not errors, "; ".join(errors)

    def run(self):
        while not self.stop_requested.is_set():
            csm, mezz = self.selected[self.target_index]
            try:
                with sca_reply_retry_reporting(self._report_retry):
                    values, valid, detail = self._test(csm, mezz)
            except Exception as exc:
                # Initialization failures also count once; retry initialization
                # on the next visit without stopping the other mezzanines.
                values, valid, detail = {}, False, str(exc)
            if not valid:
                print(f"[Mezz Monitor Test] CSM{csm}, Mezz{mezz} error: {detail}")
            self.target_index = (self.target_index + 1) % len(self.selected)
            self.result.emit(csm, mezz, values, valid, detail)

    def _report_retry(self, message):
        self.message_out.emit(message)
        print(f"[Mezz Monitor Test] {message}")


class MezzMonitorTestDialog(JTAGDebugDialog):
    """Use the same Start/Stop/Continue/Reset/Close lifecycle as JTAG debug."""

    def __init__(self, controller, selected, parent=None):
        super().__init__(controller, selected, parent)
        self.setWindowTitle("Mezz Monitor Test")
        self.description.setText(
            "Continuously read AVDD, DVDD and temperature on the selected mezzanines.\n"
            "One test reads all six ADC inputs for one mezzanine. Any command failure or invalid "
            "ADC code or out-of-range reading counts as one error. SCA reply mismatches get up to 3 attempts "
            "with fresh transaction IDs.\n"
            "ADC-enable acknowledgement mismatches are ignored; mux and conversion replies are checked.\n"
            "Recovered mismatches appear in the history without adding a failed test.\n"
            "Start begins a new run; Stop pauses; Continue resumes; Reset stops and clears results.\n"
            "A test with multiple failed readings still adds only one error."
        )
        self.limit_editor = MonitorLimitsWidget(
            controller.get_monitor_limits() if hasattr(controller, "get_monitor_limits")
            else DEFAULT_MONITOR_LIMITS)
        self.layout().insertWidget(1, self.limit_editor)
        self.error_history = QtWidgets.QPlainTextEdit()
        self.error_history.setReadOnly(True)
        self.error_history.setMaximumBlockCount(200)
        self.error_history.setPlaceholderText("Errors will appear here.")
        self.layout().insertWidget(self.layout().count() - 1, self.error_history)
        self.resize(850, 550)

    def _make_worker(self):
        worker = MezzMonitorTestWorker(self.controller, self.selected, self)
        worker.limits = self.limit_editor.values()
        worker.message_out.connect(self._retry_message)
        return worker

    def start(self):
        super().start()
        self.limit_editor.setEnabled(self.worker is None)

    def continue_test(self):
        if self.paused_worker is not None:
            self.paused_worker.limits = self.limit_editor.values()
        super().continue_test()
        self.limit_editor.setEnabled(self.worker is None)

    def _finished(self):
        super()._finished()
        self.limit_editor.setEnabled(True)

    def _retry_message(self, message):
        self.last_error.setText(f"Last retry: {message}")
        self.error_history.appendPlainText(f"{datetime.now():%H:%M:%S} {message}")

    def _reset_counts(self):
        self.counts = {target: [0, 0] for target in self.selected}
        self.readings = {target: {} for target in self.selected}
        if hasattr(self, "error_history"):
            self.error_history.clear()
        self._update_counts()

    def _update_counts(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Mezz", "Tests", "Errors", "AVDD (V)", "DVDD (V)", "Temp (°C)"])
        tests = errors = 0
        for row, target in enumerate(self.selected):
            counts = self.counts[target]
            tests += counts[0]
            errors += counts[1]
            cells = [str(value) for value in counts]
            cells.extend(self._display(self.readings[target].get(label))
                         for label in ("AVDD", "DVDD", "Temp"))
            for column, value in enumerate(cells, 1):
                item = QtWidgets.QTableWidgetItem(value)
                if column >= 3:
                    label = ("AVDD", "DVDD", "Temp")[column - 3]
                    limits = self.limit_editor.values() if hasattr(self, "limit_editor") else DEFAULT_MONITOR_LIMITS
                    if self.counts[target][0] and range_error(label, self.readings[target].get(label), limits):
                        item.setForeground(QtGui.QColor("red"))
                self.table.setItem(row, column, item)
        self.totals.setText(f"Total: {tests} tests, {errors} errors")

    @staticmethod
    def _display(value):
        return "NA" if value is None else f"{value:.3f}"

    def _result(self, csm, mezz, values, valid, detail):
        target = (csm, mezz)
        self.counts[target][0] += 1
        self.counts[target][1] += int(not valid)
        self.readings[target] = values
        self._update_counts()
        # Update the main monitor's labels on the GUI thread as well.
        for index, label in enumerate(("AVDD", "DVDD", "Temp")):
            widget = self.controller.cell_list[csm][mezz].label_list[index]
            widget.setText(self._display(values.get(label)))
            widget.setStyleSheet(ALARM_STYLE if range_error(label, values.get(label), self.limit_editor.values()) else "")
        if not valid:
            message = f"CSM{csm}, local Mezz{mezz}: {detail}"
            self.last_error.setText(f"Last error: {message}")
            self.error_history.appendPlainText(f"{datetime.now():%H:%M:%S} {message}")
