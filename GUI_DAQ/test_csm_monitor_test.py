import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5 import QtWidgets
from tab_csm import tab_csm
from pop_csm_monitor_test import CSMMonitorTestDialog, CSMMonitorTestWorker
from SCA_share import SCA_share


class CSMMonitorDebugTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.host = QtWidgets.QWidget()
        self.controller = tab_csm(self.host, object())
        self.path = Path(self.directory.name) / 'normal.csv'
        self.path.write_text('existing normal results\n')
        self.controller.lineEdit_CSM_csv.setText(str(self.path))
        self.controller._prepare_monitor_limits()

    def tearDown(self):
        self.host.close()
        self.directory.cleanup()

    def values(self, csm):
        return {key: sum(self.controller._monitor_limits[key]) / 2
                for key, name, unit, col in self.controller._monitor_metrics() if key[0] == csm}

    def test_range_failures_missing_values_and_retries(self):
        worker = CSMMonitorTestWorker(self.controller, [0])
        with patch.object(worker.reader, 'initialize_csm'), patch.object(worker.reader, 'scan_csm') as scan:
            def good(*args):
                worker.reader.values.update(self.values(0))
            scan.side_effect = good
            self.assertTrue(worker._test(0)[1])
            # Exact limits pass; compare unrounded values to catch slight excursions.
            def outside(*args):
                good()
                worker.reader.values[0, -1, 0] = 2.60001
                worker.reader.values[0, 1, 0] = float('nan')
            scan.side_effect = outside
            values, valid, detail = worker._test(0)
            self.assertFalse(valid)
            self.assertIn('VDD2V5', detail)
            self.assertIn('no valid reading', detail)
            scan.side_effect = lambda *args: None
            self.assertFalse(worker._test(0)[1])  # Previous good readings cannot hide missing ones.
            def recovered(*args):
                good()
                worker.notes.append('retrying with a fresh transaction ID')
            scan.side_effect = recovered
            self.assertTrue(worker._test(0)[1])
            self.assertIn('retrying', worker._test(0)[2])
        self.assertEqual(self.path.read_text(), 'existing normal results\n')
        worker.deleteLater()

    def test_adc_status_and_command_failures(self):
        worker = CSMMonitorTestWorker(self.controller, [0])
        reader = worker.reader
        reader.validate_sca_adc(SCA_share.ADC_CHANNEL, 0, 4095)
        reader.validate_lpgbt_adc(0, 1, 1023)
        for args in ((0, 0, 100), (SCA_share.ADC_CHANNEL, 1, 100),
                     (SCA_share.ADC_CHANNEL, 0, 4096)):
            with self.assertRaises(RuntimeError):
                reader.validate_sca_adc(*args)
        for args in ((1, 1, 100), (0, 0, 100), (0, 1, 1024)):
            with self.assertRaises(RuntimeError):
                reader.validate_lpgbt_adc(*args)
        with patch.object(reader, 'initialize_csm', side_effect=RuntimeError('no Ethernet reply')):
            values, valid, detail = worker._test(0)
        self.assertFalse(valid)
        self.assertIn('no Ethernet reply', detail)
        worker.deleteLater()

    def wait_for(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertTrue(condition())

    def test_dialog_lifecycle_counts_one_error_and_bounds_history(self):
        dialog = CSMMonitorTestDialog(self.controller, [0, 1])
        attempts = []
        def one_test(worker, csm):
            attempts.append(csm)
            worker.stop()  # Complete one test before each pause.
            values = self.values(csm)
            values[csm, -1, 0] = 9
            values[csm, 0, 0] = 9
            return values, False, 'two values outside range'
        with patch.object(CSMMonitorTestWorker, '_test', one_test):
            dialog.start()
            self.wait_for(lambda: dialog.worker is None)
            self.assertEqual(dialog.counts[0], [1, 1])
            self.assertEqual(dialog.counts[1], [0, 0])
            self.assertTrue(dialog.continue_button.isEnabled())
            self.assertIn('color: red', self.controller.cell_list[0].SCA_temp_value_widget[0].styleSheet())
            dialog.continue_test()
            self.wait_for(lambda: dialog.worker is None)
            self.assertEqual(attempts, [0, 1])
            self.assertEqual(dialog.totals.text(), 'Total: 2 tests, 2 errors')
            for index in range(300):
                dialog.error_history.appendPlainText(str(index))
            self.assertLessEqual(dialog.error_history.document().blockCount(), 200)
            dialog.reset()
            self.assertEqual(dialog.counts, {0: [0, 0], 1: [0, 0]})
            self.assertFalse(dialog.continue_button.isEnabled())
            dialog.start()
            self.wait_for(lambda: dialog.worker is None)
            self.assertEqual(attempts[-1], 0)
        dialog.reject()

    def test_close_waits_for_running_test(self):
        dialog = CSMMonitorTestDialog(self.controller, [0])
        def wait_for_stop(worker, csm):
            worker.stop_requested.wait(2)
            return self.values(csm), True, ''
        with patch.object(CSMMonitorTestWorker, '_test', wait_for_stop):
            dialog.start()
            dialog.reject()
            self.assertEqual(dialog.pending_action, 'close')
            self.wait_for(lambda: dialog.worker is None)
            self.assertEqual(dialog.result(), QtWidgets.QDialog.Rejected)


if __name__ == '__main__':
    unittest.main()
