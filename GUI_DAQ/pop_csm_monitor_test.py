"""Continuous CSM monitoring checks using the normal acquisition path."""

from datetime import datetime
import math
import threading
from PyQt5 import QtCore, QtGui, QtWidgets

from monitor_readers import CSMMonitorReader
from SCA_share import SCA_share
from TDC_config_low_level_function import ethernet_exclusive_session, sca_reply_retry_reporting


class DebugCSMReader(CSMMonitorReader):
    def __init__(self, controller):
        super().__init__(controller)
        self.values = {}

    def record_monitor_value(self, scan_index, which_csm, source, label, raw_adc,
                             display_value, unit, display_text, lpgbt_addr='', monitor_index=''):
        chip = -1 if source == 'SCA' else 0 if source == 'lpGBT master' else 1
        cell = self.csm_tab.cell_list[which_csm]
        labels = cell.SCA_temp_label if chip == -1 else cell.lpGBT_list[chip].lpGBT_monitor_label
        self.values[which_csm, chip, labels.index(label)] = display_value

    def validate_sca_adc(self, channel, error, value):
        if channel != SCA_share.ADC_CHANNEL or error or not 0 <= value < 4096:
            raise RuntimeError(f'Invalid SCA ADC reply: channel={channel}, error={error}, value={value}')

    def validate_lpgbt_adc(self, busy, done, value):
        if busy or not done or not 0 <= value < 1024:
            raise RuntimeError(f'Invalid lpGBT ADC reply: busy={busy}, done={done}, value={value}')


class CSMMonitorTestWorker(QtCore.QThread):
    result = QtCore.pyqtSignal(int, object, bool, str)

    def __init__(self, controller, selected, parent=None):
        super().__init__(parent)
        self.selected = tuple(selected)
        self.metrics = tuple(metric for metric in controller._monitor_metrics() if metric[0][0] in selected)
        self.limits = dict(controller._monitor_limits)
        self.reader = DebugCSMReader(controller)
        # The reader has no event-driven slots or timers here. Its acquisition
        # methods run only in run(); ownership stays with this QThread object.
        self.reader.setParent(self)
        self.reader.message_out.connect(self._reader_message, QtCore.Qt.DirectConnection)
        self.stop_requested = threading.Event()
        self.result_consumed = threading.Event()
        self.target_index = 0
        self.initialized = set()
        self.errors = []
        self.notes = []

    def _reader_message(self, message):
        # Calibration fallback is part of normal monitoring; actual missing ADC
        # readings and command failures are evaluated below.
        if 'CHIPID' not in message:
            self.errors.append(message)

    def stop(self):
        self.stop_requested.set()
        self.result_consumed.set()

    def _test(self, csm):
        self.errors = []
        self.notes = []
        self.reader.values = {}
        self.reader.display_values.take()
        try:
            with sca_reply_retry_reporting(self.notes.append):
                # Keep the lpGBT mux, conversion and status reads together too.
                with ethernet_exclusive_session(self.reader.eth):
                    if csm not in self.initialized:
                        self.reader.initialize_csm(csm)
                        self.initialized.add(csm)
                    self.reader.scan_csm(0, csm)
        except Exception as exc:
            self.errors.append(str(exc))
        values = self.reader.values.copy()
        for key, name, unit, column in self.metrics:
            if key[0] != csm:
                continue
            value = values.get(key)
            bounds = self.limits.get(key)
            if value is None or not math.isfinite(value):
                self.errors.append(f'{name}: no valid reading')
            elif bounds is not None and not bounds[0] <= value <= bounds[1]:
                self.errors.append(f'{name}: {value:.3f} {unit}, expected {bounds[0]:.3f}–{bounds[1]:.3f}')
        if self.errors:
            self.initialized.discard(csm)
        detail = '; '.join(self.errors + self.notes)
        return values, not self.errors, detail

    def run(self):
        while self.selected and not self.stop_requested.is_set():
            csm = self.selected[self.target_index]
            values, valid, detail = self._test(csm)
            self.target_index = (self.target_index + 1) % len(self.selected)
            if not valid:
                print(f'[CSM Monitor Test] CSM{csm}: {detail}')
            self.result_consumed.clear()
            self.result.emit(csm, values, valid, detail)
            # At most one outstanding result, even if the GUI is busy with DAQ.
            while not self.stop_requested.is_set() and not self.result_consumed.wait(0.1):
                pass


