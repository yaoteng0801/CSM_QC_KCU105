from functools import partial
from PyQt5 import QtWidgets, QtGui, QtCore
from acquisition_settings import BOARD_SETTINGS
from TDC_config_low_level_function import fpga_config, fpga_readback, value_to_list


class pop_miniDAQ_setup(QtWidgets.QDialog):
    """Board/link controls. Acquisition controls live in Capture mode panels."""
    def __init__(self, eth, miniDAQ_reg, parent=None, *, start_callback=None, stop_callback=None):
        super().__init__(parent)
        self.eth = eth
        self.miniDAQ_reg = miniDAQ_reg
        self.setWindowTitle("MiniDAQ Setup")
        self.MiniDAQ_reg_readback()
        self.board_controls = {}
        self.gridLayout = QtWidgets.QFormLayout(self)
        for address, name, width, value in miniDAQ_reg.register_table:
            if name not in BOARD_SETTINGS:
                continue
            if width == 1:
                widget = QtWidgets.QCheckBox()
                widget.setChecked(bool(value))
                widget.toggled.connect(partial(self._write, address, name))
            elif width > 32:
                widget = QtWidgets.QLineEdit(hex(value))
                rx = QtCore.QRegularExpression(rf"0x[0-9A-Fa-f]{{1,{(width+3)//4}}}")
                widget.setValidator(QtGui.QRegularExpressionValidator(rx, widget))
                widget.editingFinished.connect(
                    lambda address=address, name=name, widget=widget: self._write_hex(address, name, widget))
            else:
                widget = QtWidgets.QSpinBox()
                widget.setRange(*miniDAQ_reg.value_limits(name, width))
                widget.setValue(value)
                widget.editingFinished.connect(
                    lambda address=address, name=name, widget=widget: self._write(address, name, widget.value()))
            self.board_controls[name] = widget
            self.gridLayout.addRow(name, widget)
        miniDAQ_reg.register_changed.connect(self._refresh)
        self.resize(600, 400)

    def _write_hex(self, address, name, widget):
        if widget.hasAcceptableInput():
            self._write(address, name, int(widget.text(), 16))
        else:
            self._refresh(name, next(r[3] for r in self.miniDAQ_reg.register_table if r[1] == name))

    def _write(self, address, name, value):
        try:
            fpga_config(self.eth, address, value_to_list(int(value)))
            self.miniDAQ_reg.set_named_value(name, int(value))
        except Exception as exc:
            self._refresh(name, next(r[3] for r in self.miniDAQ_reg.register_table if r[1] == name))
            QtWidgets.QMessageBox.warning(self, "MiniDAQ setting failed", str(exc))

    def _refresh(self, name, value):
        widget = self.board_controls.get(name)
        if widget is None:
            return
        widget.blockSignals(True)
        if isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(value)
        else:
            widget.setText(hex(value))
        widget.blockSignals(False)

    def MiniDAQ_reg_readback(self):
        # Read only board controls; opening Setup must preserve Capture drafts.
        fields = {"TRST": (1, 0, 1), "master_rst": (1, 1, 1),
                  "event_rst": (1, 2, 1), "bc_rst": (1, 3, 1),
                  "global_rst": (1, 4, 1), "sca_reset": (1, 5, 1),
                  "down_rst": (1, 6, 1), "uplink_rst": (1, 7, 1),
                  "enable_320M": (1, 19, 1), "enable_K28_1": (1, 20, 1),
                  "correct_counter_th": (2, 88, 20)}
        try:
            pages = {}
            for page in (1, 2):
                bits = fpga_readback(self.eth, page)
                if not isinstance(bits, str) or len(bits) != 160 or set(bits) - {'0', '1'}:
                    raise ValueError("Invalid 160-bit readback")
                pages[page] = int(bits, 2)
            for name, (page, shift, width) in fields.items():
                self.miniDAQ_reg.set_named_value(name, (pages[page] >> shift) & ((1 << width)-1))
        except Exception as exc:
            print(f"[WARN] MiniDAQ board readback unavailable; using cached values: {exc}")
