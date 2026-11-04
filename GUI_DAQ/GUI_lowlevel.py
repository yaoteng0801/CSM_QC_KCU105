from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from functools import partial

def create_checkbox(label, row, column, width, slot_function, setchecked=False, layout=None):
    if layout is None:
        raise ValueError("Layout must be provided for checkbox placement.")
    checkbox = QtWidgets.QCheckBox()
    checkbox.setText(label)
    checkbox.setChecked(setchecked)
    layout.addWidget(checkbox, row, column, 1, width)
    checkbox.stateChanged.connect(slot_function)
    return checkbox

def create_button(label, row, column, width, slot_function, layout=None):
    if layout is None:
        raise ValueError("Layout must be provided for button placement.")
    button = QtWidgets.QPushButton()
    button.setText(label)
    layout.addWidget(button, row, column, 1, width)
    button.clicked.connect(slot_function)
    return button

def create_combobox(label, row, column, width, slot_function, options=None,value=0, layout=None):
    if layout is None:
        raise ValueError("Layout must be provided for combobox placement.")
    if options is None:
        options = []

    qlabel = QtWidgets.QLabel(label)
    layout.addWidget(qlabel, row, column, 1, width)

    combobox = QtWidgets.QComboBox()
    combobox.addItems(options)
    combobox.setCurrentIndex(value if 0 <= value < len(options) else 0)
    layout.addWidget(combobox, row, column + 1, 1, width)

    combobox.currentIndexChanged[int].connect(slot_function)
    return combobox