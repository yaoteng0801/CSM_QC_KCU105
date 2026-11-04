import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets

from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS, MonitorLimitsWidget, range_error
from tab_sca import tab_sca
from monitor_readers import MezzMonitorReader


class MezzMonitorLimitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_defaults_and_inclusive_bounds(self):
        editor = MonitorLimitsWidget()
        self.assertEqual(editor.values(), {"AVDD": (2.9, 3.1), "DVDD": (1.1, 1.3), "Temp": (20, 60)})
        for label, (low, high) in DEFAULT_MONITOR_LIMITS.items():
            for value in (low, (low + high) / 2, high):
                self.assertIsNone(range_error(label, value, editor.values()))
            for value in (low - 0.001, high + 0.001, None, float("nan")):
                self.assertIsNotNone(range_error(label, value, editor.values()))
        editor.close()

    def test_editors_keep_limits_ordered(self):
        editor = MonitorLimitsWidget()
        low, high = editor.editors["AVDD"]
        high.setValue(3.6)
        low.setValue(3.2)
        self.assertEqual(editor.values()["AVDD"], (3.2, 3.6))
        self.assertIsNone(range_error("AVDD", 3.35, editor.values()))
        low.setValue(4)
        self.assertLessEqual(low.value(), high.value())
        editor.close()

    def test_csv_keeps_available_ground_code_when_signal_read_fails(self):
        from SCA_share import SCA_share
        host = QtWidgets.QWidget()
        controller = tab_sca(host, object())
        worker = MezzMonitorReader(controller)
        worker.current_scan_row = {}
        selected = {}
        signal_mux = worker.df['0']['AVDD']
        def config(*args, **kwargs):
            if kwargs['command'] == SCA_share.ADC_W_MUX:
                selected['mux'] = kwargs['data']
            elif kwargs['command'] == SCA_share.ADC_GO and selected['mux'] == signal_mux:
                raise RuntimeError('signal ADC read failed')
            return [SCA_share.ADC_CHANNEL, 0, 81]
        with patch('monitor_readers.SCA_config', config):
            worker.scan_mezz(0)
        self.assertEqual(worker.current_scan_row['CSM0_Mezz0_AVDD_signal_raw_adc'], 'NA')
        self.assertEqual(worker.current_scan_row['CSM0_Mezz0_AVDD_ground_reference_raw_adc'], 81)
        self.assertEqual(worker.current_scan_row['CSM0_Mezz0_AVDD_display_V'], 'NA')
        worker.deleteLater()
        host.close()

    def test_normal_scan_highlights_and_clears_red_using_snapshot_limits(self):
        host = QtWidgets.QWidget()
        controller = tab_sca(host, object())
        with patch("monitor_readers.pd.read_csv", return_value=Mock()):
            worker = MezzMonitorReader(controller)
        worker.display_update.connect(controller.apply_monitor_reading)
        label = controller.cell_list[0][0].label_list[0]
        worker.update_display_item(0, 0, "AVDD", "V", (1, 2), 3.2)
        self.assertEqual(label.text(), "3.200")
        self.assertIn("color: red", label.styleSheet())
        worker.update_display_item(0, 0, "AVDD", "V", (1, 2), 3.0)
        self.assertEqual(label.styleSheet(), "")
        worker.update_display_item(0, 0, "AVDD", "V", (None, None), None)
        self.assertEqual(label.text(), "NA")
        self.assertIn("color: red", label.styleSheet())
        worker.update_display_item(0, 2, "Temp", "C", (1, 2), 110.0)
        self.assertEqual(controller.cell_list[0][0].label_list[2].text(), "110.000")
        self.assertIn("color: red", controller.cell_list[0][0].label_list[2].styleSheet())
        host.close()


if __name__ == "__main__":
    unittest.main()
