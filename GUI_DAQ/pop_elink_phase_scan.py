from PyQt5 import QtCore, QtGui, QtWidgets

from TDC_config_low_level_function import fpga_config, fpga_readback, fpga_readback_BER


class pop_elink_phase_scan(QtWidgets.QDialog):
    def __init__(self, tab_elink, which_csm, parent=None):
        super().__init__(parent)
        self.tab_elink = tab_elink
        self.which_csm = int(which_csm)
        self.rows = self.tab_elink.rows_for_csm(self.which_csm)
        self.phase_values = list(range(16))
        self.wait_ms = 5000
        self.current_phase_index = 0
        self.running = False
        self.results = {}
        self.key_to_table_row = {}
        self.key_to_source = {}
        self.suggested_phases = {}
        self.apply_buttons = {}

        self.setWindowTitle("CSM%d fixed phase scan" % self.which_csm)
        self.resize(1200, 720)
        self.setup_UI()

    def setup_UI(self):
        layout = QtWidgets.QVBoxLayout(self)

        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.start_button = QtWidgets.QPushButton("Start phase scan")
        self.start_button.clicked.connect(self.start_scan)
        controls_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scan)
        controls_layout.addWidget(self.stop_button)

        self.apply_all_button = QtWidgets.QPushButton("Apply all suggested")
        self.apply_all_button.setEnabled(False)
        self.apply_all_button.clicked.connect(self.apply_all_suggested_phases)
        controls_layout.addWidget(self.apply_all_button)

        controls_layout.addWidget(QtWidgets.QLabel("Wait after reset"))
        self.wait_spin = QtWidgets.QSpinBox()
        self.wait_spin.setRange(1, 60)
        self.wait_spin.setValue(5)
        self.wait_spin.setSuffix(" s")
        self.wait_spin.setFixedWidth(90)
        controls_layout.addWidget(self.wait_spin)

        controls_layout.addStretch(1)
        self.status_label = QtWidgets.QLabel("Ready")
        controls_layout.addWidget(self.status_label)
        layout.addWidget(controls)

        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self._setup_result_table()

    def _setup_result_table(self):
        dline_rows = []
        for row in sorted(self.rows, key=lambda item: item["mezz_global"]):
            role = "Master" if row["is_master"] else "Slave"
            dline_rows.append((row, role, "dline1", row["dline1_elink"]))
            dline_rows.append((row, role, "dline0", row["dline0_elink"]))

        headers = ["CSM", "Role", "Mezz", "DLine", "eLink"]
        headers.extend("P%d" % phase for phase in self.phase_values)
        headers.extend(["Suggested", "Apply"])
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(dline_rows))

        self.key_to_table_row = {}
        self.key_to_source = {}
        self.apply_buttons = {}
        for table_row, (row, role, dline_name, elink) in enumerate(dline_rows):
            key = self._result_key(row, dline_name)
            self.key_to_table_row[key] = table_row
            self.key_to_source[key] = (row, dline_name)
            values = [
                "CSM%d" % row["which_csm"],
                role,
                str(row["mezz_global"]),
                dline_name,
                str(elink),
            ]
            for column, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(table_row, column, item)
            for phase in self.phase_values:
                item = QtWidgets.QTableWidgetItem("")
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(table_row, 5 + phase, item)

            suggest_item = QtWidgets.QTableWidgetItem("")
            suggest_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(table_row, self._suggest_column(), suggest_item)

            apply_button = QtWidgets.QPushButton("Apply")
            apply_button.setEnabled(False)
            apply_button.clicked.connect(
                lambda checked=False, key=key: self.apply_suggested_phase(key)
            )
            self.table.setCellWidget(table_row, self._apply_column(), apply_button)
            self.apply_buttons[key] = apply_button

        self.table.resizeColumnsToContents()

    def start_scan(self):
        if self.running:
            return
        if not self.rows:
            QtWidgets.QMessageBox.warning(self, "Phase scan", "No eLinks found for CSM%d." % self.which_csm)
            return

        self.wait_ms = int(self.wait_spin.value()) * 1000
        self.current_phase_index = 0
        self.results = {}
        self.suggested_phases = {}
        self._clear_phase_cells()
        self.running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.apply_all_button.setEnabled(False)
        self.wait_spin.setEnabled(False)

        try:
            self.status_label.setText("Disabling TDC inputs...")
            QtWidgets.QApplication.processEvents()
            self.tab_elink.disable_tdc_inputs_for_phase_scan()
        except Exception as e:
            self.running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.wait_spin.setEnabled(True)
            self.status_label.setText("TDC input disable failed")
            self._update_suggestions()
            QtWidgets.QMessageBox.warning(self, "Phase scan", "TDC input disable failed: %s" % e)
            return

        self._start_next_phase()

    def stop_scan(self):
        if not self.running:
            return
        self.running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.wait_spin.setEnabled(True)
        self.status_label.setText("Stopped")
        self._update_suggestions()
        print("[eLink phase scan] CSM%d stopped" % self.which_csm)

    def closeEvent(self, event):
        if self.running:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Phase scan",
                "Stop the running phase scan?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self.stop_scan()
        event.accept()

    def _clear_phase_cells(self):
        for table_row in range(self.table.rowCount()):
            for phase in self.phase_values:
                item = self.table.item(table_row, 5 + phase)
                if item is not None:
                    item.setText("")
                    item.setToolTip("")
                    item.setBackground(QtGui.QBrush())
            suggest_item = self.table.item(table_row, self._suggest_column())
            if suggest_item is not None:
                suggest_item.setText("")
                suggest_item.setToolTip("")
                suggest_item.setBackground(QtGui.QBrush())
        for button in self.apply_buttons.values():
            button.setEnabled(False)
        self.apply_all_button.setEnabled(False)

    def _start_next_phase(self):
        if not self.running:
            return
        if self.current_phase_index >= len(self.phase_values):
            self._finish_scan()
            return

        phase = self.phase_values[self.current_phase_index]
        try:
            self.status_label.setText("Setting fixed phase %d..." % phase)
            QtWidgets.QApplication.processEvents()
            self.tab_elink.configure_csm_fixed_phase(self.which_csm, phase)
            self.tab_elink.send_global_reset()
        except Exception as e:
            self.running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.wait_spin.setEnabled(True)
            self.status_label.setText("Phase %d failed" % phase)
            QtWidgets.QMessageBox.warning(self, "Phase scan", "Phase %d setup failed: %s" % (phase, e))
            return

        self.status_label.setText("Phase %d: waiting %d s..." % (phase, self.wait_ms // 1000))
        QtCore.QTimer.singleShot(self.wait_ms, self._read_current_phase_ber)

    def _read_current_phase_ber(self):
        if not self.running:
            return

        phase = self.phase_values[self.current_phase_index]
        try:
            self.status_label.setText("Phase %d: reading BER..." % phase)
            QtWidgets.QApplication.processEvents()
            phase_results = self._read_ber_results()
            self.results[phase] = phase_results
            self._update_phase_column(phase, phase_results)
            self._update_suggestions()
            self._print_phase_results(phase, phase_results)
        except Exception as e:
            self.running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.wait_spin.setEnabled(True)
            self.status_label.setText("BER read failed")
            QtWidgets.QMessageBox.warning(self, "Phase scan", "Phase %d BER read failed: %s" % (phase, e))
            return

        self.current_phase_index += 1
        self._start_next_phase()

    def _read_ber_results(self):
        phase_results = {}
        dline_locks = self._read_dline_locks()

        for row in sorted(self.rows, key=lambda item: item["mezz_global"]):
            tdc = row["mezz_global"]
            lock1 = dline_locks.get((tdc, "dline1"), False)
            lock0 = dline_locks.get((tdc, "dline0"), False)
            if lock1 or lock0:
                bin_str = fpga_readback_BER(self.tab_elink.eth, tdc)
            else:
                bin_str = ""

            if lock1 or lock0:
                if not isinstance(bin_str, str) or len(bin_str) != 160:
                    print("[eLink phase scan] Bad BER readback for TDC%d: %s" % (tdc, bin_str))
                    rec1, rec0, err1, err0 = 0, 0, 0, 0
                else:
                    rec1, rec0, err1, err0 = self._decode_ber_info(bin_str)
            else:
                rec1, rec0, err1, err0 = 0, 0, 0, 0

            phase_results[self._result_key(row, "dline1")] = self._make_ber_record(rec1, err1, lock1)
            phase_results[self._result_key(row, "dline0")] = self._make_ber_record(rec0, err0, lock0)

        return phase_results

    def _read_dline_locks(self):
        bin_str = fpga_readback(self.tab_elink.eth, 3)
        locks = {}
        if not isinstance(bin_str, str) or len(bin_str) < 96:
            print("[eLink phase scan] Bad dline lock readback: %s" % bin_str)
            return locks

        locked_dline0 = bin_str[-86:-76] + bin_str[-66:-56] + bin_str[-46:-36] + bin_str[-26:-16]
        locked_dline1 = bin_str[-96:-86] + bin_str[-76:-66] + bin_str[-56:-46] + bin_str[-36:-26]
        locked_dline0 = locked_dline0[::-1]
        locked_dline1 = locked_dline1[::-1]

        for tdc in range(min(40, len(locked_dline0), len(locked_dline1))):
            locks[(tdc, "dline1")] = locked_dline1[tdc] == "1"
            locks[(tdc, "dline0")] = locked_dline0[tdc] == "1"
        return locks

    @staticmethod
    def _decode_ber_info(bin_str):
        rec_dline1 = int(bin_str[0:44], 2)
        rec_dline0 = int(bin_str[44:88], 2)
        err_dline1 = int(bin_str[88:124], 2)
        err_dline0 = int(bin_str[124:160], 2)
        return rec_dline1, rec_dline0, err_dline1, err_dline0

    @staticmethod
    def _make_ber_record(rec40, err, locked):
        ber = float(err) / float(rec40) / 40.0 if rec40 > 0 else 0.0
        return {
            "locked": bool(locked),
            "rec40": int(rec40),
            "err": int(err),
            "ber": ber,
        }

    def _update_phase_column(self, phase, phase_results):
        column = 5 + int(phase)
        for key, record in phase_results.items():
            table_row = self.key_to_table_row.get(key)
            if table_row is None:
                continue
            item = self.table.item(table_row, column)
            if item is None:
                item = QtWidgets.QTableWidgetItem()
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(table_row, column, item)
            if not record["locked"]:
                item.setText("N")
                item.setToolTip("dline unlocked\nBER unavailable")
                item.setBackground(QtGui.QColor(255, 205, 210))
            else:
                item.setText(self._format_count(record["err"]))
                item.setToolTip(
                    "locked=yes\nrec40=%s\nerr=%s\nBER=%s"
                    % (
                        self._format_count(record["rec40"]),
                        self._format_count(record["err"]),
                        self._format_metric(record["ber"]),
                    )
                )
                if record["err"] == 0:
                    item.setBackground(QtGui.QColor(200, 230, 201))
                else:
                    item.setBackground(QtGui.QColor(255, 205, 210))
        self.table.resizeColumnsToContents()

    def _update_suggestions(self):
        self.suggested_phases = {}
        self._refresh_phase_cell_backgrounds()
        for key, table_row in self.key_to_table_row.items():
            phase, reason = self._suggest_phase_for_key(key)
            suggest_item = self.table.item(table_row, self._suggest_column())
            button = self.apply_buttons.get(key)
            if phase is None:
                if suggest_item is not None:
                    suggest_item.setText("N")
                    suggest_item.setToolTip("No locked phase")
                    suggest_item.setBackground(QtGui.QColor(255, 205, 210))
                if button is not None:
                    button.setEnabled(False)
                continue

            self.suggested_phases[key] = phase
            record = self.results.get(phase, {}).get(key)
            if suggest_item is not None:
                suggest_item.setText(str(phase))
                suggest_item.setToolTip(reason)
                if record is not None and record["locked"] and record["err"] == 0:
                    suggest_item.setBackground(QtGui.QColor(200, 230, 201))
                else:
                    suggest_item.setBackground(QtGui.QColor(255, 205, 210))
            phase_item = self.table.item(table_row, 5 + int(phase))
            if phase_item is not None:
                phase_item.setBackground(QtGui.QColor(187, 222, 251))
            if button is not None:
                button.setEnabled(not self.running)
        self.apply_all_button.setEnabled((not self.running) and bool(self.suggested_phases))
        self.table.resizeColumnsToContents()

    def _refresh_phase_cell_backgrounds(self):
        for key, table_row in self.key_to_table_row.items():
            for phase in self.phase_values:
                item = self.table.item(table_row, 5 + phase)
                if item is None or phase not in self.results or key not in self.results[phase]:
                    continue
                record = self.results[phase][key]
                if record["locked"] and record["err"] == 0:
                    item.setBackground(QtGui.QColor(200, 230, 201))
                else:
                    item.setBackground(QtGui.QColor(255, 205, 210))

    def _suggest_phase_for_key(self, key):
        available = [
            phase
            for phase in self.phase_values
            if phase in self.results and key in self.results[phase]
        ]
        if not available:
            return None, ""

        good = [
            phase
            for phase in available
            if self.results[phase][key]["locked"] and self.results[phase][key]["err"] == 0
        ]
        all_scanned = all(phase in self.results for phase in self.phase_values)
        if good:
            start, length = self._longest_good_run(good, circular=all_scanned)
            phase = (start + (length // 2)) % len(self.phase_values)
            return phase, "center of %d-phase zero-error lock window" % length

        locked = [
            (phase, self.results[phase][key]["err"])
            for phase in available
            if self.results[phase][key]["locked"]
        ]
        if locked:
            phase, err = min(locked, key=lambda item: (item[1], item[0]))
            return phase, "fallback: minimum locked error count %s" % self._format_count(err)

        return None, ""

    def _longest_good_run(self, good_phases, circular):
        good = set(int(phase) for phase in good_phases)
        if circular and len(good) == len(self.phase_values):
            return 0, len(self.phase_values)

        best_start = None
        best_length = 0
        phase_count = len(self.phase_values)
        starts = []
        for phase in self.phase_values:
            previous = (phase - 1) % phase_count
            if phase in good and (previous not in good or not circular):
                starts.append(phase)

        for start in starts:
            length = 0
            phase = start
            while phase in good:
                length += 1
                phase = (phase + 1) % phase_count
                if not circular and phase == 0:
                    break
                if length >= phase_count:
                    break
            if length > best_length:
                best_start = start
                best_length = length

        if best_start is None:
            best_start = min(good)
            best_length = 1
        return best_start, best_length

    def apply_suggested_phase(self, key):
        if self.running:
            return
        phase = self.suggested_phases.get(key)
        if phase is None:
            return
        row, dline_name = self.key_to_source[key]
        try:
            self.tab_elink.apply_dline_fixed_phase(row["mezz_global"], dline_name, phase)
            self.status_label.setText(
                "Applied Mezz%d %s phase %d" % (row["mezz_global"], dline_name, phase)
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Apply suggested phase",
                "Failed to apply Mezz%d %s phase %d: %s"
                % (row["mezz_global"], dline_name, phase, e),
            )

    def apply_all_suggested_phases(self):
        if self.running or not self.suggested_phases:
            return

        errors = []
        applied = 0
        self.apply_all_button.setEnabled(False)
        for button in self.apply_buttons.values():
            button.setEnabled(False)

        for key in sorted(self.suggested_phases.keys()):
            phase = self.suggested_phases[key]
            row, dline_name = self.key_to_source[key]
            try:
                self.tab_elink.apply_dline_fixed_phase(row["mezz_global"], dline_name, phase)
                applied += 1
                QtWidgets.QApplication.processEvents()
            except Exception as e:
                errors.append(
                    "Mezz%d %s phase %d: %s"
                    % (row["mezz_global"], dline_name, phase, e)
                )

        self._update_suggestions()
        self.status_label.setText("Applied %d suggested phases" % applied)
        print("[eLink phase scan] Applied %d suggested phases" % applied)

        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "Apply all suggested phases",
                "Some suggested phases failed:\n%s" % "\n".join(errors[:10]),
            )

    def _print_phase_results(self, phase, phase_results):
        print("[eLink phase scan] CSM%d phase %d BER results" % (self.which_csm, phase))
        for key in sorted(phase_results.keys()):
            mezz, dline_name = key
            record = phase_results[key]
            if not record["locked"]:
                print("  Mezz%d %s: N" % (mezz, dline_name))
            else:
                print(
                    "  Mezz%d %s: rec40=%s err=%s BER=%s"
                    % (
                        mezz,
                        dline_name,
                        self._format_count(record["rec40"]),
                        self._format_count(record["err"]),
                        self._format_metric(record["ber"]),
                    )
                )

    def _finish_scan(self):
        self.running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.wait_spin.setEnabled(True)
        self.status_label.setText("Done")
        self._update_suggestions()
        self._print_final_results()

    def _print_final_results(self):
        print("[eLink phase scan] Final CSM%d fixed-phase BER results" % self.which_csm)
        for table_row in range(self.table.rowCount()):
            csm = self.table.item(table_row, 0).text()
            role = self.table.item(table_row, 1).text()
            mezz = self.table.item(table_row, 2).text()
            dline = self.table.item(table_row, 3).text()
            elink = self.table.item(table_row, 4).text()
            parts = []
            for phase in self.phase_values:
                item = self.table.item(table_row, 5 + phase)
                text = item.text() if item is not None else ""
                parts.append("P%d=%s" % (phase, text if text else ""))
            suggest_item = self.table.item(table_row, self._suggest_column())
            suggest = suggest_item.text() if suggest_item is not None else ""
            print(
                "  %s %s Mezz%s %s eLink%s suggested=%s: %s"
                % (csm, role, mezz, dline, elink, suggest if suggest else "N", ", ".join(parts))
            )

    @staticmethod
    def _result_key(row, dline_name):
        return int(row["mezz_global"]), str(dline_name)

    def _suggest_column(self):
        return 5 + len(self.phase_values)

    def _apply_column(self):
        return self._suggest_column() + 1

    @staticmethod
    def _format_count(value):
        value = int(value)
        if abs(value) > 99999:
            return "%.3e" % value
        return str(value)

    @staticmethod
    def _format_metric(value):
        value = float(value)
        if value == 0.0:
            return "0"
        text = "%.6f" % value
        text = text.rstrip("0").rstrip(".")
        if text == "0" or len(text.replace(".", "").replace("-", "")) > 5:
            return "%.3e" % value
        return text
