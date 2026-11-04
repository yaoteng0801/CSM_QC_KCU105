from PyQt5 import QtCore, QtGui, QtWidgets
from sca_transaction_ids import next_sca_transaction_id
from csm_monitor_limits import CSMLimitsDialog, default_bounds, latest_csv_values
from pop_csm_monitor_test import CSMMonitorTestDialog
from monitor_limits_ini import MONITOR_LIMITS_INI, load_csm_limits, save_csm_limits
import math

from TDC_config_low_level_function import *

import os
import tempfile
import time
import datetime
import pandas as pd
from pathlib import Path
from lpgbt_register_map_v1 import LpgbtRegisterMapV1


class lpGBT_cell(object):
    def __init__(self,address):
        self.address = address            
        self.lpGBT_monitor_label = ['VSSA','VDDTX','VDDRX','VDD','VDDA','Temp','VREF']    
        self.lpGBT_monitor_index = [9,10,11,12,13,14,15]
        self.lpGBT_monitor_ADCmon = [0,8,4,16,1,0,0]
        self.lpGBT_monitor_unit = ['V','V','V','V','V','C','V']
        if self.address == 115:  #slave lpgbt monitors VTRX_Temp
            self.lpGBT_monitor_label.append('VTRX_Temp')
            self.lpGBT_monitor_index.append(1)
            self.lpGBT_monitor_ADCmon.append(0)
            self.lpGBT_monitor_unit.append('C')

            
        self.lpGBT_monitor_label_widget = [QtWidgets.QLabel(data) for data in self.lpGBT_monitor_label]
        self.lpGBT_monitor_value_widget = [QtWidgets.QLabel('—') for data in self.lpGBT_monitor_label]

    def add_to_layout(self,layout,row,column,first_row=True):
        for i in range(len(self.lpGBT_monitor_label_widget)):
            if first_row:
                layout.addWidget(self.lpGBT_monitor_label_widget[i],   row,    column+i, 1, 1)
                layout.addWidget(self.lpGBT_monitor_value_widget[i],   row+1,  column+i, 1, 1)
            else:
                layout.addWidget(self.lpGBT_monitor_value_widget[i],   row,  column+i, 1, 1)

class CSM_cell(object):
    def __init__(self):
        self.SCA_temp_label = ['VDD2V5','VDD1V2','SCA0_Temp','SCA1_Temp','SCA2_Temp','SCA3_Temp']
        self.SCA_mapping =[0b0100,0b1000,0b0001,0b0010,0b0100,0b1000]
        self.SCA_ADC_input = [SCA_share.CSM_2V5_SENSE,SCA_share.CSM_1V2_SENSE,SCA_share.SCA_INT_TEMP,SCA_share.SCA_INT_TEMP,SCA_share.SCA_INT_TEMP,SCA_share.SCA_INT_TEMP]
        self.SCA_temp_unit = ['V','V','C','C','C','C']
        self.SCA_temp_label_widget = [QtWidgets.QLabel(data) for data in self.SCA_temp_label]
        self.SCA_temp_value_widget = [QtWidgets.QLabel('—') for data in self.SCA_temp_label]
        self.lpGBT_list = []
        self.lpGBT_list.append(lpGBT_cell(117))
        self.lpGBT_list.append(lpGBT_cell(115))

    def add_to_layout(self, layout):
        sca_group = QtWidgets.QGroupBox("SCA Measurements")
        sca_group.setStyleSheet("QLabel { font-size: 14px; }")
        sca_layout = QtWidgets.QGridLayout(sca_group)
        sca_layout.setHorizontalSpacing(4)
        for i in range(len(self.SCA_temp_label_widget)):
            label_widget = self.SCA_temp_label_widget[i]
            value_widget = self.SCA_temp_value_widget[i]
            label_widget.setAlignment(QtCore.Qt.AlignCenter)
            value_widget.setAlignment(QtCore.Qt.AlignCenter)
            value_widget.setMinimumWidth(58)
            value_widget.setStyleSheet("font-weight: 600;")
            sca_layout.addWidget(label_widget, 0, i)
            sca_layout.addWidget(value_widget, 1, i)
            sca_layout.setColumnStretch(i, 1)
        layout.addWidget(sca_group)

        lpgbt_group = QtWidgets.QGroupBox("lpGBT Measurements")
        lpgbt_group.setStyleSheet("QLabel { font-size: 14px; }")
        lpgbt_layout = QtWidgets.QGridLayout(lpgbt_group)
        lpgbt_layout.setHorizontalSpacing(4)
        lpgbt_layout.setRowMinimumHeight(3, 6)

        master = self.lpGBT_list[0]
        slave = self.lpGBT_list[1]
        header_widgets = master.lpGBT_monitor_label_widget + [
            slave.lpGBT_monitor_label_widget[-1]
        ]
        for block in range(2):
            first_metric = block * 4
            header_row = block * 4
            master_row = header_row + 1
            slave_row = header_row + 2

            lpgbt_layout.addWidget(QtWidgets.QLabel("Source"), header_row, 0)
            lpgbt_layout.addWidget(QtWidgets.QLabel("Master"), master_row, 0)
            lpgbt_layout.addWidget(QtWidgets.QLabel("Slave"), slave_row, 0)

            for block_column in range(4):
                metric = first_metric + block_column
                column = block_column + 1
                header_widget = header_widgets[metric]
                header_widget.setAlignment(QtCore.Qt.AlignCenter)
                lpgbt_layout.addWidget(header_widget, header_row, column)
                lpgbt_layout.setColumnStretch(column, 1)

                if metric < len(master.lpGBT_monitor_value_widget):
                    master_value = master.lpGBT_monitor_value_widget[metric]
                    master_value.setStyleSheet("font-weight: 600;")
                else:
                    master_value = QtWidgets.QLabel("—")
                master_value.setAlignment(QtCore.Qt.AlignCenter)
                master_value.setMinimumWidth(58)
                lpgbt_layout.addWidget(master_value, master_row, column)

                slave_value = slave.lpGBT_monitor_value_widget[metric]
                slave_value.setAlignment(QtCore.Qt.AlignCenter)
                slave_value.setMinimumWidth(58)
                slave_value.setStyleSheet("font-weight: 600;")
                lpgbt_layout.addWidget(slave_value, slave_row, column)
        layout.addWidget(lpgbt_group)


