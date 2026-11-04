"""Editable CSM limits with fixed defaults shared by master and slave."""

import csv
import math
from PyQt5 import QtWidgets


DEFAULT_BOUNDS = {
    'VDD2V5': (2.4, 2.6),
    'VDD1V2': (1.1, 1.3),
    'SCA_TEMP': (20, 60),
    'VSSA': (0, 0.1),
    'VDDTX': (1.1, 1.3),
    'VDDRX': (1.1, 1.3),
    'VDD': (1.1, 1.3),
    'VDDA': (1.1, 1.3),
    'TEMP': (20, 60),
    'VREF': (0.45, 0.55),
    'VTRX_TEMP': (20, 60),
}


def default_bounds(label):
    label = label.upper()
    if label in ('SCA0_TEMP', 'SCA1_TEMP', 'SCA2_TEMP', 'SCA3_TEMP'):
        label = 'SCA_TEMP'
    return DEFAULT_BOUNDS.get(label)


def latest_csv_values(path):
    """Read the last completed numeric monitor row without loading the run."""
    if not path.exists():
        return {}
    with path.open('rb') as source:
        header = next(csv.reader([source.readline().decode('utf-8-sig')]), [])
        header_end = source.tell()
        source.seek(0, 2)
        end = source.tell()
        start = max(header_end, end - 65536)
        source.seek(start)
        tail = source.read()
    lines = tail.splitlines()
    if start > header_end and lines:
        lines.pop(0)  # A possibly partial first row in this tail window.
    if tail and not tail.endswith((b'\n', b'\r')) and lines:
        lines.pop()  # A scan still being written is not a complete result.
    if not lines:
        return {}
    row = next(csv.reader([lines[-1].decode('utf-8')]))
    values = {}
    for name, text in zip(header, row):
        if '_display_' in name:
            try:
                value = float(text)
            except ValueError:
                continue
            if math.isfinite(value):
                values[name] = value
    return values


class CSMLimitsDialog(QtWidgets.QDialog):
    def __init__(self, metrics, latest, limits, parent=None, *, persist=True):
        super().__init__(parent)
        self.setWindowTitle('CSM Monitor Limits')
        layout = QtWidgets.QVBoxLayout(self)
        description = QtWidgets.QLabel(
            'Master and slave use the same default ranges. Edit minimum and maximum to override.\n' +
            ('Save writes the limits to monitor_limits.ini for future GUI sessions.\n' if persist else
             'Apply updates the current ranges. Use Save to file in Monitoring to save all ranges together.\n') +
            'Limits are inclusive and stay fixed between runs until edited.'
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        table = QtWidgets.QTableWidget(len(metrics), 4)
        table.setHorizontalHeaderLabels(['Reading', 'Latest result', 'Minimum', 'Maximum'])
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.editors = {}
        for row, (key, name, unit, column) in enumerate(metrics):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(f'{name} ({unit})'))
            value = latest.get(key)
            table.setItem(row, 1, QtWidgets.QTableWidgetItem('—' if value is None else f'{value:.3f}'))
            original = limits.get(key)
            bounds = original or (0, 0)
            low, high = QtWidgets.QDoubleSpinBox(), QtWidgets.QDoubleSpinBox()
            for col, editor in enumerate((low, high), 2):
                editor.setRange(-1e6, 1e6)
                editor.setDecimals(3)
                editor.setSingleStep(0.1)
                editor.setKeyboardTracking(False)
                table.setCellWidget(row, col, editor)
            low.setValue(bounds[0])
            high.setValue(bounds[1])
            low.setMaximum(high.value())
            high.setMinimum(low.value())
            low.valueChanged.connect(high.setMinimum)
            high.valueChanged.connect(low.setMaximum)
            # Compare with rounded editor values so opening/saving alone does
            # not turn automatically generated limits into manual overrides.
            self.editors[key] = (low, high, original, (low.value(), high.value()))
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        layout.addWidget(table)
        action = QtWidgets.QDialogButtonBox.Save if persist else QtWidgets.QDialogButtonBox.Ok
        buttons = QtWidgets.QDialogButtonBox(action | QtWidgets.QDialogButtonBox.Cancel)
        if not persist:
            buttons.button(action).setText('Apply')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(900, 600)

    def changes(self):
        return {key: (low.value(), high.value())
                for key, (low, high, original, displayed) in self.editors.items()
                if (low.value(), high.value()) != displayed}
