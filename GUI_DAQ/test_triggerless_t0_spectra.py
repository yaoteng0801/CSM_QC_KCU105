"""Event-T0 spectra, acquisition-mode isolation, and queued-fit finalization."""
import os
import queue
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
from PyQt5 import QtCore, QtWidgets

from backend import Backend
from DecodeThread import DecodeThread, EventBuffer
from EventQuality import EventQualityChecker
from TrackFit import TrackFitResult
from tab_spectra import tab_tdc_spectra, tab_tdc_channels


class EventEmitter(QtCore.QObject):
    event = QtCore.pyqtSignal(object)


class TriggerlessT0SpectraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.backend = Backend()
        self.backend.set_acquisition_mode(1)

    def tearDown(self):
        self.backend.deleteLater()
        self.app.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)

    @staticmethod
    def snapshot():
        decoder = DecodeThread(queue.Queue(), EventBuffer(), use_native_decoder=False,
                               tdc_bins=1024, tdc_shift=0, ch_tdc_bins=1024,
                               ch_tdc_shift=0, tdc_max_ns=800, ch_tdc_max_ns=800)
        snap = decoder.make_snapshot(copy_arrays=True)
        snap.tdc_hist[0, 10] = 14
        snap.tdc_ch_hist[0, 0, 10] = 14
        snap.adc_hist[0, 30] = 100
        return snap

    def emitted_snapshot(self, snap):
        emitted = []
        self.backend.analysis_1hz.connect(emitted.append)
        self.backend._on_decode_1hz(snap)
        self.backend.analysis_1hz.disconnect(emitted.append)
        return emitted[-1]

    def prepare_event(self, event_id, t0=10.0, drift=None, used=None):
        drift = np.asarray([5, 20, 35, 50, 65, 80] if drift is None else drift, dtype=float)
        hits = [SimpleNamespace(tdcid=i % 2, ch=i, width=30, x=float(i), y=float(i), layer=i)
                for i in range(len(drift))]
        event = SimpleNamespace(event_id20=event_id, chambers={0: SimpleNamespace(hits=hits)})
        tw = SimpleNamespace(t_corr_ns=drift + t0, keep_mask=np.ones(len(hits), dtype=bool))
        used = np.ones(len(hits), dtype=bool) if used is None else np.asarray(used, dtype=bool)
        n_used = int(used.sum())
        result = TrackFitResult(0, True, "ok", len(hits), n_used,
            dict(t0_ns=t0, used_mask_input=used, dof=n_used-3, nx=1, ny=0, c=0))
        self.backend._quality.compute_for_event = Mock(return_value=EventQualityChecker.Result({0: tw}, {0: True}))
        self.backend._trackfit = SimpleNamespace(min_hits=6, nrt=1,
            fit_chamber_hits=Mock(return_value=result),
            radius_from_time_ns=lambda times, multilayer=None: np.zeros_like(times))
        return event, drift

    def test_different_event_t0_values_produce_identical_drift_spectra(self):
        for event_id, t0 in ((1, -35.0), (2, 140.0)):
            event, drift = self.prepare_event(event_id, t0)
            self.backend._on_decoded_event(event)
        out = self.emitted_snapshot(self.snapshot())
        self.assertEqual(int(out.tdc_hist.sum()), 12)
        self.assertEqual(int(out.tdc_ch_hist.sum()), 12)
        for i, time in enumerate(drift):
            bin_index = int((time - out.tdc_time_min_ns) / out.tdc_time_binw_ns)
            self.assertEqual(out.tdc_ch_hist[i % 2, i, bin_index], 2)
        self.assertEqual(out.fit_evt_total, 2)
        self.assertEqual(out.fit_evt_valid, 2)
        self.assertEqual(out.tdc_hist_source, "fit_drift_time_ns:t_corr_minus_t0")
        self.assertEqual(int(out.adc_hist.sum()), 100)

    def test_fit_outliers_are_excluded_from_t0_spectra(self):
        event, _ = self.prepare_event(3, drift=[5, 20, 35, 50, 65, 80, 95],
                                      used=[True]*6 + [False])
        self.backend._on_decoded_event(event)
        self.assertEqual(int(self.backend._fit_tdc_hist.sum()), 6)
        self.assertEqual(int(self.backend._fit_tdc_ch_hist[:, 6].sum()), 0)

    def test_triggered_and_noise_modes_keep_decoder_histograms(self):
        for acquisition_mode, noise_mode in ((0, 0), (1, 1), (1, 2)):
            with self.subTest(mode=(acquisition_mode, noise_mode)):
                self.backend.set_acquisition_mode(acquisition_mode)
                self.backend.set_noise_test_mode(noise_mode)
                event, _ = self.prepare_event(4)
                self.backend._on_decoded_event(event)
                self.backend._trackfit.fit_chamber_hits.assert_not_called()
                snap = self.snapshot()
                out = self.emitted_snapshot(snap)
                np.testing.assert_array_equal(out.tdc_hist, snap.tdc_hist)
                np.testing.assert_array_equal(out.tdc_ch_hist, snap.tdc_ch_hist)
                self.assertEqual(out.tdc_time_max_ns, 800)

    def test_missing_fit_never_falls_back_to_absolute_counter(self):
        out = self.emitted_snapshot(self.snapshot())
        self.assertEqual(int(out.tdc_hist.sum()), 0)
        self.assertEqual(int(out.tdc_hist_raw.sum()), 14)
        self.assertIn("t_corr_minus_t0", out.tdc_hist_source)

    def test_mdt_range_and_fitter_survive_mode_selection_after_rt_loading(self):
        self.backend.set_acquisition_mode(0)
        rt = SimpleNamespace(T0=0, Tmax=800, file_path="test.root", nrt=2,
            time_ranges=np.array([[0, 800], [0, 800]]), params_by_ml=[np.ones(10)]*2)
        with patch("backend.TrackFit.from_rt") as create:
            self.backend.set_trackfit_rt(rt)
            self.assertIs(self.backend._trackfit, create.return_value)
        self.backend.set_acquisition_mode(1)
        event, _ = self.prepare_event(5, drift=np.arange(6) + 700)
        self.backend._on_decoded_event(event)
        out = self.emitted_snapshot(self.snapshot())
        self.assertGreaterEqual(out.tdc_time_max_ns, 800)
        self.assertEqual(int(out.tdc_hist.sum()), 6)

    def test_triggerless_quality_ignores_unrelated_trigger_word(self):
        hits = [SimpleNamespace(ledge=(131050 + i*20) % 131072, width=30) for i in range(6)]
        self.backend._quality.checkHitcount = False
        times = []
        for event_id, trigger in ((10, None), (11, 40000)):
            event = SimpleNamespace(event_id20=event_id, trigger_ledge=trigger,
                                    chambers={0: SimpleNamespace(hits=hits)})
            time_by, _ = self.backend._compute_quality_by_chamber(event)
            self.assertEqual(time_by[0].reference_kind, "hit0")
            times.append(time_by[0].t_corr_ns)
        np.testing.assert_array_equal(*times)

    def test_stop_finishes_queued_fits_before_final_snapshot(self):
        event, _ = self.prepare_event(12)
        emitter = EventEmitter()
        emitter.event.connect(self.backend._fit_event_receiver.process, QtCore.Qt.QueuedConnection)
        for event_id in range(20):
            emitter.event.emit(SimpleNamespace(event_id20=event_id, chambers=event.chambers))
        self.assertEqual(self.backend._fit_evt_total, 0)
        snap = self.snapshot()
        self.backend._dec_thread = SimpleNamespace(stop=Mock(), wait=Mock(), make_snapshot=Mock(return_value=snap))
        final = []
        self.backend.analysis_1hz.connect(final.append)
        self.backend.stop_capture()
        self.assertEqual(final[-1].fit_evt_total, 20)
        self.assertEqual(int(final[-1].tdc_hist.sum()), 120)

    def test_both_tdc_tabs_label_current_timing_reference(self):
        parents = [QtWidgets.QWidget(), QtWidgets.QWidget()]
        tabs = [tab_tdc_spectra(parents[0], self.backend, n_tdcs=2),
                tab_tdc_channels(parents[1], self.backend, n_tdcs=2)]
        for mode, expected in ((1, "Drift time (event T0)"), (0, "hit_ledge - trigger_ledge")):
            self.backend.set_acquisition_mode(mode)
            self.emitted_snapshot(self.snapshot())
            for tab in tabs:
                tab._redraw()
                self.assertEqual(tab.x_label, expected)
                self.assertEqual(tab._plots[0].plot.getAxis("bottom").labelText, expected)
        for parent in parents:
            parent.close()
            parent.deleteLater()


if __name__ == "__main__":
    unittest.main()
