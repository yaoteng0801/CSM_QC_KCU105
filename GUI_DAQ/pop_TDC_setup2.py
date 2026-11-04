# pop_TDC_setup2.py
from PyQt5 import QtWidgets
from TDCreg import *

class pop_TDC_setup2(QtWidgets.QDialog):
    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("TDC Setup2")
        self.resize(600, 400)
        self.setup_UI()

    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Define each variable with its possible binary options
        lut_variables = {
            "fine_sel": (self.TDC_inst.fine_sel, 4),
            "lut0": (self.TDC_inst.lut0, 2),
            "lut1": (self.TDC_inst.lut1, 2),
            "lut2": (self.TDC_inst.lut2, 2),
            "lut3": (self.TDC_inst.lut3, 2),
            "lut4": (self.TDC_inst.lut4, 2),
            "lut5": (self.TDC_inst.lut5, 2),
            "lut6": (self.TDC_inst.lut6, 2),
            "lut7": (self.TDC_inst.lut7, 2),
            "lut8": (self.TDC_inst.lut8, 2),
            "lut9": (self.TDC_inst.lut9, 2),
            "luta": (self.TDC_inst.luta, 2),
            "lutb": (self.TDC_inst.lutb, 2),
            "lutc": (self.TDC_inst.lutc, 2),
            "lutd": (self.TDC_inst.lutd, 2),
            "lute": (self.TDC_inst.lute, 2),
            "lutf": (self.TDC_inst.lutf, 2)
        }

        # Store QComboBox widgets for each variable
        self.comboboxes = {}

        for var_name, (binary_val, bit_length) in lut_variables.items():
            max_value = 2**bit_length - 1
            binary_options = [f"{i:0{bit_length}b}" for i in range(max_value + 1)]  # Generate all binary options
            combobox = QtWidgets.QComboBox()
            combobox.addItems(binary_options)  # Add binary options to the dropdown
            combobox.setCurrentText(binary_val[0])  # Set initial value

            # Connect dropdown change to update binary in TDC_inst
            combobox.currentTextChanged.connect(lambda selected_value, var=var_name: self.update_binary(var, selected_value))

            # Add to form layout
            form_layout.addRow(f"{var_name}:", combobox)
            self.comboboxes[var_name] = combobox

        layout.addLayout(form_layout)

    def update_binary(self, var_name, selected_value):
        """Update TDCreg variable based on dropdown selection."""
        setattr(self.TDC_inst, var_name, [selected_value])
