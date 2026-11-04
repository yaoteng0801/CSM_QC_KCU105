# tab_TDC.py
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from functools import partial
from TDCreg import *

class pop_TDC_setup0(QtWidgets.QDialog):

    #tab version:

    # def __init__(self, MainWindow):
    #     self.TDC_inst = TDCreg() 
    #     self.setup_UI(MainWindow)
        

    #dialog version:
    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("TDC Setup0")
        self.resize(800, 600)  # Set initial size of the popup window
        self.setup_UI()

    def setup_UI(self):

        sectionLayout = QtWidgets.QVBoxLayout(self)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)


        # Define all single-bit variables as checkboxes
        bit_variables = {
            "enable_new_ttc"          : self.TDC_inst.enable_new_ttc,
            "enable_master_reset_code": self.TDC_inst.enable_master_reset_code,
            "enable_direct_bunch_reset": self.TDC_inst.enable_direct_bunch_reset,
            "enable_direct_event_reset": self.TDC_inst.enable_direct_event_reset,
            "enable_direct_trigger"   : self.TDC_inst.enable_direct_trigger,
            "auto_roll_over"          : self.TDC_inst.auto_roll_over,
            "bypass_bcr_distribution" : self.TDC_inst.bypass_bcr_distribution,
            "enable_trigger"          : self.TDC_inst.enable_trigger,
            "channel_data_debug"      : self.TDC_inst.channel_data_debug,
            "enable_leading"          : self.TDC_inst.enable_leading,
            "enable_pair"             : self.TDC_inst.enable_pair,
            "enable_fake_hit"         : self.TDC_inst.enable_fake_hit,
            "TDC_ID"                  : self.TDC_inst.TDC_ID,
            "enable_trigger_timeout"  : self.TDC_inst.enable_trigger_timeout,
            "enable_high_speed"       : self.TDC_inst.enable_high_speed,
            "enable_legacy"           : self.TDC_inst.enable_legacy,
            "full_width_res"          : self.TDC_inst.full_width_res,
            "enable_8b10b"            : self.TDC_inst.enable_8b10b,
            "enable_insert"           : self.TDC_inst.enable_insert,
            "enable_error_packet"     : self.TDC_inst.enable_error_packet,
            "enable_TDC_ID"           : self.TDC_inst.enable_TDC_ID,
            "enable_error_notify"     : self.TDC_inst.enable_error_notify,
        }

        # Create and add checkboxes to the grid layout for single-bit variables
        self.checkboxes = {}
        row, col = 0, 0
        for bit_name, bit_var in bit_variables.items():
            checkbox = QtWidgets.QCheckBox(bit_name)
            checkbox.setChecked(bit_var[0] == '1')  # Set checkbox state based on variable value
            checkbox.stateChanged.connect(partial(self.update_bit_variable, bit_name=bit_name))
            self.gridLayout.addWidget(checkbox, row, col)
            self.checkboxes[bit_name] = checkbox
            col += 1
            if col > 4:  # Adjust columns per row as needed
                col = 0
                row += 1

        
         # Add dropdown for width_select instead of a checkbox
        width_select_label = QtWidgets.QLabel("width_select")
        self.gridLayout.addWidget(width_select_label, row, col)

        col += 1
        self.width_select_dropdown = QtWidgets.QComboBox()
        width_options = ["000", "001", "010", "011", "100", "101", "110", "111"]
        self.width_select_dropdown.addItems(width_options)

        # Set initial dropdown selection based on TDC_inst width_select value
        if self.TDC_inst.width_select[0] in width_options:
            self.width_select_dropdown.setCurrentText(self.TDC_inst.width_select[0])

        # Update TDC_inst.width_select when a new option is selected
        self.width_select_dropdown.currentTextChanged.connect(self.update_width_select)
        self.gridLayout.addWidget(self.width_select_dropdown, row, col)

        row += 1
        # Add sections for 24-bit variables with "Select/Unselect All" checkboxes in the main grid layout
        for bit_group_name in ["rising_is_leading", "channel_enable_r", "channel_enable_f"]:
            # Title label and "Select/Unselect All" checkbox for each 24-bit group

            select_all_checkbox = QtWidgets.QCheckBox(f"{bit_group_name} all")
            self.gridLayout.addWidget(select_all_checkbox, row, 0, 1, 3)
            row += 1

            # Add a new grid layout for the 24 individual checkboxes
            bit_group_layout = QtWidgets.QGridLayout()
            bit_checkboxes = []
            for i in range(24):
                checkbox = QtWidgets.QCheckBox(str(23-i))  # Label each checkbox with only the index number
                checkbox.setChecked(self.TDC_inst.__dict__[bit_group_name][0][i] == '1')  # Initial value
                checkbox.stateChanged.connect(
                    lambda state, group=bit_group_name, index=i: self.update_24bit_variable(state, group, index)
                )
                sub_row, sub_col = divmod(i, 24)  # 24 checkboxes per row
                bit_group_layout.addWidget(checkbox, sub_row, sub_col)
                bit_checkboxes.append(checkbox)

            # Add the group layout to the main grid layout
            self.gridLayout.addLayout(bit_group_layout, row, 0, 1, 24)  # Span across 24 columns for alignment
            self.checkboxes[bit_group_name] = bit_checkboxes
            row += 1  # Move to the next row section for the next 24-bit group

            # Connect "Select/Unselect All" functionality
            select_all_checkbox.stateChanged.connect(
                lambda state, checkboxes=bit_checkboxes, group=bit_group_name: self.select_unselect_all(state, checkboxes, group)
            )

        # Add the button window to the main section layout
        sectionLayout.addWidget(buttonWindow)

    def update_bit_variable(self, state, bit_name):
        """Update single-bit variable in TDCreg based on checkbox state."""
        self.TDC_inst.__dict__[bit_name][0] = '1' if state == Qt.Checked else '0'

    def update_24bit_variable(self, state, group, index):
        """Update specific bit in a 24-bit variable string based on checkbox state."""
        bit_list = list(self.TDC_inst.__dict__[group][0])
        bit_list[index] = '1' if state == Qt.Checked else '0'
        self.TDC_inst.__dict__[group][0] = ''.join(bit_list)

    def select_unselect_all(self, state, checkboxes, group):
        """Select or unselect all checkboxes in a 24-bit group and update the TDCreg variable."""
        for i, checkbox in enumerate(checkboxes):
            checkbox.setChecked(state == Qt.Checked)
            self.update_24bit_variable(state, group, i)

    def update_width_select(self, selected_value):
        """Update TDCreg width_select based on dropdown selection."""
        self.TDC_inst.width_select[0] = selected_value
