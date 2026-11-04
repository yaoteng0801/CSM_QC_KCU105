import os
from functools import partial

from PyQt5 import QtWidgets

from lpgbt_register_map_v1 import LpgbtRegisterMapV1
from TDC_config_low_level_function import fpga_config, lpgbt_config_write, lpgbt_read
from pop_elink_phase_scan import pop_elink_phase_scan


class tab_elink(object):
    """
    lpGBT uplink eLink phase-aligner controls.

    Mezz-to-eLink mapping is taken from:
    ../firmware/sources/TDCV2/tdcv2_decoder_wrapper.sv

    The lpGBT track mode is configured per ePortRx group, not per channel. The
    UI still shows one row per mezz; rows that share an ePortRx group are kept
    synchronized when the mode changes.
    """

    MODE_OPTIONS = [
        "Fixed phase",
        "Initial training",
        "Continuous tracking",
        "Tracking+initial",
    ]

    EPRX_CONTROL_REGS = tuple(
        getattr(LpgbtRegisterMapV1, "EPRX%dCONTROL" % group).address
        for group in range(7)
    )
    EPRX_CHN_CNTR_REGS = tuple(
        getattr(LpgbtRegisterMapV1, "EPRX%d%dCHNCNTR" % (group, channel)).address
        for group in range(7)
        for channel in range(4)
    )
    EPRX_LOCKED_REGS = tuple(
        getattr(LpgbtRegisterMapV1, "EPRX%dLOCKED" % group).address
        for group in range(7)
    )
    EPRX_CURRENT_PHASE_REGS = tuple(
        (
            getattr(LpgbtRegisterMapV1, "EPRX%dCURRENTPHASE10" % group).address,
            getattr(LpgbtRegisterMapV1, "EPRX%dCURRENTPHASE32" % group).address,
        )
        for group in range(7)
    )
    EPRX_TRAIN_REGS = (
        LpgbtRegisterMapV1.EPRXTRAIN10.address,
        LpgbtRegisterMapV1.EPRXTRAIN10.address,
        LpgbtRegisterMapV1.EPRXTRAIN32.address,
        LpgbtRegisterMapV1.EPRXTRAIN32.address,
        LpgbtRegisterMapV1.EPRXTRAIN54.address,
        LpgbtRegisterMapV1.EPRXTRAIN54.address,
        LpgbtRegisterMapV1.EPRXTRAINEC6.address,
    )
    EPRX_TRAIN_OFFSETS = (
        LpgbtRegisterMapV1.EPRXTRAIN10.EPRX0TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAIN10.EPRX1TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAIN32.EPRX2TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAIN32.EPRX3TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAIN54.EPRX4TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAIN54.EPRX5TRAIN.offset,
        LpgbtRegisterMapV1.EPRXTRAINEC6.EPRX6TRAIN.offset,
    )
    TRACK_MODE_MASK = LpgbtRegisterMapV1.EPRX0CONTROL.EPRX0TRACKMODE.bit_mask
    TRACK_MODE_OFFSET = LpgbtRegisterMapV1.EPRX0CONTROL.EPRX0TRACKMODE.offset
    PHASE_SELECT_MASK = LpgbtRegisterMapV1.EPRX00CHNCNTR.EPRX00PHASESELECT.bit_mask
    PHASE_SELECT_OFFSET = LpgbtRegisterMapV1.EPRX00CHNCNTR.EPRX00PHASESELECT.offset
    CHN_LOCKED_MASK = LpgbtRegisterMapV1.EPRX0LOCKED.EPRX0CHNLOCKED.bit_mask
    CHN_LOCKED_OFFSET = LpgbtRegisterMapV1.EPRX0LOCKED.EPRX0CHNLOCKED.offset
    CURRENT_PHASE_FIELDS = (
        (
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE10.EPRX0CURRENTPHASE0.bit_mask,
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE10.EPRX0CURRENTPHASE0.offset,
        ),
        (
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE10.EPRX0CURRENTPHASE1.bit_mask,
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE10.EPRX0CURRENTPHASE1.offset,
        ),
        (
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE32.EPRX0CURRENTPHASE2.bit_mask,
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE32.EPRX0CURRENTPHASE2.offset,
        ),
        (
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE32.EPRX0CURRENTPHASE3.bit_mask,
            LpgbtRegisterMapV1.EPRX0CURRENTPHASE32.EPRX0CURRENTPHASE3.offset,
        ),
    )

    MASTER_DLINE_ELINKS = {
        0: (27, 26),
        1: (21, 20),
        2: (25, 24),
        3: (19, 18),
        4: (23, 22),
        5: (4, 5),
        6: (0, 1),
        7: (6, 7),
        8: (2, 3),
        9: (8, 9),
    }
    SLAVE_DLINE_ELINKS = {
        0: (27, 26),
        1: (17, 16),
        2: (25, 24),
        3: (15, 14),
        4: (19, 18),
        5: (4, 5),
        6: (0, 1),
        7: (6, 7),
        8: (2, 3),
        9: (8, 9),
    }

    def __init__(self, MainWindow, eth):
        self.eth = eth
        self.CSM_per_MiniDAQ = 2
        self.mezz_per_CSM = 20
        self.lpgbt_master_addr = 117
        self.lpgbt_slave_addr = 115
        self._updating_ui = False
        self._rows = []
        self._rows_by_group = {}
        self._mezz_tab = None
        self._csv_defaults = {
            self.lpgbt_master_addr: self._load_csv_defaults("lpgbt_master_reg.csv"),
            self.lpgbt_slave_addr: self._load_csv_defaults("lpgbt_slave_reg.csv"),
        }

        self.setup_UI(MainWindow)

    def set_ethernet_client(self, eth):
        self.eth = eth

    def set_mezz_tab(self, mezz_tab):
        self._mezz_tab = mezz_tab

    def setup_UI(self, MainWindow):
        sectionLayout = QtWidgets.QVBoxLayout(MainWindow)

        self.pushButton_refresh = []
        self.pushButton_apply_fixed = []
        self.pushButton_train = []
        self.pushButton_phase_scan = []
        self.combo_all_mode = []
        self.csm_tabs = QtWidgets.QTabWidget()
        sectionLayout.addWidget(self.csm_tabs)

        for which_csm in range(self.CSM_per_MiniDAQ):
            tab = QtWidgets.QWidget()
            tabLayout = QtWidgets.QVBoxLayout(tab)

            controls = QtWidgets.QWidget()
            controlsLayout = QtWidgets.QHBoxLayout(controls)
            controlsLayout.setContentsMargins(0, 0, 0, 0)

            controlsLayout.addWidget(QtWidgets.QLabel("All eLinks mode"))
            all_mode_combo = QtWidgets.QComboBox()
            all_mode_combo.addItem("Set mode...")
            all_mode_combo.addItems(self.MODE_OPTIONS)
            all_mode_combo.setMinimumWidth(220)
            all_mode_combo.currentIndexChanged[int].connect(
                lambda index, which_csm=which_csm, combo=all_mode_combo:
                    self.handle_all_mode_changed(which_csm, combo, index)
            )
            controlsLayout.addWidget(all_mode_combo)
            self.combo_all_mode.append(all_mode_combo)

            refresh_button = QtWidgets.QPushButton("Refresh current phases")
            refresh_button.clicked.connect(
                lambda checked=False, which_csm=which_csm: self.refresh_csm(which_csm)
            )
            controlsLayout.addWidget(refresh_button)
            self.pushButton_refresh.append(refresh_button)

            apply_button = QtWidgets.QPushButton("Apply fixed phases")
            apply_button.clicked.connect(
                lambda checked=False, which_csm=which_csm: self.apply_csm_fixed_phases(which_csm)
            )
            controlsLayout.addWidget(apply_button)
            self.pushButton_apply_fixed.append(apply_button)

            train_button = QtWidgets.QPushButton("Pulse training")
            train_button.clicked.connect(
                lambda checked=False, which_csm=which_csm: self.pulse_train_csm(which_csm)
            )
            controlsLayout.addWidget(train_button)
            self.pushButton_train.append(train_button)

            phase_scan_button = QtWidgets.QPushButton("Fixed phase scan")
            phase_scan_button.clicked.connect(
                lambda checked=False, which_csm=which_csm: self.open_phase_scan(which_csm)
            )
            controlsLayout.addWidget(phase_scan_button)
            self.pushButton_phase_scan.append(phase_scan_button)

            controlsLayout.addStretch(1)
            tabLayout.addWidget(controls)

            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            buttonWindow = QtWidgets.QWidget()
            gridLayout = QtWidgets.QGridLayout(buttonWindow)
            gridLayout.setHorizontalSpacing(14)
            gridLayout.setVerticalSpacing(4)

            for column, (is_master, title) in enumerate(self._uplink_columns()):
                box = QtWidgets.QGroupBox(title)
                boxLayout = QtWidgets.QGridLayout(box)
                boxLayout.setHorizontalSpacing(6)
                boxLayout.setVerticalSpacing(3)
                self._add_header_row(boxLayout)

                for local_tdc in range(10):
                    row = self._build_row(which_csm, is_master, local_tdc)
                    self._rows.append(row)
                    self._rows_by_group.setdefault(row["group_key"], []).append(row)
                    self._add_mezz_row(boxLayout, local_tdc + 1, row)

                gridLayout.addWidget(box, 0, column, 1, 1)

            scroll.setWidget(buttonWindow)
            tabLayout.addWidget(scroll)
            self.csm_tabs.addTab(tab, "CSM%d" % which_csm)

        for row in self._rows:
            self._set_phase_spin_editable(row, row["mode_combo"].currentIndex() == 0)

    def _uplink_columns(self):
        return [
            (True, "Master"),
            (False, "Slave"),
        ]

    def _add_header_row(self, layout):
        headers = ["Mezz", "eLinks", "Mode", "dline1 Phase", "dline0 Phase", "Status"]
        for column, text in enumerate(headers):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet("font-weight: bold;")
            layout.addWidget(label, 0, column, 1, 1)

    def _add_mezz_row(self, layout, layout_row, row):
        label = QtWidgets.QLabel("Mezz%d" % row["mezz_global"])
        layout.addWidget(label, layout_row, 0, 1, 1)

        elink_label = QtWidgets.QLabel(
            "G%d E%d/E%d" % (row["group"], row["dline1_elink"], row["dline0_elink"])
        )
        elink_label.setToolTip(
            "dline1 -> eLink %d, dline0 -> eLink %d"
            % (row["dline1_elink"], row["dline0_elink"])
        )
        layout.addWidget(elink_label, layout_row, 1, 1, 1)

        combo = QtWidgets.QComboBox()
        combo.addItems(self.MODE_OPTIONS)
        combo.setCurrentIndex(row["default_mode"])
        combo.currentIndexChanged[int].connect(partial(self.handle_mode_changed, row["row_id"]))
        layout.addWidget(combo, layout_row, 2, 1, 1)
        row["mode_combo"] = combo

        phase1_spin = self._create_phase_spin(row["default_phase1"])
        phase1_spin.valueChanged[int].connect(partial(self.handle_phase_changed, row["row_id"], "phase1"))
        layout.addWidget(phase1_spin, layout_row, 3, 1, 1)
        row["phase1_spin"] = phase1_spin

        phase0_spin = self._create_phase_spin(row["default_phase0"])
        phase0_spin.valueChanged[int].connect(partial(self.handle_phase_changed, row["row_id"], "phase0"))
        layout.addWidget(phase0_spin, layout_row, 4, 1, 1)
        row["phase0_spin"] = phase0_spin

        status_label = QtWidgets.QLabel("cfg %d/%d" % (row["default_phase1"], row["default_phase0"]))
        status_label.setMinimumWidth(70)
        layout.addWidget(status_label, layout_row, 5, 1, 1)
        row["status_label"] = status_label

    def _create_phase_spin(self, value):
        spin = QtWidgets.QSpinBox()
        spin.setRange(0, 15)
        spin.setKeyboardTracking(False)
        spin.setValue(value)
        spin.setFixedWidth(64)
        return spin

    def _build_row(self, which_csm, is_master, local_tdc):
        mapping = self.MASTER_DLINE_ELINKS if is_master else self.SLAVE_DLINE_ELINKS
        dline1_elink, dline0_elink = mapping[local_tdc]
        group1, channel1 = self._elink_group_channel(dline1_elink)
        group0, channel0 = self._elink_group_channel(dline0_elink)
        if group1 != group0:
            print(
                "[eLink] Warning: Mezz local TDC%d spans ePortRx groups %d and %d"
                % (local_tdc, group1, group0)
            )

        lpgbt_addr = self.lpgbt_master_addr if is_master else self.lpgbt_slave_addr
        uplink_index = which_csm * 2 + (0 if is_master else 1)
        mezz_in_csm = local_tdc if is_master else local_tdc + 10
        mezz_global = which_csm * self.mezz_per_CSM + mezz_in_csm
        defaults = self._csv_defaults.get(lpgbt_addr, {})
        control_addr = self.EPRX_CONTROL_REGS[group1]
        phase1_addr = self.EPRX_CHN_CNTR_REGS[dline1_elink]
        phase0_addr = self.EPRX_CHN_CNTR_REGS[dline0_elink]
        default_mode = self._track_mode_from_value(int(defaults.get(control_addr, 0)))
        default_phase1 = self._phase_select_from_value(int(defaults.get(phase1_addr, 0)))
        default_phase0 = self._phase_select_from_value(int(defaults.get(phase0_addr, 0)))

        return {
            "row_id": len(self._rows),
            "which_csm": int(which_csm),
            "is_master": bool(is_master),
            "lpgbt_addr": int(lpgbt_addr),
            "uplink_index": int(uplink_index),
            "local_tdc": int(local_tdc),
            "mezz_global": int(mezz_global),
            "dline1_elink": int(dline1_elink),
            "dline0_elink": int(dline0_elink),
            "group": int(group1),
            "dline1_channel": int(channel1),
            "dline0_channel": int(channel0),
            "group_key": (int(which_csm), int(lpgbt_addr), int(group1)),
            "control_addr": int(control_addr),
            "phase1_addr": int(phase1_addr),
            "phase0_addr": int(phase0_addr),
            "default_mode": int(default_mode),
            "default_phase1": int(default_phase1),
            "default_phase0": int(default_phase0),
            "mode_combo": None,
            "phase1_spin": None,
            "phase0_spin": None,
            "status_label": None,
        }

    @staticmethod
    def _elink_group_channel(elink):
        return int(elink) // 4, int(elink) % 4

    @classmethod
    def _track_mode_from_value(cls, value):
        return (int(value) & cls.TRACK_MODE_MASK) >> cls.TRACK_MODE_OFFSET

    @classmethod
    def _phase_select_from_value(cls, value):
        return (int(value) & cls.PHASE_SELECT_MASK) >> cls.PHASE_SELECT_OFFSET

    @classmethod
    def _current_phase_from_value(cls, value, channel):
        mask, offset = cls.CURRENT_PHASE_FIELDS[int(channel) % 4]
        return (int(value) & mask) >> offset

    @staticmethod
    def _load_csv_defaults(filename):
        defaults = {}
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            with open(path, "r", encoding="ascii") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    defaults[int(parts[0], 16)] = int(parts[1], 16)
        except Exception as e:
            print("[eLink] Failed to load %s: %s" % (filename, e))
        return defaults

    def rows_for_csm(self, which_csm):
        which_csm = int(which_csm)
        return [row for row in self._rows if row["which_csm"] == which_csm]

    def open_phase_scan(self, which_csm):
        self.phase_scan_popup = pop_elink_phase_scan(self, which_csm)
        self.phase_scan_popup.exec_()

    def disable_tdc_inputs_for_phase_scan(self):
        if self._mezz_tab is None or not hasattr(self._mezz_tab, "TDC_input_config"):
            raise RuntimeError("Mezz Config tab is not connected")
        self._mezz_tab.TDC_input_config(False)

    def send_global_reset(self):
        fpga_config(self.eth, 5, [1])
        fpga_config(self.eth, 5, [0])
        print("Global reset sent")

    def configure_csm_fixed_phase(self, which_csm, phase):
        which_csm = int(which_csm)
        phase = max(0, min(15, int(phase)))
        include_row = lambda row: row["which_csm"] == which_csm

        was_updating_ui = self._updating_ui
        self._updating_ui = True
        try:
            for row in self._rows:
                if include_row(row):
                    self._set_row_phase_values(row, phase, phase)
        finally:
            self._updating_ui = was_updating_ui

        for group_key, rows in self._rows_by_group.items():
            row = rows[0]
            if include_row(row):
                self._write_track_mode(row, 0)

        for row in self._rows:
            if include_row(row):
                self._write_fixed_phases(row)

    def apply_dline_fixed_phase(self, mezz_global, dline_name, phase):
        mezz_global = int(mezz_global)
        dline_name = str(dline_name)
        phase = max(0, min(15, int(phase)))
        row = next((item for item in self._rows if item["mezz_global"] == mezz_global), None)
        if row is None:
            raise RuntimeError("Mezz%d is not in the eLink table" % mezz_global)
        if dline_name == "dline1":
            phase_key = "phase1"
            spin = row["phase1_spin"]
        elif dline_name == "dline0":
            phase_key = "phase0"
            spin = row["phase0_spin"]
        else:
            raise RuntimeError("Unknown dline %s" % dline_name)

        self._write_track_mode(row, 0)
        if spin is not None:
            spin.blockSignals(True)
            spin.setValue(phase)
            spin.blockSignals(False)
        self._write_fixed_phase(row, phase_key, phase)
        print(
            "[eLink] Applied suggested phase Mezz%d %s -> %d"
            % (mezz_global, dline_name, phase)
        )

    def handle_mode_changed(self, row_id, mode):
        if self._updating_ui:
            return
        row = self._rows[row_id]
        try:
            self._write_track_mode(row, int(mode))
            if int(mode) == 0:
                self._write_fixed_phases(row)
            else:
                self.refresh_group(row["group_key"])
        except Exception as e:
            self._set_row_status(row, "mode err")
            print("[eLink] Failed to set Mezz%d mode: %s" % (row["mezz_global"], e))

    def handle_phase_changed(self, row_id, phase_key, value):
        if self._updating_ui:
            return
        row = self._rows[row_id]
        if row["mode_combo"].currentIndex() != 0:
            return
        try:
            self._write_fixed_phase(row, str(phase_key), int(value))
        except Exception as e:
            self._set_row_status(row, "phase err")
            print("[eLink] Failed to set Mezz%d fixed phase: %s" % (row["mezz_global"], e))

    def handle_all_mode_changed(self, which_csm, combo, index):
        if self._updating_ui or int(index) <= 0:
            return
        try:
            self.set_csm_modes(which_csm, int(index) - 1)
        finally:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def set_all_modes(self, mode):
        include_row = lambda row: True
        self._set_modes(include_row, int(mode))
        if int(mode) == 0:
            self._apply_fixed_phases(include_row)
        else:
            self.refresh_all()

    def set_csm_modes(self, which_csm, mode):
        which_csm = int(which_csm)
        include_row = lambda row: row["which_csm"] == which_csm
        self._set_modes(include_row, int(mode))
        if int(mode) == 0:
            self._apply_fixed_phases(include_row)
        else:
            self.refresh_csm(which_csm)

    def _set_modes(self, include_row, mode):
        for group_key, rows in self._rows_by_group.items():
            row = rows[0]
            if not include_row(row):
                continue
            try:
                self._write_track_mode(row, int(mode))
            except Exception as e:
                for group_row in rows:
                    self._set_row_status(group_row, "mode err")
                print("[eLink] Failed to set group %s mode: %s" % (group_key, e))

    def refresh_all(self):
        self._refresh_rows(lambda row: True)

    def refresh_csm(self, which_csm):
        which_csm = int(which_csm)
        self._refresh_rows(lambda row: row["which_csm"] == which_csm)

    def _refresh_rows(self, include_row):
        read_cache = {}
        self._updating_ui = True
        try:
            for group_key, rows in self._rows_by_group.items():
                row = rows[0]
                if not include_row(row):
                    continue
                try:
                    mode = self._track_mode_from_value(
                        self._read_reg_cached(row, row["control_addr"], read_cache)
                    )
                except Exception as e:
                    print("[eLink] Failed to read group %s mode: %s" % (group_key, e))
                    mode = row["mode_combo"].currentIndex()
                self._set_group_mode(group_key, mode)

            for row in self._rows:
                if not include_row(row):
                    continue
                self._refresh_row(row, read_cache)
        finally:
            self._updating_ui = False

    def refresh_group(self, group_key):
        rows = self._rows_by_group.get(group_key, [])
        if not rows:
            return
        read_cache = {}
        self._updating_ui = True
        try:
            row0 = rows[0]
            try:
                mode = self._track_mode_from_value(
                    self._read_reg_cached(row0, row0["control_addr"], read_cache)
                )
            except Exception:
                mode = row0["mode_combo"].currentIndex()
            self._set_group_mode(group_key, mode)
            for row in rows:
                self._refresh_row(row, read_cache)
        finally:
            self._updating_ui = False

    def apply_all_fixed_phases(self):
        self._apply_fixed_phases(lambda row: True)

    def apply_csm_fixed_phases(self, which_csm):
        which_csm = int(which_csm)
        self._apply_fixed_phases(lambda row: row["which_csm"] == which_csm)

    def _apply_fixed_phases(self, include_row):
        for row in self._rows:
            if not include_row(row):
                continue
            if row["mode_combo"].currentIndex() != 0:
                continue
            try:
                self._write_fixed_phases(row)
            except Exception as e:
                self._set_row_status(row, "phase err")
                print("[eLink] Failed to apply Mezz%d fixed phase: %s" % (row["mezz_global"], e))

    def pulse_train_all(self):
        self._pulse_train(lambda row: True)
        self.refresh_all()

    def pulse_train_csm(self, which_csm):
        which_csm = int(which_csm)
        self._pulse_train(lambda row: row["which_csm"] == which_csm)
        self.refresh_csm(which_csm)

    def _pulse_train(self, include_row):
        train_by_uplink = {}
        row_by_uplink = {}
        for row in self._rows:
            if not include_row(row):
                continue
            key = (row["which_csm"], row["lpgbt_addr"], row["uplink_index"])
            row_by_uplink.setdefault(key, row)
            train_by_uplink.setdefault(
                key,
                {reg_addr: 0 for reg_addr in sorted(set(self.EPRX_TRAIN_REGS))},
            )
            for channel in (row["dline1_channel"], row["dline0_channel"]):
                reg_addr = self.EPRX_TRAIN_REGS[row["group"]]
                shift = self.EPRX_TRAIN_OFFSETS[row["group"]] + channel
                train_by_uplink[key][reg_addr] |= 1 << shift

        for key, train_regs in train_by_uplink.items():
            row = row_by_uplink[key]
            try:
                for reg_addr, value in sorted(train_regs.items()):
                    if value:
                        self._write_reg(row, reg_addr, value)
                for reg_addr, value in sorted(train_regs.items()):
                    if value:
                        self._write_reg(row, reg_addr, 0)
                print("[eLink] Pulsed training for CSM%d lpGBT%d" % (row["which_csm"], row["lpgbt_addr"]))
            except Exception as e:
                print("[eLink] Failed to pulse training for %s: %s" % (key, e))

    def _refresh_row(self, row, read_cache):
        mode = row["mode_combo"].currentIndex()
        self._set_phase_spin_editable(row, mode == 0)
        try:
            if mode == 0:
                phase1 = self._phase_select_from_value(
                    self._read_reg_cached(row, row["phase1_addr"], read_cache)
                )
                phase0 = self._phase_select_from_value(
                    self._read_reg_cached(row, row["phase0_addr"], read_cache)
                )
                self._set_row_phase_values(row, phase1, phase0)
                self._set_row_status(row, "manual %d/%d" % (phase1, phase0))
                self._print_phase_readback(row, mode, phase1, phase0)
            else:
                phase1 = self._read_current_phase(row, row["dline1_channel"], read_cache)
                phase0 = self._read_current_phase(row, row["dline0_channel"], read_cache)
                locked1, locked0 = self._read_lock_bits(row, read_cache)
                self._set_row_phase_values(row, phase1, phase0)
                self._set_row_status(
                    row,
                    "cur %d/%d %s/%s" % (
                        phase1,
                        phase0,
                        "L" if locked1 else "-",
                        "L" if locked0 else "-",
                    ),
                )
                self._print_phase_readback(row, mode, phase1, phase0, locked1, locked0)
        except Exception as e:
            self._set_row_status(row, "read err")
            print("[eLink] Failed to refresh Mezz%d: %s" % (row["mezz_global"], e))

    def _print_phase_readback(self, row, mode, phase1, phase0, locked1=None, locked0=None):
        role = "Master" if row["is_master"] else "Slave"
        mode_name = self.MODE_OPTIONS[int(mode)] if int(mode) in range(len(self.MODE_OPTIONS)) else str(mode)
        if int(mode) == 0:
            detail = (
                "phase-select dline1/eLink%d=%d dline0/eLink%d=%d"
                % (row["dline1_elink"], phase1, row["dline0_elink"], phase0)
            )
        else:
            detail = (
                "current dline1/eLink%d=%d(%s) dline0/eLink%d=%d(%s)"
                % (
                    row["dline1_elink"],
                    phase1,
                    "L" if locked1 else "-",
                    row["dline0_elink"],
                    phase0,
                    "L" if locked0 else "-",
                )
            )
        print(
            "[eLink] Readback CSM%d %s Mezz%d G%d mode %s: %s"
            % (row["which_csm"], role, row["mezz_global"], row["group"], mode_name, detail)
        )

    def _write_track_mode(self, row, mode):
        old_value = self._read_control_or_default(row)
        new_value = (
            old_value & ~self.TRACK_MODE_MASK
        ) | ((int(mode) << self.TRACK_MODE_OFFSET) & self.TRACK_MODE_MASK)
        self._write_reg(row, row["control_addr"], new_value)
        self._set_group_mode(row["group_key"], mode)
        print(
            "[eLink] CSM%d lpGBT%d group%d mode -> %s"
            % (row["which_csm"], row["lpgbt_addr"], row["group"], self.MODE_OPTIONS[mode])
        )

    def _write_fixed_phases(self, row):
        phase1 = row["phase1_spin"].value()
        phase0 = row["phase0_spin"].value()
        self._write_fixed_phase(row, "phase1", phase1)
        self._write_fixed_phase(row, "phase0", phase0)
        self._set_row_status(row, "manual %d/%d" % (phase1, phase0))

    def _write_fixed_phase(self, row, phase_key, phase):
        phase = max(0, min(15, int(phase)))
        if phase_key == "phase1":
            reg_addr = row["phase1_addr"]
            elink = row["dline1_elink"]
        else:
            reg_addr = row["phase0_addr"]
            elink = row["dline0_elink"]

        old_value = self._read_channel_control_or_default(row, reg_addr)
        new_value = (
            old_value & ~self.PHASE_SELECT_MASK
        ) | ((phase << self.PHASE_SELECT_OFFSET) & self.PHASE_SELECT_MASK)
        self._write_reg(row, reg_addr, new_value)
        phase1 = row["phase1_spin"].value()
        phase0 = row["phase0_spin"].value()
        self._set_row_status(row, "manual %d/%d" % (phase1, phase0))
        print(
            "[eLink] Mezz%d eLink%d fixed phase -> %d"
            % (row["mezz_global"], elink, phase)
        )

    def _read_control_or_default(self, row):
        try:
            return self._read_reg(row, row["control_addr"])
        except Exception:
            return int(self._csv_defaults.get(row["lpgbt_addr"], {}).get(row["control_addr"], 0))

    def _read_channel_control_or_default(self, row, reg_addr):
        try:
            return self._read_reg(row, reg_addr)
        except Exception:
            return int(self._csv_defaults.get(row["lpgbt_addr"], {}).get(reg_addr, 0))

    def _read_current_phase(self, row, channel, read_cache):
        reg_addr = self.EPRX_CURRENT_PHASE_REGS[row["group"]][1 if int(channel) >= 2 else 0]
        value = self._read_reg_cached(row, reg_addr, read_cache)
        return self._current_phase_from_value(value, channel)

    def _read_lock_bits(self, row, read_cache):
        value = self._read_reg_cached(row, self.EPRX_LOCKED_REGS[row["group"]], read_cache)
        locked = (value & self.CHN_LOCKED_MASK) >> self.CHN_LOCKED_OFFSET
        return (
            bool(locked & (1 << row["dline1_channel"])),
            bool(locked & (1 << row["dline0_channel"])),
        )

    def _set_group_mode(self, group_key, mode):
        for row in self._rows_by_group.get(group_key, []):
            combo = row["mode_combo"]
            if combo is not None:
                combo.blockSignals(True)
                combo.setCurrentIndex(int(mode))
                combo.blockSignals(False)
            self._set_phase_spin_editable(row, int(mode) == 0)

    def _set_phase_spin_editable(self, row, editable):
        for spin, elink, label in (
            (row["phase1_spin"], row["dline1_elink"], "dline1"),
            (row["phase0_spin"], row["dline0_elink"], "dline0"),
        ):
            if spin is None:
                continue
            spin.setReadOnly(not editable)
            spin.setButtonSymbols(
                QtWidgets.QAbstractSpinBox.UpDownArrows
                if editable
                else QtWidgets.QAbstractSpinBox.NoButtons
            )
            if editable:
                spin.setToolTip("Fixed phase: writes %s/eLink %d phase." % (label, elink))
            else:
                spin.setToolTip("Read-only: current %s/eLink %d phase." % (label, elink))

    def _set_row_phase_values(self, row, phase1, phase0):
        for spin, value in (
            (row["phase1_spin"], phase1),
            (row["phase0_spin"], phase0),
        ):
            if spin is None:
                continue
            spin.blockSignals(True)
            spin.setValue(max(0, min(15, int(value))))
            spin.blockSignals(False)

    def _set_row_status(self, row, text):
        label = row["status_label"]
        if label is not None:
            label.setText(str(text))

    def _read_reg_cached(self, row, reg_addr, read_cache):
        key = (row["which_csm"], row["lpgbt_addr"], int(reg_addr))
        if key not in read_cache:
            read_cache[key] = self._read_reg(row, reg_addr)
        return read_cache[key]

    def _read_reg(self, row, reg_addr):
        data = lpgbt_read(
            self.eth,
            lpgbt_addr=row["lpgbt_addr"],
            reg_addr=int(reg_addr),
            nb_to_be_read=1,
            verbose=False,
            which_csm=row["which_csm"],
        )
        if not isinstance(data, list) or len(data) < 1:
            raise RuntimeError("bad lpGBT readback for reg 0x%03X: %s" % (int(reg_addr), data))
        return int(data[0]) & 0xFF

    def _write_reg(self, row, reg_addr, value):
        lpgbt_config_write(
            self.eth,
            reg_addr=int(reg_addr),
            value_list=[int(value) & 0xFF],
            which_csm=row["which_csm"],
            lpgbt_addr=row["lpgbt_addr"],
            verbose=False,
        )
