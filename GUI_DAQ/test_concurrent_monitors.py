import csv
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from monitor_readers import CSMMonitorReader, MezzMonitorReader
from SCA_share import SCA_share


class ConcurrentMonitorTests(unittest.TestCase):
    def test_csm_cannot_change_mux_during_mezz_adc_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            eth = object()
            common = dict(eth=eth, get_scan_count=lambda: 1, get_transID=lambda: 1)
            mezz_path, csm_path = Path(directory) / 'mezz.csv', Path(directory) / 'csm.csv'
            mezz = MezzMonitorReader(SimpleNamespace(
                **common, get_csv_filename=lambda: str(mezz_path), mezz_enable='1',
                CSM_count=1, mezz_per_CSM=20,
                cell_list=[[SimpleNamespace(value_list=[0] * 6)]],
            ))
            csm = CSMMonitorReader(SimpleNamespace(
                **common, get_csv_filename=lambda: str(csm_path), CSM_count=1,
                checkbox_list=[SimpleNamespace(isChecked=lambda: True)],
                cell_list=[SimpleNamespace(
                    SCA_temp_label=['Supply'], SCA_temp_unit=['V'],
                    SCA_mapping=[1], SCA_ADC_input=[31],
                    lpGBT_list=[SimpleNamespace(
                        address=address, lpGBT_monitor_label=[], lpGBT_monitor_index=[]
                    ) for address in (117, 118)],
                )],
            ))
            selected_mux = {}
            expected_mux = threading.local()
            first_mux = threading.Event()
            release_conversion = threading.Event()
            csm_started = threading.Event()
            csm_done = threading.Event()
            violations = []

            def config(eth, **kwargs):
                if kwargs['channel'] != SCA_share.ADC_CHANNEL:
                    return [kwargs['channel'], 0, 0]
                key = (kwargs['which_csm'], kwargs['sca_enable'])
                if kwargs['command'] == SCA_share.ADC_W_MUX:
                    selected_mux[key] = kwargs['data']
                    expected_mux.value = kwargs['data']
                    if threading.current_thread().name == 'mezz-reader' and not first_mux.is_set():
                        first_mux.set()
                        if not release_conversion.wait(2):
                            raise RuntimeError('Test conversion release timed out')
                elif kwargs['command'] == SCA_share.ADC_GO:
                    if selected_mux[key] != expected_mux.value:
                        violations.append((selected_mux[key], expected_mux.value))
                    return [SCA_share.ADC_CHANNEL, 0, selected_mux[key]]
                return [kwargs['channel'], 0, 0]

            def run_csm():
                csm_started.set()
                try:
                    csm.scan_csm(0, 0)
                finally:
                    csm_done.set()

            with patch('monitor_readers.SCA_connect', lambda *a, **kw: None), patch(
                'monitor_readers.SCA_connect', lambda *a, **kw: None
            ), patch('monitor_readers.SCA_config', config), patch('monitor_readers.SCA_config', config), patch(
                'monitor_readers.lpgbt_config_write', lambda *a, **kw: [2, 0]
            ), patch.object(csm, 'get_lpgbt_calibration', lambda *a: None):
                mezz.current_scan_row = {}
                csm.current_scan_row = {}
                mezz_thread = threading.Thread(target=lambda: mezz.scan_mezz(0), name='mezz-reader')
                csm_thread = threading.Thread(target=run_csm, name='csm-reader')
                mezz_thread.start()
                try:
                    self.assertTrue(first_mux.wait(2))
                    csm_thread.start()
                    self.assertTrue(csm_started.wait(2))
                    self.assertFalse(csm_done.wait(0.1), 'CSM interleaved a paused mezz measurement')
                    release_conversion.set()
                    mezz_thread.join(2)
                    csm_thread.join(2)
                finally:
                    release_conversion.set()
                    mezz_thread.join(2)
                    if csm_thread.ident is not None:
                        csm_thread.join(2)
                self.assertFalse(mezz_thread.is_alive())
                self.assertFalse(csm_thread.is_alive())
            self.assertEqual(violations, [])
            self.assertEqual(mezz.current_scan_row['CSM0_Mezz0_AVDD_signal_raw_adc'], 30)
            self.assertEqual(mezz.current_scan_row['CSM0_Mezz0_AVDD_ground_reference_raw_adc'], 27)
            self.assertEqual(csm.current_scan_row['CSM0_SCA_Supply_raw_adc'], 31)


if __name__ == '__main__':
    unittest.main()
