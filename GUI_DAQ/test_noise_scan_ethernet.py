"""Noise scan startup and run logging use only the selected Ethernet interface."""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PyQt5 import QtWidgets
from tab_capture import tab_capture
from pop_noise_scan import NOISE_SCAN_TRIGGERED, NOISE_SCAN_TRIGGERLESS_RAW, NOISE_SCAN_TRIGGERLESS_COUNT


class NoiseScanEthernetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_each_noise_mode_starts_and_logs_without_usb_device_api(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            'tab_capture.SETTINGS_FILE', str(Path(directory) / 'settings.ini')
        ), patch('tab_capture.pcapy.findalldevs', return_value=[]):
            host = QtWidgets.QWidget()
            capture = tab_capture(host)
            self.assertFalse(hasattr(capture, 'current_usb_device'))
            capture.combo_iface.addItem('test-ethernet')
            capture.backend = SimpleNamespace(prepare_run_log=Mock(return_value='run.log'), start_capture=Mock())
            scan = capture.noise_scan
            scan._scan_active = True
            scan._values = [120]
            scan._current_threshold = 120
            scan._current_hyst = 7
            scan._selected_mezz = [(0, 0)]
            scan._active_channels = {0: [0]}
            scan._output_dir = directory
            with ExitStack() as stack:
                stack.enter_context(patch.object(scan, '_configure_asd_setting', return_value=True))
                stack.enter_context(patch.object(scan, '_apply_minidaq_noise_scan_setup', return_value=True))
                stack.enter_context(patch.object(scan, '_file_stem', return_value='noise'))
                stack.enter_context(patch.object(scan, '_start_hardware_run', return_value=True))
                for mode in (NOISE_SCAN_TRIGGERED, NOISE_SCAN_TRIGGERLESS_RAW, NOISE_SCAN_TRIGGERLESS_COUNT):
                    with self.subTest(mode=mode):
                        scan._noise_acquisition_mode = mode
                        capture.backend.prepare_run_log.reset_mock()
                        capture.backend.start_capture.reset_mock()
                        try:
                            scan._start_next_point()
                        finally:
                            scan._timer.stop()
                        context = capture.backend.prepare_run_log.call_args.kwargs['context']
                        self.assertEqual(context['ethernet_device'], 'test-ethernet')
                        self.assertNotIn('usb_device', context)
                        capture.backend.start_capture.assert_called_once()
                        self.assertEqual(capture.backend.start_capture.call_args.args[0], 'test-ethernet')
            scan._scan_active = False
            host.close()


if __name__ == '__main__':
    unittest.main()
