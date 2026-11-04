import unittest
from unittest.mock import patch

from tab_eom import EOMScanWorker


class EOMScanWorkerTests(unittest.TestCase):
    @staticmethod
    def _worker():
        return EOMScanWorker(
            eth=object(),
            which_csm=1,
            lpgbt_addr=115,
            uplink_index=3,
            lpgbt_role="Slave",
            phase_values=[2],
            vof_values=[4],
            end_count_sel=7,
            normalize_mode="raw",
            bias_delay_ms=0,
            settle_delay_ms=0,
            poll_interval_ms=1,
            timeout_ms=10,
        )

    def test_scan_starts_without_obsolete_uplink_select_method(self):
        worker = self._worker()
        results = []
        errors = []
        worker.finished.connect(results.append)
        worker.error.connect(errors.append)

        with (
            patch.object(worker, "_write_reg"),
            patch.object(worker, "_wait_for_eom_done", return_value=(1, 12, 24)),
            patch("tab_eom.time.sleep"),
        ):
            worker.run()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["error"])
        self.assertEqual(results[0]["rows"][0]["counter"], 12)
        self.assertEqual(results[0]["rows"][0]["uplink_index"], 3)

    def test_ethernet_access_routes_to_selected_second_csm_slave(self):
        worker = self._worker()

        with patch("tab_eom.lpgbt_config_read", return_value=[1, 2]) as read:
            self.assertEqual(worker._read_regs(0x100, 2), [1, 2])
        self.assertEqual(read.call_args.kwargs["which_csm"], 1)
        self.assertEqual(read.call_args.kwargs["lpgbt_addr"], 115)

        with patch("tab_eom.lpgbt_config_write", return_value=[7]) as write:
            worker._write_reg(0x101, 7)
        self.assertEqual(write.call_args.kwargs["which_csm"], 1)
        self.assertEqual(write.call_args.kwargs["lpgbt_addr"], 115)


if __name__ == "__main__":
    unittest.main()
