from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from functools import partial
from GUI_lowlevel import *
from TDC_config_low_level_function import *
from StyleSheet import *
from ethernet_control_protocol import EthernetControlError, LPGBT_WRITE
from firmware_links import MAX_UPLINKS, detect_uplink_count


class pop_prbs(QtWidgets.QDialog):
    def __init__(self, eth, rxprbssel, parent=None):
        super().__init__(parent)
        self.eth = eth
        self.lpgbt_master_addr = 117
        self.lpgbt_slave_addr = 115
        self.drpen_index = 31
        self.drpwe_index = 32
        self.drpaddr_index = 33
        self.drpdi_index = 34
        self.rxprbscntreset_index = 35
        self.rxprbssel_index = 36
        self.rxprbs_err_cnt_low_addr = 0x15E
        self.rxprbs_err_cnt_high_addr = 0x15F
        self.rxprbssel = rxprbssel
        self.options = ["None","PRBS-7","PRBS-15","PRBS-23","PRBS-31"]
        self.checker_modes = (0, 1, 3, 4, 5)  # FPGA also supports PRBS-9.
        self.mode_controls = []
        self.uplink_count = None  # Read from the firmware at the first status update.

        self.setWindowTitle("PRBS test")
        self.setup_UI()

    def setup_UI(self):
        sectionLayout = QtWidgets.QVBoxLayout(self)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)

        row = 0
        column = 0

        row += 1
        column = 0
        self.led_locked = []
        self.led_error = []
        self.bit_error = []

        for which_csm in range(2):
            for lpGBT_address in [self.lpgbt_master_addr,self.lpgbt_slave_addr]:

                is_master = 1 if lpGBT_address==self.lpgbt_master_addr else 0
                mapping_index = which_csm*2+1-is_master
                checker_mode = (self.rxprbssel[0] >> (mapping_index*4)) & 0xF
                combobox_index = self.checker_modes.index(checker_mode) if checker_mode in self.checker_modes else 0

                label = QtWidgets.QLabel()
                label.setText(f'CSM{which_csm} '+f'master'if is_master else f'CSM{which_csm} '+f'slave')
                self.gridLayout.addWidget(label, row, mapping_index*2, 1, 2)
                row+=1

                combobox = create_combobox("prbs option", row, column, 1,
                    partial(self.set_prbs_mode, which_csm, lpGBT_address, "prbs option"),
                    options = self.options, #lpGBT does not support 2:PRBS-9
                    value=combobox_index, layout=self.gridLayout)
                self.mode_controls.append(combobox)
                row+=1
                create_button("Counter reset", row, column, 1, 
                    partial(self.handle_button, which_csm, lpGBT_address,self.rxprbscntreset_index,'Counter reset'), layout=self.gridLayout)
                row+=1
                label = QtWidgets.QLabel()
                label.setText("Err Bit")
                self.gridLayout.addWidget(label, row, column, 1, 1)

                column+=1
                label = QtWidgets.QLabel()
                label.setText("-")
                self.gridLayout.addWidget(label, row, column, 1, 1)
                self.bit_error.append(label)
                column-=1

               
                row +=1
                label = QtWidgets.QLabel()
                label.setText("PRBS lock")
                self.gridLayout.addWidget(label, row, column, 1, 1)

                column+=1
                status = QtWidgets.QLabel()
                status.setStyleSheet(LedGray)
                self.gridLayout.addWidget(status, row, column, 1, 1)
                column-=1
                self.led_locked.append(status)

                row +=1
                label = QtWidgets.QLabel()
                label.setText("PRBS err")
                self.gridLayout.addWidget(label, row, column, 1, 1)

                column+=1
                status = QtWidgets.QLabel()
                status.setStyleSheet(LedGray)
                self.gridLayout.addWidget(status, row, column, 1, 1)
                column-=1
                self.led_error.append(status)

                row-=5
                column += 2

        row += 6
        column = 0
        create_button("Update PRBS Status", row, column, 4, self.update_prbs_status, layout=self.gridLayout)
        # column += 4
        # create_button("Update Err counter", row, column, 4, self.read_PRBS_error, layout=self.gridLayout)
        
        sectionLayout.addWidget(buttonWindow)
        self.message_label = QtWidgets.QLabel("")
        self.message_label.setWordWrap(True)
        sectionLayout.addWidget(self.message_label)


    def set_uplink_prbs(self, which_csm, lpgbt_addr, state):
        set_enable = 1 if state == Qt.Checked else 0
        if set_enable:
            lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.ULDATASOURCE0.address, value_list=[0x04], which_csm=which_csm, lpgbt_addr=lpgbt_addr)
        else:
            lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.ULDATASOURCE0.address, value_list=[0x00], which_csm=which_csm, lpgbt_addr=lpgbt_addr)

    def set_prbs_mode(self, which_csm, lpgbt_addr, name, selection_index):
        is_master = 1 if lpgbt_addr==self.lpgbt_master_addr else 0
        mapping_index = which_csm*2+1-is_master


        print(f"CSM{which_csm} {lpgbt_addr} {name} set to {self.options[selection_index]}")

        missing_reply = False
        try:
            with ethernet_exclusive_session(self.eth):
                try:
                    lpgbt_config_write(self.eth, reg_addr=LpgbtRegisterMapV1.ULDATASOURCE0.address, value_list=[selection_index], which_csm=which_csm, lpgbt_addr=lpgbt_addr)
                except EthernetControlError as error:
                    # Raw PRBS replaces the framed uplink, including IC replies.
                    # Only accept the FPGA's explicit IC timeout when enabling
                    # PRBS; transport errors and other failures remain errors.
                    if selection_index == 0 or error.status != 3 or error.opcode != LPGBT_WRITE:
                        raise
                    missing_reply = True
                value = self.rxprbssel[0] & ~(0xF << (mapping_index*4))
                value |= self.checker_modes[selection_index] << (mapping_index*4)
                fpga_config(self.eth, self.rxprbssel_index, value_to_list(value))
                self.rxprbssel[0] = value
        except Exception as error:
            control = self.mode_controls[mapping_index]
            previous = (self.rxprbssel[0] >> (mapping_index*4)) & 0xF
            blocked = control.blockSignals(True)
            control.setCurrentIndex(self.checker_modes.index(previous) if previous in self.checker_modes else 0)
            control.blockSignals(blocked)
            self.message_label.setText(f"PRBS configuration failed: {error}. Read status before retrying.")
            return
        message = f"CSM{which_csm} {'master' if is_master else 'slave'}: {self.options[selection_index]} checker configured."
        if missing_reply:
            message += " No IC reply after switching to raw PRBS; update status to verify PRBS lock."
        self.message_label.setText(message)

    def handle_button(self, which_csm, lpgbt_addr, index, name):
        is_master = 1 if lpgbt_addr==self.lpgbt_master_addr else 0
        mapping_index = which_csm*2+1-is_master
        value = 1 << mapping_index

        #set
        fpga_config(self.eth, index, value_to_list(value))
        print(f"CSM{which_csm} {lpgbt_addr} {name} ({index}) set to {value:04b}")
        #stop
        fpga_config(self.eth, index, value_to_list(0))
        print(f"CSM{which_csm} {lpgbt_addr} {name} ({index}) set to 0000")

    def read_PRBS_error(self):

        low_addr = self.rxprbs_err_cnt_low_addr
        low_addr |= low_addr<<9
        low_addr |= low_addr<<9
        low_addr |= low_addr<<9
        high_addr = self.rxprbs_err_cnt_high_addr
        high_addr |= high_addr<<9
        high_addr |= high_addr<<9
        high_addr |= high_addr<<9
        print(f'low_addr={low_addr:x}')
        print(f'high_addr={high_addr:x}')
        #set drp reg address for lower 16 bits
        fpga_config(self.eth, self.drpaddr_index, value_to_list(low_addr))
        #read drp
        fpga_config(self.eth, self.drpen_index, value_to_list(0b1111))
        fpga_config(self.eth, self.drpen_index, value_to_list(0))
        #read to GUI
        low_str=fpga_readback(self.eth, 6)
        print(f'low_str ='+low_str)

        #set drp reg address for higher 16 bits
        fpga_config(self.eth, self.drpaddr_index, value_to_list(high_addr))
        #read drp
        fpga_config(self.eth, self.drpen_index, value_to_list(0b1111))
        fpga_config(self.eth, self.drpen_index, value_to_list(0))
        #read to GUI
        high_str=fpga_readback(self.eth, 6)
        print(f'high_str ='+high_str)
        low, high = int(low_str, 2), int(high_str, 2)
        for link, label in enumerate(self.bit_error):  # DRP data: one 16-bit word per uplink from bit 0
            if link >= self.uplink_count:
                label.setText("n/a")
                continue
            count = (((high >> (link*16)) & 0xFFFF) << 16) | ((low >> (link*16)) & 0xFFFF)
            label.setText(f'{count:08X}')



    def update_prbs_status(self):
        try:
            with ethernet_exclusive_session(self.eth):
                if self.uplink_count is None:
                    self.uplink_count = detect_uplink_count(self.eth)
                bin_str = fpga_readback(self.eth, 6)
                if not isinstance(bin_str, str) or len(bin_str) != 160:
                    raise RuntimeError("Incomplete FPGA PRBS status")
                self.read_PRBS_error()
            # Page 6, from bit 0: DRP data, locked byte, error byte (see firmware_links.py).
            page = int(bin_str, 2)
            uplinks = self.uplink_count
            mask = (1 << uplinks) - 1
            locked = (page >> (uplinks*16)) & mask
            error = (page >> (uplinks*16 + 8)) & mask
            self.update_prbs_led(error=format(error, f'0{uplinks}b'),
                                 locked=format(locked, f'0{uplinks}b'))
            message = "PRBS status updated."
            if uplinks < MAX_UPLINKS:
                message += f" This firmware has {uplinks} uplinks; the other columns are not available."
            self.message_label.setText(message)
        except Exception as error:
            self.update_prbs_led()
            for label in self.bit_error:
                label.setText("-")
            self.message_label.setText(f"PRBS status failed: {error}")

    def update_prbs_led(self,error='',locked=''):
        if error:
            # reverse the string and iterate with LEDs
            for led, c in zip(self.led_error, reversed(error)):
                if c == '0':
                    led.setStyleSheet(LedGreen)
                else:
                    led.setStyleSheet(LedRed)
            for led in self.led_error[len(error):]:
                led.setStyleSheet(LedGray)
        else:
            for led in self.led_error:
                led.setStyleSheet(LedGray)

        if locked:
            # reverse the string and iterate with LEDs
            for led, c in zip(self.led_locked, reversed(locked)):
                if c == '1':
                    led.setStyleSheet(LedGreen)
                else:
                    led.setStyleSheet(LedRed)
            for led in self.led_locked[len(locked):]:
                led.setStyleSheet(LedGray)
        else:
            for led in self.led_locked:
                led.setStyleSheet(LedGray)





