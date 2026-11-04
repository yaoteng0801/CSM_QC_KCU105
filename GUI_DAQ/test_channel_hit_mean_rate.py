import unittest
from types import SimpleNamespace

import numpy as np

from tab_spectra import (
    _enabled_total_mean,
    _weighted_mean_std,
    tab_channel_hits_base,
)


class ChannelHitMeanRateTests(unittest.TestCase):
    def test_shared_histogram_statistics_remain_available(self):
        mean, std = _weighted_mean_std([0.0, 1.0, 2.0], [1.0, 2.0, 1.0])

        self.assertEqual(mean, 1.0)
        self.assertAlmostEqual(std, np.sqrt(0.5))

    def test_mean_uses_only_enabled_channels(self):
        total, mean, count = _enabled_total_mean(
            [100.0, 900.0, 300.0, 700.0],
            [True, False, True, False],
        )

        self.assertEqual(count, 2)
        self.assertEqual(total, 400.0)
        self.assertEqual(mean, 200.0)

    def test_zero_enabled_channels_is_safe(self):
        total, mean, count = _enabled_total_mean(
            [100.0, 200.0],
            [False, False],
        )

        self.assertEqual((total, mean, count), (0.0, 0.0, 0))

    def test_plot_mask_comes_from_mezz_active_channels(self):
        view = SimpleNamespace(
            _active_channels_callback=lambda: {7: [0, 2, 23]}
        )

        mask = tab_channel_hits_base._enabled_channel_mask(view, 7, 24)

        expected = np.zeros(24, dtype=bool)
        expected[[0, 2, 23]] = True
        np.testing.assert_array_equal(mask, expected)

    def test_unselected_tdc_has_no_enabled_channels(self):
        view = SimpleNamespace(
            _active_channels_callback=lambda: {7: [0, 2, 23]}
        )

        mask = tab_channel_hits_base._enabled_channel_mask(view, 8, 24)

        self.assertFalse(np.any(mask))


if __name__ == "__main__":
    unittest.main()