class tab_csm(object):


    def __init__(self, MainWindow,eth):
        self.transID = 0

        self.cell_list = []
        self.checkbox_list = []
        self.CSM_count = 2
        self.eth = eth
        self.plot_windows = []
        self._monitor_values = None
        self._monitor_limits = {}
        self._custom_monitor_limits = set()
        self._latest_monitor_values = {}
        self.setup_UI(MainWindow) 
        self._monitor_limits.update(load_csm_limits(self._monitor_metrics(), MONITOR_LIMITS_INI))
        self._custom_monitor_limits.update(self._monitor_limits)
        
    def setup_UI(self, MainWindow):

        sectionLayout = QtWidgets.QVBoxLayout(MainWindow)
        buttonWindow = QtWidgets.QWidget()
        buttonWindow.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.gridLayout = QtWidgets.QGridLayout(buttonWindow)
        self.gridLayout.setVerticalSpacing(10)

        run_group = QtWidgets.QGroupBox("Monitor Run")
        run_layout = QtWidgets.QGridLayout(run_group)
        run_layout.addWidget(QtWidgets.QLabel('CSV output'), 0, 0)
        self.lineEdit_CSM_csv = QtWidgets.QLineEdit()
        self.lineEdit_CSM_csv.setText('csm_monitor.csv')
        self.lineEdit_CSM_csv.setMinimumWidth(280)
        run_layout.addWidget(self.lineEdit_CSM_csv, 0, 1)

        self.checkBox_CSM_count_limit = QtWidgets.QCheckBox('Use scan count limit')
        self.checkBox_CSM_count_limit.setToolTip('Unchecked: monitor until Stop CSM Monitor is pressed.')
        run_layout.addWidget(self.checkBox_CSM_count_limit, 0, 2)
        self.spinBox_CSM_scan_count = QtWidgets.QSpinBox()
        self.spinBox_CSM_scan_count.setMinimum(1)
        self.spinBox_CSM_scan_count.setMaximum(1000000)
        self.spinBox_CSM_scan_count.setValue(1)
        self.spinBox_CSM_scan_count.setEnabled(False)
        self.checkBox_CSM_count_limit.toggled.connect(
            lambda checked: self.spinBox_CSM_scan_count.setEnabled(
                checked and self.checkBox_CSM_count_limit.isEnabled()))
        self.spinBox_CSM_scan_count.setMinimumWidth(100)
        run_layout.addWidget(self.spinBox_CSM_scan_count, 0, 3)

        self.pushButton_CSM_start = QtWidgets.QPushButton()
        self.pushButton_CSM_start.setText("Start CSM Monitor")
        self.pushButton_CSM_start.setMinimumSize(170, 32)
        run_layout.addWidget(self.pushButton_CSM_start, 0, 4)
        self.pushButton_CSM_stop = QtWidgets.QPushButton('Stop CSM Monitor')
        self.pushButton_CSM_stop.setEnabled(False)
        run_layout.addWidget(self.pushButton_CSM_stop, 1, 4)
        run_layout.addWidget(QtWidgets.QLabel('Scan interval'), 1, 0)
        self.spinBox_CSM_interval = QtWidgets.QDoubleSpinBox()
        self.spinBox_CSM_interval.setRange(0, 1440)
        self.spinBox_CSM_interval.setDecimals(3)
        self.spinBox_CSM_interval.setValue(1)
        self.spinBox_CSM_interval.setSuffix(' min')
        self.spinBox_CSM_interval.setToolTip('Time between scan starts. First scan runs immediately; 0 disables waiting.')
        run_layout.addWidget(self.spinBox_CSM_interval, 1, 1)
        self.pushButton_CSM_limits = QtWidgets.QPushButton('Reading limits…')
        self.pushButton_CSM_limits.clicked.connect(self.monitor_limits_dialog)
        run_layout.addWidget(self.pushButton_CSM_limits, 1, 2, 1, 2)
        self.pushButton_CSM_test = QtWidgets.QPushButton('CSM Monitor Test…')
        self.pushButton_CSM_test.clicked.connect(self.monitor_test_dialog)
        run_layout.addWidget(self.pushButton_CSM_test, 1, 5)

        self.pushButton_CSM_plot = QtWidgets.QPushButton()
        self.pushButton_CSM_plot.setText("Plot CSV")
        self.pushButton_CSM_plot.setMinimumSize(130, 32)
        run_layout.addWidget(self.pushButton_CSM_plot, 0, 5)
        self.pushButton_CSM_plot.clicked.connect(self.plot_csv)
        run_layout.setColumnStretch(1, 1)
        self.gridLayout.addWidget(run_group, 0, 0, 1, self.CSM_count)

        self.checkBox_checkCSM0 = QtWidgets.QCheckBox()
        self.checkBox_checkCSM0.setText("Monitor CSM0")
        self.checkBox_checkCSM0.setChecked(True)
        self.checkbox_list.append(self.checkBox_checkCSM0)

        self.checkBox_checkCSM1 = QtWidgets.QCheckBox()
        self.checkBox_checkCSM1.setText("Monitor CSM1")
        self.checkBox_checkCSM1.setChecked(False)
        self.checkbox_list.append(self.checkBox_checkCSM1)

        for which_csm in range(self.CSM_count):
            csm_group = QtWidgets.QGroupBox(f"CSM{which_csm}")
            csm_layout = QtWidgets.QVBoxLayout(csm_group)
            csm_layout.addWidget(self.checkbox_list[which_csm])
            csm_cell = CSM_cell()
            csm_cell.add_to_layout(csm_layout)
            self.cell_list.append(csm_cell)
            self.gridLayout.addWidget(csm_group, 1, which_csm)
            self.gridLayout.setColumnStretch(which_csm, 1)

        self.gridLayout.setRowStretch(2, 1)

        sectionLayout.addWidget(buttonWindow)


    def get_transID(self):
        self.transID = next_sca_transaction_id(self.transID)
        return self.transID

    def get_csv_filename(self):
        return self.lineEdit_CSM_csv.text().strip()

    def get_csv_path(self):
        filename = self.get_csv_filename() or 'csm_monitor.csv'
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
        return self.spinBox_CSM_scan_count.value() if self.checkBox_CSM_count_limit.isChecked() else 0

    def get_monitor_interval_seconds(self):
        return self.spinBox_CSM_interval.value() * 60.0

    def _monitor_metrics(self):
        metrics = []
        for csm, cell in enumerate(self.cell_list):
            for index, (label, unit) in enumerate(zip(cell.SCA_temp_label, cell.SCA_temp_unit)):
                metrics.append(((csm, -1, index), f'CSM{csm} {label}', unit,
                                f'CSM{csm}_SCA_{label}_display_{unit}'))
            for chip, lpgbt in enumerate(cell.lpGBT_list):
                source = 'master' if chip == 0 else 'slave'
                for index, (label, unit) in enumerate(zip(lpgbt.lpGBT_monitor_label, lpgbt.lpGBT_monitor_unit)):
                    metrics.append(((csm, chip, index), f'CSM{csm} {source} {label}', unit,
                                    f'CSM{csm}_lpGBT_{source}_{lpgbt.address}_{label}_display_{unit}'))
        return metrics

    def _prepare_monitor_limits(self):
        try:
            csv_values = latest_csv_values(self.get_csv_path())
        except (OSError, UnicodeError, ValueError) as exc:
            print(f'WARNING: Cannot load previous CSM monitor results: {exc}')
            csv_values = {}
        for key, name, unit, column in self._monitor_metrics():
            if key not in self._latest_monitor_values and column in csv_values:
                self._latest_monitor_values[key] = csv_values[column]
            if key not in self._custom_monitor_limits:
                self._monitor_limits[key] = default_bounds(name.rsplit(' ', 1)[-1])

    def monitor_limits_dialog(self):
        self._prepare_monitor_limits()
        dialog = CSMLimitsDialog(self._monitor_metrics(), self._latest_monitor_values,
                                 self._monitor_limits, self.pushButton_CSM_limits.window())
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            changes = dialog.changes()
            limits = dict(self._monitor_limits)
            limits.update(changes)
            try:
                save_csm_limits(self._monitor_metrics(), limits, MONITOR_LIMITS_INI)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self.pushButton_CSM_limits, 'Cannot save monitoring limits',
                    f'Limits were not changed. Could not save {MONITOR_LIMITS_INI}:\n{exc}')
                return
            self._monitor_limits.update(changes)
            self._custom_monitor_limits.update(changes)

    def monitor_test_dialog(self):
        selected = [i for i, checkbox in enumerate(self.checkbox_list) if checkbox.isChecked()]
        if not selected or not self.pushButton_CSM_start.isEnabled():
            QtWidgets.QMessageBox.information(self.pushButton_CSM_test, 'CSM Monitor Test',
                'Select at least one CSM and wait for any normal CSM scan to finish.')
            return
        self._prepare_monitor_limits()
        dialog = CSMMonitorTestDialog(self, selected, self.pushButton_CSM_test.window())
        dialog.exec_()

    def compact_csv_label(self, column):
        label = column.rsplit('_display_', 1)[0]
        label = label.replace('lpGBT_master', 'master')
        label = label.replace('lpGBT_slave', 'slave')
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

        figure.suptitle(f"CSM monitor stability: {csv_path.name}")
        if any_outliers:
            figure.text(0.08, 0.02, "Red x marks omitted outliers clipped to the visible inlier range.", color='red', fontsize=9)
        figure.subplots_adjust(left=0.08, right=0.72, top=0.90, bottom=0.08, hspace=0.35)

        png_path = csv_path.with_suffix('.png')
        try:
            figure.savefig(png_path, dpi=150, bbox_inches='tight')
            print(f"CSM monitor plot saved: {png_path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "PNG save failed", f"Cannot save PNG file:\n{e}")

        dialog = QtWidgets.QDialog()
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle(f"CSM CSV Plot - {csv_path.name}")
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


 


    def print_message(self,str):
        print(str)

    def _flush_monitor_display(self):
        if self._monitor_values is None:
            return
        for (csm, chip, index), text in self._monitor_values.take().items():
            cell = self.cell_list[csm]
            labels = (cell.SCA_temp_value_widget if chip == -1
                      else cell.lpGBT_list[chip].lpGBT_monitor_value_widget)
            labels[index].setText(text)
            key = (csm, chip, index)
            try:
                value = float(text.split()[0])
            except (ValueError, IndexError):
                value = float('nan')
            if math.isfinite(value):
                self._latest_monitor_values[key] = value
            if key not in self._monitor_limits:
                metric_labels = (cell.SCA_temp_label if chip == -1
                                 else cell.lpGBT_list[chip].lpGBT_monitor_label)
                self._monitor_limits[key] = default_bounds(metric_labels[index])
            bounds = self._monitor_limits.get(key)
            abnormal = not math.isfinite(value) or (bounds is not None and not bounds[0] <= value <= bounds[1])
            labels[index].setStyleSheet('color: red; font-weight: bold;' if abnormal else 'font-weight: 600;')
            labels[index].setToolTip('No valid reading' if not math.isfinite(value) else
                                     f'Acceptable range: {bounds[0]:.3f}–{bounds[1]:.3f}' if bounds else '')

    def _set_monitor_inputs_enabled(self, enabled):
        for widget in (self.checkBox_CSM_count_limit, self.lineEdit_CSM_csv, self.spinBox_CSM_interval,
                       self.pushButton_CSM_limits, self.pushButton_CSM_test, *self.checkbox_list):
            widget.setEnabled(enabled)
        self.spinBox_CSM_scan_count.setEnabled(enabled and self.checkBox_CSM_count_limit.isChecked())
