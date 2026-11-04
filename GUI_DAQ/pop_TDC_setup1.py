
# pop_TDC_setup1.py
from PyQt5 import QtWidgets, QtGui  # Import QIntValidator from QtGui
from PyQt5.QtCore import Qt
from TDCreg import *

class pop_TDC_setup1(QtWidgets.QDialog):
    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("TDC Setup1")
        self.resize(600, 400)
        self.setup_UI()

    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Dictionary to map each variable's name to its binary length
        config_variables = {
            "combine_time_out_config": (self.TDC_inst.combine_time_out_config, 10),
            "fake_hit_time_interval": (self.TDC_inst.fake_hit_time_interval, 12),
            "syn_packet_number": (self.TDC_inst.syn_packet_number, 12),
            "roll_over": (self.TDC_inst.roll_over, 12),
            "coarse_count_offset": (self.TDC_inst.coarse_count_offset, 12),
            "bunch_offset": (self.TDC_inst.bunch_offset, 12),
            "event_offset": (self.TDC_inst.event_offset, 12),
            "match_window": (self.TDC_inst.match_window, 12)
        }

        # Store QLineEdits for updating values dynamically
        self.inputs = {}

        for var_name, (binary_val, bit_length) in config_variables.items():
            decimal_value = int(binary_val[0], 2)  # Convert binary to decimal for display
            line_edit = QtWidgets.QLineEdit(str(decimal_value))
            line_edit.setValidator(QtGui.QIntValidator(0, 2**bit_length - 1))  # Set valid range for input

            # Connect input change to update binary in TDC_inst
            line_edit.editingFinished.connect(lambda var=var_name, bits=bit_length: self.update_binary(var, bits))
            
            # Add to form layout
            form_layout.addRow(f"{var_name} (decimal):", line_edit)
            self.inputs[var_name] = line_edit

        layout.addLayout(form_layout)

    def update_binary(self, var_name, bit_length):
        """Convert decimal input to binary and store it in TDC_inst."""
        line_edit = self.inputs[var_name]
        decimal_value = int(line_edit.text())  # Get decimal value from input
        binary_value = f"{decimal_value:0{bit_length}b}"  # Convert to binary with leading zeros

        # Update the corresponding variable in TDC_inst
        setattr(self.TDC_inst, var_name, [binary_value])

    def get_decimal_value(self, var_name):
        """Helper to get the current decimal value from a binary sequence."""
        binary_val = getattr(self.TDC_inst, var_name)[0]
        return int(binary_val, 2)


