import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tab_mezz import tab_mezz


class MezzSelectedCSMRoutingTests(unittest.TestCase):
    @staticmethod
    def _controller():
        controller = object.__new__(tab_mezz)
        controller.CSM_per_MiniDAQ = 2
        controller.mezz_per_CSM = 20
        controller.eth = object()
        controller.jtag_rate_spinbox = SimpleNamespace(value=lambda: 10)
        controller.get_transID = Mock(return_value=1)
        controller.SCA_GPIO_init = Mock()
        controller.Mezz_enable = Mock()
        controller.CSM_list = [
            SimpleNamespace(
                TDC_enable=["0" * 20],
                TDC_list=[object() for _ in range(20)],
            ),
            SimpleNamespace(
                TDC_enable=["1" + "0" * 19],
                TDC_list=[object() for _ in range(20)],
            ),
        ]
        controller.csm_indicator_list = [
            [[SimpleNamespace(setStyleSheet=Mock()) for _ in range(3)] for _ in range(20)]
            for _ in range(2)
        ]
        return controller

    def test_second_csm_is_the_only_selected_csm(self):
        controller = self._controller()

        self.assertEqual(controller.selected_csm_indices(), [1])

    def test_tdc_programming_skips_unselected_first_csm(self):
        controller = self._controller()
        controller._write_tdc_once = Mock(return_value=True)

        with patch("tab_mezz.SCA_clk_div") as set_clock:
            controller.write_TDC_all()

        set_clock.assert_called_once()
        self.assertEqual(set_clock.call_args.kwargs["which_csm"], 1)
        controller.SCA_GPIO_init.assert_called_once_with(which_csm=1)
        controller.Mezz_enable.assert_called_once_with(0, which_csm=1)
        controller._write_tdc_once.assert_called_once_with(
            controller.CSM_list[1].TDC_list[0],
            which_csm=1,
        )

    def test_asd_programming_skips_unselected_first_csm(self):
        controller = self._controller()
        controller._write_asd_once = Mock(return_value=True)

        with patch("tab_mezz.SCA_clk_div") as set_clock:
            controller.write_ASD_all()

        set_clock.assert_called_once()
        self.assertEqual(set_clock.call_args.kwargs["which_csm"], 1)
        controller.SCA_GPIO_init.assert_called_once_with(which_csm=1)
        controller.Mezz_enable.assert_called_once_with(0, which_csm=1)
        controller._write_asd_once.assert_called_once_with(
            controller.CSM_list[1].TDC_list[0],
            1,
            0,
        )

    def test_scan_reinitializes_sca_after_clock_or_asd_failure(self):
        for failure in ("clock", "gpio", "asd"):
            with self.subTest(failure=failure):
                controller = self._controller()
                tdc = SimpleNamespace(ASD_list=[SimpleNamespace(threshold=["old"])])
                controller._write_asd_once = Mock(
                    side_effect=[False, True] if failure == "asd" else [True]
                )
                if failure == "gpio":
                    controller.SCA_GPIO_init.side_effect = [RuntimeError("GPIO failure"), None]
                with patch("tab_mezz.SCA_clk_div") as clock:
                    if failure == "clock":
                        clock.side_effect = [RuntimeError("divider read failed"), None]
                    self.assertTrue(controller._configure_asd_mezz_with_retries(
                        tdc, 1, 0, "threshold", "10011000"
                    ))
                self.assertEqual(clock.call_count, 2)
                self.assertEqual(controller.SCA_GPIO_init.call_count,
                                 1 if failure == "clock" else 2)
                self.assertEqual(tdc.ASD_list[0].threshold[0], "10011000")

    def test_scan_stops_after_five_retries(self):
        controller = self._controller()
        tdc = SimpleNamespace(ASD_list=[SimpleNamespace(threshold=["old"])])
        controller._write_asd_once = Mock(return_value=False)
        with patch("tab_mezz.SCA_clk_div") as clock:
            self.assertFalse(controller._configure_asd_mezz_with_retries(
                tdc, 1, 0, "threshold", "10011000"
            ))
        self.assertEqual(clock.call_count, 6)
        self.assertEqual(controller.SCA_GPIO_init.call_count, 6)
        self.assertEqual(controller._write_asd_once.call_count, 6)

    def test_scan_accepts_success_on_last_retry(self):
        controller = self._controller()
        tdc = SimpleNamespace(ASD_list=[SimpleNamespace(threshold=["old"])])
        controller._write_asd_once = Mock(side_effect=[False] * 5 + [True])
        with patch("tab_mezz.SCA_clk_div"):
            self.assertTrue(controller._configure_asd_mezz_with_retries(
                tdc, 1, 0, "threshold", "10011000"
            ))
        self.assertEqual(controller._write_asd_once.call_count, 6)


if __name__ == "__main__":
    unittest.main()
