import unittest
from unittest.mock import Mock, patch

from tab_lpgbt import tab_lpgbt


class UplinkReadyPollTests(unittest.TestCase):
    def setUp(self):
        self.tab = tab_lpgbt.__new__(tab_lpgbt)
        self.tab._link_ready_timer = Mock()
        self.tab._link_ready_poll = None
        self.tab._set_uplink_text_ready = Mock()
        self.tab.update_status = Mock()
        self.clock = patch("tab_lpgbt.time.monotonic", return_value=10.0)
        self.now = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.tab._start_uplink_ready_poll(2)

    def sample(self, timestamp, mask):
        self.now.return_value = timestamp
        self.tab.update_status.return_value = mask
        self.tab._poll_loaded_uplink_ready()

    def test_three_consecutive_samples_confirm_selected_link(self):
        for timestamp in (10.1, 10.2):
            self.sample(timestamp, 4)
            self.tab._set_uplink_text_ready.assert_called_with(2, False)
        self.sample(10.3, 4)
        self.tab._set_uplink_text_ready.assert_called_with(2, True)
        self.assertIsNone(self.tab._link_ready_poll)
        self.tab._link_ready_timer.stop.assert_called()

    def test_not_ready_or_invalid_read_breaks_consecutive_successes(self):
        for failure in (0, None, 3):  # Other links ready do not count.
            with self.subTest(failure=failure):
                self.tab._start_uplink_ready_poll(2)
                for timestamp, mask in ((10.1, 4), (10.2, 4), (10.3, failure),
                                        (10.4, 4), (10.5, 4)):
                    self.sample(timestamp, mask)
                self.assertEqual(self.tab._link_ready_poll["successes"], 2)
                self.sample(10.6, 4)
                self.assertIsNone(self.tab._link_ready_poll)

    def test_timeout_stops_polling_without_reading_again(self):
        self.sample(10.9, 4)
        self.tab.update_status.reset_mock()
        self.sample(11.001, 4)
        self.tab.update_status.assert_not_called()
        self.tab._set_uplink_text_ready.assert_called_with(2, False)
        self.assertIsNone(self.tab._link_ready_poll)

    def test_late_third_reply_does_not_confirm_ready(self):
        self.sample(10.1, 4)
        self.sample(10.2, 4)
        self.now.side_effect = (10.9, 11.1)
        self.tab._poll_loaded_uplink_ready()
        self.tab._set_uplink_text_ready.assert_called_with(2, False)
        self.assertIsNone(self.tab._link_ready_poll)

    def test_load_resets_rx_then_starts_poll_without_immediate_status(self):
        self.tab.worker_lpGBT = Mock()
        self.tab.fpga_physical_rx_reset = Mock()
        with patch.object(self.tab, "_start_uplink_ready_poll") as start:
            ordered = Mock()
            ordered.attach_mock(self.tab.fpga_physical_rx_reset, "reset")
            ordered.attach_mock(start, "start")
            self.tab.load_lpgbt(1, False)
            self.assertEqual([call[0] for call in ordered.mock_calls], ["reset", "start"])
            start.assert_called_once_with(3)
        self.tab.update_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
