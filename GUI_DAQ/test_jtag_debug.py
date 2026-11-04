import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PyQt5 import QtCore, QtWidgets

from pop_jtag_debug import JTAGDebugDialog, JTAGDebugWorker, TDC_CHAINS, random_registers
from crc8_D81 import crc_cal
from SCA_share import SCA_share
from tab_mezz import tab_mezz
from TDCreg import TDCreg


class JTAGDebugTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.controller = object.__new__(tab_mezz)
        self.controller.eth = object()
        self.controller.get_transID = Mock(return_value=2)
        self.controller.SCA_GPIO_init = Mock()
        self.controller.Mezz_enable = Mock()
        self.controller.mezz_per_CSM = 20
        self.controller.jtag_rate_spinbox = SimpleNamespace(value=lambda: 10)
        self.controller.CSM_list = [SimpleNamespace(TDC_list=[TDCreg() for _ in range(20)])
                                    for _ in range(2)]
        self.worker = JTAGDebugWorker(self.controller, [(1, 3)], 10)
        self.tdc = random_registers(random.Random(13))

    def test_random_patterns_preserve_chain_lengths_and_defaults(self):
        defaults = TDCreg()
        widths = lambda tdc: [sum(len("".join(f)) for f in getattr(tdc, name))
                              for name, _ in TDC_CHAINS]
        self.assertEqual(widths(self.tdc), widths(defaults))
        self.assertEqual(sum(widths(self.tdc)), 245)
        self.assertEqual(self.tdc.control_0, defaults.control_0)
        self.assertEqual(self.tdc.control_1, defaults.control_1)
        self.assertEqual([len("".join("".join(f) for f in a.setup))
                          for a in self.tdc.ASD_list], [55, 55, 55])
        self.assertNotEqual(self.tdc.setup_0, defaults.setup_0)
        self.assertEqual(defaults.setup_0, TDCreg().setup_0)

    def test_tdc_initializes_fixed_controls_once_and_checks_three_setup_chains(self):
        status = ("0" + format(int(crc_cal(self.tdc), 16), "032b"))[::-1]
        with patch("pop_jtag_debug.SCA_clk_div") as clock, patch(
            "tab_mezz.SCA_JTAG_go", return_value=status
        ) as jtag:
            valid, _ = self.worker._test(self.tdc, 1, 3, "TDC")
        self.assertTrue(valid)
        self.assertEqual(clock.call_args.kwargs["which_csm"], 1)
        self.controller.Mezz_enable.assert_called_once_with(3, which_csm=1, verbose=False)
        self.assertFalse(clock.call_args.kwargs["verbose"])
        self.assertEqual([int(c.kwargs["ir_value"], 2) for c in jtag.call_args_list],
                         [SCA_share.TDC_CONTROL0, SCA_share.TDC_CONTROL1] +
                         [ir for _, ir in TDC_CHAINS] + [SCA_share.TDC_STATUS0])
        self.assertTrue(all(c.kwargs["which_csm"] == 1 for c in jtag.call_args_list))
        self.assertTrue(all(c.kwargs["verbose"] is False for c in jtag.call_args_list))
        with patch("pop_jtag_debug.SCA_clk_div"), patch(
            "tab_mezz.SCA_JTAG_go", return_value=status
        ) as jtag:
            self.assertTrue(self.worker._test(self.tdc, 1, 3, "TDC")[0])
        self.assertEqual([int(c.kwargs["ir_value"], 2) for c in jtag.call_args_list],
                         [ir for _, ir in TDC_CHAINS] + [SCA_share.TDC_STATUS0])

    def test_tdc_bad_crc_and_truncated_readback_fail(self):
        good = ("0" + format(int(crc_cal(self.tdc), 16), "032b"))[::-1]
        bad = ("1" if good[0] == "0" else "0") + good[1:]
        for response in (bad, good[:-1], None, "x" * 33):
            with self.subTest(response=response), patch("pop_jtag_debug.SCA_clk_div"), patch(
                "tab_mezz.SCA_JTAG_go", return_value=response
            ):
                self.assertFalse(self.worker._test(self.tdc, 1, 3, "TDC")[0])

    def test_asd_writes_then_reads_all_three_and_detects_each_chip_error(self):
        self.worker.controls_initialized.add((1, 3))
        expected = self.controller._asd_dr_value(self.tdc)
        for bit in (None, 0, 55, 110):
            response = expected if bit is None else (
                expected[:bit] + ("1" if expected[bit] == "0" else "0") + expected[bit + 1:])
            with self.subTest(bit=bit), patch("pop_jtag_debug.SCA_clk_div"), patch(
                "tab_mezz.SCA_JTAG_go", return_value=response[::-1]
            ) as jtag:
                self.assertEqual(self.worker._test(self.tdc, 1, 3, "ASD")[0], bit is None)
                self.assertEqual([int(c.kwargs["ir_value"], 2) for c in jtag.call_args_list],
                                 [SCA_share.ASD_WRITE, SCA_share.ASD_READ])
                self.assertEqual(jtag.call_args_list[0].kwargs["dr_value"], expected)

    def test_asd_preserves_fixed_controls_and_random_tdc_pattern(self):
        original = self.tdc.control_0
        original_crc = crc_cal(self.tdc)
        expected = self.controller._asd_dr_value(self.tdc)
        with patch("pop_jtag_debug.SCA_clk_div"), patch(
            "tab_mezz.SCA_JTAG_go", return_value=expected[::-1]
        ):
            self.assertTrue(self.worker._test(self.tdc, 1, 3, "ASD")[0])
        self.assertIs(self.tdc.control_0, original)
        self.assertEqual(crc_cal(self.tdc), original_crc)

    def test_randomization_preserves_custom_configured_controls(self):
        template = TDCreg()
        template.debug_port_select[0] = "0000"
        template.phase_clk160[0] = "10001"
        template.ePllIcp[0] = "0110"
        for seed in range(5):
            tdc = random_registers(random.Random(seed), template)
            self.assertEqual(tdc.control_0, template.control_0)
            self.assertEqual(tdc.control_1, template.control_1)
            self.assertNotEqual(tdc.setup_0, template.setup_0)

    def test_transport_write_errors_propagate(self):
        with patch("pop_jtag_debug.SCA_clk_div"), patch(
            "tab_mezz.SCA_JTAG_go", side_effect=RuntimeError("write timeout")
        ):
            with self.assertRaisesRegex(RuntimeError, "write timeout"):
                self.worker._test(self.tdc, 1, 3, "TDC")

    def test_loop_counts_failure_once_continues_and_stops(self):
        results = []

        def result(*args):
            results.append(args)
            if len(results) == 4:
                self.worker.stop()

        self.worker.result.connect(result)
        with patch.object(self.worker, "_test", side_effect=[
            RuntimeError("timeout"), (False, "multiple bad bits"), (True, "ok"), (True, "ok")
        ]) as test, patch("builtins.print") as output:
            self.worker.run()
        self.assertEqual(test.call_count, 4)
        self.assertEqual(output.call_count, 2)
        self.assertIn("TDC error: timeout", output.call_args_list[0].args[0])
        self.assertIn("ASD error: multiple bad bits", output.call_args_list[1].args[0])
        self.assertEqual([r[2:4] for r in results],
                         [("TDC", False), ("ASD", False), ("TDC", True), ("ASD", True)])
        dialog = JTAGDebugDialog(self.controller, [(1, 3)])
        for args in results:
            dialog._result(*args)
        self.assertEqual(dialog.counts[(1, 3)], [2, 1, 2, 1])
        self.assertIn("2 tests, 1 errors", dialog.totals.text())
        dialog.close()

    def test_closing_running_dialog_requests_stop_and_keeps_worker_alive(self):
        dialog = JTAGDebugDialog(self.controller, [(1, 3)])
        worker = Mock()
        dialog.worker = worker
        dialog.reject()
        worker.stop.assert_called_once()
        self.assertIs(dialog.worker, worker)
        self.assertFalse(dialog.stop_button.isEnabled())
        self.assertEqual(dialog.pending_action, "close")
        dialog._finished()
        self.assertIsNone(dialog.worker)
        self.assertTrue(dialog.start_button.isEnabled())
        dialog.close()

    def test_continue_resumes_next_test_with_same_pattern(self):
        self.worker.result.connect(lambda *args: self.worker.stop())
        with patch.object(self.worker, "_test", return_value=(True, "ok")) as test:
            self.worker.run()
            pattern = test.call_args.args[0]
            self.assertEqual(test.call_args.args[-1], "TDC")
            self.worker.stop_requested.clear()
            self.worker.run()
            self.assertEqual(test.call_args.args[-1], "ASD")
            self.assertIs(test.call_args.args[0], pattern)
            self.assertEqual(test.call_count, 2)

    def test_reset_stops_then_clears_results(self):
        dialog = JTAGDebugDialog(self.controller, [(1, 3)])
        dialog._result(1, 3, "TDC", False, "CRC mismatch")
        worker = Mock()
        dialog.worker = worker
        dialog.reset()
        worker.stop.assert_called_once()
        self.assertEqual(dialog.counts[(1, 3)], [1, 1, 0, 0])
        dialog._result(1, 3, "ASD", True, "ok")
        dialog._finished()
        self.assertEqual(dialog.counts[(1, 3)], [0, 0, 0, 0])
        self.assertEqual(dialog.last_error.text(), "")
        self.assertEqual(dialog.status.text(), "Ready")
        self.assertFalse(dialog.continue_button.isEnabled())
        self.assertIsNone(dialog.paused_worker)
        worker.deleteLater.assert_called_once()
        dialog.close()

    def test_start_stop_thread_keeps_counters_and_can_restart(self):
        dialog = JTAGDebugDialog(self.controller, [(1, 3)])

        def test(worker, tdc, csm, mezz, kind):
            worker.stop_requested.wait(0.002)
            return True, "ok"

        with patch.object(JTAGDebugWorker, "_test", test):
            for action in (dialog.start, dialog.continue_test, dialog.start):
                previous = dialog.counts[(1, 3)][:]
                action()
                worker = dialog.worker
                loop = QtCore.QEventLoop()
                worker.result.connect(lambda *args: dialog.stop())
                worker.finished.connect(loop.quit)
                timer = QtCore.QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(dialog.stop)
                timer.start(2000)
                loop.exec_()
                timer.stop()
                self.assertIsNone(dialog.worker)
                self.assertGreaterEqual(dialog.counts[(1, 3)][0], 1)
                self.assertEqual(dialog.counts[(1, 3)][1], 0)
                self.assertTrue(dialog.start_button.isEnabled())
                self.assertTrue(dialog.continue_button.isEnabled())
                if action == dialog.continue_test:
                    self.assertGreater(sum(dialog.counts[(1, 3)]), sum(previous))
        dialog.close()


if __name__ == "__main__":
    unittest.main()
