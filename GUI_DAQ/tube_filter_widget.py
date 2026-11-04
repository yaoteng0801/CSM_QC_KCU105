"""Shared four-cut editor used by Capture and MiniDAQ Reg."""
from PyQt5 import QtCore, QtWidgets
from triggerless_filters import FILTER_FIELDS, MAX_THRESHOLD, TubeFilterSettings


class TubeFilterWidget(QtWidgets.QGroupBox):
    settingsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Tube filters — selected cuts are ANDed", parent)
        self._updating = False
        self.checks, self.spins = [[], []], [[], []]
        grid = QtWidgets.QGridLayout(self)
        for chamber in range(2):
            grid.addWidget(QtWidgets.QLabel(f"Chamber {chamber}"), 0, 1+2*chamber, 1, 2)
        for row, (_name, label) in enumerate(FILTER_FIELDS, 1):
            grid.addWidget(QtWidgets.QLabel(label), row, 0)
            for chamber in range(2):
                check = QtWidgets.QCheckBox("Enable")
                spin = QtWidgets.QSpinBox()
                spin.setRange(0, MAX_THRESHOLD)
                check.setObjectName(f"chamber{chamber}_{_name}_enabled")
                spin.setObjectName(f"chamber{chamber}_{_name}")
                check.toggled.connect(self._changed)
                spin.valueChanged.connect(self._changed)
                self.checks[chamber].append(check)
                self.spins[chamber].append(spin)
                grid.addWidget(check, row, 1+2*chamber)
                grid.addWidget(spin, row, 2+2*chamber)
        note = QtWidgets.QLabel(
            "Distinct tubes, not hit words. Every ML/layer in the uploaded geometry must pass.\n"
            "Staged for the next framed triggerless Start; raw/count noise streams ignore these cuts."
        )
        note.setWordWrap(True)
        grid.addWidget(note, 5, 0, 1, 5)
        self.set_values((TubeFilterSettings(), TubeFilterSettings()))

    def values(self):
        return tuple(TubeFilterSettings(
            sum(int(check.isChecked()) << bit for bit, check in enumerate(self.checks[c])),
            *(spin.value() for spin in self.spins[c])) for c in range(2))

    def set_values(self, settings):
        self._updating = True
        try:
            for c, cfg in enumerate(settings):
                for bit, (name, _label) in enumerate(FILTER_FIELDS):
                    self.checks[c][bit].setChecked(bool(cfg.enabled & (1 << bit)))
                    self.spins[c][bit].setValue(getattr(cfg, name))
                    self.spins[c][bit].setEnabled(self.checks[c][bit].isChecked())
        finally:
            self._updating = False

    def _changed(self, *_args):
        if not self._updating:
            self.set_values(self.values())
            self.settingsChanged.emit()


class _GeometryUploadThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, int, str)

    def __init__(self, upload, parent):
        super().__init__(parent)
        self.upload, self.error = upload, None

    def run(self):
        try:
            self.upload(self.report_progress)
            if self.isInterruptionRequested():
                raise RuntimeError("Geometry upload cancelled; DAQ was not started")
        except Exception as exc:
            self.error = exc

    def report_progress(self, done, total, message):
        if self.isInterruptionRequested():
            raise RuntimeError("Geometry upload cancelled; DAQ was not started")
        self.progress.emit(done, total, message)


class GeometryUploadDialog(QtWidgets.QDialog):
    """Modal controls, responsive UI; no nested UI events inside Ethernet locks."""
    def __init__(self, upload, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload triggerless geometry")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Uploading and verifying the Geometry-tab mapping…")
        self.bar = QtWidgets.QProgressBar()
        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        self.cancel = QtWidgets.QPushButton("Cancel")
        self.cancel.clicked.connect(self.reject)
        layout.addWidget(self.cancel)
        self.worker = _GeometryUploadThread(upload, self)
        self.worker.progress.connect(self._progress)
        self.worker.finished.connect(self.accept)

    def _progress(self, done, total, message):
        self.bar.setMaximum(total)
        self.bar.setValue(done)
        self.label.setText(message)

    def reject(self):
        if self.worker.isRunning():
            self.worker.requestInterruption()
            self.cancel.setEnabled(False)
            self.label.setText("Cancelling after the current control transaction…")
        else:
            super().reject()

    def upload(self):
        self.worker.start()
        self.exec_()
        self.worker.wait()
        if self.worker.error is not None:
            raise self.worker.error
