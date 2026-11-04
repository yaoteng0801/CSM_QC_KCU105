from PyQt5 import QtCore, QtWidgets

from firmware_links import detect_uplink_count, downlink_count
from TDC_config_low_level_function import fpga_config, fpga_readback, value_to_list


class pop_link_setup(QtWidgets.QDialog):
    UPLINK_COUNT = 4
    DOWNLINK_COUNT = 2
    UPLINK_LABELS = (
        "Uplink 0\nCSM0 master",
        "Uplink 1\nCSM0 slave",
        "Uplink 2\nCSM1 master",
        "Uplink 3\nCSM1 slave",
    )
    DOWNLINK_LABELS = (
        "Downlink 0\nCSM0",
        "Downlink 1\nCSM1",
    )

    UPLINK_REGISTERS = {
        "interleaver_bypass": 46,
        "fec_bypass": 47,
        "scrambler_bypass": 48,
        "rx_polarity": 49,
        "fec_clear": 50,
        "phase_calib": 51,
        "phase_force": 52,
    }
    DOWNLINK_REGISTERS = {
        "interleaver_bypass": 53,
        "fec_bypass": 54,
        "scrambler_bypass": 55,
        "tx_pi_calib": 56,
        "tx_calib_enable": 57,
        "tx_polarity": 58,
        "phase_calib": 59,
        "phase_force": 60,
    }

    def __init__(self, eth, parent=None):
        super().__init__(parent)
        self.eth = eth
        self.setWindowTitle("FPGA lpGBT Link Controls")
        self.resize(760, 520)

        self.uplink_controls = {}
        self.uplink_status = {}
        self.downlink_controls = {}
        self.downlink_status = {}
        self.firmware_uplinks = None  # Read from the firmware at the first refresh.

        self._setup_ui()
        QtCore.QTimer.singleShot(0, self.refresh_from_fpga)

    @staticmethod
    def _new_spinbox(maximum):
        widget = QtWidgets.QSpinBox()
        widget.setRange(0, maximum)
        return widget

    @staticmethod
    def _add_header(layout, labels):
        layout.addWidget(QtWidgets.QLabel("Option"), 0, 0)
        for link, text in enumerate(labels):
            label = QtWidgets.QLabel(text)
            label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(label, 0, link + 1)

    @staticmethod
    def _add_control_row(layout, row, label, widgets):
        layout.addWidget(QtWidgets.QLabel(label), row, 0)
        for link, widget in enumerate(widgets):
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setToolTip(f"{label} for link {link}")
                cell = QtWidgets.QWidget()
                cell_layout = QtWidgets.QHBoxLayout(cell)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.addStretch(1)
                cell_layout.addWidget(widget)
                cell_layout.addStretch(1)
                layout.addWidget(cell, row, link + 1)
            else:
                layout.addWidget(widget, row, link + 1)

    @staticmethod
    def _add_status_row(layout, row, label, widgets):
        layout.addWidget(QtWidgets.QLabel(label), row, 0)
        for link, widget in enumerate(widgets):
            widget.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(widget, row, link + 1)

    def _setup_ui(self):
        root_layout = QtWidgets.QVBoxLayout(self)

        description = QtWidgets.QLabel(
            "Controls are packed per logical link. Read from FPGA before editing, "
            "then apply the uplink or downlink group."
        )
        description.setWordWrap(True)
        root_layout.addWidget(description)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_uplink_tab(), "Uplinks")
        tabs.addTab(self._build_downlink_tab(), "Downlinks")
        root_layout.addWidget(tabs, 1)

        self.message_label = QtWidgets.QLabel("Waiting for FPGA readback…")
        self.message_label.setWordWrap(True)
        root_layout.addWidget(self.message_label)

        button_layout = QtWidgets.QHBoxLayout()
        refresh_button = QtWidgets.QPushButton("Read from FPGA")
        refresh_button.clicked.connect(self.refresh_from_fpga)
        self.apply_uplink_button = QtWidgets.QPushButton("Apply uplinks")
        self.apply_uplink_button.setEnabled(False)
        self.apply_uplink_button.clicked.connect(self.apply_uplinks)
        self.apply_downlink_button = QtWidgets.QPushButton("Apply downlinks")
        self.apply_downlink_button.setEnabled(False)
        self.apply_downlink_button.clicked.connect(self.apply_downlinks)
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.accept)

        button_layout.addWidget(refresh_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.apply_uplink_button)
        button_layout.addWidget(self.apply_downlink_button)
        button_layout.addWidget(close_button)
        root_layout.addLayout(button_layout)

    def _build_uplink_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(tab)
        self._add_header(layout, self.UPLINK_LABELS)

        boolean_rows = (
            ("interleaver_bypass", "Interleaver bypass"),
            ("fec_bypass", "FEC bypass"),
            ("scrambler_bypass", "Scrambler bypass"),
            ("rx_polarity", "RX polarity invert"),
        )
        row = 1
        for key, label in boolean_rows:
            widgets = [QtWidgets.QCheckBox() for _ in range(self.UPLINK_COUNT)]
            self.uplink_controls[key] = widgets
            self._add_control_row(layout, row, label, widgets)
            row += 1

        phase_calib = [self._new_spinbox(7) for _ in range(self.UPLINK_COUNT)]
        self.uplink_controls["phase_calib"] = phase_calib
        self._add_control_row(layout, row, "Phase calibration (3-bit)", phase_calib)
        row += 1

        phase_force = [QtWidgets.QCheckBox() for _ in range(self.UPLINK_COUNT)]
        self.uplink_controls["phase_force"] = phase_force
        self._add_control_row(layout, row, "Force calibrated phase", phase_force)
        row += 1

        clear_buttons = []
        for link in range(self.UPLINK_COUNT):
            button = QtWidgets.QPushButton("Clear")
            button.clicked.connect(lambda _checked=False, index=link: self.clear_uplink_fec(index))
            clear_buttons.append(button)
        self._add_control_row(layout, row, "FEC corrected latch", clear_buttons)
        row += 1

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        layout.addWidget(separator, row, 0, 1, self.UPLINK_COUNT + 1)
        row += 1

        for key, label in (
            ("ready", "Ready"),
            ("fec_corrected", "FEC corrected"),
            ("phase", "Measured phase"),
        ):
            widgets = [QtWidgets.QLabel("—") for _ in range(self.UPLINK_COUNT)]
            self.uplink_status[key] = widgets
            self._add_status_row(layout, row, label, widgets)
            row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _build_downlink_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(tab)
        self._add_header(layout, self.DOWNLINK_LABELS)

        row = 1
        for key, label in (
            ("interleaver_bypass", "Interleaver bypass"),
            ("fec_bypass", "FEC bypass"),
            ("scrambler_bypass", "Scrambler bypass"),
        ):
            widgets = [QtWidgets.QCheckBox() for _ in range(self.DOWNLINK_COUNT)]
            self.downlink_controls[key] = widgets
            self._add_control_row(layout, row, label, widgets)
            row += 1

        tx_pi_calib = [self._new_spinbox(127) for _ in range(self.DOWNLINK_COUNT)]
        self.downlink_controls["tx_pi_calib"] = tx_pi_calib
        self._add_control_row(layout, row, "TX PI calibration (7-bit)", tx_pi_calib)
        row += 1

        for key, label in (
            ("tx_calib_enable", "TX calibration enable"),
            ("tx_polarity", "TX polarity invert"),
        ):
            widgets = [QtWidgets.QCheckBox() for _ in range(self.DOWNLINK_COUNT)]
            self.downlink_controls[key] = widgets
            self._add_control_row(layout, row, label, widgets)
            row += 1

        phase_calib = [self._new_spinbox(1023) for _ in range(self.DOWNLINK_COUNT)]
        self.downlink_controls["phase_calib"] = phase_calib
        self._add_control_row(layout, row, "Phase calibration (10-bit)", phase_calib)
        row += 1

        phase_force = [QtWidgets.QCheckBox() for _ in range(self.DOWNLINK_COUNT)]
        self.downlink_controls["phase_force"] = phase_force
        self._add_control_row(layout, row, "Force calibrated phase", phase_force)
        row += 1

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        layout.addWidget(separator, row, 0, 1, self.DOWNLINK_COUNT + 1)
        row += 1

        for key, label in (
            ("ready", "Ready"),
            ("phase", "Measured phase"),
            ("tx_aligned", "TX aligned"),
            ("tx_pi_phase", "TX PI phase"),
        ):
            widgets = [QtWidgets.QLabel("—") for _ in range(self.DOWNLINK_COUNT)]
            self.downlink_status[key] = widgets
            self._add_status_row(layout, row, label, widgets)
            row += 1

        layout.setColumnStretch(self.DOWNLINK_COUNT + 1, 1)
        layout.setRowStretch(row, 1)
        return tab

    def _set_message(self, text, error=False):
        self.message_label.setText(text)
        self.message_label.setStyleSheet("color: #b00020;" if error else "")
        print(f"[Link controls] {text}")

    @staticmethod
    def _set_boolean_status(label, value, bad_when_true=False):
        value = bool(value)
        label.setText("Yes" if value else "No")
        bad = value if bad_when_true else not value
        label.setStyleSheet(
            "background-color: #ffcdd2; padding: 2px;" if bad
            else "background-color: #c8e6c9; padding: 2px;"
        )

    @staticmethod
    def _set_numeric_status(label, value):
        label.setText(str(value))
        label.setStyleSheet("")

    @staticmethod
    def _decode_page(raw, expected_page):
        if not isinstance(raw, str):
            raise ValueError(f"page {expected_page} readback is empty")
        bits = "".join(raw.split())
        if len(bits) < 160 or any(bit not in "01" for bit in bits):
            raise ValueError(
                f"page {expected_page} readback has {len(bits)} valid/invalid bits"
            )
        value = int(bits[-160:], 2)
        # The Ethernet response/request ID identifies the transaction. The
        # former page byte at [159:152] is no longer embedded in readback data.
        return value

    def _select_fpga_mapping(self):
        # FPGA monitoring requests carry their own destination and need no
        # global reply-source selection.
        return None

    def _write_register(self, address, value):
        result = fpga_config(self.eth, address, value_to_list(int(value)))
        if result != 0:
            raise RuntimeError(
                f"register {address} write returned {result}"
            )

    @staticmethod
    def _pack_checks(widgets):
        value = 0
        for link, widget in enumerate(widgets):
            if widget.isChecked():
                value |= 1 << link
        return value

    @staticmethod
    def _pack_spins(widgets, width):
        mask = (1 << width) - 1
        value = 0
        for link, widget in enumerate(widgets):
            value |= (widget.value() & mask) << (width * link)
        return value

    @staticmethod
    def _load_checks(widgets, value):
        for link, widget in enumerate(widgets):
            widget.setChecked(bool(value & (1 << link)))

    @staticmethod
    def _load_spins(widgets, value, width):
        mask = (1 << width) - 1
        for link, widget in enumerate(widgets):
            widget.setValue((value >> (width * link)) & mask)

    def refresh_from_fpga(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self._select_fpga_mapping()
            if self.firmware_uplinks is None:
                self.firmware_uplinks = detect_uplink_count(self.eth)
                self._disable_absent_links()
            status_page = self._decode_page(fpga_readback(self.eth, 3), 3)
            uplink_page = self._decode_page(fpga_readback(self.eth, 7), 7)
            downlink_page = self._decode_page(fpga_readback(self.eth, 8), 8)
            self._load_uplink_page(status_page, uplink_page)
            self._load_downlink_page(status_page, downlink_page)
        except Exception as error:
            self.apply_uplink_button.setEnabled(False)
            self.apply_downlink_button.setEnabled(False)
            self._set_message(f"FPGA readback failed: {error}", error=True)
        else:
            self.apply_uplink_button.setEnabled(True)
            self.apply_downlink_button.setEnabled(True)
            self._set_message("Readback pages 3, 7, and 8 updated.")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _disable_absent_links(self):
        # Keep every column visible; links this firmware lacks cannot be edited.
        uplinks = self.firmware_uplinks
        for widgets in self.uplink_controls.values():
            for link, widget in enumerate(widgets):
                widget.setEnabled(link < uplinks)
        for widgets in self.downlink_controls.values():
            for link, widget in enumerate(widgets):
                widget.setEnabled(link < downlink_count(uplinks))

    def _load_uplink_page(self, status_page, page):
        # Page 7 fields are sized by the firmware's uplink count (MiniDAQ_reg.sv).
        count = self.firmware_uplinks
        mask = (1 << count) - 1
        phase_mask = (1 << (3 * count)) - 1
        fields = {
            "interleaver_bypass": page & mask,
            "fec_bypass": (page >> count) & mask,
            "scrambler_bypass": (page >> (2 * count)) & mask,
            "rx_polarity": (page >> (3 * count)) & mask,
            "phase_force": (page >> (5 * count)) & mask,
        }
        for key, value in fields.items():
            self._load_checks(self.uplink_controls[key], value)
        self._load_spins(
            self.uplink_controls["phase_calib"],
            (page >> (6 * count)) & phase_mask,
            3,
        )

        ready = (status_page >> 8) & mask
        fec_corrected = (page >> (9 * count)) & mask
        phase = (page >> (10 * count)) & phase_mask
        for link in range(count):
            self._set_boolean_status(
                self.uplink_status["ready"][link],
                ready & (1 << link),
            )
            self._set_boolean_status(
                self.uplink_status["fec_corrected"][link],
                fec_corrected & (1 << link),
                bad_when_true=True,
            )
            self._set_numeric_status(
                self.uplink_status["phase"][link],
                (phase >> (3 * link)) & 0x7,
            )

    def _load_downlink_page(self, status_page, page):
        # Page 8 fields are sized by the firmware's downlink count (MiniDAQ_reg.sv).
        count = downlink_count(self.firmware_uplinks)
        mask = (1 << count) - 1
        pi_mask = (1 << (7 * count)) - 1
        phase_mask = (1 << (10 * count)) - 1
        fields = {
            "interleaver_bypass": page & mask,
            "fec_bypass": (page >> count) & mask,
            "scrambler_bypass": (page >> (2 * count)) & mask,
            "tx_calib_enable": (page >> (10 * count)) & mask,
            "tx_polarity": (page >> (11 * count)) & mask,
            "phase_force": (page >> (22 * count)) & mask,
        }
        for key, value in fields.items():
            self._load_checks(self.downlink_controls[key], value)
        self._load_spins(
            self.downlink_controls["tx_pi_calib"],
            (page >> (3 * count)) & pi_mask,
            7,
        )
        self._load_spins(
            self.downlink_controls["phase_calib"],
            (page >> (12 * count)) & phase_mask,
            10,
        )

        ready = status_page & mask
        phase = (page >> (24 * count)) & phase_mask
        tx_aligned = (page >> (34 * count)) & mask
        tx_pi_phase = (page >> (35 * count)) & pi_mask
        for link in range(count):
            self._set_boolean_status(
                self.downlink_status["ready"][link],
                ready & (1 << link),
            )
            self._set_numeric_status(
                self.downlink_status["phase"][link],
                (phase >> (10 * link)) & 0x3FF,
            )
            self._set_boolean_status(
                self.downlink_status["tx_aligned"][link],
                tx_aligned & (1 << link),
            )
            self._set_numeric_status(
                self.downlink_status["tx_pi_phase"][link],
                (tx_pi_phase >> (7 * link)) & 0x7F,
            )

    def apply_uplinks(self):
        values = {
            "interleaver_bypass": self._pack_checks(
                self.uplink_controls["interleaver_bypass"]
            ),
            "fec_bypass": self._pack_checks(
                self.uplink_controls["fec_bypass"]
            ),
            "scrambler_bypass": self._pack_checks(
                self.uplink_controls["scrambler_bypass"]
            ),
            "rx_polarity": self._pack_checks(
                self.uplink_controls["rx_polarity"]
            ),
            "phase_calib": self._pack_spins(
                self.uplink_controls["phase_calib"], 3
            ),
            "phase_force": self._pack_checks(
                self.uplink_controls["phase_force"]
            ),
        }
        self._apply_register_group(
            self.UPLINK_REGISTERS,
            values,
            (
                "interleaver_bypass",
                "fec_bypass",
                "scrambler_bypass",
                "rx_polarity",
                "phase_calib",
                "phase_force",
            ),
            "Uplink controls applied.",
        )

    def apply_downlinks(self):
        values = {
            "interleaver_bypass": self._pack_checks(
                self.downlink_controls["interleaver_bypass"]
            ),
            "fec_bypass": self._pack_checks(
                self.downlink_controls["fec_bypass"]
            ),
            "scrambler_bypass": self._pack_checks(
                self.downlink_controls["scrambler_bypass"]
            ),
            "tx_pi_calib": self._pack_spins(
                self.downlink_controls["tx_pi_calib"], 7
            ),
            "tx_calib_enable": self._pack_checks(
                self.downlink_controls["tx_calib_enable"]
            ),
            "tx_polarity": self._pack_checks(
                self.downlink_controls["tx_polarity"]
            ),
            "phase_calib": self._pack_spins(
                self.downlink_controls["phase_calib"], 10
            ),
            "phase_force": self._pack_checks(
                self.downlink_controls["phase_force"]
            ),
        }
        self._apply_register_group(
            self.DOWNLINK_REGISTERS,
            values,
            (
                "interleaver_bypass",
                "fec_bypass",
                "scrambler_bypass",
                "tx_pi_calib",
                "tx_polarity",
                "phase_calib",
                "tx_calib_enable",
                "phase_force",
            ),
            "Downlink controls applied.",
        )

    def _apply_register_group(self, register_map, values, order, success_message):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self._select_fpga_mapping()
            for key in order:
                self._write_register(register_map[key], values[key])
        except Exception as error:
            self._set_message(f"FPGA write failed: {error}", error=True)
        else:
            self._set_message(success_message)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def clear_uplink_fec(self, link):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self._select_fpga_mapping()
            self._write_register(
                self.UPLINK_REGISTERS["fec_clear"],
                1 << link,
            )
            self._write_register(self.UPLINK_REGISTERS["fec_clear"], 0)
        except Exception as error:
            self._set_message(
                f"Uplink {link} FEC-clear pulse failed: {error}",
                error=True,
            )
        else:
            self._set_message(f"Uplink {link} FEC-corrected latch cleared.")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.refresh_from_fpga()
