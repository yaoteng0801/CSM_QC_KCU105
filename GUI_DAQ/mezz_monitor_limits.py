"""Shared physical limits for normal and continuous mezzanine monitoring."""

import math
from PyQt5 import QtWidgets


DEFAULT_MONITOR_LIMITS = {"AVDD": (2.9, 3.1), "DVDD": (1.1, 1.3), "Temp": (20.0, 60.0)}
ALARM_STYLE = "color: red; font-weight: bold;"


def range_error(label, value, limits):
    low, high = limits[label]
    if value is None or not math.isfinite(float(value)):
        return f"{label}: no valid reading"
    if not low <= value <= high:
        unit = "°C" if label == "Temp" else "V"
        return f"{label}={value:.3f} {unit} outside {low:g}–{high:g} {unit}"
    return None


class MonitorLimitsWidget(QtWidgets.QGroupBox):
    def __init__(self, limits=None, parent=None):
        super().__init__("Acceptable ranges (inclusive)", parent)
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(QtWidgets.QLabel("Minimum"), 0, 1)
        layout.addWidget(QtWidgets.QLabel("Maximum"), 0, 2)
        self.editors = {}
        for row, (label, bounds) in enumerate((limits or DEFAULT_MONITOR_LIMITS).items(), 1):
            unit = "°C" if label == "Temp" else "V"
            layout.addWidget(QtWidgets.QLabel(f"{label} ({unit})"), row, 0)
            low, high = QtWidgets.QDoubleSpinBox(), QtWidgets.QDoubleSpinBox()
            for column, editor in enumerate((low, high), 1):
                editor.setRange(-273.15 if label == "Temp" else -100, 1000 if label == "Temp" else 100)
                editor.setDecimals(3)
                editor.setSingleStep(1 if label == "Temp" else 0.1)
                editor.setKeyboardTracking(False)
                layout.addWidget(editor, row, column)
            low.setValue(bounds[0])
            high.setValue(bounds[1])
            low.setMaximum(high.value())
            high.setMinimum(low.value())
            low.valueChanged.connect(high.setMinimum)
            high.valueChanged.connect(low.setMaximum)
            self.editors[label] = (low, high)

    def values(self):
        return {label: (low.value(), high.value()) for label, (low, high) in self.editors.items()}

    def set_values(self, limits):
        for label, (minimum, maximum) in limits.items():
            low, high = self.editors[label]
            low.setMaximum(high.maximum())
            high.setMinimum(low.minimum())
            low.setValue(minimum)
            high.setValue(maximum)
            low.setMaximum(high.value())
            high.setMinimum(low.value())
