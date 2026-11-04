# pop_TDC_control0.py
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from functools import partial
from TDCreg import *

class pop_TDC_control0(QtWidgets.QDialog):
    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("TDC control0")
        self.resize(600, 400)
        self.setup_UI()

    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Define the variables with bit lengths and widget types
        config_variables = {
            "rst_ePLL": (self.TDC_inst.rst_ePLL, 1, "checkbox"),
            "reset_jtag_in": (self.TDC_inst.reset_jtag_in, 1, "checkbox"),
            "event_reset_jtag_in": (self.TDC_inst.event_reset_jtag_in, 1, "checkbox"),
            "chnl_fifo_overflow_clear": (self.TDC_inst.chnl_fifo_overflow_clear, 1, "checkbox"),
            "debug_port_select": (self.TDC_inst.debug_port_select, 4, "combobox"),
        }

        # Store widgets for updating values dynamically
        self.widgets = {}

        for var_name, (binary_val, bit_length, widget_type) in config_variables.items():
            if widget_type == "checkbox":
                # Create a checkbox for 1-bit variables
                checkbox = QtWidgets.QCheckBox()
                checkbox.setChecked(binary_val[0] == '1')  # Initial state based on the variable value
                checkbox.stateChanged.connect(partial(self.update_checkbox, var_name))  # Connect to update function

                # Add to form layout
                form_layout.addRow(f"{var_name}:", checkbox)
                self.widgets[var_name] = checkbox

            elif widget_type == "combobox":
                # Create a combobox for multi-bit variables
                max_value = 2**bit_length - 1
                binary_options = [f"{i:0{bit_length}b}" for i in range(max_value + 1)]  # Generate all binary options
                combobox = QtWidgets.QComboBox()
                combobox.addItems(binary_options)  # Add binary options to the dropdown
                combobox.setCurrentText(binary_val[0])  # Set initial value

                # Connect dropdown change to update binary in TDC_inst
                combobox.currentTextChanged.connect(partial(self.update_combobox, var_name))

                # Add to form layout
                form_layout.addRow(f"{var_name}:", combobox)
                self.widgets[var_name] = combobox

        layout.addLayout(form_layout)

    def update_checkbox(self, var_name):
        """Update single-bit variable based on checkbox state."""
        checkbox = self.widgets[var_name]
        self.TDC_inst.__dict__[var_name][0] = '1' if checkbox.isChecked() else '0'

    def update_combobox(self, var_name, selected_value):
        """Update multi-bit variable based on combobox selection."""
        self.TDC_inst.__dict__[var_name][0] = selected_value
