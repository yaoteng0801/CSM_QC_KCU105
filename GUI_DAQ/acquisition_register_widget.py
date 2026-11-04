from PyQt5 import QtWidgets
from MiniDAQ_reg import MiniDAQ_reg
from acquisition_settings import PULSE_FIELDS


class AcquisitionRegisterWidget(QtWidgets.QGroupBox):
    """Mode-specific views of a shared register model; commit edits through controller."""
    def __init__(self, names, write, read):
        super().__init__("Acquisition registers")
        self.controls = {}
        self._write = write
        self._defaults = MiniDAQ_reg()
        grid = QtWidgets.QGridLayout(self)
        table = {r[1]: r for r in self._defaults.register_table}
        for row, name in enumerate(names):
            _, _, width, value = table[name]
            label = {
                "enable_hit": "Enable periodic triggers", "hit_inv": "Active-low generator output",
                "hit_width": "Pulse width (25 ns)", "hit_interval": "Pulse interval (25 ns)",
                "hit_single": "Single trigger", "fsm_watchdog_cycles": "Event watchdog (25 ns)",
                "tdc_chamber_map": "TDC enable / chamber map",
            }.get(name, name.replace('_', ' ').capitalize())
            if name == 'trigger_deadtime':
                label = 'Dead time (25 ns)'
            if name in PULSE_FIELDS:
                control = QtWidgets.QPushButton('Send single trigger' if name == 'hit_single' else 'Clear noise counters')
                control.clicked.connect(lambda _checked=False, name=name: write(name, 1))
            elif width == 1:
                control = QtWidgets.QCheckBox()
                control.setChecked(bool(value))
                control.toggled.connect(lambda value, name=name: write(name, int(value)))
            elif width > 32:
                control = QtWidgets.QLineEdit(hex(value))
                control.editingFinished.connect(lambda name=name, control=control: self._commit_hex(name, control))
                control.setToolTip('80-bit hex: low 40 bits enable TDCs; high 40 bits select chamber 1. Geometry assignment is uploaded at Start.')
            else:
                control = QtWidgets.QSpinBox()
                minimum, maximum = self._defaults.value_limits(name, width)
                if name == "fsm_watchdog_cycles":
                    maximum = min(maximum, 2000000)
                control.setRange(minimum, maximum)
                control.setValue(value)
                control.editingFinished.connect(lambda name=name, control=control: write(name, control.value()))
            self.controls[name] = control
            grid.addWidget(QtWidgets.QLabel(label), row // 2, (row % 2) * 2)
            grid.addWidget(control, row // 2, (row % 2) * 2 + 1)
        self.read_button = QtWidgets.QPushButton('Read acquisition registers')
        self.read_button.clicked.connect(lambda: read(tuple(n for n in names if n not in PULSE_FIELDS)))
        grid.addWidget(self.read_button, (len(names)+1)//2, 0, 1, 4)

    def _commit_hex(self, name, control):
        try:
            value = int(control.text(), 16)
        except ValueError:
            value = -1  # Controller rejects and restores the cached value.
        self._write(name, value)

    def refresh(self, name, value):
        control = self.controls.get(name)
        if control is None or name in PULSE_FIELDS:
            return
        control.blockSignals(True)
        if isinstance(control, QtWidgets.QCheckBox):
            control.setChecked(bool(value))
        elif isinstance(control, QtWidgets.QSpinBox):
            control.setValue(value)
        else:
            control.setText(hex(value))
        control.blockSignals(False)

    def set_available(self, connected, running):
        for name, control in self.controls.items():
            control.setEnabled(connected and (not running or name in PULSE_FIELDS))
        self.read_button.setEnabled(connected and not running)
