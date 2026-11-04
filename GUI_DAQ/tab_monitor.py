"""Combined mezzanine and CSM monitoring with a common schedule and CSV."""

from datetime import datetime
from pathlib import Path
from PyQt5 import QtCore, QtWidgets

from tab_sca import tab_sca
from tab_csm import tab_csm
from Worker_Monitor import Worker_Monitor
from mezz_monitor_limits import MonitorLimitsWidget
from csm_monitor_limits import CSMLimitsDialog
from monitor_limits_ini import MONITOR_LIMITS_INI, save_monitor_limits, load_monitor_limits


class tab_monitor:
    def __init__(self, parent, eth):
        self.parent = parent
        self.worker = None
        self.thread = None
        self.csv_path = None
        self.scan_limit = 0  # Worker_Monitor stops after this many scans; 0 runs until Stop.
        self.ranges_file = MONITOR_LIMITS_INI
        layout = QtWidgets.QVBoxLayout(parent)
        run_group = QtWidgets.QGroupBox('Monitoring run')
        grid = QtWidgets.QGridLayout(run_group)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setVerticalSpacing(4)
        sources = QtWidgets.QFrame()
        sources.setFrameShape(QtWidgets.QFrame.StyledPanel)
        source_layout = QtWidgets.QHBoxLayout(sources)
        source_layout.setContentsMargins(8, 4, 8, 4)
        source_layout.addWidget(QtWidgets.QLabel('<b>Monitor</b>'))
        self.checkBox_monitor_mezz = QtWidgets.QCheckBox('Mezz')
        self.checkBox_monitor_csm = QtWidgets.QCheckBox('CSM')
        for checkbox in (self.checkBox_monitor_mezz, self.checkBox_monitor_csm):
            checkbox.setChecked(True)
            checkbox.setStyleSheet('QCheckBox { font-weight: bold; font-size: 16px; padding: 3px; } '
                                  'QCheckBox::indicator { width: 20px; height: 20px; }')
            source_layout.addWidget(checkbox)
        grid.addWidget(sources, 0, 0, 1, 2)
        grid.addWidget(QtWidgets.QLabel('Interval'), 0, 2)
        self.interval = QtWidgets.QDoubleSpinBox()
        self.interval.setRange(0, 86400)
        self.interval.setDecimals(3)
        self.interval.setValue(60)
        self.interval.setSuffix(' s')
        self.interval.setToolTip('Seconds between full scan starts. First scan runs immediately; 0 means no waiting. Runs until Stop.')
        grid.addWidget(self.interval, 0, 3)
        self.start_button = QtWidgets.QPushButton('Start')
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.setEnabled(False)
        self.plot_button = QtWidgets.QPushButton('Plot CSV')
        for col, button in enumerate((self.start_button, self.stop_button, self.plot_button), 4):
            grid.addWidget(button, 0, col)
        grid.addWidget(QtWidgets.QLabel('CSV folder'), 1, 0)
        self.lineEdit_csv_directory = QtWidgets.QLineEdit(str(Path(__file__).resolve().parent / 'output'))
        self.lineEdit_csv_directory.setToolTip('Every run creates a new monitor_YYYYMMDD_HHMMSS_microseconds.csv in this folder.')
        grid.addWidget(self.lineEdit_csv_directory, 1, 1, 1, 5)
        self.browse_button = QtWidgets.QPushButton('Browse')
        grid.addWidget(self.browse_button, 1, 6)
        self.csv_file_label = QtWidgets.QLabel('A new timestamped CSV is created for each run.')
        self.csv_file_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        grid.addWidget(self.csv_file_label, 2, 0, 1, 4)
        self.status = QtWidgets.QLabel('Idle')
        self.status.setWordWrap(True)
        grid.addWidget(self.status, 2, 4, 1, 3)
        grid.setColumnStretch(1, 1)
        layout.addWidget(run_group)

        settings = QtWidgets.QGroupBox('Acceptable ranges and debug tests')
        settings_grid = QtWidgets.QGridLayout(settings)
        self.mezz_limits_button = QtWidgets.QPushButton('Mezz ranges')
        self.sca_limits_button = QtWidgets.QPushButton('CSM SCA ranges')
        self.master_limits_button = QtWidgets.QPushButton('Master lpGBT ranges')
        self.slave_limits_button = QtWidgets.QPushButton('Slave lpGBT ranges')
        for col, button in enumerate((self.mezz_limits_button, self.sca_limits_button,
                                      self.master_limits_button, self.slave_limits_button)):
            settings_grid.addWidget(button, 0, col)
        self.mezz_test_button = QtWidgets.QPushButton('Mezz monitor test')
        self.csm_test_button = QtWidgets.QPushButton('CSM monitor test')
        settings_grid.addWidget(self.mezz_test_button, 1, 0)
        settings_grid.addWidget(self.csm_test_button, 1, 1)
        self.save_ranges_button = QtWidgets.QPushButton('Save to file')
        self.load_ranges_button = QtWidgets.QPushButton('Load from file')
        settings_grid.addWidget(self.save_ranges_button, 1, 2)
        settings_grid.addWidget(self.load_ranges_button, 1, 3)
        layout.addWidget(settings)

        self.readings_tabs = QtWidgets.QTabWidget()
        mezz_page, csm_page = QtWidgets.QWidget(), QtWidgets.QWidget()
        self.mezz = tab_sca(mezz_page, eth)
        self.csm = tab_csm(csm_page, eth)
        # Reuse target selection and reading displays, with one shared run panel.
        self.mezz.pushButton_SCA_start.parentWidget().hide()
        self.csm.pushButton_CSM_start.parentWidget().hide()
        self.readings_tabs.addTab(mezz_page, 'Mezz selection and readings')
        self.readings_tabs.addTab(csm_page, 'CSM selection and readings')
        layout.addWidget(self.readings_tabs)
        self.timer = QtCore.QTimer(parent)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._flush_display)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.plot_button.clicked.connect(self.plot_csv)
        self.browse_button.clicked.connect(self.browse_csv_directory)
        self.save_ranges_button.clicked.connect(self.save_ranges)
        self.load_ranges_button.clicked.connect(self.load_ranges)
        self.mezz_limits_button.clicked.connect(self.mezz_limits_dialog)
        self.sca_limits_button.clicked.connect(lambda: self.csm_limits_dialog(-1))
        self.master_limits_button.clicked.connect(lambda: self.csm_limits_dialog(0))
        self.slave_limits_button.clicked.connect(lambda: self.csm_limits_dialog(1))
        self.mezz_test_button.clicked.connect(self.mezz.monitor_test_dialog)
        self.csm_test_button.clicked.connect(self.csm.monitor_test_dialog)
        self.checkBox_monitor_mezz.toggled.connect(self._update_sources)
        self.checkBox_monitor_csm.toggled.connect(self._update_sources)
        self._update_sources()

    def csv_directory(self):
        text = self.lineEdit_csv_directory.text().strip()
        return Path(text).expanduser().resolve() if text else Path(__file__).resolve().parent / 'output'

    def new_csv_path(self):
        return self.csv_directory() / f'monitor_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'

    def get_csv_filename(self):
        if self.csv_path is None:
            self.csv_path = self.new_csv_path()
        return str(self.csv_path)

    def get_csv_path(self):
        return Path(self.get_csv_filename())

    def get_monitor_interval_seconds(self):
        return self.interval.value()

    def browse_csv_directory(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Select monitoring CSV folder',
                                                            str(self.csv_directory()))
        if folder:
            self.lineEdit_csv_directory.setText(folder)

    def _sync_csv_path(self):
        if self.csv_path is not None:
            for field in (self.mezz.lineEdit_SCA_csv, self.csm.lineEdit_CSM_csv):
                field.setText(str(self.csv_path))

    def _update_sources(self):
        enabled = self.worker is None
        for index, (box, test_button) in enumerate(((self.checkBox_monitor_mezz, self.mezz_test_button),
                                                  (self.checkBox_monitor_csm, self.csm_test_button))):
            self.readings_tabs.setTabEnabled(index, box.isChecked())
            test_button.setEnabled(enabled and box.isChecked())
        if not self.readings_tabs.isTabEnabled(self.readings_tabs.currentIndex()):
            for index in range(2):
                if self.readings_tabs.isTabEnabled(index):
                    self.readings_tabs.setCurrentIndex(index)
                    break

    def _set_running(self, running):
        for widget in (self.lineEdit_csv_directory, self.browse_button, self.interval,
                       self.save_ranges_button, self.load_ranges_button,
                       self.checkBox_monitor_mezz, self.checkBox_monitor_csm,
                       self.mezz_limits_button, self.sca_limits_button,
                       self.master_limits_button, self.slave_limits_button):
            widget.setEnabled(not running)
        self.mezz._set_monitor_inputs_enabled(not running)
        self.csm._set_monitor_inputs_enabled(not running)
        self.mezz.pushButton_SCA_start.setEnabled(not running)
        self.csm.pushButton_CSM_start.setEnabled(not running)
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self._update_sources()

    def start(self):
        if self.worker is not None:
            return
        error = None
        if not (self.checkBox_monitor_mezz.isChecked() or self.checkBox_monitor_csm.isChecked()):
            error = 'Select Mezz monitoring, CSM monitoring, or both.'
        elif self.checkBox_monitor_mezz.isChecked() and '1' not in self.mezz.mezz_enable:
            error = 'Select at least one mezzanine, or uncheck Monitor mezzanines.'
        elif self.checkBox_monitor_csm.isChecked() and not any(box.isChecked() for box in self.csm.checkbox_list):
            error = 'Select at least one CSM, or uncheck Monitor CSMs.'
        if error:
            QtWidgets.QMessageBox.information(self.parent, 'Monitoring selection', error)
            return
        self.csv_path = self.new_csv_path()
        self._sync_csv_path()
        self.csm._prepare_monitor_limits()
        try:
            self.worker = Worker_Monitor(self)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.parent, 'Cannot start monitoring', str(exc))
            return
        self.thread = QtCore.QThread(self.parent)
        self.worker.moveToThread(self.thread)
        if self.worker.csm_reader is not None:
            self.csm._monitor_values = self.worker.csm_reader.display_values
        self.thread.started.connect(self.worker.run)
        self.worker.message_out.connect(self._message)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self._set_running(True)
        self._show_csv_path()
        self.status.setText('Starting…')
        self.timer.start()
        self.thread.start()

    def stop(self):
        if self.worker is not None:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.status.setText('Stopping after the current full scan…')

    def _message(self, message):
        print(message)
        if 'failed' in message.lower() or 'error' in message.lower():
            self.status.setText(message)

    def _flush_display(self):
        if self.worker is None:
            return
        for key, value in self.worker.display_values.take().items():
            if key == 'csv_path':
                self.csv_path = Path(value)
                self._sync_csv_path()
                self._show_csv_path()
            elif key == 'status':
                if self.stop_button.isEnabled():
                    self.status.setText(value)
            else:
                kind, index, label_index = key
                self.mezz.apply_monitor_reading(index, label_index, *value)
        self.csm._flush_monitor_display()

    def _finished(self):
        self.timer.stop()
        self._flush_display()
        self.csm._monitor_values = None
        self.worker = self.thread = None
        self._set_running(False)
        self.status.setText('Stopped · ' + self.status.text())

    def _show_csv_path(self):
        self.csv_file_label.setText(self.csv_path.name)
        self.csv_file_label.setToolTip(str(self.csv_path))

    def plot_csv(self):
        path = self.csv_path
        if path is None or not path.is_file():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.parent, 'Select monitoring CSV', str(self.csv_directory()), 'CSV files (*.csv)')
            if not filename:
                return
            path = Path(filename)
        self.mezz.lineEdit_SCA_csv.setText(str(path))
        self.mezz.plot_csv()

    def mezz_limits_dialog(self):
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle('Mezz monitoring ranges')
        layout = QtWidgets.QVBoxLayout(dialog)
        editor = MonitorLimitsWidget(self.mezz.get_monitor_limits())
        layout.addWidget(editor)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Apply')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.mezz.monitor_limits.set_values(editor.values())

    def csm_limits_dialog(self, chip):
        self._sync_csv_path()
        self.csm._prepare_monitor_limits()
        metrics = [metric for metric in self.csm._monitor_metrics() if metric[0][1] == chip]
        dialog = CSMLimitsDialog(metrics, self.csm._latest_monitor_values, self.csm._monitor_limits, self.parent, persist=False)
        dialog.setWindowTitle({-1: 'CSM SCA ranges', 0: 'Master lpGBT ranges', 1: 'Slave lpGBT ranges'}[chip])
        dialog.resize(780, 500)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            changes = dialog.changes()
            self.csm._monitor_limits.update(changes)
            self.csm._custom_monitor_limits.update(changes)

    def save_ranges(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, 'Save all monitoring ranges', str(self.ranges_file), 'INI files (*.ini)')
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix('.ini')
        self.csm._prepare_monitor_limits()
        try:
            save_monitor_limits(self.csm._monitor_metrics(), self.csm._monitor_limits,
                                self.mezz.get_monitor_limits(), path)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.parent, 'Cannot save ranges', str(exc))
            return
        self.ranges_file = path
        self.status.setText(f'Ranges saved: {path.name}')

    def load_ranges(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.parent, 'Load all monitoring ranges', str(self.ranges_file), 'INI files (*.ini)')
        if not filename:
            return
        path = Path(filename)
        try:
            csm_limits, mezz_limits = load_monitor_limits(self.csm._monitor_metrics(), path)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.parent, 'Cannot load ranges', str(exc))
            return
        self.mezz.monitor_limits.set_values(mezz_limits)
        self.csm._monitor_limits.update(csm_limits)
        self.csm._custom_monitor_limits.update(csm_limits)
        self.ranges_file = path
        self.status.setText(f'Ranges loaded: {path.name}')
