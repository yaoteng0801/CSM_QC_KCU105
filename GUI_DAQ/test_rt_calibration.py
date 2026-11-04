"""Calibration loading, multilayer fitting, and capture UI regression tests."""
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from geometry import Geometry
from rt_function import RTFunction
from TrackFit import TrackFit

CATALOGUE = Path(__file__).resolve().parents[1] / 'rt_catalogue' / 'EML'
ROOT_FILE = CATALOGUE / 'EML1A05.root'


class RTLoadingTests(unittest.TestCase):
    def test_legacy_coefficients_and_inverse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'linear.txt'
            path.write_text('# r(t) = t / 20\n5 # constant\n5\n' + '0\n' * 8)
            rt = RTFunction(path)
            self.assertEqual(rt.nrt, 1)
            np.testing.assert_allclose(rt.r_of_t([0, 100, 200]), [0, 5, 10])
            self.assertEqual(float(rt.r_of_t(100, 1)), 5)
            rt.build_fast_inverse()
            np.testing.assert_allclose(rt.t_from_r_fast([0, 5, 10]), [0, 100, 200])
            with self.assertRaisesRegex(ValueError, 'NRT=2 requires a ROOT'):
                RTFunction(path, nrt=2)
            path.write_text('nan\n' * 10)
            with self.assertRaisesRegex(ValueError, 'Invalid coefficients'):
                RTFunction(path)

    def test_missing_vectors_and_wrong_root_type(self):
        import uproot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.root'
            with uproot.recreate(path) as root:
                root['unrelated'] = 'not a calibration'
            with self.assertRaisesRegex(ValueError, 'missing RTParam0'):
                RTFunction(path, nrt=2, t_min=0, t_max=200)
            with uproot.recreate(path) as root:
                root['RTParam0'] = 'not a coefficient vector'
            with self.assertRaisesRegex(ValueError, 'coefficient vector'):
                RTFunction(path, t_min=0, t_max=200)

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_catalogue_root_uses_both_vectors_and_table_times(self):
        rt = RTFunction(ROOT_FILE)
        self.assertEqual(rt.nrt, 2)
        np.testing.assert_allclose(rt.time_ranges, [[0, 743.82], [0, 743.82]])
        np.testing.assert_allclose(rt.r_of_t([100, 100], [0, 1]), [4.46134179, 4.46134180], atol=1e-8)
        with self.assertRaisesRegex(ValueError, 'multilayer index'):
            rt.r_of_t(100)
        with self.assertRaisesRegex(ValueError, 'indices must be'):
            rt.r_of_t(100, 2)
        with self.assertRaisesRegex(ValueError, 'catalogue radius/time'):
            RTFunction(CATALOGUE / 'EML1A05_ML1.txt')

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_standalone_root_requires_explicit_time_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ROOT_FILE.name
            shutil.copyfile(ROOT_FILE, path)
            with self.assertRaisesRegex(ValueError, 'contains no time limits'):
                RTFunction(path)
            rt = RTFunction(path, nrt=2, time_ranges=[[0, 200], [10, 410]])
            # Each midpoint maps to normalized time zero despite different ranges.
            np.testing.assert_allclose(rt.r_of_t([100, 210], [0, 1]), [10.23027625] * 2, atol=1e-8)
            self.assertGreater(abs(float(rt.r_of_t(100, 0) - rt.r_of_t(100, 1))), 1)
            with self.assertRaisesRegex(ValueError, 'Tmin < Tmax'):
                RTFunction(path, time_ranges=[[0, 200], [10, 10]])
            single = RTFunction(path, nrt=1, t_min=0, t_max=200)
            self.assertEqual(single.nrt, 1)
            np.testing.assert_equal(single.r_of_t([100, 100], [0, 1]), [single.r_of_t(100)] * 2)

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_nrt_two_rejects_missing_second_vector(self):
        import uproot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ROOT_FILE.name
            shutil.copyfile(ROOT_FILE, path)
            with uproot.update(path) as root:
                del root['RTParam1']
            with self.assertRaisesRegex(ValueError, 'missing RTParam1'):
                RTFunction(path, nrt=2, t_min=0, t_max=200)
            self.assertEqual(RTFunction(path, t_min=0, t_max=200).nrt, 1)


