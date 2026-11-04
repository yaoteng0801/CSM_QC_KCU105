import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from types import SimpleNamespace
import unittest
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from tab_spectra import _BarPlot24, tab_adc_channel_hits, CH_HIT_RATE_REF_HZ


class Backend(QtCore.QObject):
    analysis_1hz = QtCore.pyqtSignal(object)


class ChannelHitsLogScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_log_bar_geometry_reference_line_and_linear_statistics(self):
        plot = pg.PlotWidget()
        bars = _BarPlot24(plot)
        values = np.zeros(24)
        values[:3] = [.1, 1, 100]
        kwargs = dict(title='Rates', rate_ref_hz=CH_HIT_RATE_REF_HZ, show_rate_ref_below=True)
        bars.update_counts(values, **kwargs)
        stats = bars.stats_text.textItem.toPlainText()
        bars.set_log_y(True)
        bars.update_counts(values, **kwargs)
        tops = bars.bars.opts['y0'] + bars.bars.opts['height']
        np.testing.assert_allclose(tops[:3], [-1, 0, 2])
        np.testing.assert_allclose(bars.bars.opts['height'][3:], 0)
        self.assertEqual(bars.rate_ref_line.value(), np.log10(CH_HIT_RATE_REF_HZ))
        self.assertEqual(bars.stats_text.textItem.toPlainText(), stats)
        bars.set_log_y(False)
        bars.update_counts(values, **kwargs)
        np.testing.assert_allclose(bars.bars.opts['height'], values)
        self.assertEqual(bars.bars.opts['y0'], 0)
        self.assertEqual(bars.rate_ref_line.value(), CH_HIT_RATE_REF_HZ)
        bars.set_log_y(True)
        bars.update_counts(np.zeros(24), **kwargs)
        self.assertTrue(np.all(np.isfinite(bars.bars.opts['height'])))
        plot.close()

    def test_checkbox_applies_to_all_plots_and_survives_updates_and_count_mode(self):
        host = QtWidgets.QWidget()
        backend = Backend()
        tab = tab_adc_channel_hits(host, backend, n_tdcs=2)
        rates = np.zeros((2, 24))
        rates[:, :3] = [.1, 1, 100]
        counts = np.zeros((2, 24, 1), dtype=np.int64)
        counts[:, :3, 0] = [1, 10, 100]
        tab._last_snap = SimpleNamespace(acquisition_mode=1, noise_counters=1,
                                         noise_counter_rate=rates, adc_ch_hist=counts)
        tab._redraw()
        self.assertFalse(tab.chk_log_y.isChecked())
        tab.chk_log_y.setChecked(True)
        self.assertTrue(all(hp._log_y for hp in tab._plots))
        np.testing.assert_allclose(tab._plots[0].bars.opts['y0'] +
                                   tab._plots[0].bars.opts['height'][:3], [-1, 0, 2])
        tab._redraw()
        tab.chk_rate.setChecked(False)
        np.testing.assert_allclose(tab._plots[0].bars.opts['y0'] +
                                   tab._plots[0].bars.opts['height'][:3], [0, 1, 2])
        tab.chk_log_y.setChecked(False)
        self.assertTrue(all(not hp._log_y for hp in tab._plots))
        np.testing.assert_allclose(tab._plots[0].bars.opts['height'][:3], [1, 10, 100])
        host.close()


if __name__ == '__main__':
    unittest.main()
