from PyQt5 import QtCore, QtGui, QtWidgets
from sca_transaction_ids import next_sca_transaction_id

from TDC_config_low_level_function import *

import os
import tempfile
import time
import datetime
import pandas as pd
from pathlib import Path

from pop_mezz_monitor_test import MezzMonitorTestDialog
from mezz_monitor_limits import MonitorLimitsWidget, ALARM_STYLE
from monitor_limits_ini import load_mezz_limits

class mezz_cell(object):
    def __init__(self):
        self.name_label = QtWidgets.QLabel('0')
        self.checkBox = QtWidgets.QCheckBox()
        self.AVDD_raw = 0
        self.AVDD_return = 0
        self.DVDD_raw = 0
        self.DVDD_return = 0
        self.temp_raw = 0
        self.temp_return = 0
        self.AVDD_cal = QtWidgets.QLabel('0')
        self.DVDD_cal = QtWidgets.QLabel('0')
        self.temp_cal = QtWidgets.QLabel('0')
        self.value_list = [self.AVDD_raw,self.AVDD_return,self.DVDD_raw,self.DVDD_return,self.temp_raw,self.temp_return]
        self.label_list = [self.AVDD_cal,self.DVDD_cal,self.temp_cal]

    def add_to_layout(self,layout,row,column):
        widgets = (
            self.name_label,
            self.checkBox,
            self.AVDD_cal,
            self.DVDD_cal,
            self.temp_cal,
        )
        for row_offset, widget in enumerate(widgets):
            if isinstance(widget, QtWidgets.QLabel):
                widget.setMinimumWidth(42)
                widget.setAlignment(QtCore.Qt.AlignCenter)
            else:
                # Keep the checkbox at its indicator-sized hint so AlignCenter
                # centers the visible square, not an empty text area.
                widget.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed,
                    QtWidgets.QSizePolicy.Fixed,
                )
            layout.addWidget(
                widget,
                row + row_offset,
                column,
                1,
                1,
                QtCore.Qt.AlignCenter,
            )