@unittest.skipUnless(TrackFit.available(), 'native track fitter not installed')
class MultilayerFitTests(unittest.TestCase):
    @staticmethod
    def fitter(ranges=None):
        return TrackFit(r_lut=[np.linspace(0, 8, 2048), np.linspace(0, 14, 2048)],
                        T0=0, Tmax=200, time_ranges=ranges, min_hits=6)

    def test_native_and_python_interpolation_match_including_first_bin(self):
        fitter = self.fitter([[0, 200], [10, 410]])
        times = np.array([-10, 0, 0.02, 50, 199.99, 300, 410, 500])
        for ml in (0, 1):
            expected = np.interp(times, fitter.time_ranges[ml], [0, (8, 14)[ml]])
            np.testing.assert_allclose(fitter.radius_from_time_ns(times, ml), expected, atol=1e-12)
            native = [fitter._fitter.r_of_t(float(t), ml) for t in times]
            np.testing.assert_allclose(native, expected, atol=1e-12)
        with self.assertRaisesRegex(ValueError, 'requires multilayer'):
            fitter.radius_from_time_ns(times)

    def test_fit_recovers_track_and_t0_with_different_multilayer_curves(self):
        fitter = self.fitter()
        y = np.array([5, 18, 31, 44, 100, 113, 126, 139.])
        radii = np.array([2, 3, 4, 2.5, 5, 3, 6, 4.])
        sides = np.array([1, -1, 1, -1, 1, -1, -1, 1])
        x = (60 + sides * radii - np.sin(.15) * y) / np.cos(.15)
        times = radii / np.array([.04] * 4 + [.07] * 4) + 23
        hits = [SimpleNamespace(x=xx, y=yy, layer=i) for i, (xx, yy) in enumerate(zip(x, y))]
        fit = fitter.fit_chamber_hits(chamber_id=0, hits=hits, t_corr_ns=times,
                                      geometry=Geometry(MAX_TDC_LAYER=4))
        self.assertTrue(fit.ok, fit.reason)
        self.assertEqual(fit.n_used, 8)
        self.assertAlmostEqual(fit.values['t0_ns'], 23, places=4)
        self.assertAlmostEqual(fit.values['theta'], .15, places=5)
        self.assertAlmostEqual(fit.values['c'], 60, places=4)
        np.testing.assert_allclose(fitter.radius_from_time_ns(times - fit.values['t0_ns'], [0]*4+[1]*4), radii)

    def test_t0_bounds_use_each_hit_domain_and_geometry_layer_count(self):
        fitter = self.fitter([[0, 100], [20, 320]])
        native = Mock()
        native.fit.return_value = {'used_idx': list(range(6)), 'n_used': 6}
        fitter._fitter = native
        # Three layers per ML, as in EML, rather than assuming four.
        hits = [SimpleNamespace(x=20+i, y=20+i, layer=i) for i in range(6)]
        result = fitter.fit_chamber_hits(chamber_id=0, hits=hits,
            t_corr_ns=[30, 50, 90, 200, 240, 270], geometry=Geometry(MAX_TDC_LAYER=3))
        self.assertTrue(result.ok, result.reason)
        args = native.fit.call_args.kwargs
        self.assertEqual(args['t0_min'], -10)
        self.assertEqual(args['t0_max'], 30)
        np.testing.assert_array_equal(args['rt_indices'], [0, 0, 0, 1, 1, 1])

    def test_single_curve_fit_matches_two_identical_curves(self):
        lut = np.linspace(0, 8, 2048)
        single = TrackFit(r_lut=lut, T0=0, Tmax=200)
        dual = TrackFit(r_lut=[lut, lut], T0=0, Tmax=200)
        y = np.array([5, 18, 31, 44, 100, 113, 126, 139.])
        radii = np.array([2, 3, 4, 2.5, 5, 3, 6, 4.])
        sides = np.array([1, -1, 1, -1, 1, -1, -1, 1])
        x = (60 + sides * radii - np.sin(.15) * y) / np.cos(.15)
        times = radii / .04 + 23
        result1 = single._fit_arrays(x, y, times)
        result2 = dual._fit_arrays(x, y, times, [0]*4+[1]*4)
        for name in ('theta', 'c', 't0_ns', 'chi2'):
            self.assertAlmostEqual(result1[name], result2[name], places=10)

    def test_mask_preserves_alignment_of_times_and_multilayers(self):
        fitter = self.fitter()
        native = Mock()
        native.fit.return_value = {'used_idx': list(range(6)), 'n_used': 6}
        fitter._fitter = native
        hits = [SimpleNamespace(x=20+i, y=20+i, layer=i) for i in range(8)]
        result = fitter.fit_chamber_hits(chamber_id=0, hits=hits, t_corr_ns=np.arange(8)+30,
            keep_mask=[False, True, True, True, True, False, True, True],
            geometry=Geometry(MAX_TDC_LAYER=4))
        self.assertTrue(result.ok, result.reason)
        args = native.fit.call_args.kwargs
        np.testing.assert_array_equal(args['rt_indices'], [0, 0, 0, 1, 1, 1])
        self.assertEqual(result.values['used_indices_input'], [1, 2, 3, 4, 6, 7])


class CalibrationUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PyQt5 import QtWidgets
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_capture_selection_and_settings_roundtrip(self):
        from PyQt5 import QtWidgets
        from tab_capture import tab_capture
        with tempfile.TemporaryDirectory() as directory, \
                patch('tab_capture.SETTINGS_FILE', str(Path(directory)/'settings.ini')), \
                patch('tab_capture.pcapy.findalldevs', return_value=['lo']):
            parent = QtWidgets.QWidget()
            callback = Mock(return_value=True)
            capture = tab_capture(parent, rt_apply_callback=callback)
            capture.edit_rtfile.setText(str(ROOT_FILE))
            capture.combo_nrt.setCurrentIndex(capture.combo_nrt.findData(2))
            capture.check_rt_catalogue_ranges.setChecked(False)
            capture.rt_range_spins[1][1].setValue(750)
            self.assertTrue(capture._apply_rt_selection())
            callback.assert_called_once_with(str(ROOT_FILE), nrt=2, time_ranges=[[0,200],[0,750]])
            capture._save_settings()
            parent2 = QtWidgets.QWidget()
            restored = tab_capture(parent2)
            self.assertEqual(restored.combo_nrt.currentData(), 2)
            self.assertFalse(restored.check_rt_catalogue_ranges.isChecked())
            self.assertEqual(restored.rt_range_spins[1][1].value(), 750)
            parent.close()
            parent2.close()

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_apply_updates_both_displays_and_rejects_invalid_replacement(self):
        from GUI_DAQ_init import StartQT5
        from backend import Backend
        backend = Backend()
        geo_tabs = [SimpleNamespace(set_rt=Mock()), SimpleNamespace(set_rt=Mock())]
        window = SimpleNamespace(backend=backend, rt=None,
            ui=SimpleNamespace(tab_geometries=geo_tabs, tab_capture_inst=SimpleNamespace(set_rt_summary=Mock())))
        window._load_rt_from_file = lambda path, **kwargs: StartQT5._load_rt_from_file(window, path, **kwargs)
        self.assertTrue(StartQT5.apply_rt_file(window, str(ROOT_FILE), nrt=2))
        self.assertEqual(window.rt.nrt, 2)
        self.assertAlmostEqual(backend._quality.max_window_ns, 743.82)
        for tab in geo_tabs:
            tab.set_rt.assert_called_once_with(window.rt)
        previous = window.rt
        self.assertFalse(StartQT5.apply_rt_file(window, '/missing.root', nrt=2))
        self.assertIs(window.rt, previous)
        with patch.object(backend, 'is_running', return_value=True):
            self.assertFalse(StartQT5.apply_rt_file(window, '', nrt=1))
        self.assertIs(window.rt, previous)

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_drift_circles_use_geometry_multilayer(self):
        import pyqtgraph as pg
        from tab_geometry import tab_geometry
        rt = RTFunction(ROOT_FILE, time_ranges=[[0, 200], [0, 400]])
        hits = [SimpleNamespace(x=30, y=30, layer=0, col=0),
                SimpleNamespace(x=30, y=100, layer=3, col=0)]
        tw = SimpleNamespace(keep_mask=np.array([True, True]), t_corr_ns=np.array([100., 100.]))
        tab = SimpleNamespace(_rt=rt, geo=Geometry(MAX_TDC_LAYER=3, max_drift_dist=15),
            _hits_for_this_chamber=lambda ev: hits, _timewindow_for_this_chamber=lambda tws: tw,
            view=Mock(), _tube_by_lc={}, _pen_blue=pg.mkPen('b'), _brush_blue=pg.mkBrush('b'),
            _pen_red_radius=pg.mkPen('r'), _brush_red_radius=pg.mkBrush('r'), _brush_red=pg.mkBrush('r'),
            _drift_circle_items=[], _drift_text_items=[], _removed_tubes=set(), _removed_text_items=[])
        tab_geometry._draw_drift_circles_from_timewindow(tab, object(), {0: tw})
        actual = [circle.rect().width()/2 for circle in tab._drift_circle_items]
        np.testing.assert_allclose(actual, rt.r_of_t([100, 100], [0, 1]))
        self.assertGreater(abs(actual[0]-actual[1]), 1)

    @unittest.skipUnless(ROOT_FILE.is_file(), 'local RT catalogue not available')
    def test_run_snapshot_records_root_coefficients_and_checksum(self):
        import hashlib
        from backend import Backend
        backend = Backend()
        backend.set_trackfit_rt(RTFunction(ROOT_FILE))
        backend._run_context = {'rt_file': str(ROOT_FILE)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'config.txt'
            backend._current_config_path = str(path)
            backend._write_run_config()
            snapshot = path.read_text()
            self.assertIn('"nrt": 2', snapshot)
            self.assertIn('"coefficients":', snapshot)
            self.assertIn('743.82', snapshot)
            self.assertIn(hashlib.sha256(ROOT_FILE.read_bytes()).hexdigest(), snapshot)
            self.assertIn('EML1A05_ML2.txt', snapshot)


if __name__ == '__main__':
    unittest.main()
