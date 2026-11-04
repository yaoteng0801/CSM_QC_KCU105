import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PyQt5 import QtCore, QtWidgets

from pop_mezz_monitor_test import MezzMonitorTestDialog, MezzMonitorTestWorker, MUX_NAMES
from SCA_share import SCA_share
from sca_transaction_ids import next_sca_transaction_id
from TDC_config_low_level_function import SCA_config as real_sca_config


class MezzMonitorTestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.controller = SimpleNamespace(
            eth=object(), mezz_per_CSM=20,
            get_monitor_limits=lambda: {"AVDD": (0, 10), "DVDD": (0, 10), "Temp": (-100, 100)},
            cell_list=[[SimpleNamespace(label_list=[Mock() for _ in range(3)])
                        for _ in range(20)] for _ in range(2)],
        )
        self.trans_id = 0xFD

        def next_id():
            self.trans_id = next_sca_transaction_id(self.trans_id)
            return self.trans_id

        self.controller.get_transID = next_id
        self.worker = MezzMonitorTestWorker(self.controller, [(1, 0)])
        self.current_mux = None

    def config(self, eth, **kwargs):
        if kwargs["channel"] == SCA_share.CR_CHANNEL:
            return [SCA_share.CR_CHANNEL, 0, 0]
        if kwargs["command"] == SCA_share.ADC_W_MUX:
            self.current_mux = kwargs["data"]
            return [SCA_share.ADC_CHANNEL, 0, 0]
        values = {"AVDD": 2048, "AVDD_GND": 0, "DVDD": 1024,
                  "DVDD_GND": 0, "TEMP": 1024, "TEMP_GND": 0}
        adc = {int(self.worker.mapping[name]["0"]): value for name, value in values.items()}
        return [SCA_share.ADC_CHANNEL, 0, adc[self.current_mux]]

    def test_readings_routing_and_initialization_once(self):
        with patch("pop_mezz_monitor_test.SCA_connect") as connect, patch(
            "pop_mezz_monitor_test.SCA_config", side_effect=self.config
        ) as config, patch("TDC_config_low_level_function.SCA_config", config), patch("builtins.print") as output:
            for _ in range(2):
                values, valid, detail = self.worker._test(1, 0)
                self.assertTrue(valid)
                self.assertEqual(detail, "")
                self.assertAlmostEqual(values["AVDD"], 3.35)
                self.assertAlmostEqual(values["DVDD"], 1.675)
                self.assertAlmostEqual(values["Temp"], 25.0)
        connect.assert_called_once()
        self.assertEqual(connect.call_args.kwargs["which_csm"], 1)
        self.assertEqual(connect.call_args.kwargs["sca_enable"], 1)
        self.assertEqual(config.call_count, 25)
        self.assertTrue(all(c.kwargs["which_csm"] == 1 for c in config.call_args_list))
        self.assertTrue(all(1 <= c.kwargs["transID"] <= 254 for c in config.call_args_list))
        output.assert_not_called()

    def test_multiple_read_failures_count_once_and_retry_initialization(self):
        def failing(eth, **kwargs):
            if kwargs["command"] == SCA_share.ADC_GO and self.current_mux in (
                int(self.worker.mapping["AVDD"]["0"]), int(self.worker.mapping["DVDD"]["0"])
            ):
                raise RuntimeError("reply timeout")
            return self.config(eth, **kwargs)

        with patch("pop_mezz_monitor_test.SCA_connect") as connect, patch(
            "pop_mezz_monitor_test.SCA_config", side_effect=failing
        ) as config, patch("TDC_config_low_level_function.SCA_config", config):
            values, valid, detail = self.worker._test(1, 0)
            self.assertFalse(valid)
            self.assertIsNone(values["AVDD"])
            self.assertIsNone(values["DVDD"])
            self.assertEqual(values["Temp"], 25.0)
            self.assertIn("AVDD: reply timeout", detail)
            self.assertIn("DVDD: reply timeout", detail)
            self.assertNotIn((1, 0), self.worker.initialized)
            self.worker._test(1, 0)
            self.assertEqual(connect.call_count, 2)
        dialog = MezzMonitorTestDialog(self.controller, [(1, 0)])
        dialog._result(1, 0, values, valid, detail)
        self.assertEqual(dialog.counts[(1, 0)], [1, 1])
        self.assertIn("DVDD: reply timeout", dialog.error_history.toPlainText())
        self.assertEqual(dialog.table.item(0, 3).text(), "NA")
        dialog.reset()
        self.assertEqual(dialog.counts[(1, 0)], [0, 0])
        self.assertEqual(dialog.error_history.toPlainText(), "")
        dialog.close()

    def test_invalid_adc_reply_is_error(self):
        with patch("pop_mezz_monitor_test.SCA_connect"), patch(
            "pop_mezz_monitor_test.SCA_config",
            return_value=[SCA_share.ADC_CHANNEL, 0, 4096]
        ) as config, patch("TDC_config_low_level_function.SCA_config", config):
            values, valid, detail = self.worker._test(1, 0)
        self.assertFalse(valid)
        self.assertTrue(all(value is None for value in values.values()))
        self.assertEqual(detail.count("Invalid ADC reply"), len(MUX_NAMES))

    def test_out_of_range_readings_fail_once_without_reinitializing_adc(self):
        from mezz_monitor_limits import DEFAULT_MONITOR_LIMITS
        self.worker.limits = dict(DEFAULT_MONITOR_LIMITS)
        with patch("pop_mezz_monitor_test.SCA_connect") as connect, patch(
            "pop_mezz_monitor_test.SCA_config", side_effect=self.config
        ) as command, patch("TDC_config_low_level_function.SCA_config", command):
            values, valid, detail = self.worker._test(1, 0)
            self.assertFalse(valid)
            self.assertIn("AVDD=3.350 V outside", detail)
            self.assertIn("DVDD=1.675 V outside", detail)
            self.assertNotIn("Temp=25.000 °C outside", detail)
            self.worker._test(1, 0)
            connect.assert_called_once()
        self.controller.get_monitor_limits = lambda: dict(DEFAULT_MONITOR_LIMITS)
        dialog = MezzMonitorTestDialog(self.controller, [(1, 0)])
        dialog._result(1, 0, values, valid, detail)
        self.assertEqual(dialog.counts[(1, 0)], [1, 1])
        for column in (3, 4):
            self.assertEqual(dialog.table.item(0, column).foreground().color().name(), "#ff0000")
        self.assertNotEqual(dialog.table.item(0, 5).foreground().color().name(), "#ff0000")
        self.controller.cell_list[1][0].label_list[0].setStyleSheet.assert_called_with(
            "color: red; font-weight: bold;")
        dialog.close()

    def test_enable_ack_is_ignored_without_errors_or_reconnect(self):
        attempts = []
        self.controller.eth = SimpleNamespace(request=Mock(return_value=SimpleNamespace(data=bytes(9))))

        def config(eth, **kwargs):
            if kwargs["channel"] == SCA_share.CR_CHANNEL:
                attempts.append(kwargs["transID"])
                return real_sca_config(eth, **kwargs)
            return self.config(eth, **kwargs)

        messages = []
        self.worker.message_out.connect(messages.append)
        with patch("pop_mezz_monitor_test.SCA_connect") as connect, patch(
            "pop_mezz_monitor_test.SCA_config", side_effect=config
        ) as command, patch("TDC_config_low_level_function.SCA_config", command), patch("builtins.print"):
            values, valid, detail = self.worker._test(1, 0)
        self.assertTrue(valid)
        self.assertEqual(detail, "")
        self.assertEqual(values["Temp"], 25.0)
        self.assertEqual(attempts, [254])
        connect.assert_called_once()
        self.assertEqual(messages, [])
        dialog = MezzMonitorTestDialog(self.controller, [(1, 0)])
        dialog._result(1, 0, values, valid, detail)
        self.assertEqual(dialog.counts[(1, 0)], [1, 0])
        self.assertEqual(dialog.error_history.toPlainText(), "")
        dialog.close()

    def test_loop_continues_after_initialization_error_and_prints_errors_only(self):
        worker = MezzMonitorTestWorker(self.controller, [(0, 0), (1, 0)])
        results = []

        def result(*args):
            results.append(args)
            if len(results) == 2:
                worker.stop()

        worker.result.connect(result)
        with patch.object(worker, "_test", side_effect=[
            RuntimeError("connect failed"), ({"AVDD": 3.3}, True, "")
        ]), patch("builtins.print") as output:
            worker.run()
        self.assertEqual([r[:2] for r in results], [(0, 0), (1, 0)])
        self.assertEqual([r[3] for r in results], [False, True])
        output.assert_called_once()
        self.assertIn("connect failed", output.call_args.args[0])
        self.assertEqual(worker.target_index, 0)

    def test_threaded_start_stop_continue_reset_and_close(self):
        dialog = MezzMonitorTestDialog(self.controller, [(1, 0)])

        def test(worker, csm, mezz):
            worker.stop_requested.wait(0.002)
            return {"AVDD": 3.3, "DVDD": 1.2, "Temp": 25}, True, ""

        with patch.object(MezzMonitorTestWorker, "_test", test):
            for action in (dialog.start, dialog.continue_test):
                before = dialog.counts[(1, 0)][0]
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
                self.assertGreater(dialog.counts[(1, 0)][0], before)
                self.assertEqual(dialog.counts[(1, 0)][1], 0)
                self.assertTrue(dialog.continue_button.isEnabled())
                self.assertEqual(dialog.table.item(0, 3).text(), "3.300")
        dialog.reset()
        self.assertEqual(dialog.counts[(1, 0)], [0, 0])
        self.assertFalse(dialog.continue_button.isEnabled())
        dialog.close()


if __name__ == "__main__":
    unittest.main()
