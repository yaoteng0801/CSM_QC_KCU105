import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from tab_lpgbt import tab_lpgbt


class FpgaIdcodeProgressTests(unittest.TestCase):
    @staticmethod
    def _controller():
        return SimpleNamespace(
            _set_fpga_status_ready=Mock(),
            progress_bar=SimpleNamespace(setValue=Mock()),
        )

    def test_unconfigured_idcode_result_resets_progress(self):
        controller = self._controller()

        tab_lpgbt._on_fpga_idcode_result(
            controller,
            0,
            0x0362D093,
            False,
        )

        controller._set_fpga_status_ready.assert_called_once_with(0, False)
        controller.progress_bar.setValue.assert_called_once_with(0)

    def test_configured_idcode_result_preserves_progress(self):
        controller = self._controller()

        tab_lpgbt._on_fpga_idcode_result(
            controller,
            1,
            0x0362D093,
            True,
        )

        controller._set_fpga_status_ready.assert_called_once_with(1, True)
        controller.progress_bar.setValue.assert_not_called()


if __name__ == "__main__":
    unittest.main()
