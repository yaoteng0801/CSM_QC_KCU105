"""Editor for trigger enables, polarity, and Boolean logic while acquisition is stopped."""
from PyQt5 import QtWidgets, QtCore
from external_trigger import compile_lut, pack_config


class ExternalTriggerWidget(QtWidgets.QGroupBox):
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, config, apply_callback, read_callback, parent=None):
        super().__init__("External trigger logic (configure while stopped)", parent)
        self._updating = True
        self.apply_callback = apply_callback
        layout = QtWidgets.QGridLayout(self)
        self.enables, self.polarities = [], []
        for i, name in enumerate("ABCD"):
            enable = QtWidgets.QCheckBox(f"{name} / TRIGGER[{i}]")
            polarity = QtWidgets.QComboBox()
            polarity.addItems(["Active high", "Active low"])
            layout.addWidget(enable, i, 0)
            layout.addWidget(polarity, i, 1)
            self.enables.append(enable)
            self.polarities.append(polarity)
        layout.addWidget(QtWidgets.QLabel("Expression"), 0, 2)
        self.expression = QtWidgets.QLineEdit("A")
        self.expression.setPlaceholderText("Example: (A & B) | (C & ~D)")
        layout.addWidget(self.expression, 0, 3)
        self.hex_mode = QtWidgets.QCheckBox("Use hexadecimal LUT instead")
        layout.addWidget(self.hex_mode, 1, 2, 1, 2)
        self.lut = QtWidgets.QLineEdit()
        self.lut.setMaxLength(6)
        layout.addWidget(QtWidgets.QLabel("Truth table (hex)"), 2, 2)
        layout.addWidget(self.lut, 2, 3)
        self.preview = QtWidgets.QLabel()
        layout.addWidget(self.preview, 3, 2, 1, 2)
        self.read_button = QtWidgets.QPushButton("Read FPGA")
        self.read_button.clicked.connect(read_callback)
        layout.addWidget(self.read_button, 4, 3)
        self.hardware_status = QtWidgets.QLabel()
        self.hardware_status.setWordWrap(True)
        self.hardware_status.hide()
        layout.addWidget(self.hardware_status, 5, 0, 1, 4)
        self.set_config(config)
        self.expression.textChanged.connect(self._expression_changed)
        self.hex_mode.toggled.connect(self._changed)
        for index, (enable, polarity) in enumerate(zip(self.enables, self.polarities)):
            enable.toggled.connect(self._changed)
            polarity.currentIndexChanged.connect(lambda _value, index=index: self._polarity_changed(index))
        self.lut.textChanged.connect(self._changed)

    def set_hardware_status(self, message):
        self.hardware_status.setText(message)
        self.hardware_status.setVisible(bool(message))

    def settings_state(self):
        return {
            "enabled": sum(int(w.isChecked()) << i for i, w in enumerate(self.enables)),
            "active_low": sum(w.currentIndex() << i for i, w in enumerate(self.polarities)),
            "expression": self.expression.text(), "hex_mode": self.hex_mode.isChecked(),
            "lut": self.lut.text(),
        }

    def restore_settings(self, state):
        enabled, active_low = int(state["enabled"]), int(state["active_low"])
        if not 0 <= enabled <= 15 or not 0 <= active_low <= 15:
            raise ValueError("Invalid saved trigger masks")
        expression, lut = state["expression"], state["lut"]
        if not isinstance(expression, str) or not isinstance(lut, str) or not isinstance(state["hex_mode"], bool):
            raise ValueError("Invalid saved trigger editor")
        self._updating = True
        try:
            for i in range(4):
                self.enables[i].setChecked(bool(enabled & (1 << i)))
                self.polarities[i].setCurrentIndex((active_low >> i) & 1)
            self.expression.setText(expression)
            self.hex_mode.setChecked(state["hex_mode"])
            self.lut.setText(lut)
            try:
                self._last_config = self.config()
            except ValueError:
                self._last_config = None
            self._polarity_indices = [widget.currentIndex() for widget in self.polarities]
        finally:
            self._updating = False
        self._preview()

    def set_config(self, config):
        self._updating = True
        try:
            for i in range(4):
                self.enables[i].setChecked(bool(config & (1 << i)))
                self.polarities[i].setCurrentIndex((config >> (4 + i)) & 1)
            try:
                matches = compile_lut(self.expression.text(), config & 15) == config >> 8
            except ValueError:
                matches = False
            # Preserve a matching expression (including default A). Arbitrary
            # readback tables stay in hex mode until an expression is entered.
            self.hex_mode.setChecked(not matches)
            if not matches:
                self.expression.clear()
            self.lut.setText(f"0x{config >> 8:04X}")
            self._last_config = config
            self._polarity_indices = [widget.currentIndex() for widget in self.polarities]
        finally:
            self._updating = False
        self._preview()

    def _confirm_polarity_change(self):
        return QtWidgets.QMessageBox.warning(
            self, 'Change trigger polarity',
            'Adjust the threshold and/or channel biasing on the board before changing this',
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Cancel,
        ) == QtWidgets.QMessageBox.Ok

    def _polarity_changed(self, index):
        if self._updating:
            return
        polarity = self.polarities[index]
        previous = self._polarity_indices[index]
        if polarity.currentIndex() == previous:
            return
        if not self._confirm_polarity_change():
            blocker = QtCore.QSignalBlocker(polarity)
            polarity.setCurrentIndex(previous)
            del blocker
            return
        self._polarity_indices[index] = polarity.currentIndex()
        self._changed()

    def _expression_changed(self, *_args):
        if self._updating:
            return
        self.hex_mode.blockSignals(True)
        self.hex_mode.setChecked(False)
        self.hex_mode.blockSignals(False)
        self._changed()

    def _changed(self, *_args):
        if self._updating:
            return
        self._preview()
        try:
            config = self.config()
        except ValueError:
            self.settings_changed.emit()
            return  # Keep incomplete expressions editable without programming them.
        if self.isEnabled() and config != self._last_config:
            if self.apply_callback() is not False:
                self._last_config = config
        self.settings_changed.emit()

    def config(self):
        enabled = sum(int(w.isChecked()) << i for i, w in enumerate(self.enables))
        active_low = sum(w.currentIndex() << i for i, w in enumerate(self.polarities))
        if self.hex_mode.isChecked():
            try:
                lut = int(self.lut.text(), 16)
            except ValueError as exc:
                raise ValueError("Enter a 16-bit hexadecimal truth table") from exc
        else:
            lut = compile_lut(self.expression.text(), enabled)
        return pack_config(enabled, active_low, lut)

    def _preview(self, *_args):
        self.lut.setReadOnly(not self.hex_mode.isChecked())
        self.expression.setToolTip("Editing this field selects expression mode and applies valid expressions immediately.")
        try:
            config = self.config()
            lut = config >> 8
            if not self.hex_mode.isChecked():
                self.lut.blockSignals(True)
                self.lut.setText(f"0x{lut:04X}")
                self.lut.blockSignals(False)
            self.preview.setText("Output is high at idle" if lut & 1 and config & 15
                                 else "Output is low at idle")
        except ValueError as exc:
            self.preview.setText(str(exc))
