import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5 import QtWidgets

from monitor_limits_ini import load_csm_limits, save_csm_limits
from tab_csm import tab_csm


class MonitorLimitsIniTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_defaults_overrides_and_atomic_roundtrip(self):
        metrics = [((0, 0, 0), 'CSM0 master VSSA', 'V', ''),
                   ((0, 1, 0), 'CSM0 slave VSSA', 'V', ''),
                   ((1, -1, 2), 'CSM1 SCA0_Temp', 'C', '')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'limits.ini'
            path.write_text('[CSM.defaults]\nVSSA = 0, 0.1\nSCA_temp = 25,45\n'
                            '[other]\nkeep = yes\n[CSM0.master]\nvssa = 0,0.2\n')
            limits = load_csm_limits(metrics, path)
            self.assertEqual(limits, {(0, 0, 0): (0, .2), (0, 1, 0): (0, .1),
                                      (1, -1, 2): (25, 45)})
            limits[0, 1, 0] = (-.01, .15)
            save_csm_limits(metrics, limits, path)
            self.assertEqual(load_csm_limits(metrics, path), limits)
            self.assertIn('keep = yes', path.read_text())
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_invalid_and_missing_settings_fall_back(self):
        metrics = [((0, 0, 0), 'CSM0 master VSSA', 'V', '')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'limits.ini'
            self.assertEqual(load_csm_limits(metrics, path), {})
            for value in ('nan, 1', '2, 1', 'not a range', '0, inf'):
                path.write_text(f'[CSM0.master]\nvssa = {value}\n')
                self.assertEqual(load_csm_limits(metrics, path), {})
            path.write_text('malformed INI')
            self.assertEqual(load_csm_limits(metrics, path), {})
            with self.assertRaises(Exception):
                save_csm_limits(metrics, {(0, 0, 0): (0, .1)}, path)
            self.assertEqual(path.read_text(), 'malformed INI')

    def test_gui_save_restores_custom_limits_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'limits.ini'
            with patch('tab_csm.MONITOR_LIMITS_INI', path):
                host = QtWidgets.QWidget()
                monitor = tab_csm(host, object())
                monitor.lineEdit_CSM_csv.setText(str(Path(directory) / 'missing.csv'))
                with patch('tab_csm.CSMLimitsDialog') as factory:
                    factory.return_value.exec_.return_value = QtWidgets.QDialog.Accepted
                    factory.return_value.changes.return_value = {(0, -1, 0): (2.3, 2.7)}
                    monitor.monitor_limits_dialog()
                self.assertTrue(path.exists())
                other_host = QtWidgets.QWidget()
                restored = tab_csm(other_host, object())
                restored.lineEdit_CSM_csv.setText(str(Path(directory) / 'missing.csv'))
                restored._prepare_monitor_limits()
                self.assertEqual(restored._monitor_limits[0, -1, 0], (2.3, 2.7))
                self.assertEqual(restored._monitor_limits[0, 0, 0], (0, .1))
                other_host.close()
                host.close()


if __name__ == '__main__':
    unittest.main()
