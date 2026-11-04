from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from GUI_lowlevel import *
from TDC_config_low_level_function import *

class pop_BER(QtWidgets.QDialog):
    def __init__(self, eth, miniDAQ_reg, parent=None):
        super().__init__(parent)
        self.eth = eth
        self.miniDAQ_reg = miniDAQ_reg
        self.setWindowTitle("BER monitor")
        
        self.setup_UI()

    def setup_UI(self):
        sectionLayout = QtWidgets.QVBoxLayout(self)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                   QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)

        self.value_labels_groups = []

        headers = [
            "TDC",
            "dline1_rec40",
            "dline0_rec40",
            "dline1_err",            
            "dline0_err",
            "dline1_BER",
            "dline0_BER"
        ]

        groups = [
            (39, 30, 0, 0),  # top-left
            (29, 20, 0, 1),  # top-right
            (19, 10, 1, 0),  # bottom-left
            (9, 0, 1, 1)     # bottom-right
        ]

        for start, end, grid_row, grid_col in groups:
            widget = QtWidgets.QWidget()
            grid = QtWidgets.QGridLayout(widget)

            # Add headers
            for col, header in enumerate(headers):
                lbl = QtWidgets.QLabel(header)
                lbl.setAlignment(Qt.AlignCenter)
                grid.addWidget(lbl, 0, col)

            group_labels = []
            for row, tdc in enumerate(range(start, end - 1, -1), start=1):
                tdc_lbl = QtWidgets.QLabel(f"{tdc}")
                tdc_lbl.setAlignment(Qt.AlignCenter)
                grid.addWidget(tdc_lbl, row, 0)

                row_labels = []
                for col in range(1, len(headers)):  # 6 value columns
                    lbl = QtWidgets.QLabel("0")
                    lbl.setAlignment(Qt.AlignCenter)
                    grid.addWidget(lbl, row, col)
                    row_labels.append(lbl)
                group_labels.append((tdc, row_labels))

            self.value_labels_groups.append(group_labels)
            self.gridLayout.addWidget(widget, grid_row, grid_col)

        sectionLayout.addWidget(buttonWindow)

        # --- Update button ---
        update_btn = QtWidgets.QPushButton("Update")
        update_btn.clicked.connect(self.on_update_clicked)
        sectionLayout.addWidget(update_btn, alignment=Qt.AlignCenter)

    def decode_BER_info(self, bin_str):
        """
        Decode 160-bit binary string into 4 decimal values.
        Returns (rec_dline1, rec_dline0, err_dline1, err_dline0).
        """
        if len(bin_str) != 160:
            raise ValueError(f"BER_info length mismatch: got {len(bin_str)}")

        rec_dline1 = int(bin_str[0:44], 2)     # bits 159..116
        rec_dline0 = int(bin_str[44:88], 2)    # bits 115..72
        err_dline1 = int(bin_str[88:124], 2)   # bits 71..36
        err_dline0 = int(bin_str[124:160], 2)  # bits 35..0

        return (rec_dline1, rec_dline0, err_dline1, err_dline0)

    def on_update_clicked(self):
        BER_info_list = []

        for tdc in range(40):
            bin_str = fpga_readback_BER(self.eth, tdc)
            if len(bin_str) != 160:
                print(f"Readback str length = {len(bin_str)} for TDC {tdc}")
                values = (0, 0, 0, 0)
            else:
                values = self.decode_BER_info(bin_str)
            BER_info_list.append(values)

        self.update_BER_info(BER_info_list)

    def format_value(self, val, sci=False):
        """Helper: format val as scientific if sci==True and val!=0."""
        if sci:
            return f"{val:.3e}" if val != 0 else "0"
        else:
            return f"{val:d}"

    def update_BER_info(self, BER_info_list):
        """
        BER_info_list: list of 40 entries (TDC 0..39),
        each entry a tuple/list of 4 integers
        [dline1_rec40, dline0_rec40, dline1_err, dline0_err]
        """
        for group in self.value_labels_groups:
            for tdc, labels in group:
                rec1, rec0, err1, err0 = BER_info_list[tdc]

                # Compute BER values safely
                ber1 = err1 / rec1 / 40 if rec1 > 0 else 0.0
                ber0 = err0 / rec0 / 40 if rec0 > 0 else 0.0

                values = [rec1, rec0, err1, err0, ber1, ber0]

                for col_idx, val in enumerate(values):
                    if col_idx in (0, 1, 4, 5):  # rec40 + BER
                        labels[col_idx].setText(self.format_value(val, sci=True))
                    else:  # error counts as integer
                        labels[col_idx].setText(self.format_value(val, sci=False))