class CSMMonitorTestDialog(QtWidgets.QDialog):
    def __init__(self, controller, selected, parent=None):
        super().__init__(parent)
        self.setWindowTitle('CSM Monitor Debug Test')
        self.setModal(True)
        self.controller = controller
        self.selected = tuple(selected)
        self.worker = None
        self.pending_action = None
        self.next_target = 0
        self.metrics = tuple(metric for metric in controller._monitor_metrics() if metric[0][0] in selected)
        layout = QtWidgets.QVBoxLayout(self)
        description = QtWidgets.QLabel(
            'Continuously read SCA, master and slave lpGBT monitoring values on the selected CSMs.\n'
            'One complete CSM scan counts as one test. Any command failure, invalid ADC reply, '
            'missing reading or value outside the configured Reading limits counts as one error per test.\n'
            'Recovered ADC reply retries appear in the history without adding an error. '
            'Start clears results; Stop pauses; Continue resumes; Reset stops and clears results.\n'
            'Tests run continuously, independently of the normal scan count and interval. No CSV is written.')
        description.setWordWrap(True)
        layout.addWidget(description)
        self.table = QtWidgets.QTableWidget(len(self.selected), 3)
        self.table.setHorizontalHeaderLabels(['CSM', 'Tests', 'Errors'])
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        self.readings_table = QtWidgets.QTableWidget(len(self.metrics), 3)
        self.readings_table.setHorizontalHeaderLabels(['Reading', 'Latest value', 'Acceptable range'])
        self.readings_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        for row, (key, name, unit, column) in enumerate(self.metrics):
            self.readings_table.setItem(row, 0, QtWidgets.QTableWidgetItem(f'{name} ({unit})'))
            bounds = controller._monitor_limits.get(key)
            self.readings_table.setItem(row, 2, QtWidgets.QTableWidgetItem(
                f'{bounds[0]:.3f}–{bounds[1]:.3f}' if bounds else ''))
        for table in (self.table, self.readings_table):
            table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        layout.addWidget(self.readings_table)
        self.totals = QtWidgets.QLabel()
        self.status = QtWidgets.QLabel('Ready')
        layout.addWidget(self.totals)
        layout.addWidget(self.status)
        self.error_history = QtWidgets.QPlainTextEdit()
        self.error_history.setReadOnly(True)
        self.error_history.setMaximumBlockCount(200)
        self.error_history.setPlaceholderText('Errors and recovered retries will appear here.')
        layout.addWidget(self.error_history)
        buttons = QtWidgets.QHBoxLayout()
        for name, text, slot in [('start', 'Start', self.start), ('stop', 'Stop', self.stop),
                                 ('continue', 'Continue', self.continue_test),
                                 ('reset', 'Reset', self.reset), ('close', 'Close', self.reject)]:
            button = QtWidgets.QPushButton(text)
            setattr(self, name + '_button', button)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.stop_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self._reset_counts()
        self.resize(900, 750)

    def _reset_counts(self):
        self.counts = {csm: [0, 0] for csm in self.selected}
        self.error_history.clear()
        self.next_target = 0
        for row in range(len(self.metrics)):
            self.readings_table.setItem(row, 1, QtWidgets.QTableWidgetItem('—'))
        self._update_counts()

    def _update_counts(self):
        for row, csm in enumerate(self.selected):
            for col, value in enumerate((f'CSM{csm}', *self.counts[csm])):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))
        self.totals.setText(f'Total: {sum(v[0] for v in self.counts.values())} tests, '
                            f'{sum(v[1] for v in self.counts.values())} errors')

    def start(self):
        if self.worker is None:
            self._reset_counts()
            self._launch()

    def continue_test(self):
        if self.worker is None and self.continue_button.isEnabled():
            self._launch()

    def _launch(self):
        try:
            self.worker = CSMMonitorTestWorker(self.controller, self.selected, self)
        except Exception as exc:
            self.status.setText(f'Could not start: {exc}')
            return
        self.worker.target_index = self.next_target
        self.worker.result.connect(self._result)
        self.worker.finished.connect(self._finished)
        self.start_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.setText('Running')
        self.worker.start()

    def _result(self, csm, values, valid, detail):
        self.counts[csm][0] += 1
        self.counts[csm][1] += int(not valid)
        self._update_counts()
        self.next_target = (self.selected.index(csm) + 1) % len(self.selected)
        for row, (key, name, unit, column) in enumerate(self.metrics):
            if key[0] != csm:
                continue
            value = values.get(key)
            bounds = self.controller._monitor_limits.get(key)
            abnormal = value is None or not math.isfinite(value) or (
                bounds is not None and not bounds[0] <= value <= bounds[1])
            text = 'NA' if value is None else f'{value:.3f}'
            item = QtWidgets.QTableWidgetItem(text)
            if abnormal:
                item.setForeground(QtGui.QColor('red'))
            self.readings_table.setItem(row, 1, item)
            cell = self.controller.cell_list[csm]
            widgets = (cell.SCA_temp_value_widget if key[1] == -1
                       else cell.lpGBT_list[key[1]].lpGBT_monitor_value_widget)
            widgets[key[2]].setText(f'{text} {unit}')
            widgets[key[2]].setStyleSheet('color: red; font-weight: bold;' if abnormal else 'font-weight: 600;')
        if detail:
            kind = 'Error' if not valid else 'Recovered retry'
            self.error_history.appendPlainText(f'{datetime.now():%H:%M:%S} CSM{csm} {kind}: {detail}')
        if self.worker is not None:
            self.worker.result_consumed.set()

    def stop(self):
        if self.worker is not None:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.status.setText('Stopping after the current CSM test…')

    def _finished(self):
        worker, self.worker = self.worker, None
        worker.deleteLater()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.continue_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.status.setText('Stopped')
        action, self.pending_action = self.pending_action, None
        if action == 'reset':
            self.reset()
        elif action == 'close':
            self.reject()

    def reset(self):
        if self.worker is not None:
            self.pending_action = 'reset'
            self.reset_button.setEnabled(False)
            self.stop()
        else:
            self._reset_counts()
            self.continue_button.setEnabled(False)
            self.status.setText('Ready')

    def reject(self):
        if self.worker is not None:
            self.pending_action = 'close'
            self.stop()
        else:
            super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            self.reject()
            event.ignore()
        else:
            super().closeEvent(event)
