# pop_mezz.py

from PyQt5 import QtCore, QtGui, QtWidgets

from TDC_config_low_level_function import *

from SCA_share import *
from TDCreg import *
from CSMreg import *
from pop_single_mezz import pop_single_mezz
from pop_mezz_setup import pop_mezz_setup
from pop_jtag_debug import JTAGDebugDialog
from sca_transaction_ids import next_sca_transaction_id


class tab_mezz(object):


    def __init__(self, MainWindow,eth):
        self.eth = eth
        self.transID = 1
        self.CSM_per_MiniDAQ = 2
        self.mezz_per_CSM = 20
        self.gpio_tdc_mapping = [10, 14, 1, 13, 17, 6, 26, 20, 12, 19, 23, 15, 27, 24, 21, 18, 28, 16, 25, 22]
        self.gpio_output_bit = self.gpio_tdc_mapping+[29]
        self.jtag_gen = JTAGTAPController()
        self.CSM_list = []
        for i in range(self.CSM_per_MiniDAQ):
            self.CSM_list.append(CSMreg())
        self._geometry_sync_callback = None
        self._suspend_geometry_sync = False
        
        

        self.setup_UI(MainWindow) 
        

        
    def setup_UI(self, MainWindow):
        sectionLayout = QtWidgets.QVBoxLayout(MainWindow)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)
        self.gridLayout.setHorizontalSpacing(12)

        # Create checkboxes linked to self.TDC_enable.
        self.csm_checkbox_list = []  # self.csm_checkbox_list[CSM][Mezz]
        self.csm_indicator_list = []
        # e.g. self.csm_indicator_list[CSM][Mezz][0] is TDC config status, [CSM][Mezz][1] is ASD status, 
        # [CSM][Mezz][2] is dline lock status
        self.check_all_checkboxes_list = []

        selection_group = QtWidgets.QGroupBox("Mezzanine Selection and Status")
        selection_layout = QtWidgets.QVBoxLayout(selection_group)
        selection_layout.setAlignment(QtCore.Qt.AlignTop)

        legend = QtWidgets.QGridLayout()
        legend.setHorizontalSpacing(18)
        legend.addWidget(
            QtWidgets.QLabel("<b>Indicators:</b> TDC config | ASD config | D-line lock"),
            0, 0,
        )
        legend.addWidget(
            QtWidgets.QLabel("Green = OK, red = error, gray = not checked"),
            0, 1,
        )
        legend.addWidget(
            QtWidgets.QLabel("Cyan mezz label = detected by Mezz Scan"),
            1, 0, 1, 2,
        )
        legend.setColumnStretch(1, 1)
        selection_layout.addLayout(legend)

        indicator_tooltips = (
            "TDC configuration/readback status",
            "ASD configuration/readback status",
            "D-line lock status",
        )

        for which_csm in range(self.CSM_per_MiniDAQ):
            single_csm_checkboxes = []
            single_csm_indicators = []

            first_mezz = which_csm * self.mezz_per_CSM
            last_mezz = first_mezz + self.mezz_per_CSM - 1
            csm_group = QtWidgets.QGroupBox(
                f"CSM{which_csm} — Mezz {first_mezz}–{last_mezz}"
            )
            csm_layout = QtWidgets.QGridLayout(csm_group)
            csm_layout.setHorizontalSpacing(8)
            csm_layout.setVerticalSpacing(6)

            check_all = QtWidgets.QCheckBox(f"Select all CSM{which_csm}")
            check_all.setChecked(
                all(bit == '1' for bit in self.CSM_list[which_csm].TDC_enable[0])
            )
            check_all.stateChanged.connect(
                lambda state, which_csm=which_csm:
                self.check_all_checkboxes(which_csm, state)
            )
            csm_layout.addWidget(check_all, 0, 0, 1, 10)
            self.check_all_checkboxes_list.append(check_all)
            self.check_all_checkbox = check_all

            for mezz in range(self.mezz_per_CSM):
                global_mezz = first_mezz + mezz
                mezz_widget = QtWidgets.QWidget()
                mezz_layout = QtWidgets.QVBoxLayout(mezz_widget)
                mezz_layout.setContentsMargins(2, 2, 2, 2)
                mezz_layout.setSpacing(3)

                checkbox = QtWidgets.QCheckBox(str(global_mezz))
                checkbox.setToolTip(f"Select Mezzanine {global_mezz}")
                checkbox.setChecked(self.CSM_list[which_csm].TDC_enable[0][mezz] == '1')
                checkbox.stateChanged.connect(
                    lambda state, which_csm=which_csm, idx=mezz:
                    self.update_TDC_enable(which_csm, idx, state)
                )
                single_csm_checkboxes.append(checkbox)
                mezz_layout.addWidget(checkbox)

                indicator_layout = QtWidgets.QHBoxLayout()
                indicator_layout.setContentsMargins(0, 0, 0, 0)
                indicator_layout.setSpacing(5)
                color_indicators = []
                for tooltip in indicator_tooltips:
                    color_indicator = QtWidgets.QLabel()
                    color_indicator.setFixedSize(16, 16)
                    color_indicator.setToolTip(tooltip)
                    color_indicator.setStyleSheet("background-color: lightgray; border: 1px solid black;")
                    indicator_layout.addWidget(color_indicator)
                    color_indicators.append(color_indicator)
                indicator_layout.addStretch(1)
                mezz_layout.addLayout(indicator_layout)
                single_csm_indicators.append(color_indicators)

                grid_row = 1 + mezz // 10
                grid_column = mezz % 10
                csm_layout.addWidget(mezz_widget, grid_row, grid_column)
                csm_layout.setColumnStretch(grid_column, 1)

            self.csm_checkbox_list.append(single_csm_checkboxes)
            self.csm_indicator_list.append(single_csm_indicators)
            selection_layout.addWidget(csm_group)

        self.gridLayout.addWidget(selection_group, 0, 0)

        controls_widget = QtWidgets.QWidget()
        controls_widget.setMinimumWidth(270)
        controls_widget.setMaximumWidth(340)
        controls_layout = QtWidgets.QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        def action_button(text, slot):
            button = QtWidgets.QPushButton(text)
            button.setMinimumHeight(30)
            button.clicked.connect(slot)
            return button

        control_group = QtWidgets.QGroupBox("Controls")
        control_layout = QtWidgets.QGridLayout(control_group)
        control_layout.addWidget(QtWidgets.QLabel("JTAG rate divider"), 0, 0)
        self.jtag_rate_spinbox = QtWidgets.QSpinBox()
        self.jtag_rate_spinbox.setValue(10)  # valid for mezz config, not FPGA bit files
        control_layout.addWidget(self.jtag_rate_spinbox, 0, 1)

        self.pushButton_reset_status = action_button(
            "Reset Selection and Status",
            self.reset_status,
        )
        control_layout.addWidget(self.pushButton_reset_status, 1, 0, 1, 2)

        self.pushButton_scanID = action_button("Run Mezz Scan", self.mezz_scan)
        control_layout.addWidget(self.pushButton_scanID, 2, 0, 1, 2)

        self.pushButton_write_TDC_all = action_button(
            "Program Selected TDCs",
            self.write_TDC_all,
        )
        control_layout.addWidget(self.pushButton_write_TDC_all, 3, 0, 1, 2)

        self.pushButton_write_ASD_all = action_button(
            "Program Selected ASDs",
            self.write_ASD_all,
        )
        control_layout.addWidget(self.pushButton_write_ASD_all, 4, 0, 1, 2)

        self.pushButton_TDC_input_disable = action_button(
            "Disable TDC Inputs",
            lambda: self.TDC_input_config(False),
        )
        control_layout.addWidget(self.pushButton_TDC_input_disable, 5, 0, 1, 2)

        self.pushButton_global_reset = action_button(
            "Global Reset",
            self.fpga_global_reset,
        )
        control_layout.addWidget(self.pushButton_global_reset, 6, 0, 1, 2)

        self.pushButton_dline_status = action_button(
            "Update D-line Status",
            self.get_dline_status,
        )
        control_layout.addWidget(self.pushButton_dline_status, 7, 0, 1, 2)

        self.pushButton_TDC_input_enable = action_button(
            "Enable TDC Inputs",
            lambda: self.TDC_input_config(True),
        )
        control_layout.addWidget(self.pushButton_TDC_input_enable, 8, 0, 1, 2)

        self.pushButton_TDC_setup = action_button(
            "Open TDC/ASD Setup…",
            self.TDC_setup_dialog,
        )
        control_layout.addWidget(self.pushButton_TDC_setup, 9, 0, 1, 2)

        self.pushButton_ASD_disable_all = action_button(
            "Disable All ASD Channels",
            lambda: self.ASD_channel_mode_config(False),
        )
        control_layout.addWidget(self.pushButton_ASD_disable_all, 10, 0, 1, 2)

        self.pushButton_ASD_enable_all = action_button(
            "Enable All ASD Channels",
            lambda: self.ASD_channel_mode_config(True),
        )
        control_layout.addWidget(self.pushButton_ASD_enable_all, 11, 0, 1, 2)

        control_layout.addWidget(QtWidgets.QLabel("ASD main threshold"), 12, 0)
        self.spinBox_ASD_main_thr = QtWidgets.QSpinBox()
        self.spinBox_ASD_main_thr.setRange(0, 255)
        self.spinBox_ASD_main_thr.setValue(114)
        self.spinBox_ASD_main_thr.setKeyboardTracking(False)
        control_layout.addWidget(self.spinBox_ASD_main_thr, 12, 1)
        self._set_all_asd_main_thr(self.spinBox_ASD_main_thr.value())
        self.spinBox_ASD_main_thr.valueChanged.connect(self._set_all_asd_main_thr)

        self.pushButton_jtag_debug = action_button("JTAG Debug Test…", self.jtag_debug_dialog)
        control_layout.addWidget(self.pushButton_jtag_debug, 13, 0, 1, 2)

        controls_layout.addWidget(control_group)
        controls_layout.addStretch(1)

        self.gridLayout.addWidget(controls_widget, 0, 1, alignment=QtCore.Qt.AlignTop)
        self.gridLayout.setColumnStretch(0, 1)

        sectionLayout.addWidget(buttonWindow)



    def TDC_input_config(self,enable):
        for j in range(self.CSM_per_MiniDAQ):
            for i in range(self.mezz_per_CSM):
                if enable:
                    self.CSM_list[j].TDC_list[i].channel_enable_r[0]=24*'1'
                    self.CSM_list[j].TDC_list[i].channel_enable_f[0]=24*'1'
                    self.CSM_list[j].TDC_list[i].enable_leading[0] = '0'
                    self.CSM_list[j].TDC_list[i].enable_pair[0] = '1'
                else:
                    self.CSM_list[j].TDC_list[i].channel_enable_r[0]=24*'0'
                    self.CSM_list[j].TDC_list[i].channel_enable_f[0]=24*'0'
                    self.CSM_list[j].TDC_list[i].enable_leading[0] = '1'
                    self.CSM_list[j].TDC_list[i].enable_pair[0] = '0'
                if self.CSM_list[j].TDC_enable[0][i]=='1':
                    self.Mezz_enable(i,which_csm=j)
                    self.config_single(SCA_share.TDC_SETUP0,  self.CSM_list[j].TDC_list[i],which_csm=j)
                    crc_valid = self.read_status0(self.CSM_list[j].TDC_list[i],which_csm=j)
                    if crc_valid:
                        self.csm_indicator_list[j][i][0].setStyleSheet("background-color: green; border: 1px solid black;")
                    else:
                        self.csm_indicator_list[j][i][0].setStyleSheet("background-color: red; border: 1px solid black;")
        if enable:
            print("All TDC input enabled.")
        else:
            print("All TDC input disabled.")
        self._notify_geometry_sync("TDC input configuration changed")


    def ASD_channel_mode_config(self, active):
        self._set_all_asd_channel_modes(active)
        try:
            self.write_ASD_all()
        finally:
            if active:
                print("All ASD channels enabled.")
            else:
                print("All ASD channels disabled.")
            self._notify_geometry_sync("ASD channel mode configuration changed")

    def _set_all_asd_channel_modes(self, active):
        mode = "10" if active else "01"
        for j in range(self.CSM_per_MiniDAQ):
            for i in range(self.mezz_per_CSM):
                tdc_inst = self.CSM_list[j].TDC_list[i]
                for asd in tdc_inst.ASD_list:
                    for ch in range(8):
                        getattr(asd, f"channel_{ch}_mode")[0] = mode

    def _set_all_asd_main_thr(self, value):
        value_bits = format(max(0, min(255, int(value))), '08b')
        for j in range(self.CSM_per_MiniDAQ):
            for i in range(self.mezz_per_CSM):
                tdc_inst = self.CSM_list[j].TDC_list[i]
                for asd in tdc_inst.ASD_list:
                    asd.main_thr[0] = value_bits

    def asd_main_thr_value(self):
        return int(self.spinBox_ASD_main_thr.value())



    def check_all_checkboxes(self, which_csm, state):
        """Set all TDC checkboxes to checked or unchecked."""
        self._suspend_geometry_sync = True
        try:
            for checkbox in self.csm_checkbox_list[which_csm]:
                checkbox.setChecked(state == QtCore.Qt.Checked)
        finally:
            self._suspend_geometry_sync = False
        self._sync_select_all_checkbox(which_csm)
        self._notify_geometry_sync("mezz selection changed")

    def update_TDC_enable(self, which_csm, index, state):
        """Update the corresponding bit in self.TDC_enable based on checkbox state."""
        tdc_enable_list = list(self.CSM_list[which_csm].TDC_enable[0])
        new_value = '1' if state == QtCore.Qt.Checked else '0'
        if tdc_enable_list[index] == new_value:
            return
        tdc_enable_list[index] = new_value
        self.CSM_list[which_csm].TDC_enable[0] = ''.join(tdc_enable_list)
        self._sync_select_all_checkbox(which_csm)
        self._notify_geometry_sync("mezz selection changed")

    def _sync_select_all_checkbox(self, which_csm):
        """Keep the CSM-level selector consistent with its mezz checkboxes."""
        if which_csm >= len(self.check_all_checkboxes_list):
            return
        select_all = self.check_all_checkboxes_list[which_csm]
        all_selected = all(
            bit == '1' for bit in self.CSM_list[which_csm].TDC_enable[0]
        )
        blocker = QtCore.QSignalBlocker(select_all)
        select_all.setChecked(all_selected)
        del blocker

    def selected_mezz_indices(self):
        selected = []
        for which_csm in range(self.CSM_per_MiniDAQ):
            enable_bits = self.CSM_list[which_csm].TDC_enable[0]
            for mezz in range(self.mezz_per_CSM):
                if enable_bits[mezz] == '1':
                    selected.append((which_csm, mezz))
        return selected

    def selected_csm_indices(self):
        return [
            which_csm
            for which_csm in range(self.CSM_per_MiniDAQ)
            if '1' in self.CSM_list[which_csm].TDC_enable[0]
        ]

    def selected_noise_scan_channels(self, selected_mezz=None):
        selected_mezz = selected_mezz if selected_mezz is not None else self.selected_mezz_indices()
        active = {}
        for which_csm, mezz in selected_mezz:
            try:
                which_csm = int(which_csm)
                mezz = int(mezz)
                tdc_inst = self.CSM_list[which_csm].TDC_list[mezz]
            except Exception:
                continue

            tdc_global = which_csm * self.mezz_per_CSM + mezz
            active[tdc_global] = [
                ch for ch in range(24)
                if self._tdc_channel_enabled(tdc_inst, ch)
                and self._asd_channel_enabled(tdc_inst, ch)
            ]
        return active

    def selected_disabled_channels(self, selected_mezz=None):
        selected_mezz = selected_mezz if selected_mezz is not None else self.selected_mezz_indices()
        disabled = []
        for which_csm, mezz in selected_mezz:
            try:
                which_csm = int(which_csm)
                mezz = int(mezz)
                tdc_inst = self.CSM_list[which_csm].TDC_list[mezz]
            except Exception:
                continue

            tdc_global = which_csm * self.mezz_per_CSM + mezz
            for ch in range(24):
                sources = []
                reasons = []

                tdc_reasons = self._tdc_channel_disable_reasons(tdc_inst, ch)
                if tdc_reasons:
                    sources.append("TDC")
                    reasons.extend(f"TDC: {reason}" for reason in tdc_reasons)

                adc_reasons = self._adc_channel_disable_reasons(tdc_inst, ch)
                if adc_reasons:
                    sources.append("ADC")
                    reasons.extend(f"ADC: {reason}" for reason in adc_reasons)

                if not sources:
                    continue

                disabled.append({
                    "tdc_global": int(tdc_global),
                    "tdc_id": int(tdc_global),
                    "csm_id": int(which_csm),
                    "mezz": int(mezz),
                    "channel_id": int(ch),
                    "disabled_in": "+".join(sources),
                    "disabled_reason": "; ".join(reasons),
                    "location": f"CSM{which_csm}/Mezz{mezz}/TDC{tdc_global:02d}/CH{ch:02d}",
                })
        return disabled

    def configure_selected_asd_threshold(self, threshold, selected_mezz=None):
        threshold = max(0, min(255, int(threshold)))
        threshold_bits = format(threshold, '08b')
        return self._configure_selected_asd_field(
            "main_thr",
            threshold,
            threshold_bits,
            selected_mezz=selected_mezz,
        )

    def configure_selected_asd_hyst(self, hyst, selected_mezz=None):
        hyst = max(0, min(15, int(hyst)))
        hyst_bits = format(hyst, '04b')[::-1]
        return self._configure_selected_asd_field(
            "hyst",
            hyst,
            hyst_bits,
            selected_mezz=selected_mezz,
        )

    def _configure_selected_asd_field(self, field_name, value, value_bits, selected_mezz=None):
        selected = list(selected_mezz if selected_mezz is not None else self.selected_mezz_indices())
        if not selected:
            print("[NoiseScan] No selected mezz to configure.")
            return False

        print(f"[NoiseScan] Setting selected ASD {field_name} to {value} ({value_bits})")

        selected_by_csm = {}
        for which_csm, mezz in selected:
            selected_by_csm.setdefault(which_csm, []).append(mezz)

        readback_settings = {"threshold": [], "hyst": []}
        for which_csm, mezz_list in selected_by_csm.items():
            for mezz in mezz_list:
                try:
                    tdc_inst = self.CSM_list[which_csm].TDC_list[mezz]
                except Exception as e:
                    print(f"[NoiseScan] Failed to access CSM{which_csm}, Mezz{mezz}: {e}")
                    ok = False
                else:
                    ok = self._configure_asd_mezz_with_retries(
                        tdc_inst,
                        which_csm,
                        mezz,
                        field_name,
                        value_bits,
                    )

                if ok:
                    self._collect_asd_setting_values(tdc_inst, readback_settings)
                    print(f"[NoiseScan] ASD readback OK for CSM{which_csm}, Mezz{mezz}")
                    self.csm_indicator_list[which_csm][mezz][1].setStyleSheet("background-color: green; border: 1px solid black;")
                else:
                    print(f"[NoiseScan] SCA/ASD configuration failed for CSM{which_csm}, Mezz{mezz}")
                    self.csm_indicator_list[which_csm][mezz][1].setStyleSheet("background-color: red; border: 1px solid black;")
                    return False

        return {
            "threshold": self._unique_asd_setting_value(readback_settings["threshold"]),
            "hyst": self._unique_asd_setting_value(readback_settings["hyst"]),
        }

    def _configure_asd_mezz_with_retries(
        self,
        tdc_inst,
        which_csm,
        mezz,
        field_name,
        value_bits,
        max_attempts=6,
    ):
        # Initial attempt plus five retries, each restarting SCA and ASD setup.
        max_attempts = int(max_attempts)
        for attempt in range(1, max_attempts + 1):
            try:
                print(
                    f"[NoiseScan] Configuring CSM{which_csm}, Mezz{mezz} ASDs "
                    f"(attempt {attempt}/{max_attempts})"
                )
                SCA_clk_div(
                    eth=self.eth,
                    transID=self.get_transID(),
                    sca_enable=0b0010,
                    which_csm=which_csm,
                    data=self.jtag_rate_spinbox.value(),
                )
                self.SCA_GPIO_init(which_csm=which_csm)
                self.Mezz_enable(mezz, which_csm=which_csm)

                for asd in tdc_inst.ASD_list:
                    getattr(asd, field_name)[0] = value_bits

                ok = self._write_asd_once(tdc_inst, which_csm, mezz)
            except Exception as e:
                print(
                    f"[NoiseScan] SCA/ASD config attempt {attempt}/{max_attempts} "
                    f"failed for CSM{which_csm}, Mezz{mezz}: {e}"
                )
                ok = False

            if ok:
                if attempt > 1:
                    print(
                        f"[NoiseScan] ASD readback OK for CSM{which_csm}, Mezz{mezz} "
                        f"after {attempt} attempts"
                    )
                return True

            if attempt < max_attempts:
                print(
                    f"[NoiseScan] SCA/ASD config failed for CSM{which_csm}, Mezz{mezz}; "
                    f"retry {attempt + 1}/{max_attempts}"
                )

        return False

    def _write_asd_once(self, tdc_inst, which_csm, mezz):
        dr_value = self._asd_dr_value(tdc_inst)
        self.config_single(SCA_share.ASD_WRITE, tdc_inst, which_csm=which_csm)
        valid_tdi = self.config_single(SCA_share.ASD_READ, tdc_inst, which_csm=which_csm)
        return bool(valid_tdi) and dr_value == valid_tdi[::-1]

    def _asd_dr_value(self, tdc_inst):
        dr_value = ''
        for asd_setup in (tdc_inst.ASD2.setup, tdc_inst.ASD1.setup, tdc_inst.ASD0.setup):
            for s in asd_setup:
                dr_value += ''.join(s)
        return dr_value

    def _collect_asd_setting_values(self, tdc_inst, out):
        for asd in tdc_inst.ASD_list:
            out["threshold"].append(int(asd.main_thr[0], 2))
            out["hyst"].append(int(asd.hyst[0][::-1], 2))

    @staticmethod
    def _unique_asd_setting_value(values):
        unique_values = sorted(set(values))
        if not unique_values:
            return None
        if len(unique_values) == 1:
            return unique_values[0]
        return "mixed"

    def set_geometry_sync_callback(self, callback):
        self._geometry_sync_callback = callback

    def _notify_geometry_sync(self, reason=""):
        if self._suspend_geometry_sync:
            return
        callback = getattr(self, "_geometry_sync_callback", None)
        if callback is None:
            return
        try:
            callback(reason=reason)
        except TypeError:
            callback()
        except Exception as e:
            print(f"[GeometrySync] Failed to synchronize geometry: {e}")

    def geometry_sync_state(self):
        """
        Return selected mezz slots using the current geometry convention.

        CSM number maps to chamber number. Within one CSM/chamber, even mezz
        numbers are ML0 and odd mezz numbers are ML1; the geometry slot is
        mezz//2. A disabled four-channel group removes one geometry column.
        """
        state = {}
        for which_csm in range(self.CSM_per_MiniDAQ):
            entries = []
            enable_bits = self.CSM_list[which_csm].TDC_enable[0]
            for mezz in range(self.mezz_per_CSM):
                if enable_bits[mezz] != '1':
                    continue

                try:
                    tdc_inst = self.CSM_list[which_csm].TDC_list[mezz]
                except Exception:
                    continue

                active_channels = [
                    ch for ch in range(24)
                    if self._tdc_channel_enabled(tdc_inst, ch)
                    and self._asd_channel_enabled(tdc_inst, ch)
                ]
                active_set = set(active_channels)
                disabled_columns = []
                for col in range(6):
                    column_channels = range(4 * col, 4 * col + 4)
                    if all(ch not in active_set for ch in column_channels):
                        disabled_columns.append(col)

                entries.append({
                    "which_csm": int(which_csm),
                    "mezz": int(mezz),
                    "tdc_id": int(which_csm) * int(self.mezz_per_CSM) + int(mezz),
                    "ml": int(mezz) % 2,
                    "slot": int(mezz) // 2,
                    "ncol": max(0, 6 - len(disabled_columns)),
                    "active_channels": active_channels,
                    "disabled_columns": disabled_columns,
                })
            state[int(which_csm)] = entries
        return state

    @staticmethod
    def _tdc_channel_enabled(tdc_inst, ch: int) -> bool:
        return not tab_mezz._tdc_channel_disable_reasons(tdc_inst, ch)

    @staticmethod
    def _tdc_channel_disable_reasons(tdc_inst, ch: int):
        reasons = []
        try:
            bit_index = 23 - int(ch)
            for attr in ("channel_enable_r", "channel_enable_f"):
                bits = str(getattr(tdc_inst, attr)[0])
                if bit_index < 0 or bit_index >= len(bits):
                    reasons.append(f"{attr}[{bit_index}]=missing")
                elif bits[bit_index] != '1':
                    reasons.append(f"{attr}[{bit_index}]={bits[bit_index]}")
        except Exception as e:
            reasons.append(f"channel_enable_r/f unreadable ({e})")
        return reasons

    @staticmethod
    def _asd_channel_enabled(tdc_inst, ch: int) -> bool:
        return not tab_mezz._adc_channel_disable_reasons(tdc_inst, ch)

    @staticmethod
    def _adc_channel_disable_reasons(tdc_inst, ch: int):
        try:
            asd_index = int(ch) // 8
            asd_channel = int(ch) % 8
            asd_inst = tdc_inst.ASD_list[asd_index]
            mode = getattr(asd_inst, f"channel_{asd_channel}_mode")[0]
            if str(mode) != "10":
                return [f"ASD{asd_index}.channel_{asd_channel}_mode={mode}"]
            return []
        except Exception as e:
            return [f"ASD/ADC channel mode unreadable ({e})"]

    # Helper function to create buttons
    def create_button(self, label, row, column, width, slot_function):
        button = QtWidgets.QPushButton(label)
        button.setFixedSize(150, 30)
        self.gridLayout.addWidget(button, row, column, 1, width)
        button.clicked.connect(slot_function)
        return button

    def _fpga_done_before_mezz_scan(self, which_csm):
        verification_ir = format(
            SCA_share.FPGA_IDCODE,
            'b',
        ).zfill(SCA_share.FPGA_IR_LEN)

        try:
            SCA_clk_div(
                eth=self.eth,
                transID=self.get_transID(),
                sca_enable=0b0001,
                which_csm=which_csm,
                data=0,
            )
            ir_readback, _ = SCA_JTAG_go(
                self.eth,
                transID=self.get_transID(),
                sca_enable=0b0001,
                which_csm=which_csm,
                ir_value=verification_ir,
                dr_value=32*'0',
                isASD=False,
                capture_ir_readback=True,
            )
        except Exception as error:
            print(
                f"ERROR: CSM{which_csm} FPGA DONE check failed before "
                f"mezz scan: {error}"
            )
            return False

        if not isinstance(ir_readback, str) or len(ir_readback) != SCA_share.FPGA_IR_LEN:
            readback_length = len(ir_readback) if isinstance(ir_readback, str) else 0
            print(
                f"ERROR: CSM{which_csm} FPGA returned {readback_length} IR "
                f"bits; expected {SCA_share.FPGA_IR_LEN}. Skipping mezz scan."
            )
            return False

        try:
            captured_ir = int(ir_readback[::-1], 2)
        except ValueError:
            print(
                f"ERROR: CSM{which_csm} FPGA returned invalid IR readback "
                f"{ir_readback!r}. Skipping mezz scan."
            )
            return False

        ir_capture_signature = captured_ir & 0b11
        if ir_capture_signature != 0b01:
            print(
                f"ERROR: CSM{which_csm} invalid FPGA IR capture signature: "
                f"IR[1:0]={ir_capture_signature:02b}, expected 01. "
                "Skipping mezz scan."
            )
            return False

        done = (captured_ir >> 5) & 1
        print(f"CSM{which_csm} FPGA status before mezz scan: DONE={done}")
        return bool(done)

    def mezz_scan(self):
        self._suspend_geometry_sync = True
        try:
            ready_csms = []
            for j in range(self.CSM_per_MiniDAQ):
                if self._fpga_done_before_mezz_scan(j):
                    ready_csms.append(j)
                else:
                    print(f"Skipping CSM{j} mezz scan because FPGA DONE was not confirmed.")
                    for checkbox in self.csm_checkbox_list[j]:
                        checkbox.setStyleSheet("background-color: lightgray;")
                        checkbox.setChecked(False)

            for j in ready_csms:
                SCA_clk_div(eth=self.eth,transID=self.get_transID(),sca_enable=0b0010,which_csm=j,data=self.jtag_rate_spinbox.value())
                self.SCA_GPIO_init(which_csm=j)

            for j in ready_csms:
                for i in range(self.mezz_per_CSM):
                    if self.CSM_list[j].TDC_enable[0][i]=='1':
                        self.Mezz_enable(i,which_csm=j)
                        try:
                            valid_tdi = self.config_single(SCA_share.TDC_IDCODE,self.CSM_list[j].TDC_list[i],which_csm=j)
                            if format(int(valid_tdi[::-1],2),'08x')=='fadec001':
                                self.csm_checkbox_list[j][i].setStyleSheet("background-color: cyan;")
                            else:
                                self.csm_checkbox_list[j][i].setStyleSheet("background-color: lightgray;")
                                self.csm_checkbox_list[j][i].setChecked(False)

                        except Exception as e:
                            print("Mezz scan failed for CSM%d" %(j))
                            print(e)
                            self.csm_checkbox_list[j][i].setStyleSheet("background-color: lightgray;")
                            self.csm_checkbox_list[j][i].setChecked(False)
                        else:
                            pass
        finally:
            self._suspend_geometry_sync = False
        self._notify_geometry_sync("mezz scan completed")

                        

    def _write_tdc_once(self, tdc_inst, which_csm):
        self.config_single(SCA_share.TDC_SETUP0,  tdc_inst, which_csm=which_csm)
        self.config_single(SCA_share.TDC_SETUP1,  tdc_inst, which_csm=which_csm)
        self.config_single(SCA_share.TDC_SETUP2,  tdc_inst, which_csm=which_csm)
        self.config_single(SCA_share.TDC_CONTROL0, tdc_inst, which_csm=which_csm)
        self.config_single(SCA_share.TDC_CONTROL1, tdc_inst, which_csm=which_csm)
        return self.read_status0(tdc_inst, which_csm=which_csm)

    def write_TDC_all(self):
        max_attempts = 3

        for j in self.selected_csm_indices():
            SCA_clk_div(eth=self.eth,transID=self.get_transID(),sca_enable=0b0010,which_csm=j,data=self.jtag_rate_spinbox.value())
            self.SCA_GPIO_init(which_csm=j)
            for i in range(self.mezz_per_CSM):
                if self.CSM_list[j].TDC_enable[0][i]=='1':
                    print("Start JTAG config for CSM%d, TDC%d"%(j,i))
                    crc_valid = False
                    for attempt in range(1, max_attempts + 1):
                        try:
                            print("TDC config attempt %d/%d for CSM%d, TDC%d"%(attempt,max_attempts,j,i))
                            self.Mezz_enable(i,which_csm=j)
                            crc_valid = self._write_tdc_once(self.CSM_list[j].TDC_list[i], which_csm=j)
                        except Exception as e:
                            print("TDC config attempt %d/%d failed for CSM%d, TDC%d"%(attempt,max_attempts,j,i))
                            print(e)
                            crc_valid = False

                        if crc_valid:
                            if attempt > 1:
                                print("TDC readback OK for CSM%d, TDC%d after %d attempts"%(j,i,attempt))
                            break

                        if attempt < max_attempts:
                            print("TDC config/readback failed for CSM%d, TDC%d; retry %d/%d"%(j,i,attempt + 1,max_attempts))

                    if crc_valid:
                        self.csm_indicator_list[j][i][0].setStyleSheet("background-color: green; border: 1px solid black;")
                    else:
                        print("Error! TDC config/readback failed for CSM%d, TDC%d after %d attempts"%(j,i,max_attempts))
                        self.csm_indicator_list[j][i][0].setStyleSheet("background-color: red; border: 1px solid black;")
                        print("Stopping write_TDC_all due to failed readback.")
                        return
                    print("JTAG config for CSM%d, TDC%d completed."%(j,i))


    def write_ASD_all(self):
        max_attempts = 3
        for j in self.selected_csm_indices():
            SCA_clk_div(eth=self.eth,transID=self.get_transID(),sca_enable=0b0010,which_csm=j,data=self.jtag_rate_spinbox.value())
            self.SCA_GPIO_init(which_csm=j)
            for i in range(self.mezz_per_CSM):
                if self.CSM_list[j].TDC_enable[0][i]=='1':
                    print("Start JTAG config for CSM%d, Mezz%d ASDs"%(j,i))
                    asd_valid = False
                    for attempt in range(1, max_attempts + 1):
                        try:
                            print("ASD config attempt %d/%d for CSM%d, Mezz%d"%(attempt,max_attempts,j,i))
                            self.Mezz_enable(i,which_csm=j)
                            asd_valid = self._write_asd_once(self.CSM_list[j].TDC_list[i], j, i)
                        except Exception as e:
                            print("ASD config attempt %d/%d failed for CSM%d, Mezz%d"%(attempt,max_attempts,j,i))
                            print(e)
                            asd_valid = False

                        if asd_valid:
                            if attempt > 1:
                                print("ASD readback OK for CSM%d, Mezz%d after %d attempts"%(j,i,attempt))
                            break

                        if attempt < max_attempts:
                            print("ASD config/readback failed for CSM%d, Mezz%d; retry %d/%d"%(j,i,attempt + 1,max_attempts))

                    if asd_valid:
                        print("ASD readback value same as write value")
                        self.csm_indicator_list[j][i][1].setStyleSheet("background-color: green; border: 1px solid black;")
                    else:
                        print("Error! ASD config/readback failed for CSM%d, Mezz%d after %d attempts"%(j,i,max_attempts))
                        self.csm_indicator_list[j][i][1].setStyleSheet("background-color: red; border: 1px solid black;")
                        print("Stopping write_ASD_all due to failed readback.")
                        return


    def read_status0(self,TDC_inst=0,which_csm=0):
        valid_tdi=self.config_single(SCA_share.TDC_STATUS0,TDC_inst=TDC_inst,which_csm=which_csm)
        try:
            CRC = format(int(valid_tdi[::-1][1:33],2),'08X')
        except Exception as e:
            print(e)
            return False
        else:
            print("Readback CRC = "+CRC)
            CRC_cal = crc_cal(TDC_inst)
            print("Calculated CRC = "+CRC_cal)
            if CRC == CRC_cal:
                print("TDC readback CRC same as calculated.")
                return True
            else:
                print("Error! TDC readback CRC different from calculated!")
                return False



    def get_transID(self):
        self.transID = next_sca_transaction_id(self.transID)
        return self.transID


    def SCA_GPIO_init(self,which_csm=0, verbose=True):
        SCA_config(self.eth,sca_enable=0b0100,which_csm=which_csm,sca_address=0x00,transID=self.get_transID(),channel=SCA_share.CR_CHANNEL,datalen=4,command=SCA_share.CTRL_W_CRB,data=SCA_share.ENGPIO_DATA)
       
        data = 0
        for i in range(32):
            if i in self.gpio_output_bit:
                data += 1<<i

        SCA_config(self.eth,sca_enable=0b0100,which_csm=which_csm,sca_address=0x00,transID=self.get_transID(),channel=SCA_share.GPIO_CHANNEL,datalen=4,command=SCA_share.GPIO_W_DIRECTION,data=data)
        try:
            [SCA_channel,error,data]=SCA_config(self.eth,sca_enable=0b0100,which_csm=which_csm,sca_address=0x00,transID=self.get_transID(),channel=SCA_share.GPIO_CHANNEL,datalen=2,command=SCA_share.GPIO_R_DIRECTION,data=0xFFFFFFFF)
        except Exception as e:
            print("GPIO_R_DIRECTION failed for CSM%d" %(which_csm))
            print(e)
            raise
        else:
            if verbose:
                print("CSM%d GPIO_R_DIRECTION = %08x" %(which_csm, data))
                print("SCA GPIO init succeeds for CSM%d"%which_csm)

    def Mezz_enable(self,i,which_csm=0, verbose=True):
        data = (1<<SCA_share.GPIO_JTAG_RESET)+(1<<self.gpio_tdc_mapping[i])
        SCA_config(self.eth,sca_enable=0b0100,which_csm=which_csm,sca_address=0x00,transID=self.get_transID(),channel=SCA_share.GPIO_CHANNEL,datalen=4,command=SCA_share.GPIO_W_DATAOUT,data=data)
        try:
            [SCA_channel,error,data]=SCA_config(self.eth,sca_enable=0b0100,which_csm=which_csm,sca_address=0x00,transID=self.get_transID(),channel=SCA_share.GPIO_CHANNEL,datalen=2,command=SCA_share.GPIO_R_DATAOUT,data=data)
        except Exception as e:
            print("GPIO_R_DATAOUT failed for CSM%d" %(which_csm))
            print(e)
            raise
        else:
            if verbose:
                print("CSM%d GPIO_R_DATAOUT = %08x" %(which_csm,data))



    def config_single(self, ir, TDC_inst,which_csm, raise_errors=False, verbose=True):
         # Mapping of IR values to corresponding TDC register data
        ir_to_dr_mapping = {
            SCA_share.TDC_SETUP0: TDC_inst.setup_0,
            SCA_share.TDC_SETUP1: TDC_inst.setup_1,
            SCA_share.TDC_SETUP2: TDC_inst.setup_2,
            SCA_share.TDC_CONTROL0: TDC_inst.control_0,
            SCA_share.TDC_CONTROL1: TDC_inst.control_1,
            SCA_share.TDC_IDCODE: TDC_inst.IDCODE,
            SCA_share.TDC_STATUS0: TDC_inst.status_0,
            SCA_share.TDC_STATUS1: TDC_inst.status_1, 
            SCA_share.ASD_WRITE: (TDC_inst.ASD2.setup,TDC_inst.ASD1.setup,TDC_inst.ASD0.setup),
            SCA_share.ASD_READ: (TDC_inst.ASD2.setup,TDC_inst.ASD1.setup,TDC_inst.ASD0.setup)
        }

        ir_value = format(ir, 'b').zfill(SCA_share.TDC_IR_LEN)
        dr_value = ''
        isASD = ir in (SCA_share.ASD_WRITE, SCA_share.ASD_READ)

        if ir in ir_to_dr_mapping:
            if isASD:
                # Handle ASD_WRITE and ASD_READ differently to add extra bit
                for ASD in ir_to_dr_mapping[ir]:
                    for s in ASD:
                        dr_value += ''.join(s)
                # print(self.dr_value)
                # print(len(self.dr_value))
                # print("ASD2 in DR seq: "+format(int(self.dr_value[0:55],2),'x'))
                # print("ASD1 in DR seq: "+format(int(self.dr_value[55:55*2],2),'x'))
                # print("ASD0 in DR seq: "+format(int(self.dr_value[55*2:55*3],2),'x'))

            else:
                for s in ir_to_dr_mapping[ir]:
                    dr_value += ''.join(s)
        else:
            print(f"Unsupported IR value: {ir}")
            return

        # print(self.dr_value)
        # print("TDO prepared to write: %d bits" %len(self.dr_value))
        # print("TDO DR seq: %x" %int(self.dr_value, 2))
        if verbose:
            print(f"Start to program IR={ir_value}, DR_length={len(dr_value)}")
        try:
            tdi=SCA_JTAG_go(self.eth,transID=self.get_transID(),sca_enable=0b0010,which_csm=which_csm,ir_value=ir_value,dr_value=dr_value,isASD=isASD,verbose=verbose)
        except Exception as e:
            if raise_errors:
                raise
            print("mezz config failed for CSM%d" %(which_csm))
            print(e)
        else:
            return tdi


    # def open_Mezz_config(self):
    #     # Create and show the TDC configuration popup window
    #     self.mezz_popup = pop_mezz(self.TDC_inst)
    #     self.mezz_popup.exec_()  # exec_() for modal behavior, show() for non-modal

    def jtag_debug_dialog(self):
        selected = self.selected_mezz_indices()
        if not selected:
            QtWidgets.QMessageBox.information(
                self.pushButton_jtag_debug, "JTAG Debug Test", "Select at least one mezzanine first."
            )
            return
        dialog = JTAGDebugDialog(self, selected, self.pushButton_jtag_debug.window())
        dialog.exec_()

    def TDC_setup_dialog(self):
        # Create and show the TDC configuration popup window
        self.TDC_setup_popup = pop_mezz_setup(self.CSM_list)
        self.TDC_setup_popup.exec_()  # exec_() for modal behavior, show() for non-modal
        self._notify_geometry_sync("mezz configuration changed")

    def get_dline_status(self):
        bin_str=fpga_readback(self.eth, 3)

        locked_dline0 = bin_str[-86:-76]+bin_str[-66:-56]+bin_str[-46:-36]+bin_str[-26:-16]
        locked_dline1 = bin_str[-96:-86]+bin_str[-76:-66]+bin_str[-56:-46]+bin_str[-36:-26]
        locked_dline = ''.join(str(int(a) & int(b)) for a, b in zip(locked_dline0, locked_dline1))
        locked_dline_reversed = locked_dline[::-1]
        locked_dline_diff = ''.join(str(int(a) ^ int(b)) for a, b in zip(locked_dline0, locked_dline1))
        print("locked_dline0="+locked_dline0)
        print("locked_dline1="+locked_dline1)
        print("locked_dline ="+locked_dline)
        for j in range(self.CSM_per_MiniDAQ):
            for i in range(self.mezz_per_CSM):
                if self.csm_checkbox_list[j][i].isChecked():
                    if locked_dline_reversed[i+20*j]=='1':
                        self.csm_indicator_list[j][i][2].setStyleSheet("background-color: green; border: 1px solid black;")
                    else:
                        self.csm_indicator_list[j][i][2].setStyleSheet("background-color: red; border: 1px solid black;")
    
    def reset_status(self):
        self._suspend_geometry_sync = True
        try:
            for j in range(self.CSM_per_MiniDAQ):
                self.CSM_list[j].TDC_enable[0] = self.mezz_per_CSM * '1'
                for i in range(self.mezz_per_CSM):
                    self.csm_checkbox_list[j][i].setChecked(True)
                    self.csm_checkbox_list[j][i].setStyleSheet("")
                    for k in range(3):
                        self.csm_indicator_list[j][i][k].setStyleSheet("background-color: lightgray; border: 1px solid black;")
                self._sync_select_all_checkbox(j)
        finally:
            self._suspend_geometry_sync = False
        self._notify_geometry_sync("mezz status and selection reset")

    def fpga_global_reset(self):
        fpga_config(self.eth, 5, [1])
        fpga_config(self.eth, 5, [0])
        print("Glocal reset sent")
