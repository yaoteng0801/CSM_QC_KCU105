# pop_noise_scan.py
from PyQt5 import QtGui, QtWidgets
import csv
import os
import re

import numpy as np
import pyqtgraph as pg
from sparse_log_axis import SparseLogAxisItem


CH_HIT_TIME_WINDOW_S = 60.0 * 25.0e-9

NOISE_SCAN_TRIGGERED = "triggered"
NOISE_SCAN_TRIGGERLESS_RAW = "triggerless_raw"
NOISE_SCAN_TRIGGERLESS_COUNT = "triggerless_count"
NOISE_SCAN_DEFAULT_EVENTS = 20000
NOISE_SCAN_DEFAULT_SECONDS = 15


class NoiseScanDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent=None,
        *,
        start_threshold=40,
        end_threshold=100,
        step=5,
        event_count=20000,
        scan_type="threshold",
        acquisition_mode=NOISE_SCAN_TRIGGERED,
        hyst_values=None,
        fixed_threshold=40,
        fixed_hyst=7,
    ):
        super().__init__(parent)
        self.setWindowTitle("Noise Scan")
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.combo_scan_type = QtWidgets.QComboBox()
        self.combo_scan_type.addItem("main_thr", "threshold")
        self.combo_scan_type.addItem("hyst", "hyst")
        scan_type_index = self.combo_scan_type.findData(str(scan_type or "threshold"))
        if scan_type_index >= 0:
            self.combo_scan_type.setCurrentIndex(scan_type_index)
        self.combo_scan_type.currentIndexChanged.connect(self._update_scan_controls)
        form.addRow("Scan:", self.combo_scan_type)

        self.combo_acquisition_mode = QtWidgets.QComboBox()
        self.combo_acquisition_mode.addItem(
            "Triggered",
            NOISE_SCAN_TRIGGERED,
        )
        self.combo_acquisition_mode.addItem(
            "Triggerless raw hits",
            NOISE_SCAN_TRIGGERLESS_RAW,
        )
        self.combo_acquisition_mode.addItem(
            "Triggerless hit counters (1 Hz)",
            NOISE_SCAN_TRIGGERLESS_COUNT,
        )
        mode_index = self.combo_acquisition_mode.findData(
            str(acquisition_mode or NOISE_SCAN_TRIGGERED)
        )
        if mode_index >= 0:
            self.combo_acquisition_mode.setCurrentIndex(mode_index)
        form.addRow("Acquisition:", self.combo_acquisition_mode)

        self.edit_event_count = QtWidgets.QLineEdit()
        self.edit_event_count.setValidator(QtGui.QIntValidator(1, 1000000000, self))
        self.edit_event_count.setText(str(int(event_count or 20000)))
        self.label_point_target = QtWidgets.QLabel()
        form.addRow(self.label_point_target, self.edit_event_count)
        self.combo_acquisition_mode.currentIndexChanged.connect(
            self._on_acquisition_mode_changed
        )

        self.threshold_group = QtWidgets.QGroupBox("main_thr scan")
        threshold_form = QtWidgets.QFormLayout(self.threshold_group)

        self.spin_start = QtWidgets.QSpinBox()
        self.spin_start.setRange(0, 255)
        self.spin_start.setValue(int(start_threshold))
        threshold_form.addRow("Start main_thr:", self.spin_start)

        self.spin_end = QtWidgets.QSpinBox()
        self.spin_end.setRange(0, 255)
        self.spin_end.setValue(int(end_threshold))
        threshold_form.addRow("End main_thr:", self.spin_end)

        self.spin_step = QtWidgets.QSpinBox()
        self.spin_step.setRange(1, 255)
        self.spin_step.setValue(int(step))
        threshold_form.addRow("Step:", self.spin_step)
        layout.addWidget(self.threshold_group)

        self.fixed_hyst_group = QtWidgets.QGroupBox("hyst setting")
        fixed_hyst_form = QtWidgets.QFormLayout(self.fixed_hyst_group)
        self.combo_fixed_hyst = QtWidgets.QComboBox()
        for value in range(16):
            self.combo_fixed_hyst.addItem(str(value), value)
        fixed_hyst_index = self.combo_fixed_hyst.findData(int(fixed_hyst))
        if fixed_hyst_index >= 0:
            self.combo_fixed_hyst.setCurrentIndex(fixed_hyst_index)
        fixed_hyst_form.addRow("hyst for main_thr scan:", self.combo_fixed_hyst)
        layout.addWidget(self.fixed_hyst_group)

        self.fixed_threshold_group = QtWidgets.QGroupBox("main_thr setting")
        fixed_threshold_form = QtWidgets.QFormLayout(self.fixed_threshold_group)
        self.spin_fixed_threshold = QtWidgets.QSpinBox()
        self.spin_fixed_threshold.setRange(0, 255)
        self.spin_fixed_threshold.setValue(int(fixed_threshold))
        fixed_threshold_form.addRow("main_thr for hyst scan:", self.spin_fixed_threshold)
        layout.addWidget(self.fixed_threshold_group)

        self.hyst_group = QtWidgets.QGroupBox("hyst scan")
        hyst_layout = QtWidgets.QVBoxLayout(self.hyst_group)
        hyst_buttons = QtWidgets.QHBoxLayout()
        self.btn_hyst_check_all = QtWidgets.QPushButton("Check All")
        self.btn_hyst_check_all.clicked.connect(lambda: self._set_all_hyst(True))
        hyst_buttons.addWidget(self.btn_hyst_check_all)
        self.btn_hyst_uncheck_all = QtWidgets.QPushButton("Uncheck All")
        self.btn_hyst_uncheck_all.clicked.connect(lambda: self._set_all_hyst(False))
        hyst_buttons.addWidget(self.btn_hyst_uncheck_all)
        hyst_buttons.addStretch(1)
        hyst_layout.addLayout(hyst_buttons)

        hyst_grid = QtWidgets.QGridLayout()
        hyst_layout.addLayout(hyst_grid)
        selected_hyst = set(int(v) for v in (hyst_values or [7]))
        self.hyst_checks = []
        for value in range(16):
            checkbox = QtWidgets.QCheckBox(str(value))
            checkbox.setChecked(value in selected_hyst)
            self.hyst_checks.append(checkbox)
            hyst_grid.addWidget(checkbox, value // 8, value % 8)
        layout.addWidget(self.hyst_group)

        self._update_scan_controls()
        self._update_point_target_label()

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def scan_type(self) -> str:
        return str(self.combo_scan_type.currentData() or "threshold")

    def acquisition_mode(self) -> str:
        return str(self.combo_acquisition_mode.currentData() or NOISE_SCAN_TRIGGERED)

    def event_count(self) -> int:
        try:
            return int(self.edit_event_count.text().strip())
        except Exception:
            return 0

    def start_threshold(self) -> int:
        return int(self.spin_start.value())

    def end_threshold(self) -> int:
        return int(self.spin_end.value())

    def step(self) -> int:
        return int(self.spin_step.value())

    def thresholds(self):
        start = self.start_threshold()
        end = self.end_threshold()
        step = self.step()
        if start <= end:
            return list(range(start, end + 1, step))
        return list(range(start, end - 1, -step))

    def hyst_values(self):
        return [index for index, checkbox in enumerate(self.hyst_checks) if checkbox.isChecked()]

    def fixed_threshold(self) -> int:
        return int(self.spin_fixed_threshold.value())

    def fixed_hyst(self) -> int:
        return int(self.combo_fixed_hyst.currentData())

    def scan_values(self):
        if self.scan_type() == "hyst":
            return self.hyst_values()
        return self.thresholds()

    def accept(self):
        if self.event_count() <= 0:
            target = "Event count" if self.acquisition_mode() == NOISE_SCAN_TRIGGERED else "Duration"
            QtWidgets.QMessageBox.warning(self, "Noise Scan", f"{target} must be positive.")
            return
        if self.scan_type() == "hyst" and not self.hyst_values():
            QtWidgets.QMessageBox.warning(self, "Noise Scan", "Select at least one hyst value.")
            return
        super().accept()

    def _set_all_hyst(self, checked: bool):
        for checkbox in self.hyst_checks:
            checkbox.setChecked(bool(checked))

    def _update_scan_controls(self):
        is_hyst = self.scan_type() == "hyst"
        self.threshold_group.setVisible(not is_hyst)
        self.fixed_hyst_group.setVisible(not is_hyst)
        self.fixed_threshold_group.setVisible(is_hyst)
        self.hyst_group.setVisible(is_hyst)

    def _update_point_target_label(self):
        if self.acquisition_mode() == NOISE_SCAN_TRIGGERED:
            self.label_point_target.setText("Events per point:")
        else:
            self.label_point_target.setText("Seconds per point:")

    def _on_acquisition_mode_changed(self):
        if self.acquisition_mode() == NOISE_SCAN_TRIGGERED:
            self.edit_event_count.setText(str(NOISE_SCAN_DEFAULT_EVENTS))
        else:
            self.edit_event_count.setText(str(NOISE_SCAN_DEFAULT_SECONDS))
        self._update_point_target_label()


class NoiseScanResultDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, *, start_dir=""):
        super().__init__(parent)
        self.setWindowTitle("Noise Scan Result")
        self.resize(880, 560)
        self._series = []
        self._row_map = []
        self._last_dir = str(start_dir or "")
        self._legend = None

        layout = QtWidgets.QVBoxLayout(self)

        controls = QtWidgets.QHBoxLayout()
        layout.addLayout(controls)
        self.btn_add_files = QtWidgets.QPushButton("Add Files...")
        self.btn_add_files.clicked.connect(self._add_files)
        controls.addWidget(self.btn_add_files)
        self.btn_remove_selected = QtWidgets.QPushButton("Remove Selected")
        self.btn_remove_selected.setEnabled(False)
        self.btn_remove_selected.clicked.connect(self.remove_selected_files)
        controls.addWidget(self.btn_remove_selected)
        self.btn_clear_files = QtWidgets.QPushButton("Clear")
        self.btn_clear_files.clicked.connect(self.clear_results)
        controls.addWidget(self.btn_clear_files)
        controls.addStretch(1)
        self.check_log_y = QtWidgets.QCheckBox("Log Y scale")
        self.check_log_y.setToolTip("Use a logarithmic rate axis. Zero and negative rates remain in the table but cannot appear on a log axis.")
        self.check_log_y.toggled.connect(self._set_log_y)
        controls.addWidget(self.check_log_y)

        self.plot = pg.PlotWidget(axisItems={'left': SparseLogAxisItem(orientation='left')})
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("bottom", "ASD scan value")
        self.plot.setLabel("left", "Average rate per channel", units="Hz")
        layout.addWidget(self.plot, 1)

        self.table = QtWidgets.QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Source",
                "Scan",
                "Value",
                "main_thr",
                "hyst",
                "Events",
                "Channels",
                "Average rate/channel [Hz]",
                "Input file",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.itemSelectionChanged.connect(self._update_remove_button)
        header = self.table.horizontalHeader()
        for col in range(8):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_log_y(self, enabled):
        self.plot.setLogMode(x=False, y=enabled)
        self.plot.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

    def set_results(self, results, label="Current scan"):
        self.clear_results()
        self.add_results(results, label=label)

    def replace_results(self, results, label="Current scan"):
        label = str(label or "Current scan")
        normalized = self._normalize_results(results)
        for index, series in enumerate(self._series):
            if series["label"] == label:
                if normalized:
                    series["results"] = normalized
                else:
                    del self._series[index]
                self._refresh()
                return
        if normalized:
            self._series.insert(0, {"label": label, "results": normalized})
        self._refresh()

    def add_results(self, results, label="Noise scan"):
        normalized = self._normalize_results(results)
        if normalized:
            self._series.append({"label": str(label or "Noise scan"), "results": normalized})
        self._refresh()

    def clear_results(self):
        self._series = []
        self._refresh()

    def remove_selected_files(self):
        rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in rows:
            if 0 <= row < len(self._row_map):
                series_index, result_index = self._row_map[row]
                if 0 <= series_index < len(self._series):
                    results = self._series[series_index]["results"]
                    if 0 <= result_index < len(results):
                        del results[result_index]
        self._series = [series for series in self._series if series["results"]]
        self._refresh()

    def _normalize_results(self, results):
        normalized = []
        for result in results or []:
            try:
                scan_type = str(result.get("scan_type", "") or "").strip() or "threshold"
                scan_value = int(result.get("scan_value", result.get("hyst", result.get("threshold", 0))))
                avg_rate = float(result.get("avg_rate_hz", float("nan")))
            except Exception:
                continue
            normalized.append(
                {
                    "scan_type": scan_type,
                    "scan_value": scan_value,
                    "threshold": int(result.get("threshold", scan_value if scan_type == "threshold" else -1)),
                    "hyst": int(result.get("hyst", scan_value if scan_type == "hyst" else -1)),
                    "events": int(result.get("events", 0) or 0),
                    "avg_rate_hz": avg_rate,
                    "n_channels": int(result.get("n_channels", result.get("active_channels", 0)) or 0),
                    "csv_path": str(result.get("csv_path", "") or ""),
                    "dat_path": str(result.get("dat_path", "") or ""),
                    "input_path": str(result.get("input_path", "") or ""),
                }
            )
        return normalized

    def _refresh(self):
        self.plot.clear()
        self._reset_legend()

        row_count = sum(len(series["results"]) for series in self._series)
        self.table.setRowCount(row_count)
        self._row_map = []

        row = 0
        for series_index, series in enumerate(self._series):
            label = series["label"]
            color = self._series_color(series_index)
            xs = []
            ys = []

            for result_index, result in enumerate(series["results"]):
                scan_type = str(result.get("scan_type", "threshold") or "threshold")
                scan_value = int(result.get("scan_value", result.get("threshold", 0)))
                avg_rate = float(result.get("avg_rate_hz", float("nan")))
                input_path = (
                    str(result.get("input_path", "") or "")
                    or str(result.get("csv_path", "") or "")
                    or str(result.get("dat_path", "") or "")
                )

                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(label))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(self._scan_type_label(scan_type)))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(scan_value)))
                self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(self._setting_text(result.get("threshold", -1))))
                self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(self._setting_text(result.get("hyst", -1))))
                self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(int(result.get("events", 0) or 0))))
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(int(result.get("n_channels", 0) or 0))))
                rate_text = "nan" if not np.isfinite(avg_rate) else f"{avg_rate:.6g}"
                self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(rate_text))
                self.table.setItem(row, 8, QtWidgets.QTableWidgetItem(input_path))
                self._row_map.append((series_index, result_index))
                row += 1

                if np.isfinite(avg_rate):
                    xs.append(scan_value)
                    ys.append(avg_rate)

            if xs:
                points = sorted(zip(xs, ys), key=lambda item: item[0])
                xs, ys = [list(values) for values in zip(*points)]
                self.plot.plot(
                    xs,
                    ys,
                    pen=pg.mkPen(color=color, width=2),
                    symbol="o",
                    symbolBrush=pg.mkBrush(color),
                    symbolPen=pg.mkPen(color=color),
                    name=label,
                )
        self._update_remove_button()

    def _update_remove_button(self):
        self.btn_remove_selected.setEnabled(bool(self.table.selectionModel().selectedRows()))

    @staticmethod
    def _scan_type_label(scan_type: str) -> str:
        if str(scan_type).lower() == "hyst":
            return "hyst"
        return "main_thr"

    @staticmethod
    def _setting_text(value) -> str:
        try:
            value = int(value)
        except Exception:
            return str(value or "-")
        if value < 0:
            return "-"
        return str(value)

    def _reset_legend(self):
        if self._legend is not None:
            try:
                self._legend.scene().removeItem(self._legend)
            except Exception:
                pass
            self._legend = None
        if self._series:
            self._legend = self.plot.addLegend(offset=(10, 10))

    @staticmethod
    def _series_color(index: int):
        colors = [
            (0, 80, 200),
            (210, 80, 0),
            (0, 140, 90),
            (160, 60, 160),
            (180, 140, 0),
            (0, 150, 180),
            (190, 60, 60),
            (90, 90, 90),
        ]
        return colors[int(index) % len(colors)]

    def _add_files(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Add Noise Scan Results",
            self._last_dir,
            "Noise scan CSV files (*.csv);;All files (*)",
        )
        if not paths:
            return

        self._last_dir = os.path.dirname(paths[-1])
        failures = []
        detail_results = []
        for path in paths:
            summary_results = self._load_summary_results(path)
            if summary_results:
                self.add_results(summary_results, label=os.path.basename(path))
                continue

            detail_result = self._load_detail_result(path)
            if detail_result:
                detail_results.append(detail_result)
                continue

            failures.append(os.path.basename(path))

        if detail_results:
            label = (
                os.path.basename(detail_results[0].get("input_path", paths[0]))
                if len(detail_results) == 1
                else os.path.basename(os.path.dirname(paths[0])) or "Added scan files"
            )
            self.add_results(detail_results, label=label)

        if failures:
            QtWidgets.QMessageBox.warning(
                self,
                "Noise Scan Result",
                "No noise scan data loaded from:\n" + "\n".join(failures),
            )

    @staticmethod
    def _load_summary_results(path: str):
        if os.path.splitext(str(path))[1].lower() != ".csv":
            return []

        results = []
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = set(reader.fieldnames or [])
                rate_fields = {
                    "average_noise_rate_per_channel_hz",
                    "average_noise_rate_hz",
                    "avg_rate_hz",
                }
                value_fields = {"scan_value", "threshold", "main_thr", "hyst"}
                if not (fieldnames & value_fields) or not (fieldnames & rate_fields):
                    return []

                for row in reader:
                    avg_rate = NoiseScanResultDialog._summary_row_rate(row)
                    if not np.isfinite(avg_rate):
                        continue
                    scan_type = NoiseScanResultDialog._summary_row_scan_type(row)
                    scan_value = NoiseScanResultDialog._summary_row_scan_value(row, scan_type)
                    results.append(
                        {
                            "scan_type": scan_type,
                            "scan_value": scan_value,
                            "threshold": NoiseScanResultDialog._row_int(
                                row,
                                "threshold",
                                NoiseScanResultDialog._row_int(
                                    row,
                                    "main_thr",
                                    scan_value if scan_type == "threshold" else -1,
                                ),
                            ),
                            "hyst": NoiseScanResultDialog._row_int(
                                row,
                                "hyst",
                                scan_value if scan_type == "hyst" else -1,
                            ),
                            "events": NoiseScanResultDialog._row_int(row, "events", 0),
                            "avg_rate_hz": avg_rate,
                            "n_channels": NoiseScanResultDialog._row_int(
                                row,
                                "n_channels",
                                NoiseScanResultDialog._row_int(row, "active_channels", 0),
                            ),
                            "csv_path": row.get("detail_csv", "") or "",
                            "dat_path": row.get("dat_file", "") or "",
                            "input_path": row.get("detail_csv", "") or str(path),
                        }
                    )
        except Exception:
            return []
        return results

    @staticmethod
    def _load_detail_result(path: str):
        scan_type_from_name, value_from_name, threshold_from_name, hyst_from_name = (
            NoiseScanResultDialog._scan_settings_from_filename(path)
        )

        groups = {}
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not NoiseScanResultDialog._row_is_active(row):
                        continue
                    scan_type = str(row.get("scan_type", "") or "").strip().lower() or scan_type_from_name
                    if scan_type not in ("threshold", "hyst"):
                        scan_type = "hyst" if str(row.get("hyst", "") or "").strip() else "threshold"

                    scan_value = NoiseScanResultDialog._row_int(
                        row,
                        "scan_value",
                        value_from_name if value_from_name is not None else 0,
                    )
                    threshold = NoiseScanResultDialog._row_int(
                        row,
                        "threshold",
                        NoiseScanResultDialog._row_int(
                            row,
                            "main_thr",
                            threshold_from_name
                            if threshold_from_name is not None
                            else (scan_value if scan_type == "threshold" else -1),
                        ),
                    )
                    hyst = NoiseScanResultDialog._row_int(
                        row,
                        "hyst",
                        hyst_from_name if hyst_from_name is not None else (scan_value if scan_type == "hyst" else -1),
                    )
                    key = (scan_type, scan_value, threshold, hyst)
                    group = groups.setdefault(
                        key,
                        {
                            "rates": [],
                            "events": 0,
                            "hits": 0.0,
                            "duration_s": 0.0,
                            "channels": 0,
                        },
                    )
                    rate = NoiseScanResultDialog._row_noise_rate(row)
                    if np.isfinite(rate):
                        group["rates"].append(float(rate))
                    group["events"] = max(group["events"], NoiseScanResultDialog._row_int(row, "events", 0))
                    hit_count = NoiseScanResultDialog._row_float(row, "hit_count", float("nan"))
                    if np.isfinite(hit_count):
                        group["hits"] += hit_count
                    duration_s = NoiseScanResultDialog._row_duration_s(row)
                    if np.isfinite(duration_s):
                        group["duration_s"] = max(group["duration_s"], duration_s)
                    group["channels"] += 1
        except Exception:
            return None

        if not groups:
            return None

        results = []
        for (scan_type, scan_value, threshold, hyst), group in groups.items():
            rates = np.asarray(group["rates"], dtype=np.float64)
            if rates.size:
                avg_rate = float(np.nanmean(rates))
            elif group["duration_s"] > 0.0 and group["channels"] > 0:
                avg_rate = float(group["hits"] / (group["duration_s"] * group["channels"]))
            else:
                avg_rate = float("nan")
            if not np.isfinite(avg_rate):
                continue
            results.append(
                {
                    "scan_type": scan_type,
                    "scan_value": int(scan_value),
                    "threshold": int(threshold),
                    "hyst": int(hyst),
                    "events": int(group["events"]),
                    "avg_rate_hz": avg_rate,
                    "n_channels": int(group["channels"]),
                    "csv_path": str(path),
                    "input_path": str(path),
                }
            )
        if not results:
            return None
        if len(results) == 1:
            return results[0]
        return {
            "scan_type": results[0]["scan_type"],
            "scan_value": results[0]["scan_value"],
            "threshold": results[0]["threshold"],
            "hyst": results[0]["hyst"],
            "events": results[0]["events"],
            "avg_rate_hz": float(np.nanmean([r["avg_rate_hz"] for r in results])),
            "n_channels": sum(r["n_channels"] for r in results),
            "csv_path": str(path),
            "input_path": str(path),
        }

    @staticmethod
    def _summary_row_scan_type(row) -> str:
        scan_type = str(row.get("scan_type", "") or "").strip().lower()
        if scan_type in ("threshold", "main_thr"):
            return "threshold"
        if scan_type == "hyst":
            return "hyst"
        if str(row.get("hyst", "") or "").strip() and not str(row.get("threshold", "") or "").strip():
            return "hyst"
        return "threshold"

    @staticmethod
    def _summary_row_scan_value(row, scan_type: str) -> int:
        for key in ("scan_value", "main_thr" if scan_type == "threshold" else scan_type, "threshold"):
            try:
                value = row.get(key, "")
                if str(value).strip() != "":
                    return int(value)
            except Exception:
                continue
        return 0

    @staticmethod
    def _summary_row_rate(row) -> float:
        for key in (
            "average_noise_rate_per_channel_hz",
            "average_noise_rate_hz",
            "avg_rate_hz",
        ):
            rate = NoiseScanResultDialog._row_float(row, key, float("nan"))
            if np.isfinite(rate):
                return rate
        return float("nan")

    @staticmethod
    def _row_noise_rate(row) -> float:
        for key in ("rate_hz", "noise_rate_hz"):
            rate = NoiseScanResultDialog._row_float(row, key, float("nan"))
            if np.isfinite(rate):
                return rate

        hit_count = NoiseScanResultDialog._row_float(row, "hit_count", float("nan"))
        duration_s = NoiseScanResultDialog._row_duration_s(row)
        if np.isfinite(hit_count) and np.isfinite(duration_s) and duration_s > 0.0:
            return float(hit_count / duration_s)
        return float("nan")

    @staticmethod
    def _row_duration_s(row) -> float:
        duration_s = NoiseScanResultDialog._row_float(row, "duration_s", float("nan"))
        if np.isfinite(duration_s) and duration_s > 0.0:
            return duration_s

        events = NoiseScanResultDialog._row_int(row, "events", 0)
        time_window_s = NoiseScanResultDialog._row_float(row, "time_window_s", CH_HIT_TIME_WINDOW_S)
        if events > 0 and np.isfinite(time_window_s) and time_window_s > 0.0:
            return float(events) * float(time_window_s)
        return float("nan")

    @staticmethod
    def _row_is_active(row) -> bool:
        raw = str(row.get("active", "1") or "1").strip().lower()
        return raw not in ("0", "false", "no", "off")

    @staticmethod
    def _row_int(row, key: str, default: int) -> int:
        try:
            value = row.get(key, "")
            if str(value).strip() != "":
                return int(float(value))
        except Exception:
            pass
        return int(default)

    @staticmethod
    def _row_float(row, key: str, default: float) -> float:
        try:
            value = row.get(key, "")
            if str(value).strip() != "":
                return float(value)
        except Exception:
            pass
        return float(default)

    @staticmethod
    def _scan_settings_from_filename(path: str):
        name = os.path.basename(str(path))

        threshold_value = None
        threshold_match = re.search(r"(?:threshold|main[_-]?thr)[_-]?(\d+)", name, flags=re.IGNORECASE)
        if threshold_match:
            threshold_value = int(threshold_match.group(1))

        hyst_value = None
        hyst_match = re.search(r"hyst[_-]?(\d+)", name, flags=re.IGNORECASE)
        if hyst_match:
            hyst_value = int(hyst_match.group(1))

        noise_threshold = re.search(r"noise[_-]?(?:threshold|main[_-]?thr)[_-]?(\d+)", name, flags=re.IGNORECASE)
        if noise_threshold:
            return "threshold", int(noise_threshold.group(1)), threshold_value, hyst_value

        noise_hyst = re.search(r"noise[_-]?hyst[_-]?(\d+)", name, flags=re.IGNORECASE)
        if noise_hyst:
            return "hyst", int(noise_hyst.group(1)), threshold_value, hyst_value

        if threshold_value is not None:
            return "threshold", threshold_value, threshold_value, hyst_value
        if hyst_value is not None:
            return "hyst", hyst_value, threshold_value, hyst_value
        return None, None, threshold_value, hyst_value
