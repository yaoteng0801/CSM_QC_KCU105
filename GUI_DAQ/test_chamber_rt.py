import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
from PyQt5 import QtCore, QtWidgets
from backend import Backend
from rt_function import RTFunction
from rt_calibration_widget import RTCalibrationWidget
from EventQuality import EventQualityChecker


class ChamberRTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_independent_settings_restore_and_invalid_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'rt.txt'
            path.write_text('\n'.join(map(str, [7, 7] + [0]*8)))
            settings = QtCore.QSettings(str(Path(tmp)/'settings.ini'), QtCore.QSettings.IniFormat)
            callbacks = [Mock(), Mock()]
            widgets = [RTCalibrationWidget(cid, settings, callbacks[cid]) for cid in range(2)]
            for cid, widget in enumerate(widgets):
                widget.edit_rtfile.setText(str(path))
                widget.check_rt_catalogue_ranges.setChecked(False)
                widget.rt_range_spins[0][1].setValue(200 + cid*500)
                self.assertTrue(widget._apply_rt_selection())
            self.assertEqual(callbacks[0].call_args.args[0].Tmax, 200)
            self.assertEqual(callbacks[1].call_args.args[0].Tmax, 700)
            old = settings.value(widgets[0].key)
            widgets[0].edit_rtfile.setText('/missing.root')
            self.assertFalse(widgets[0]._apply_rt_selection())
            self.assertEqual(settings.value(widgets[0].key), old)
            for cid in range(2):
                restored = Mock()
                widget = RTCalibrationWidget(cid, settings, restored)
                self.assertEqual(restored.call_args.args[0].Tmax, 200 + cid*500)
                widget.close()
            for widget in widgets:
                widget.close()

    def test_backend_fits_each_chamber_with_its_own_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'rt.txt'
            path.write_text('\n'.join(map(str, [7, 7] + [0]*8)))
            a = RTFunction(path, time_ranges=[[0, 200]])
            b = RTFunction(path, time_ranges=[[0, 700]])
            backend = Backend()
            result = SimpleNamespace(ok=True, n_used=6, values={'dof': 3})
            def make_fitter(rt, **kwargs):
                return SimpleNamespace(min_hits=6, nrt=rt.nrt,
                    fit_chamber_hits=Mock(return_value=result))
            with patch('backend.TrackFit.from_rt', side_effect=make_fitter):
                backend.set_chamber_rt(0, a)
                first = backend.trackfit_for_chamber(0)
                backend.set_chamber_rt(1, b)
                self.assertIs(backend.trackfit_for_chamber(0), first)
                second = backend.trackfit_for_chamber(1)
                seen = []
                def quality(checker, event, **kwargs):
                    cid = next(iter(event.chambers))
                    seen.append((cid, checker.max_window_ns))
                    tw = SimpleNamespace(t_corr_ns=np.arange(6), keep_mask=np.ones(6, bool))
                    return EventQualityChecker.Result({cid: tw}, {cid: True})
                ev = SimpleNamespace(event_id20=1, chambers={cid: SimpleNamespace(hits=[object()]*6) for cid in (0,1)})
                backend.set_acquisition_mode(1)
                with patch.object(EventQualityChecker, 'compute_for_event', quality):
                    backend._compute_quality_by_chamber(ev)
                self.assertEqual(seen, [(0, 200), (1, 700)])
                self.assertEqual(first.fit_chamber_hits.call_args.kwargs['chamber_id'], 0)
                self.assertEqual(second.fit_chamber_hits.call_args.kwargs['chamber_id'], 1)
                self.assertEqual(backend._rt_calibration_snapshot['1']['time_ranges_ns'], [[0, 700]])
                self.assertGreaterEqual(backend._fit_tdc_tmax_ns, 800)
                with patch.object(backend, 'is_running', return_value=True):
                    with self.assertRaises(RuntimeError):
                        backend.set_chamber_rt(0, b)
                backend.set_chamber_rt(0, None)
                self.assertIsNone(backend.trackfit_for_chamber(0))
                self.assertIs(backend.trackfit_for_chamber(1), second)

    def test_capture_start_does_not_replace_chamber_assignments(self):
        from tab_capture import tab_capture
        capture = SimpleNamespace(_geometry_rt_managed=True, _rt_apply_callback=Mock())
        self.assertTrue(tab_capture._apply_rt_selection(capture))
        capture._rt_apply_callback.assert_not_called()
