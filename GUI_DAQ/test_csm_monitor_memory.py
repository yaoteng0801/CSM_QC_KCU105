import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import csv
import gc
import tempfile
import tracemalloc
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PyQt5 import QtCore, QtWidgets
from monitor_readers import CSMMonitorReader
from monitor_display_buffer import MonitorDisplayBuffer
from tab_csm import tab_csm


class NoWorkerWidget:
    def setText(self, text):
        raise AssertionError('Worker touched a GUI widget')


class CSMMonitorMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_full_scan_loop_has_bounded_memory_with_gui_not_consuming_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'csm.csv'
            def cell():
                return SimpleNamespace(
                    SCA_temp_label=['V0', 'V1', 'Temp'], SCA_temp_unit=['V', 'V', 'C'],
                    SCA_mapping=[1, 2, 4], SCA_ADC_input=[1, 2, 31],
                    SCA_temp_value_widget=[NoWorkerWidget() for _ in range(3)],
                    lpGBT_list=[SimpleNamespace(
                        address=address, lpGBT_monitor_index=[1, 14],
                        lpGBT_monitor_ADCmon=[0, 32], lpGBT_monitor_label=['OpticalTemp', 'InternalTemp'],
                        lpGBT_monitor_unit=['C', 'C'],
                        lpGBT_monitor_value_widget=[NoWorkerWidget(), NoWorkerWidget()],
                    ) for address in (117, 118)],
                )
            tab = SimpleNamespace(
                eth=object(), get_csv_filename=lambda: str(path), get_scan_count=lambda: 2000,
                get_transID=lambda: 1, CSM_count=2,
                checkbox_list=[SimpleNamespace(isChecked=lambda: True) for _ in range(2)],
                cell_list=[cell(), cell()],
            )
            worker = CSMMonitorReader(tab)
            samples = []
            tracemalloc.start()
            try:
                with patch('monitor_readers.SCA_connect', lambda *a, **kw: None), patch(
                    'monitor_readers.SCA_config', lambda *a, **kw: [20, 0, 2048]
                ), patch('monitor_readers.lpgbt_config_write', lambda *a, **kw: [2, 0]), patch.object(
                    worker, 'get_lpgbt_calibration', lambda *a: None
                ):
                    for scan in range(2000):
                        worker.current_scan_row = {}
                        for csm in range(2):
                            worker.scan_csm(scan, csm)
                        if scan in (99, 1999):
                            gc.collect()
                            samples.append(tracemalloc.get_traced_memory()[0])
                self.assertEqual(len(samples), 2)
                self.assertLess(samples[1] - samples[0], 256 * 1024)
            finally:
                tracemalloc.stop()
                worker.current_scan_row = None
            # Thousands of scans leave exactly one latest value per widget.
            values = worker.display_values.take()
            self.assertEqual(len(values), 14)
            self.assertEqual(values[(0, -1, 0)], '2.850 V')
            self.assertEqual(worker.display_values.take(), {})

    def test_gui_applies_latest_values_and_releases_finished_worker(self):
        host = QtWidgets.QWidget()
        monitor = tab_csm(host, object())
        monitor._monitor_values = MonitorDisplayBuffer()
        for index in range(10000):
            monitor._monitor_values.put((0, -1, 0), f'{index} V')
            monitor._monitor_values.put((0, 0, 0), f'{index} C')
        monitor._flush_monitor_display()
        self.assertEqual(monitor.cell_list[0].SCA_temp_value_widget[0].text(), '9999 V')
        self.assertEqual(monitor.cell_list[0].lpGBT_list[0].lpGBT_monitor_value_widget[0].text(), '9999 C')
        host.close()



if __name__ == '__main__':
    unittest.main()
