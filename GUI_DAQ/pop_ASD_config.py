# pop_ASD_config.py
from PyQt5 import QtWidgets, QtCore, QtGui
from TDCreg import *

class pop_ASD_config(QtWidgets.QDialog):
    
    def __init__(self, ASD_inst, parent=None):
        super().__init__(parent)
        self.ASD_inst = ASD_inst
        self.setWindowTitle("Mode Configuration Settings")
        self.resize(600, 400)
        self.setup_UI()

    def closeEvent(self, event):
        self.accept()  # Explicitly treat close as accepted
        
    def copy_to(self, other_instance):
        for key, value in self.ASD_inst.__dict__.items():
            if type(other_instance.__dict__[key][0])!=list:
                other_instance.__dict__[key][0] = value[0]

    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Define each variable with its bit length
        mode_variables = {
            "channel_0_mode": (self.ASD_inst.channel_0_mode, 2),
            "channel_1_mode": (self.ASD_inst.channel_1_mode, 2),
            "channel_2_mode": (self.ASD_inst.channel_2_mode, 2),
            "channel_3_mode": (self.ASD_inst.channel_3_mode, 2),
            "channel_4_mode": (self.ASD_inst.channel_4_mode, 2),
            "channel_5_mode": (self.ASD_inst.channel_5_mode, 2),
            "channel_6_mode": (self.ASD_inst.channel_6_mode, 2),
            "channel_7_mode": (self.ASD_inst.channel_7_mode, 2),
            "chip_mode": (self.ASD_inst.chip_mode, 1, {"0": "ADC Mode", "1": "ToT Mode"}),
            "deadtime": (self.ASD_inst.deadtime, 'spinbox'),
            "int_gate": (self.ASD_inst.int_gate, 'spinbox'),
            "rundown_curr": (self.ASD_inst.rundown_curr, 'spinbox'),
            "hyst": (self.ASD_inst.hyst, 'spinbox', 'reversed'),
            "wilk_thr": (self.ASD_inst.wilk_thr, 'spinbox'),
            "main_thr": (self.ASD_inst.main_thr, 'line_edit')
        }

        # Store widgets for each variable
        self.widgets = {}

        for var_name, params in mode_variables.items():
            reversed_spinbox = 'reversed' if len(params) > 2 and params[2] == 'reversed' else None
            binary_val = params[0]
            
            if var_name in ["main_thr", "deadtime", "int_gate", "wilk_thr", "rundown_curr", "hyst"]:
                spin_box = QtWidgets.QSpinBox()
                max_value = 255 if var_name == "main_thr" \
                else (2 ** 3 - 1) if var_name in ["deadtime", "wilk_thr", "rundown_curr"] \
                else (2 ** 4 - 1)
                spin_box.setRange(0, max_value)
                spin_box.setValue(int(binary_val[0][::-1], 2) if reversed_spinbox else int(binary_val[0], 2))
                #ASD_reg always stores the reversed binary bits, GUI stores un-reversed readable int
                spin_box.valueChanged.connect(lambda value, var=var_name: self.update_spin_box(var, value))
                form_layout.addRow(f"{var_name}:", spin_box)
                self.widgets[var_name] = spin_box
            elif "channel_" in var_name and "_mode" in var_name:
                # Special case for channel_X_mode: Use checkbox
                checkbox = QtWidgets.QCheckBox()
                checkbox.setChecked(binary_val[0] == "10")  # Set initial value
                checkbox.setText("Active" if checkbox.isChecked() else "Disabled")
                checkbox.stateChanged.connect(self.update_checkbox_text)
                checkbox.stateChanged.connect(lambda state, var=var_name: self.update_checkbox(var, state))
                form_layout.addRow(f"{var_name}:", checkbox)
                self.widgets[var_name] = checkbox
            elif var_name == 'chip_mode':
                # Specific handling for chip_mode with descriptive options
                combobox = QtWidgets.QComboBox()
                for key, value in params[2].items():
                    combobox.addItem(value, key)
                initial_key = binary_val[0]
                if initial_key in params[2]:
                    combobox.setCurrentText(params[2][initial_key])
                combobox.currentIndexChanged.connect(lambda index, var=var_name, box=combobox: self.update_combobox(var, box.currentData()))
                form_layout.addRow(f"{var_name}:", combobox)
            

        # Add 'Check All' checkbox for all checkboxes
        check_all_checkbox = QtWidgets.QCheckBox("Check All")
        check_all_checkbox.stateChanged.connect(self.check_all_checkboxes)
        layout.addWidget(check_all_checkbox)

        layout.addLayout(form_layout)

        # Automatically accept dialog on close
        self.setResult(QtWidgets.QDialog.Accepted)

        

    def update_checkbox_text(self, state):
        """Update checkbox text based on state."""
        sender = self.sender()
        if isinstance(sender, QtWidgets.QCheckBox):
            sender.setText("Active" if state == QtCore.Qt.Checked else "Disabled")

    def update_checkbox(self, var_name, state):
        """Update TDCreg variable based on checkbox state."""
        self.ASD_inst.__dict__[var_name][0] = "10" if state == QtCore.Qt.Checked else "01"

    def update_combobox(self, var_name, selected_value):
        """Update TDCreg variable based on combobox selection."""
        self.ASD_inst.__dict__[var_name][0] = selected_value

    def update_spin_box(self, var_name, value):
        """Update TDCreg variable based on spin box input."""
        if var_name == 'hyst':
            self.ASD_inst.__dict__[var_name][0] = format(value, '04b')[::-1] 
            #ASD_reg always stores the reversed binary bits, GUI stores un-reversed readable int
        elif var_name == 'main_thr':
            self.ASD_inst.__dict__[var_name][0] = format(value, '08b')
        elif var_name in ['deadtime', 'wilk_thr', 'rundown_curr']:
            self.ASD_inst.__dict__[var_name][0] = format(value, '03b')
        elif var_name == 'int_gate':
            self.ASD_inst.__dict__[var_name][0] = format(value, '04b')

    def check_all_checkboxes(self, state):
        """Set all channel mode checkboxes to checked or unchecked."""
        for var_name, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(state == QtCore.Qt.Checked)

    
