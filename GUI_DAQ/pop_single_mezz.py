# pop_single_mezz.py
from PyQt5 import QtWidgets, QtCore
import functools
from TDCreg import *

from pop_TDC_setup0 import pop_TDC_setup0  # Import the dialog class
from pop_TDC_setup1 import pop_TDC_setup1  # Import the dialog class
from pop_TDC_setup2 import pop_TDC_setup2  # Import the dialog class
from pop_TDC_control0 import pop_TDC_control0  # Import the dialog class
from pop_TDC_control1 import pop_TDC_control1  # Import the dialog class
from pop_ASD_config import pop_ASD_config  # Import the dialog class

class pop_single_mezz(QtWidgets.QDialog):

    def closeEvent(self, event):
        self.accept()  # Explicitly treat close as accepted

    def __init__(self, TDC_inst, parent=None):
        super().__init__(parent)
        self.TDC_inst = TDC_inst
        self.setWindowTitle("Single Mezz Config")
        self.resize(600, 400)
        self.setup_UI()

    def open_dialog(self, dialog_class, instance, ASD_text=''):
        if len(ASD_text):
            print("Configuring "+ASD_text)
        dialog = dialog_class(instance)
        result = dialog.exec_()  # exec_() for modal behavior, show() for non-modal

        # After closing the ASD pop-up, ask if settings should be copied to other ASD instances
        if isinstance(dialog, pop_ASD_config) and result == QtWidgets.QDialog.Accepted:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Copy Configuration",
                "Do you want to copy these configurations to all 3 ASD instances for this mezz?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                for asd_instance in [self.TDC_inst.ASD0, self.TDC_inst.ASD1, self.TDC_inst.ASD2]:
                    if asd_instance is not instance:
                        dialog.copy_to(asd_instance)
                print("Configurations shared to all ASDs on the same mezz, ready for JTAG config")
            else:
                print(ASD_text+" settings applied in GUI, ready for JTAG config")

    def setup_UI(self):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setModal(True)
        mainLayout = QtWidgets.QVBoxLayout(self)

        # Header for TDC buttons
        tdc_header = QtWidgets.QLabel("TDC Configuration")
        tdc_header.setAlignment(QtCore.Qt.AlignCenter)
        mainLayout.addWidget(tdc_header)

        # Frame for TDC buttons
        tdc_frame = QtWidgets.QFrame()
        tdc_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        tdc_layout = QtWidgets.QGridLayout(tdc_frame)

        column = 0
        row = 0

        # Use QGridLayout to arrange TDC buttons
        tdc_buttons = [
            ("TDC Setup0", pop_TDC_setup0, self.TDC_inst),
            ("TDC Setup1", pop_TDC_setup1, self.TDC_inst),
            ("TDC Setup2", pop_TDC_setup2, self.TDC_inst),
            ("TDC Control0", pop_TDC_control0, self.TDC_inst),
            ("TDC Control1", pop_TDC_control1, self.TDC_inst)
        ]
        for label, dialog_class, instance in tdc_buttons:
            self.create_button(label, row, column, functools.partial(self.open_dialog, dialog_class, instance,''), layout=tdc_layout)
            row += 1

        # Header for ASD buttons
        asd_header = QtWidgets.QLabel("ASD Configuration")
        asd_header.setAlignment(QtCore.Qt.AlignCenter)

        asd_frame = QtWidgets.QFrame()
        asd_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        asd_layout = QtWidgets.QGridLayout(asd_frame)

        row = 0
        column = 0

        asd_buttons = [
            ("ASD0 Setup ( 0~ 7)", pop_ASD_config, self.TDC_inst.ASD0),
            ("ASD1 Setup ( 8~15)", pop_ASD_config, self.TDC_inst.ASD1),
            ("ASD2 Setup (16~23)", pop_ASD_config, self.TDC_inst.ASD2)
        ]
        for label, dialog_class, instance in asd_buttons:
            self.create_button(label, row, column, functools.partial(self.open_dialog, dialog_class, instance,label[0:4]), layout=asd_layout)
            row += 1

        # Add frames to the main layout
        mainLayout.addWidget(tdc_frame)
        mainLayout.addWidget(asd_header)
        mainLayout.addWidget(asd_frame)

    def create_button(self, label, row, column, slot_function, layout=None):
        if layout is None:
            raise ValueError("Layout must be provided for button placement.")
        button = QtWidgets.QPushButton()
        button.setText(label)
        layout.addWidget(button, row, column, 1, 1)
        button.clicked.connect(slot_function)
        return button
