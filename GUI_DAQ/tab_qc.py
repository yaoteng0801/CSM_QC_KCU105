"""CSM QC page: the operator's inputs, step progress and the run's timer."""

import os

from PyQt5 import QtCore, QtWidgets

import csm_qc


_STATE_STYLE = {
    "waiting": "color: gray;",
    "running": "background-color: #fff3b0; font-weight: bold;",
    "pass": "background-color: #b7e4b0;",
    "skip": "background-color: #d6e4f0; font-style: italic;",
    "fail": "background-color: #f4a6a0; font-weight: bold;",
}


class tab_qc(QtWidgets.QWidget):
    def __init__(self, parent_widget, tabs, settings=None):
        super().__init__(parent_widget)
        self.tabs = tabs
        self.settings = settings
        self.run = None
        self._generator = None
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._resume)
        self._build_ui(parent_widget)
        self._load_settings()

    # --------------------------------------------------------------------- UI
    def _build_ui(self, parent_widget):
        outer = QtWidgets.QVBoxLayout(parent_widget)
        outer.addWidget(self)
        columns = QtWidgets.QHBoxLayout(self)
        layout = QtWidgets.QVBoxLayout()
        columns.addLayout(layout, 3)

        inputs = QtWidgets.QGroupBox("CSM QC run")
        grid = QtWidgets.QGridLayout(inputs)
        grid.setColumnStretch(1, 1)

        self.edit_serial = QtWidgets.QLineEdit()
        self.edit_operator = QtWidgets.QLineEdit()
        self.edit_bitstream = QtWidgets.QLineEdit(self.tabs.lpgbt.file_path_box.text())
        self.edit_bitstream.setPlaceholderText("Select a Xilinx .bit file")
        self.edit_output = QtWidgets.QLineEdit()
        browse_bitstream = QtWidgets.QPushButton("Browse…")
        browse_bitstream.clicked.connect(self._browse_bitstream)
        browse_output = QtWidgets.QPushButton("Browse…")
        browse_output.clicked.connect(self._browse_output)
        self.label_folder = QtWidgets.QLabel()
        self.label_folder.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label_folder.setWordWrap(True)
        for edit in (self.edit_serial, self.edit_operator, self.edit_output):
            edit.textChanged.connect(self._update_folder_hint)

        grid.addWidget(QtWidgets.QLabel("CSM serial number"), 0, 0)
        grid.addWidget(self.edit_serial, 0, 1, 1, 2)
        grid.addWidget(QtWidgets.QLabel("Operator name"), 1, 0)
        grid.addWidget(self.edit_operator, 1, 1, 1, 2)
        grid.addWidget(QtWidgets.QLabel("Bitstream file"), 2, 0)
        grid.addWidget(self.edit_bitstream, 2, 1)
        grid.addWidget(browse_bitstream, 2, 2)
        grid.addWidget(QtWidgets.QLabel("Output location"), 3, 0)
        grid.addWidget(self.edit_output, 3, 1)
        grid.addWidget(browse_output, 3, 2)
        grid.addWidget(self.label_folder, 4, 1, 1, 2)
        layout.addWidget(inputs)

        targets = QtWidgets.QGroupBox("Test targets")
        target_grid = QtWidgets.QGridLayout(targets)
        self.edit_prbs_target = QtWidgets.QLineEdit("1E-13")
        self.edit_dline_target = QtWidgets.QLineEdit("1E-11")
        for edit in (self.edit_prbs_target, self.edit_dline_target):
            edit.setToolTip("0 skips the measurement; the configuration still runs as normal.")
        self.spin_threshold = QtWidgets.QSpinBox()
        self.spin_threshold.setRange(0, 255)
        self.spin_threshold.setValue(114)
        target_grid.setColumnStretch(1, 1)
        target_grid.addWidget(QtWidgets.QLabel("PRBS target BER"), 0, 0)
        target_grid.addWidget(self.edit_prbs_target, 0, 1)
        target_grid.addWidget(QtWidgets.QLabel("BER monitor target BER"), 1, 0)
        target_grid.addWidget(self.edit_dline_target, 1, 1)
        target_grid.addWidget(QtWidgets.QLabel("ASD main threshold"), 2, 0)
        target_grid.addWidget(self.spin_threshold, 2, 1)
        layout.addWidget(targets)

        buttons = QtWidgets.QHBoxLayout()
        self.button_start = QtWidgets.QPushButton("Start QC run")
        self.button_start.setMinimumHeight(34)
        self.button_start.clicked.connect(self.start)
        self.button_stop = QtWidgets.QPushButton("Stop QC")
        self.button_stop.setMinimumHeight(34)
        self.button_stop.setEnabled(False)
        self.button_stop.clicked.connect(self.stop)
        buttons.addWidget(self.button_start, 1)
        buttons.addWidget(self.button_stop)
        layout.addLayout(buttons)
        layout.addStretch(1)

        progress = QtWidgets.QGroupBox("Progress")
        progress_layout = QtWidgets.QVBoxLayout(progress)
        self.step_labels = {}
        for key, name in csm_qc.STEPS:
            label = QtWidgets.QLabel(name)
            label.setContentsMargins(6, 2, 6, 2)
            label.setStyleSheet(_STATE_STYLE["waiting"])
            progress_layout.addWidget(label)
            self.step_labels[key] = label
        self.label_status = QtWidgets.QLabel("Idle")
        self.label_status.setWordWrap(True)
        self.label_status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        progress_layout.addWidget(self.label_status)
        progress_layout.addStretch(1)
        columns.addWidget(progress, 2)
        self._update_folder_hint()

    def _browse_bitstream(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select a bitstream", self.edit_bitstream.text(),
            "Bitstream Files (*.bit);;All Files (*)")
        if path:
            self.edit_bitstream.setText(path)

    def _browse_output(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select the output location", self.edit_output.text())
        if path:
            self.edit_output.setText(path)

    def _update_folder_hint(self):
        parts = (self.edit_output.text().strip() or "<output location>",
                 self.edit_serial.text().strip() or "<serial>",
                 self.edit_operator.text().strip() or "<operator>",
                 "YYYYMMDDHHMM")
        self.label_folder.setText("Results go to: " + os.path.join(*parts))

    # --------------------------------------------------------------- settings
    def _load_settings(self):
        if self.settings is None:
            return
        for key, edit in (("operator", self.edit_operator), ("output", self.edit_output),
                          ("bitstream", self.edit_bitstream)):
            value = self.settings.value(f"qc/{key}", "")
            if value:
                edit.setText(str(value))

    def _save_settings(self):
        if self.settings is None:
            return
        self.settings.setValue("qc/operator", self.edit_operator.text().strip())
        self.settings.setValue("qc/output", self.edit_output.text().strip())
        self.settings.setValue("qc/bitstream", self.edit_bitstream.text().strip())

    # ------------------------------------------------------------- validation
    def read_inputs(self):
        """Return (settings, None), or (None, what the operator has to fix)."""
        serial = self.edit_serial.text().strip()
        operator = self.edit_operator.text().strip()
        bitstream = self.edit_bitstream.text().strip()
        output = self.edit_output.text().strip()
        if not csm_qc.valid_path_component(serial):
            return None, "Enter the CSM serial number, using letters, digits, spaces, - _ or ."
        if not csm_qc.valid_path_component(operator):
            return None, "Enter the operator name, using letters, digits, spaces, - _ or ."
        if not os.path.isfile(bitstream):
            return None, f"Bitstream file not found:\n{bitstream}"
        if not output:
            return None, "Choose the output location."
        targets = []
        for name, edit in (("PRBS", self.edit_prbs_target), ("BER monitor", self.edit_dline_target)):
            try:
                value = float(edit.text())
            except ValueError:
                value = -1.0  # Not 0: that would mean "skip".
            if not 0.0 <= value < 1.0:
                return None, f"{name} target BER must be a number such as 1E-13, or 0 to skip it."
            targets.append(value)
        device = self.tabs.lpgbt.current_ethernet_device()
        if not device or "ERROR" in device:
            return None, "Select an Ethernet interface on the Ethernet Capture page."
        if self.tabs.backend.is_running():
            return None, "Stop the running capture first."
        if self.tabs.monitor.worker is not None:
            return None, "Stop the running monitoring first."
        return csm_qc.QcSettings(serial, operator, bitstream, output, targets[0], targets[1],
                                 self.spin_threshold.value()), None

    # ------------------------------------------------------------ run control
    def start(self):
        if self._generator is not None:
            return
        settings, problem = self.read_inputs()
        if problem:
            QtWidgets.QMessageBox.warning(self, "CSM QC", problem)
            return
        self._save_settings()
        for label in self.step_labels.values():
            label.setStyleSheet(_STATE_STYLE["waiting"])
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.run = csm_qc.CsmQcRun(self.tabs, settings, self)
        self._generator = self.run.run()
        self._timer.start(0)

    def stop(self):
        if self.run is not None:
            self.button_stop.setEnabled(False)
            self.status("Stopping at the next safe point…")
            self.run.request_stop()

    def _resume(self):
        try:
            delay = next(self._generator)
        except StopIteration:
            self._generator = None
            return
        except Exception as error:
            # run() handles board failures, so this is a fault in the QC code itself.
            self._generator = None
            self.finished("FAIL", f"{type(error).__name__}: {error}", self.run.folder)
            return
        self._timer.start(int(delay * 1000))

    # ------------------------------------------ callbacks from the QC sequence
    def status(self, text):
        self.label_status.setText(text)

    def step(self, key, state):
        self.step_labels[key].setStyleSheet(_STATE_STYLE[state])

    def confirm(self, title, text):
        answer = QtWidgets.QMessageBox.question(
            self, title, text,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        return answer == QtWidgets.QMessageBox.Yes

    def ask_redo(self, step, reason):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Critical, "CSM QC step failed",
            f"{step} failed.\n\n{reason}\n\nRedo this step, or stop the QC run?", parent=self)
        redo = dialog.addButton("Redo this step", QtWidgets.QMessageBox.AcceptRole)
        stop = dialog.addButton("Stop QC", QtWidgets.QMessageBox.RejectRole)
        dialog.setDefaultButton(redo)
        dialog.setEscapeButton(stop)
        dialog.exec_()
        return dialog.clickedButton() is redo

    def finished(self, verdict, reason, folder):
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        if verdict == "PASS":
            QtWidgets.QMessageBox.information(
                self, "CSM QC passed", f"QC PASS.\n\nResults:\n{folder}")
        elif verdict == "STOPPED":
            QtWidgets.QMessageBox.warning(
                self, "CSM QC stopped", f"QC stopped by the operator.\n\nResults so far:\n{folder}")
        else:
            QtWidgets.QMessageBox.critical(
                self, "CSM QC FAILED", f"QC FAILED.\n\n{reason}\n\nResults:\n{folder}")
