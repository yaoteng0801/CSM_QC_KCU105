"""Independent RT selection for a geometry/chamber."""
import os
import json
from PyQt5 import QtCore, QtWidgets
from rt_function import RTFunction


class RTCalibrationWidget(QtWidgets.QWidget):
    def __init__(self, chamber_id, settings, apply_callback, initial_rt=None, parent=None):
        super().__init__(parent)
        self.chamber_id = int(chamber_id)
        self.settings = settings
        self.apply_callback = apply_callback
        self.key = f"geometry/{chamber_id}/rt"
        layout = QtWidgets.QVBoxLayout(self)
        rt_group = QtWidgets.QGroupBox("RT Calibration")
        rt_layout = QtWidgets.QGridLayout(rt_group)
        rt_layout.setContentsMargins(6, 6, 6, 6)
        rt_layout.setColumnStretch(1, 1)
        self.edit_rtfile = QtWidgets.QLineEdit()
        self.edit_rtfile.setPlaceholderText("Chamber .root or coefficients .txt")
        self.edit_rtfile.editingFinished.connect(self._save_settings)
        self.btn_browse_rt = QtWidgets.QPushButton("Browse...")
        self.btn_browse_rt.clicked.connect(self._browse_rt_file)
        rt_layout.addWidget(QtWidgets.QLabel("RT file"), 0, 0)
        rt_layout.addWidget(self.edit_rtfile, 0, 1)
        rt_layout.addWidget(self.btn_browse_rt, 0, 2)

        self.combo_nrt = QtWidgets.QComboBox()
        self.combo_nrt.addItem("Auto", 0)
        self.combo_nrt.addItem("1 (shared)", 1)
        self.combo_nrt.addItem("2 (ML1 / ML2)", 2)
        self.combo_nrt.setToolTip("NRT=2 uses RTParam0 for ML1 and RTParam1 for ML2.")
        self.check_rt_catalogue_ranges = QtWidgets.QCheckBox("Catalogue times")
        self.check_rt_catalogue_ranges.setChecked(True)
        self.check_rt_catalogue_ranges.setToolTip(
            "Read time limits from matching _ML1.txt / _ML2.txt tables beside the ROOT file. "
            "Coefficient TXT files default to 0–200 ns. Uncheck to enter manual ranges."
        )
        self.btn_apply_rt = QtWidgets.QPushButton("Apply RT")
        self.btn_apply_rt.clicked.connect(self._apply_rt_selection)
        rt_layout.addWidget(QtWidgets.QLabel("NRT"), 1, 0)
        rt_layout.addWidget(self.combo_nrt, 1, 1, alignment=QtCore.Qt.AlignLeft)
        rt_layout.addWidget(self.btn_apply_rt, 1, 2)
        rt_layout.addWidget(self.check_rt_catalogue_ranges, 2, 0, 1, 3)

        self.rt_ranges_widget = QtWidgets.QWidget()
        rt_ranges = QtWidgets.QGridLayout(self.rt_ranges_widget)
        rt_ranges.setContentsMargins(0, 0, 0, 0)
        rt_ranges.setHorizontalSpacing(3)
        rt_ranges.addWidget(QtWidgets.QLabel("Tmin (ns)"), 0, 1)
        rt_ranges.addWidget(QtWidgets.QLabel("Tmax (ns)"), 0, 2)
        self.rt_range_spins = []
        for ml in (1, 2):
            rt_ranges.addWidget(QtWidgets.QLabel(f"ML{ml}"), ml, 0)
            pair = []
            for col, value in enumerate((0.0, 200.0), start=1):
                spin = QtWidgets.QDoubleSpinBox()
                spin.setRange(-100000.0, 100000.0)
                spin.setDecimals(4)
                spin.setValue(value)
                spin.valueChanged.connect(self._save_settings)
                rt_ranges.addWidget(spin, ml, col)
                pair.append(spin)
            self.rt_range_spins.append(pair)
        rt_layout.addWidget(self.rt_ranges_widget, 3, 0, 1, 3)
        self.lab_rt_status = QtWidgets.QLabel("Select a calibration and click Apply RT.")
        self.lab_rt_status.setWordWrap(True)
        rt_layout.addWidget(self.lab_rt_status, 4, 0, 1, 3)
        self.combo_nrt.currentIndexChanged.connect(self._rt_options_changed)
        self.check_rt_catalogue_ranges.toggled.connect(self._rt_options_changed)
        self._update_rt_range_controls()
        layout.addWidget(rt_group)

        saved = settings.value(self.key, "", type=str)
        if saved:
            try:
                config = json.loads(saved)
                self.edit_rtfile.setText(config["file"])
                self.combo_nrt.setCurrentIndex(max(0, self.combo_nrt.findData(config["nrt"])))
                self.check_rt_catalogue_ranges.setChecked(config["catalogue"])
                for pair, values in zip(self.rt_range_spins, config["ranges"]):
                    for spin, value in zip(pair, values):
                        spin.setValue(value)
                self._apply_rt_selection()
            except Exception as exc:
                self.lab_rt_status.setText(f"Cannot restore calibration: {exc}")
        else:
            # Seed each chamber from the previous shared choice on first use.
            self.edit_rtfile.setText(settings.value(
                "last/rt_file", getattr(initial_rt, "file_path", ""), type=str))
            self.combo_nrt.setCurrentIndex(max(0, self.combo_nrt.findData(
                settings.value("last/nrt", 0, type=int))))
            self.check_rt_catalogue_ranges.setChecked(
                settings.value("last/rt_catalogue_ranges", True, type=bool))
            for ml, pair in enumerate(self.rt_range_spins):
                for name, spin, default in zip(("min", "max"), pair, (0.0, 200.0)):
                    spin.setValue(settings.value(f"last/rt_ml{ml + 1}_{name}", default, type=float))
            if self.edit_rtfile.text():
                self._apply_rt_selection()
            else:
                self.set_rt_summary(initial_rt)

    def _save_settings(self):
        # Persist only after successful Apply, not while editing.
        pass

    def _browse_rt_file(self):
        start_dir = os.path.dirname(self.edit_rtfile.text())
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select RT file",
            start_dir,
            "RT calibrations (*.root *.txt);;ROOT files (*.root);;Coefficient TXT files (*.txt);;All files (*)",
        )
        if not path:
            return
        self.edit_rtfile.setText(path)

    def _set_current_dat_name(self, filename: str):
        name = os.path.basename((filename or "").strip()) or "-"
        self.lab_current_dat.setText(name)
        self.lab_file.setText(name)

    def _apply_rt_selection(self) -> bool:
        rt_path = self.edit_rtfile.text().strip()
        time_ranges = None if self.check_rt_catalogue_ranges.isChecked() else [
            [spin.value() for spin in pair] for pair in self.rt_range_spins
        ]
        try:
            rt = RTFunction(rt_path, nrt=self.combo_nrt.currentData() or None,
                            time_ranges=time_ranges) if rt_path else None
            self.apply_callback(rt)
            self.set_rt_summary(rt)
            self.settings.setValue(self.key, json.dumps({
                "file": rt_path, "nrt": self.combo_nrt.currentData(),
                "catalogue": self.check_rt_catalogue_ranges.isChecked(),
                "ranges": [[spin.value() for spin in pair] for pair in self.rt_range_spins],
            }))
            ok = True
        except Exception as exc:
            print(f"[RT] Chamber {self.chamber_id}: {exc}")
            ok = False
        if not ok:
            print("[ERROR] Failed to apply RT file selection.")
            self.lab_rt_status.setText("RT selection failed; previous calibration retained. See the log for details.")
        return ok

    def set_rt_summary(self, rt):
        if rt is None:
            self.lab_rt_status.setText("RT disabled for this geometry.")
            return
        ranges = "; ".join(
            f"ML{ml + 1}: {lo:g}–{hi:g} ns" for ml, (lo, hi) in enumerate(rt.time_ranges)
        )
        self.lab_rt_status.setText(f"Loaded {os.path.basename(rt.file_path)} — NRT={rt.nrt}; {ranges}")
        for pair, values in zip(self.rt_range_spins, rt.time_ranges):
            for spin, value in zip(pair, values):
                spin.blockSignals(True)
                spin.setValue(float(value))
                spin.blockSignals(False)

    def _update_rt_range_controls(self):
        manual = not self.check_rt_catalogue_ranges.isChecked()
        self.rt_ranges_widget.setVisible(manual)
        for ml, pair in enumerate(self.rt_range_spins):
            for spin in pair:
                spin.setEnabled(manual and (ml == 0 or self.combo_nrt.currentData() != 1))

    def _rt_options_changed(self):
        self._update_rt_range_controls()

