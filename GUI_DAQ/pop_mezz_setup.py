# pop_mezz_setup.py
from PyQt5 import QtWidgets, QtCore
import functools
from pop_single_mezz import pop_single_mezz
from ASDreg import *
import os




class pop_mezz_setup(QtWidgets.QDialog):

    def open_dialog(self, dialog_class, instance, mezz_no):
        print("Configuring mezz %d"%mezz_no)
        dialog = dialog_class(instance)
        result = dialog.exec_()  # exec_() for modal behavior, show() for non-modal

        # After closing the mezz pop-up, ask if settings should be copied to other mezz instances
        if result == QtWidgets.QDialog.Accepted:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Copy Configuration",
                "Do you want to copy these configurations to all mezz (both TDCs and ASDs)?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.copy_TDC_settings(mezz_no)
                print("Configurations shared to all mezz, ready for JTAG config")
            else:
                print("Mezz%d settings applied in GUI, ready for JTAG config"%mezz_no)



    def copy_TDC_settings(self, mezz_no):
        for j in range(len(self.CSM_list)):
            for i in range(len(self.CSM_list[j].TDC_list)):
                if mezz_no!=(j*20+i):
                    for key, value in self.CSM_list[j].TDC_list[i].__dict__.items():
                        # other_instance.__dict__[key][0] = value[0]
                        if isinstance(value, list) and all(not isinstance(item, list) for item in value):
                            if key != "ASD_list":
                                self.CSM_list[j].TDC_list[i].__dict__[key][0] = self.CSM_list[mezz_no//20].TDC_list[mezz_no%20].__dict__[key][0]
                            else:
                                for k in range(len(self.CSM_list[j].TDC_list[i].ASD_list)):
                                    for key, value in self.CSM_list[j].TDC_list[i].ASD_list[k].__dict__.items():
                                        self.CSM_list[j].TDC_list[i].ASD_list[k].__dict__[key][0] = self.CSM_list[mezz_no//20].TDC_list[mezz_no%20].ASD_list[k].__dict__[key][0]
                                        # print(key)
                                        # print(value)



    def __init__(self, CSM_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mezz Config")
        self.CSM_list = CSM_list
        self.resize(600, 400)
        self.setup_UI()

    def setup_UI(self):
        sectionLayout = QtWidgets.QVBoxLayout(self)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)

        row = 0
        column = 0

        for j in range(len(self.CSM_list)):
            for i in range(len(self.CSM_list[j].TDC_list)):
                self.create_button('Mezz%d'%(i+20*j),row, column, 1, 
                    functools.partial(self.open_dialog, pop_single_mezz, self.CSM_list[j].TDC_list[i],j*20+i),layout = self.gridLayout)
                column += 1
                if column ==10:
                    row +=1
                    column = 0

        row += 1
        column = 0
        self.pushButton_TDC_setup = self.create_button("Save_setup", row, column, 2, self.save_settings, layout = self.gridLayout)

        column += 2
        self.pushButton_TDC_setup = self.create_button("Load_setup", row, column, 2, self.read_settings, layout = self.gridLayout)

        column += 2
        self.pushButton_TDC_setup = self.create_button("Save_default", row, column, 2, self.save_settings_default, layout = self.gridLayout)

        column += 2
        self.pushButton_TDC_setup = self.create_button("Load_default", row, column, 2, self.read_settings_default, layout = self.gridLayout)

        # Add the button window to the main section layout
        sectionLayout.addWidget(buttonWindow)




    def save_settings(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if folder_path:
            self.save_settings_to_file(folder_path)
        else:
            print("Folder "+folder_path+" does not exist")

    def read_settings(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if folder_path:
            self.read_settings_from_file(folder_path)
        else:
            print("Folder "+folder_path+" does not exist")

    def save_settings_default(self):
        current_folder = os.getcwd()
        folder_path = current_folder+'/Mezz_setup_default'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created.")
        self.save_settings_to_file(folder_path)

    def read_settings_default(self):
        current_folder = os.getcwd()
        folder_path = current_folder+'/Mezz_setup_default'
        self.read_settings_from_file(folder_path)

    def read_settings_from_file(self,folder_path):
        if os.path.exists(folder_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Load Settings",
                f"Do you want to load settings from {folder_path}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                for j in range(len(self.CSM_list)):
                    for i in range(len(self.CSM_list[j].TDC_list)):
                        try:
                            TDC_file_path = folder_path+'/Mezz%02dTDC.txt'%(j*20+i)
                            self.populate_instance(TDC_file_path,self.CSM_list[j].TDC_list[i])
                        except Exception as e:
                            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")


                        for k in range(len(self.CSM_list[j].TDC_list[i].ASD_list)):
                            try:
                                ASD_file_path = folder_path+'/Mezz%02dASD%d.txt'%(j*20+i,k)
                                self.populate_instance(ASD_file_path,self.CSM_list[j].TDC_list[i].ASD_list[k])
                            except Exception as e:
                                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
                print("Settings loaded from "+folder_path)
            else:
                print("Settings loading canceled.")
        else:
            print("Folder "+folder_path+" does not exist")
                            

    def populate_instance(self,file_path, instance):
        with open(file_path, 'r') as file:
            for line in file:
                if not line.strip():
                    continue  # Skip empty lines
                key, value = line.strip().split(",", 1)
                key, value = key.strip(), value.strip()
                if hasattr(instance, key):
                    # Update the list attribute
                    attr = getattr(instance, key)
                    if isinstance(attr, list):
                        attr[0] = value  # Update the first element of the list
                    else:
                        setattr(instance, key, value)



    def save_settings_to_file(self,folder_path):
        if os.path.exists(folder_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Save Settings",
                f"Do you want to save settings to {folder_path}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                for j in range(len(self.CSM_list)):
                    for i in range(len(self.CSM_list[j].TDC_list)):
                        try:
                            with open(folder_path+'/Mezz%02dTDC.txt'%(j*20+i), 'w') as tdc_file:
                                for key, value in self.CSM_list[j].TDC_list[i].__dict__.items():
                                    # other_instance.__dict__[key][0] = value[0]
                                    if isinstance(value, list) and all(not isinstance(item, list) for item in value) and not isinstance(value[0], ASD_chip):
                                        tdc_file.write(key)
                                        tdc_file.write(',')
                                        tdc_file.write(value[0])
                                        tdc_file.write('\n')
                        except Exception as e:
                            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

                        for k in range(len(self.CSM_list[j].TDC_list[i].ASD_list)):
                            try:
                                with open(folder_path+'/Mezz%02dASD%d.txt'%(j*20+i,k), 'w') as asd_file:
                                    for key, value in self.CSM_list[j].TDC_list[i].ASD_list[k].__dict__.items():
                                        # other_instance.__dict__[key][0] = value[0]
                                        if isinstance(value, list) and all(not isinstance(item, list) for item in value):
                                            asd_file.write(key)
                                            asd_file.write(',')
                                            asd_file.write(value[0])
                                            asd_file.write('\n')
                            except Exception as e:
                                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
                print("All setups are saved to "+folder_path)
            else:
                print("Settings saving canceled.")
        else:
            print("Folder "+folder_path+" does not exist")


        


    def create_button(self, label, row, column, width,slot_function, layout=None):
        if layout is None:
            raise ValueError("Layout must be provided for button placement.")
        button = QtWidgets.QPushButton()
        button.setText(label)
        layout.addWidget(button, row, column, 1, width)
        button.clicked.connect(slot_function)
        return button
        

