import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import csv
from datetime import datetime
import gc
from pathlib import Path
import tempfile
import threading
import time
import tracemalloc
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from PyQt5 import QtWidgets
from tab_monitor import tab_monitor
from Worker_Monitor import Worker_Monitor
from monitor_limits_ini import load_mezz_limits, load_csm_limits


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.waits = []
        self.stopped = False

    def is_set(self):
        return self.stopped

    def wait(self, delay):
        self.waits.append(delay)
        self.now += delay
        return self.stopped

class CombinedMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'combined.csv'
        self.host = QtWidgets.QWidget()
        self.controller = tab_monitor(self.host, object())
        self.controller.lineEdit_csv_directory.setText(self.directory.name)
        self.controller.csv_path = self.path
        self.controller.mezz.select_scanned_mezz([(0, 0), (1, 0)])
        self.controller.csm.checkbox_list[1].setChecked(True)
        self.controller._sync_csv_path()
        self.controller.csm._prepare_monitor_limits()

    def tearDown(self):
        if self.controller.worker is not None:
            self.controller.stop()
            self.wait_for(lambda: self.controller.worker is None)
        self.host.close()
        self.directory.cleanup()

    def hardware(self, scans=2):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch('monitor_readers.SCA_connect', lambda *a, **kw: None))
        stack.enter_context(patch('monitor_readers.SCA_config', lambda *a, **kw: [20, 0, 2048]))
        stack.enter_context(patch('monitor_readers.lpgbt_config_write', lambda *a, **kw: [2, 0]))
        stack.enter_context(patch('monitor_readers.CSMMonitorReader.get_lpgbt_calibration', lambda *a: None))
        real_scan = Worker_Monitor._scan
        def limited_scan(worker, index):
            real_scan(worker, index)
            if index >= scans:
                worker.stop()
        stack.enter_context(patch.object(Worker_Monitor, '_scan', limited_scan))
        return stack

    def rows(self):
        path = self.controller.csv_path or self.path
        with path.open(newline='') as source:
            reader = csv.DictReader(source)
            return reader.fieldnames, list(reader)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.001)
        self.assertTrue(predicate())

    def test_source_combinations_single_csv_and_consistent_timestamps(self):
        for mezz_enabled, csm_enabled in ((True, False), (False, True), (True, True)):
            with self.subTest(mezz=mezz_enabled, csm=csm_enabled):
                self.controller.checkBox_monitor_mezz.setChecked(mezz_enabled)
                self.controller.checkBox_monitor_csm.setChecked(csm_enabled)
                worker = Worker_Monitor(self.controller)
                clock = FakeClock()
                worker.stop_requested = clock
                with self.hardware(), patch('Worker_Monitor.time.monotonic', lambda: clock.now):
                    worker.run()
                columns, rows = self.rows()
                self.assertEqual(columns[:2], ['timestamp', 'scan'])
                self.assertEqual(len(columns), len(set(columns)))
                self.assertEqual([row['scan'] for row in rows], ['1', '2'])
                self.assertEqual(clock.waits, [0, 60])
                for row in rows:
                    self.assertIsNotNone(datetime.fromisoformat(row['timestamp']).utcoffset())
                    self.assertEqual('CSM0_Mezz0_AVDD_display_V' in row, mezz_enabled)
                    self.assertEqual('CSM1_Mezz20_AVDD_display_V' in row, mezz_enabled)
                    self.assertEqual('CSM0_SCA_VDD2V5_display_V' in row, csm_enabled)
                    self.assertEqual('CSM1_lpGBT_slave_115_VTRX_Temp_display_C' in row, csm_enabled)
                    self.assertNotIn('CSM0_Mezz1_AVDD_display_V', row)
                    if mezz_enabled:
                        self.assertEqual(row['CSM0_Mezz0_AVDD_display_V'], '2.850')
                        for label in ('AVDD', 'DVDD', 'Temp'):
                            self.assertEqual(row[f'CSM0_Mezz0_{label}_signal_raw_adc'], '2048')
                            self.assertEqual(row[f'CSM0_Mezz0_{label}_ground_reference_raw_adc'], '2048')
                            self.assertNotIn(f'CSM0_Mezz0_{label}_raw_adc', row)
                    if csm_enabled:
                        self.assertEqual(row['CSM0_SCA_VDD2V5_display_V'], '2.850')
                if mezz_enabled and csm_enabled:
                    self.assertLess(columns.index('CSM1_Mezz20_Temp_display_C'),
                                    columns.index('CSM0_SCA_VDD2V5_display_V'))
                self.assertIsNone(worker.monitor_csv._file)
                self.assertEqual(list(self.path.parent.iterdir()), [self.path])
                worker.deleteLater()
                self.path.unlink()

    def test_next_scan_wait_includes_duration_and_initializes_each_csm_once(self):
        worker = Worker_Monitor(self.controller)
        clock = FakeClock()
        worker.stop_requested = clock
        real_scan = worker._scan
        def scan(index):
            real_scan(index)
            clock.now += 10
            if index >= 2:
                worker.stop()
        with self.hardware(), patch('Worker_Monitor.time.monotonic', lambda: clock.now), patch.object(
            worker, '_scan', scan
        ), patch.object(worker.mezz_reader, 'initialize_csm') as initialize:
            worker.run()
        self.assertEqual(clock.waits, [0, 50])
        self.assertEqual([call.args[0] for call in initialize.call_args_list], [0, 1])
        worker.deleteLater()

    def test_selected_second_csm_is_initialized_once_for_either_or_both_readers(self):
        self.controller.mezz.select_scanned_mezz([(1, 0)])
        self.controller.csm.checkbox_list[0].setChecked(False)
        for mezz, csm in ((True, False), (False, True), (True, True)):
            with self.subTest(mezz=mezz, csm=csm):
                self.controller.csv_path = self.path.with_name(f'{mezz}_{csm}.csv')
                self.controller.checkBox_monitor_mezz.setChecked(mezz)
                self.controller.checkBox_monitor_csm.setChecked(csm)
                worker = Worker_Monitor(self.controller)
                worker.interval_seconds = 0
                with self.hardware(scans=1), patch('monitor_readers.SCA_connect') as connect:
                    worker.run()
                connect.assert_called_once()
                self.assertEqual(connect.call_args.kwargs['which_csm'], 1)
                for reader in (worker.mezz_reader, worker.csm_reader):
                    if reader is not None:
                        self.assertFalse(hasattr(reader, 'monitor_csv'))
                        self.assertFalse(hasattr(reader, 'run'))
                        self.assertFalse(hasattr(reader, 'stop'))
                self.assertFalse(any(name.startswith('CSM0_') for name in self.rows()[0]))
                worker.deleteLater()

    def test_combined_worker_closes_its_only_csv_and_emits_finished_after_error(self):
        worker = Worker_Monitor(self.controller)
        messages, finished = [], []
        worker.message_out.connect(messages.append)
        worker.finished.connect(lambda: finished.append(True))
        def failing_scan(index):
            worker.monitor_csv.write_row({'scan': index, 'timestamp': 'test'})
            worker.mezz_reader.current_scan_row = {}
            worker.csm_reader.current_scan_row = {}
            raise RuntimeError('connection lost')
        with patch.object(worker, '_scan', failing_scan):
            worker.run()
        self.assertEqual(finished, [True])
        self.assertIn('Monitoring failed: connection lost', messages)
        self.assertIsNone(worker.monitor_csv._file)
        self.assertIsNone(worker.monitor_csv.message)
        self.assertIsNone(worker.mezz_reader.current_scan_row)
        self.assertIsNone(worker.csm_reader.current_scan_row)
        self.assertEqual(len(self.rows()[1]), 1)
        worker.deleteLater()

    def test_partial_failures_are_na_and_do_not_discard_other_targets(self):
        worker = Worker_Monitor(self.controller)
        worker.interval_seconds = 0
        real_scan = worker.csm_reader.scan_csm
        def scan(index, csm):
            if index == 1 and csm == 0:
                raise RuntimeError('no Ethernet reply')
            real_scan(index, csm)
        messages = []
        worker.message_out.connect(messages.append)
        with self.hardware(), patch.object(worker.csm_reader, 'scan_csm', scan):
            worker.run()
        columns, rows = self.rows()
        self.assertEqual(rows[0]['CSM0_SCA_VDD2V5_display_V'], '2.850')
        self.assertEqual(rows[1]['CSM0_SCA_VDD2V5_display_V'], 'NA')
        self.assertEqual(rows[1]['CSM1_SCA_VDD2V5_display_V'], '2.850')
        self.assertEqual(rows[1]['CSM0_Mezz0_AVDD_display_V'], '2.850')
        self.assertEqual(worker.csm_reader.display_values.take()[0, -1, 0], 'NA')
        self.assertTrue(any('no Ethernet reply' in message for message in messages))
        worker.deleteLater()

    def test_threaded_run_updates_both_displays_and_restores_controls(self):
        self.controller.interval.setValue(0)
        with self.hardware():
            self.controller.start()
            self.assertFalse(self.controller.mezz_test_button.isEnabled())
            self.assertFalse(self.controller.csm_test_button.isEnabled())
            self.assertFalse(self.controller.checkBox_monitor_csm.isEnabled())
            self.wait_for(lambda: self.controller.worker is None)
        self.assertEqual(self.controller.mezz.cell_list[0][0].label_list[0].text(), '2.850')
        self.assertEqual(self.controller.csm.cell_list[0].SCA_temp_value_widget[0].text(), '2.850 V')
        self.assertIn('color: red', self.controller.csm.cell_list[0].SCA_temp_value_widget[0].styleSheet())
        self.assertTrue(self.controller.start_button.isEnabled())
        self.assertTrue(self.controller.mezz_test_button.isEnabled())
        self.assertTrue(self.controller.csm_test_button.isEnabled())
        self.assertFalse(self.controller.timer.isActive())
        self.assertEqual(len(self.rows()[1]), 2)

    def test_stop_interrupts_wait_finishes_single_combined_row(self):
        with self.hardware():
            self.controller.start()
            self.wait_for(lambda: 'Completed scan 1' in self.controller.status.text())
            self.controller.stop()
            self.wait_for(lambda: self.controller.worker is None)
        self.assertEqual(len(self.rows()[1]), 1)
        self.assertTrue(self.controller.start_button.isEnabled())

    def test_main_window_close_waits_for_current_full_scan_and_csv(self):
        from GUI_DAQ_init import StartQT5
        entered = threading.Event()
        real_scan = Worker_Monitor._scan
        def delayed_scan(worker, index):
            entered.set()
            worker.stop_requested.wait(2)
            real_scan(worker, index)
        window = SimpleNamespace(ui=SimpleNamespace(tab_monitor_inst=self.controller), close=Mock())
        event = Mock()
        with self.hardware(), patch.object(Worker_Monitor, '_scan', delayed_scan):
            self.controller.start()
            self.wait_for(entered.is_set)
            StartQT5.closeEvent(window, event)
            event.ignore.assert_called_once()
            self.wait_for(lambda: self.controller.worker is None)
            self.app.processEvents()
        window.close.assert_called_once()
        columns, rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['CSM0_Mezz0_AVDD_display_V'], '2.850')
        self.assertEqual(rows[0]['CSM0_SCA_VDD2V5_display_V'], '2.850')

    def test_empty_selection_is_rejected_and_disabled_sources_skip_validation(self):
        self.controller.checkBox_monitor_mezz.setChecked(False)
        self.controller.checkBox_monitor_csm.setChecked(False)
        with patch('tab_monitor.QtWidgets.QMessageBox.information') as info:
            self.controller.start()
        info.assert_called_once()
        self.assertIsNone(self.controller.worker)
        self.assertFalse(self.path.exists())
        self.controller.checkBox_monitor_csm.setChecked(True)
        self.controller.mezz.select_scanned_mezz([])
        self.controller.interval.setValue(0)
        with self.hardware():
            self.controller.start()
            self.wait_for(lambda: self.controller.worker is None)
        self.assertFalse(any('_Mezz' in name for name in self.rows()[0]))

    def test_range_dialogs_apply_in_memory_and_common_file_roundtrip(self):
        ini = self.path.with_suffix('.ini')
        for chip in (-1, 0, 1):
            with patch('tab_monitor.CSMLimitsDialog') as dialog:
                dialog.return_value.exec_.return_value = QtWidgets.QDialog.Accepted
                dialog.return_value.changes.return_value = {}
                self.controller.csm_limits_dialog(chip)
                metrics = dialog.call_args.args[0]
                self.assertTrue(metrics)
                self.assertTrue(all(metric[0][1] == chip for metric in metrics))
                self.assertFalse(dialog.call_args.kwargs['persist'])
        expected = {'AVDD': (2.8, 3.2), 'DVDD': (1.0, 1.4), 'Temp': (21, 49)}
        with patch('tab_monitor.QtWidgets.QDialog.exec_', return_value=QtWidgets.QDialog.Accepted), patch(
            'tab_monitor.MonitorLimitsWidget.values', return_value=expected
        ):
            self.controller.mezz_limits_dialog()
        self.assertFalse(ini.exists())
        self.assertEqual(self.controller.mezz.get_monitor_limits(), expected)

        with patch('tab_monitor.QtWidgets.QFileDialog.getSaveFileName', return_value=(str(ini), '')):
            self.controller.save_ranges()
        self.assertEqual(load_mezz_limits(ini), expected)
        self.assertTrue(load_csm_limits(self.controller.csm._monitor_metrics(), ini))
        self.controller.mezz.monitor_limits.set_values({'Temp': (0, 100)})
        with patch('tab_monitor.QtWidgets.QFileDialog.getOpenFileName', return_value=(str(ini), '')):
            self.controller.load_ranges()
        self.assertEqual(self.controller.mezz.get_monitor_limits(), expected)

    def test_folder_selection_unique_timestamped_runs_and_seconds(self):
        folder = Path(self.directory.name) / 'selected folder'
        with patch('tab_monitor.QtWidgets.QFileDialog.getExistingDirectory', return_value=str(folder)):
            self.controller.browse_csv_directory()
        self.assertEqual(self.controller.csv_directory(), folder)
        self.assertEqual(self.controller.get_monitor_interval_seconds(), 60)
        self.assertFalse(hasattr(self.controller, 'count_limit'))
        self.assertFalse(hasattr(self.controller, 'count'))
        self.controller.interval.setValue(1.5)
        self.assertEqual(self.controller.get_monitor_interval_seconds(), 1.5)
        self.controller.interval.setValue(0)
        paths = []
        with patch('tab_monitor.datetime') as clock:
            clock.now.return_value = datetime(2026, 10, 21, 12, 30, 15, 123456)
            with self.hardware(scans=1):
                for _ in range(2):
                    self.controller.start()
                    self.wait_for(lambda: self.controller.worker is None)
                    paths.append(self.controller.csv_path)
        self.assertEqual(paths[0].name, 'monitor_20261021_123015_123456.csv')
        self.assertEqual(paths[1].name, 'monitor_20261021_123015_123456_1.csv')
        self.assertNotEqual(paths[0], paths[1])
        for path in paths:
            self.assertEqual(path.parent, folder)
            with path.open(newline='') as source:
                self.assertEqual(len(list(csv.DictReader(source))), 1)

    def test_invalid_range_import_does_not_change_any_current_range(self):
        ini = self.path.with_suffix('.ini')
        ini.write_text('[CSM.defaults]\nVDD2V5 = 0, 10\n[Mezz]\nTemp = 50,20\n')
        previous_csm = dict(self.controller.csm._monitor_limits)
        previous_mezz = self.controller.mezz.get_monitor_limits()
        with patch('tab_monitor.QtWidgets.QFileDialog.getOpenFileName', return_value=(str(ini), '')), patch(
            'tab_monitor.QtWidgets.QMessageBox.warning'
        ) as warning:
            self.controller.load_ranges()
        warning.assert_called_once()
        self.assertEqual(self.controller.csm._monitor_limits, previous_csm)
        self.assertEqual(self.controller.mezz.get_monitor_limits(), previous_mezz)

    def test_csm_range_dialog_has_apply_and_no_save_button(self):
        from csm_monitor_limits import CSMLimitsDialog
        dialog = CSMLimitsDialog(self.controller.csm._monitor_metrics(), {},
                                 self.controller.csm._monitor_limits, persist=False)
        texts = [button.text().replace('&', '') for button in dialog.findChildren(QtWidgets.QPushButton)]
        self.assertIn('Apply', texts)
        self.assertNotIn('Save', texts)
        dialog.close()

    def test_many_scans_keep_only_latest_gui_values_and_stream_csv(self):
        worker = Worker_Monitor(self.controller)
        worker.interval_seconds = 0
        samples = []
        write = worker.monitor_csv.write_row
        def write_row(row):
            write(row)
            if row['scan'] in (100, 1000):
                gc.collect()
                samples.append(tracemalloc.get_traced_memory()[0])
        tracemalloc.start()
        try:
            with self.hardware(scans=1000), patch.object(worker.monitor_csv, 'write_row', write_row):
                worker.run()
            self.assertLess(samples[1] - samples[0], 256 * 1024)
        finally:
            tracemalloc.stop()
        self.assertEqual(len(self.rows()[1]), 1000)
        self.assertEqual(len(worker.display_values.take()), 8)
        self.assertEqual(len(worker.csm_reader.display_values.take()), 42)
        self.assertIsNone(worker.mezz_reader.current_scan_row)
        self.assertIsNone(worker.csm_reader.current_scan_row)
        worker.deleteLater()


if __name__ == '__main__':
    unittest.main()
