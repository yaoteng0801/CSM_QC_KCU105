import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5 import QtWidgets
from csm_monitor_limits import default_bounds, latest_csv_values, CSMLimitsDialog
from monitor_display_buffer import MonitorDisplayBuffer
from tab_csm import tab_csm


class CSMMonitorSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_specified_default_ranges(self):
        expected = {
            'VDD2V5': (2.4, 2.6), 'VDD1V2': (1.1, 1.3),
            'SCA_temp': (20, 60), 'VSSA': (0, 0.1),
            'VDDTX': (1.1, 1.3), 'VDDRX': (1.1, 1.3),
            'VDD': (1.1, 1.3), 'VDDA': (1.1, 1.3),
            'temp': (20, 60), 'VREF': (0.45, 0.55), 'VTRX_Temp': (20, 60),
        }
        expected.update({f'SCA{i}_Temp': (20, 60) for i in range(4)})
        for label, bounds in expected.items():
            with self.subTest(label=label):
                self.assertEqual(default_bounds(label), bounds)

    def test_defaults_without_previous_results_apply_to_both_chips(self):
        host = QtWidgets.QWidget()
        monitor = tab_csm(host, object())
        with tempfile.TemporaryDirectory() as directory:
            monitor.lineEdit_CSM_csv.setText(str(Path(directory) / 'missing.csv'))
            monitor._prepare_monitor_limits()
            for key, name, unit, column in monitor._monitor_metrics():
                bounds = default_bounds(name.rsplit(' ', 1)[-1])
                self.assertIsNotNone(bounds, name)
                self.assertEqual(monitor._monitor_limits[key], bounds)
            for csm in range(len(monitor.cell_list)):
                for index in range(7):
                    self.assertEqual(monitor._monitor_limits[csm, 0, index],
                                     monitor._monitor_limits[csm, 1, index])
        host.close()

    def test_load_latest_completed_csv_row_with_bounded_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'csm.csv'
            column = 'CSM0_SCA_VDD2V5_display_V'
            with path.open('w', newline='') as target:
                writer = csv.writer(target)
                writer.writerow(['scan', column])
                for index in range(20000):
                    writer.writerow([index, 2.5 if index < 19999 else 2.6])
            with path.open('a') as target:
                target.write('20000,9')  # An incomplete next scan must be ignored.
            self.assertEqual(latest_csv_values(path), {column: 2.6})

    def test_limits_ignore_previous_result_remain_fixed_and_allow_overrides(self):
        host = QtWidgets.QWidget()
        monitor = tab_csm(host, object())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'csm.csv'
            path.write_text('scan,CSM0_SCA_VDD2V5_display_V\n1,2.5\n')
            monitor.lineEdit_CSM_csv.setText(str(path))
            monitor._prepare_monitor_limits()
            key = (0, -1, 0)
            self.assertEqual(monitor._monitor_limits[key], (2.4, 2.6))
            monitor._monitor_values = MonitorDisplayBuffer()
            monitor._monitor_values.put(key, '3.500 V')
            monitor._flush_monitor_display()
            self.assertEqual(monitor._monitor_limits[key], (2.4, 2.6))
            self.assertIn('color: red', monitor.cell_list[0].SCA_temp_value_widget[0].styleSheet())
            # An abnormal latest result must not move the next run's limits.
            monitor._prepare_monitor_limits()
            self.assertEqual(monitor._monitor_limits[key], (2.4, 2.6))
            monitor._monitor_limits[key] = (1, 4)
            monitor._custom_monitor_limits.add(key)
            monitor._prepare_monitor_limits()
            self.assertEqual(monitor._monitor_limits[key], (1, 4))
            monitor._monitor_values.put(key, '3.500 V')
            monitor._flush_monitor_display()
            self.assertNotIn('color: red', monitor.cell_list[0].SCA_temp_value_widget[0].styleSheet())
            dialog = CSMLimitsDialog(monitor._monitor_metrics(), monitor._latest_monitor_values,
                                     monitor._monitor_limits)
            self.assertEqual(dialog.changes(), {})
            low, high, original, shown = dialog.editors[key]
            high.setValue(5)
            self.assertEqual(dialog.changes()[key], (1, 5))
            dialog.close()
        host.close()



if __name__ == '__main__':
    unittest.main()