class tab_sca(object):


    def __init__(self, MainWindow,eth):
        self.transID = 0
        self.CSM_count = 2
        self.mezz_per_CSM = 20
        self.mezz_enable = '0'*self.CSM_count*self.mezz_per_CSM
        self.cell_list = [[],[]]
        self.eth = eth
        self.ADC_channel = 21
        self.plot_windows = []
        self.setup_UI(MainWindow) 
        
    def setup_UI(self, MainWindow):

        sectionLayout = QtWidgets.QVBoxLayout(MainWindow)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)
        self.gridLayout.setVerticalSpacing(10)

        run_group = QtWidgets.QGroupBox("Monitor Run")
        run_layout = QtWidgets.QGridLayout(run_group)
        run_layout.addWidget(QtWidgets.QLabel('CSV output'), 0, 0)
        self.lineEdit_SCA_csv = QtWidgets.QLineEdit()
        self.lineEdit_SCA_csv.setText('sca_monitor.csv')
        self.lineEdit_SCA_csv.setMinimumWidth(280)
        run_layout.addWidget(self.lineEdit_SCA_csv, 0, 1)

        self.checkBox_SCA_count_limit = QtWidgets.QCheckBox('Use scan count limit')
        self.checkBox_SCA_count_limit.setToolTip('Unchecked: monitor until Stop Mezz Monitor is pressed.')
        run_layout.addWidget(self.checkBox_SCA_count_limit, 0, 2)
        self.spinBox_SCA_scan_count = QtWidgets.QSpinBox()
        self.spinBox_SCA_scan_count.setMinimum(1)
        self.spinBox_SCA_scan_count.setMaximum(1000000)
        self.spinBox_SCA_scan_count.setValue(1)
        self.spinBox_SCA_scan_count.setEnabled(False)
        self.checkBox_SCA_count_limit.toggled.connect(
            lambda checked: self.spinBox_SCA_scan_count.setEnabled(
                checked and self.checkBox_SCA_count_limit.isEnabled()))
        self.spinBox_SCA_scan_count.setMinimumWidth(100)
        run_layout.addWidget(self.spinBox_SCA_scan_count, 0, 3)

        self.pushButton_SCA_start = QtWidgets.QPushButton()
        self.pushButton_SCA_start.setText("Start Mezz Monitor")
        self.pushButton_SCA_start.setMinimumSize(170, 32)
        run_layout.addWidget(self.pushButton_SCA_start, 0, 4)

        self.pushButton_SCA_plot = QtWidgets.QPushButton()
        self.pushButton_SCA_plot.setText("Plot CSV")
        self.pushButton_SCA_plot.setMinimumSize(130, 32)
        run_layout.addWidget(self.pushButton_SCA_plot, 0, 5)
        self.pushButton_SCA_plot.clicked.connect(self.plot_csv)
        self.pushButton_monitor_test = QtWidgets.QPushButton("Mezz Monitor Test…")
        self.pushButton_monitor_test.setMinimumHeight(32)
        self.pushButton_monitor_test.clicked.connect(self.monitor_test_dialog)
        run_layout.addWidget(self.pushButton_monitor_test, 1, 4, 1, 2)
        self.monitor_limits = MonitorLimitsWidget(load_mezz_limits())
        run_layout.addWidget(self.monitor_limits, 1, 0, 1, 4)
        run_layout.addWidget(QtWidgets.QLabel('Scan interval'), 2, 0)
        self.spinBox_SCA_interval = QtWidgets.QDoubleSpinBox()
        self.spinBox_SCA_interval.setRange(0, 1440)
        self.spinBox_SCA_interval.setDecimals(3)
        self.spinBox_SCA_interval.setValue(1)
        self.spinBox_SCA_interval.setSuffix(' min')
        self.spinBox_SCA_interval.setToolTip(
            'Time between scan starts. First scan runs immediately. 0 scans continuously without waiting.')
        run_layout.addWidget(self.spinBox_SCA_interval, 2, 1)
        self.label_SCA_status = QtWidgets.QLabel('Idle')
        run_layout.addWidget(self.label_SCA_status, 2, 2, 1, 2)
        self.pushButton_SCA_stop = QtWidgets.QPushButton('Stop Mezz Monitor')
        self.pushButton_SCA_stop.setEnabled(False)
        run_layout.addWidget(self.pushButton_SCA_stop, 2, 4, 1, 2)
        run_layout.setColumnStretch(1, 1)
        self.gridLayout.addWidget(run_group, 0, 0)

        self.checkBox_checkCSM0 = QtWidgets.QCheckBox()
        self.checkBox_checkCSM0.setText("Select all CSM0 mezzanines")
        self.checkBox_checkCSM0.stateChanged.connect(self.mezz_check_all_CSM0)
        self.checkBox_checkCSM1 = QtWidgets.QCheckBox()
        self.checkBox_checkCSM1.setText("Select all CSM1 mezzanines")
        self.checkBox_checkCSM1.stateChanged.connect(self.mezz_check_all_CSM1)

        check_all_boxes = (self.checkBox_checkCSM0, self.checkBox_checkCSM1)
        row_labels = ('Mezz', 'Monitor', 'AVDD (V)', 'DVDD (V)', 'Temp (C)')
        for which_csm in range(self.CSM_count):
            first_mezz = which_csm * self.mezz_per_CSM
            csm_group = QtWidgets.QGroupBox(
                f"CSM{which_csm} — Mezz {first_mezz}–{first_mezz + self.mezz_per_CSM - 1}"
            )
            csm_layout = QtWidgets.QGridLayout(csm_group)
            csm_layout.addWidget(check_all_boxes[which_csm], 0, 0, 1, 2)

            for block in range(2):
                block_first = first_mezz + block * 10
                block_group = QtWidgets.QGroupBox(
                    f"Mezz {block_first}–{block_first + 9}"
                )
                block_group.setStyleSheet(
                    "QLabel, QCheckBox { font-size: 14px; }"
                )
                block_layout = QtWidgets.QGridLayout(block_group)
                block_layout.setHorizontalSpacing(3)
                block_layout.setVerticalSpacing(4)

                for label_row, text in enumerate(row_labels):
                    label = QtWidgets.QLabel(text)
                    label.setStyleSheet("font-weight: 600;")
                    block_layout.addWidget(label, label_row, 0)

                for block_mezz in range(10):
                    mezz = block * 10 + block_mezz
                    global_mezz = first_mezz + mezz
                    cell = mezz_cell()
                    cell.name_label.setText(str(global_mezz))
                    if self.mezz_enable[global_mezz] == '1':
                        cell.checkBox.setChecked(True)
                    cell.checkBox.setToolTip(f"Monitor Mezzanine {global_mezz}")
                    cell.checkBox.stateChanged.connect(self.mezz_enable_update)
                    cell.add_to_layout(block_layout, 0, block_mezz + 1)
                    block_layout.setColumnStretch(block_mezz + 1, 1)
                    self.cell_list[which_csm].append(cell)

                csm_layout.addWidget(block_group, 1, block)
                csm_layout.setColumnStretch(block, 1)

            self.gridLayout.addWidget(csm_group, which_csm + 1, 0)

        self.gridLayout.setRowStretch(self.CSM_count + 1, 1)

        sectionLayout.addWidget(buttonWindow)


    def get_transID(self):
        self.transID = next_sca_transaction_id(self.transID)
        return self.transID

    def get_csv_filename(self):
        return self.lineEdit_SCA_csv.text().strip()

    def get_csv_path(self):
        filename = self.get_csv_filename() or 'sca_monitor.csv'
        csv_path = Path(filename).expanduser()
        if csv_path.suffix == '':
            csv_path = csv_path.with_suffix('.csv')
        if not csv_path.is_absolute():
            output_dir = Path(__file__).resolve().parent/'output'
            if csv_path.parts and csv_path.parts[0] == 'output':
                csv_path = Path(__file__).resolve().parent/csv_path
            else:
                csv_path = output_dir/csv_path
        return csv_path

    def get_scan_count(self):
        return self.spinBox_SCA_scan_count.value() if self.checkBox_SCA_count_limit.isChecked() else 0

    def get_monitor_interval_seconds(self):
        return self.spinBox_SCA_interval.value() * 60.0

    def get_monitor_limits(self):
        return self.monitor_limits.values()

    def apply_monitor_reading(self, mezz_index, label_index, text, abnormal):
        label = self.cell_list[mezz_index // self.mezz_per_CSM][mezz_index % self.mezz_per_CSM].label_list[label_index]
        label.setText(text)
        label.setStyleSheet(ALARM_STYLE if abnormal else "")

    def compact_csv_label(self, column):
        label = column.rsplit('_display_', 1)[0]
        return label

    def plot_outlier_mask(self, y, unit):
        y = pd.to_numeric(y, errors='coerce')
        valid = y.dropna()
        mask = pd.Series(False, index=y.index)
        if len(valid) < 5:
            return mask

        min_delta = 5.0 if unit == 'C' else 0.05 if unit == 'V' else 1.0
        median = valid.median()
        deviation = (valid-median).abs()
        mad = deviation.median()

        if mad > 0:
            sigma = 1.4826*mad
            threshold = max(6.0*sigma, min_delta)
            mask.loc[valid.index] = deviation > threshold
        else:
            q1 = valid.quantile(0.25)
            q3 = valid.quantile(0.75)
            iqr = q3-q1
            if iqr > 0:
                sigma = iqr/1.349
                threshold = max(6.0*sigma, min_delta)
                mask.loc[valid.index] = deviation > threshold
            else:
                mask.loc[valid.index] = deviation > min_delta

        if mask.sum() >= len(valid):
            mask.loc[:] = False
        return mask

    def plot_csv(self):
        csv_path = self.get_csv_path()
        if not csv_path.exists():
            QtWidgets.QMessageBox.warning(None, "CSV not found", f"Cannot find CSV file:\n{csv_path}")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "CSV read failed", f"Cannot read CSV file:\n{e}")
            return

        if 'scan' not in df.columns:
            QtWidgets.QMessageBox.warning(None, "CSV format error", "CSV file does not contain a scan column.")
            return

        display_columns = [column for column in df.columns if '_display_' in column]
        if not display_columns:
            QtWidgets.QMessageBox.warning(None, "CSV format error", "CSV file does not contain display value columns.")
            return

        try:
            mpl_config_dir = Path(tempfile.gettempdir()) / 'matplotlib'
            mpl_config_dir.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault('MPLCONFIGDIR', str(mpl_config_dir))
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
            from matplotlib.figure import Figure
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "Plot failed", f"Cannot load matplotlib:\n{e}")
            return

        x = pd.to_numeric(df['scan'], errors='coerce')
        valid_scan = x.notna()
        df = df.loc[valid_scan]
        x = x.loc[valid_scan]
        if df.empty:
            QtWidgets.QMessageBox.warning(None, "CSV format error", "CSV file has no valid scan values.")
            return

        columns_by_unit = {}
        for column in display_columns:
            unit = column.rsplit('_display_', 1)[1]
            columns_by_unit.setdefault(unit, []).append(column)

        figure_height = max(4, 3.2*len(columns_by_unit))
        figure = Figure(figsize=(12, figure_height))
        axes = figure.subplots(len(columns_by_unit), 1, squeeze=False)
        axes = axes[:, 0]

        any_outliers = False
        for ax, (unit, columns) in zip(axes, columns_by_unit.items()):
            plotted = False
            inlier_values = []
            outlier_points = []
            for column in columns:
                y = pd.to_numeric(df[column], errors='coerce')
                if y.notna().any():
                    outlier_mask = self.plot_outlier_mask(y, unit)
                    y_inlier = y.mask(outlier_mask)
                    if y_inlier.notna().any():
                        ax.plot(x, y_inlier, marker='o', markersize=3, linewidth=1, label=self.compact_csv_label(column))
                        inlier_values.extend(y_inlier.dropna().tolist())
                    if outlier_mask.any():
                        any_outliers = True
                        outlier_points.append((x.loc[outlier_mask], y.loc[outlier_mask]))
                    plotted = True

            if inlier_values:
                y_min = min(inlier_values)
                y_max = max(inlier_values)
                if y_min == y_max:
                    pad = max(abs(y_min)*0.05, 0.5 if unit == 'C' else 0.01)
                else:
                    pad = (y_max-y_min)*0.08
                y_lower = y_min-pad
                y_upper = y_max+pad
                ax.set_ylim(y_lower, y_upper)

                outlier_label_added = False
                marker_pad = (y_upper-y_lower)*0.025
                for x_out, y_out in outlier_points:
                    y_marker = y_out.copy()
                    y_marker[y_out > y_upper] = y_upper-marker_pad
                    y_marker[y_out < y_lower] = y_lower+marker_pad
                    y_marker[(y_out >= y_lower) & (y_out <= y_upper)] = y_out[(y_out >= y_lower) & (y_out <= y_upper)]
                    ax.scatter(
                        x_out,
                        y_marker,
                        marker='x',
                        color='red',
                        s=55,
                        linewidths=1.6,
                        zorder=5,
                        label='outlier' if not outlier_label_added else '_nolegend_'
                    )
                    outlier_label_added = True

            ax.set_xlabel("Scan")
            ax.set_ylabel(unit)
            ax.grid(True, alpha=0.3)
            if plotted:
                ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=7)

        figure.suptitle(f"SCA monitor stability: {csv_path.name}")
        if any_outliers:
            figure.text(0.08, 0.02, "Red x marks omitted outliers clipped to the visible inlier range.", color='red', fontsize=9)
        figure.subplots_adjust(left=0.08, right=0.72, top=0.90, bottom=0.08, hspace=0.35)

        png_path = csv_path.with_suffix('.png')
        try:
            figure.savefig(png_path, dpi=150, bbox_inches='tight')
            print(f"SCA monitor plot saved: {png_path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "PNG save failed", f"Cannot save PNG file:\n{e}")

        dialog = QtWidgets.QDialog()
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle(f"SCA CSV Plot - {csv_path.name}")
        dialog.resize(1200, 800)

        layout = QtWidgets.QVBoxLayout(dialog)
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, dialog)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        canvas.draw()

        self.plot_windows.append(dialog)
        dialog.destroyed.connect(lambda _=None, window=dialog: self.plot_windows.remove(window) if window in self.plot_windows else None)
        dialog.show()


    def mezz_enable_update(self):
        enable = ''
        for j in range(self.CSM_count):
            for cell in self.cell_list[j]:
                if cell.checkBox.isChecked():
                    enable +='1'
                else:
                    enable +='0'
        self.mezz_enable = enable

        check_all_boxes = (
            self.checkBox_checkCSM0,
            self.checkBox_checkCSM1,
        )
        for which_csm, check_all in enumerate(check_all_boxes):
            blocker = QtCore.QSignalBlocker(check_all)
            check_all.setChecked(
                all(cell.checkBox.isChecked() for cell in self.cell_list[which_csm])
            )
            del blocker
        # print(self.mezz_enable)

    def select_scanned_mezz(self, selected_mezz):
        """Mirror the detected Mezz Config scan result into this monitor."""
        selected = set()
        for which_csm, mezz in selected_mezz or []:
            try:
                which_csm = int(which_csm)
                mezz = int(mezz)
            except (TypeError, ValueError):
                continue
            if 0 <= which_csm < self.CSM_count and 0 <= mezz < self.mezz_per_CSM:
                selected.add((which_csm, mezz))

        signal_blockers = []
        try:
            for which_csm, cells in enumerate(self.cell_list):
                for mezz, cell in enumerate(cells):
                    signal_blockers.append(QtCore.QSignalBlocker(cell.checkBox))
                    cell.checkBox.setChecked((which_csm, mezz) in selected)

            check_all_boxes = (
                self.checkBox_checkCSM0,
                self.checkBox_checkCSM1,
            )
            for which_csm, check_all in enumerate(check_all_boxes):
                signal_blockers.append(QtCore.QSignalBlocker(check_all))
                check_all.setChecked(
                    all((which_csm, mezz) in selected for mezz in range(self.mezz_per_CSM))
                )
        finally:
            del signal_blockers

        self.mezz_enable_update()
        print(
            f"Mezz Monitor selected {len(selected)} mezzanine(s) from Mezz Scan: "
            f"{sorted(selected)}"
        )

    def mezz_check_all_CSM0(self):
        if self.checkBox_checkCSM0.isChecked():
            for cell in self.cell_list[0]:
                cell.checkBox.setChecked(True)
        else:
            for cell in self.cell_list[0]:
                cell.checkBox.setChecked(False)
        print(self.mezz_enable)

    def mezz_check_all_CSM1(self):
        if self.checkBox_checkCSM1.isChecked():
            for cell in self.cell_list[1]:
                cell.checkBox.setChecked(True)
        else:
            for cell in self.cell_list[1]:
                cell.checkBox.setChecked(False)
        print(self.mezz_enable)
                

    # def sca_reset(self):
    #     SCA_start_reset(self.eth,self.sca_enable,verbose=1)

    # def sca_tx_rx_reset(self):
    #     SCA_tx_rx_reset(self.eth,self.sca_enable)


    def print_message(self,str):
        print(str)

    def _set_monitor_inputs_enabled(self, enabled):
        for widget in (self.monitor_limits, self.spinBox_SCA_interval, self.checkBox_SCA_count_limit,
                       self.lineEdit_SCA_csv, self.checkBox_checkCSM0, self.checkBox_checkCSM1,
                       self.pushButton_monitor_test):
            widget.setEnabled(enabled)
        self.spinBox_SCA_scan_count.setEnabled(enabled and self.checkBox_SCA_count_limit.isChecked())
        for cells in self.cell_list:
            for cell in cells:
                cell.checkBox.setEnabled(enabled)

    def monitor_test_dialog(self):
        selected = [(i // self.mezz_per_CSM, i % self.mezz_per_CSM)
                    for i, bit in enumerate(self.mezz_enable) if bit == '1']
        if not selected:
            QtWidgets.QMessageBox.information(self.pushButton_monitor_test, "Mezz Monitor Test",
                                              "Select at least one mezzanine first.")
            return
        if not self.pushButton_SCA_start.isEnabled():
            QtWidgets.QMessageBox.information(self.pushButton_monitor_test, "Mezz Monitor Test",
                                              "Wait for the current monitor run to finish.")
            return
        dialog = MezzMonitorTestDialog(self, selected, self.pushButton_monitor_test.window())
        dialog.exec_()
