# pop_TDC_control1.py
from PyQt5 import QtWidgets, QtGui
from TDCreg import *

class pop_TDC_control1(QtWidgets.QDialog):
    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("TDC Control1")
        self.resize(600, 400)
        self.setup_UI()


    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Define each variable with its bit length
        config_variables = {
            "phase_clk160": (self.TDC_inst.phase_clk160, 5),
            "phase_clk320_0": (self.TDC_inst.phase_clk320_0, 4),
            "phase_clk320_1": (self.TDC_inst.phase_clk320_1, 4),
            "phase_clk320_2": (self.TDC_inst.phase_clk320_2, 4),
            "ePllRes": (self.TDC_inst.ePllRes, 4),
            "ePllIcp": (self.TDC_inst.ePllIcp, 4),
            "ePllCap": (self.TDC_inst.ePllCap, 2),
        }

        # Store QLineEdits for each variable
        self.inputs = {}

        for var_name, (binary_val, bit_length) in config_variables.items():
            decimal_value = int(binary_val[0], 2)  # Convert binary to decimal for display
            line_edit = QtWidgets.QLineEdit(str(decimal_value))
            line_edit.setValidator(QtGui.QIntValidator(0, 2**bit_length - 1))  # Limit based on bit length

            # Connect input change to update binary and dependent relationships
            if var_name == "phase_clk320_1":
                line_edit.editingFinished.connect(self.update_from_phase_clk320_1)
            elif var_name == "phase_clk320_0":
                line_edit.editingFinished.connect(self.update_from_phase_clk320_0)
            else:
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
        setattr(self.TDC_inst, var_name, [binary_value])

    def update_from_phase_clk320_1(self):
        """Update phase_clk320_0 and phase_clk320_2 based on phase_clk320_1."""
        # Get the current decimal value of phase_clk320_1
        phase_clk320_1_decimal = int(self.inputs["phase_clk320_1"].text())

        # Update phase_clk320_0 as phase_clk320_1 + 4
        phase_clk320_0_decimal = (phase_clk320_1_decimal + 4)%16
        if phase_clk320_0_decimal <= 15:  # Ensure it fits in 4 bits
            self.inputs["phase_clk320_0"].setText(str(phase_clk320_0_decimal))
            self.TDC_inst.phase_clk320_0 = [f"{phase_clk320_0_decimal:04b}"]

        # Update phase_clk320_2 based on the condition
        phase_clk320_2_decimal = 1 if 5 <= phase_clk320_1_decimal <= 12 else 2
        self.inputs["phase_clk320_2"].setText(str(phase_clk320_2_decimal))
        self.TDC_inst.phase_clk320_2 = [f"{phase_clk320_2_decimal:04b}"]

    def update_from_phase_clk320_0(self):
        """Update phase_clk320_1 based on phase_clk320_0 - 4, and phase_clk320_2 accordingly."""
        # Get the current decimal value of phase_clk320_0
        phase_clk320_0_decimal = int(self.inputs["phase_clk320_0"].text())

        # Update phase_clk320_1 as phase_clk320_0 - 4
        phase_clk320_1_decimal = (phase_clk320_0_decimal+16-4)%16
        if 0 <= phase_clk320_1_decimal <= 15:  # Ensure it fits in 4 bits
            self.inputs["phase_clk320_1"].setText(str(phase_clk320_1_decimal))
            self.TDC_inst.phase_clk320_1 = [f"{phase_clk320_1_decimal:04b}"]

        # Update phase_clk320_2 based on the condition
        phase_clk320_2_decimal = 1 if 5 <= phase_clk320_1_decimal <= 12 else 2
        self.inputs["phase_clk320_2"].setText(str(phase_clk320_2_decimal))
        self.TDC_inst.phase_clk320_2 = [f"{phase_clk320_2_decimal:04b}"]

        # Explicitly trigger `update_from_phase_clk320_1` to ensure consistency
        self.update_from_phase_clk320_1()
