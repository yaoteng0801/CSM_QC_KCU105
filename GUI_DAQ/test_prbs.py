import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PyQt5 import QtWidgets
from ethernet_control_protocol import EthernetControlError, FPGA_WRITE, LPGBT_WRITE
from pop_prbs import pop_prbs


class PRBSClient:
    def __init__(self, error=None):
        self._lock = threading.RLock()
        self.error = error
        self.requests = []

    def request(self, opcode, **kwargs):
        self.requests.append((opcode, kwargs))
        if opcode == LPGBT_WRITE:
            if self.error:
                raise self.error
            value = kwargs["payload"][0]
            raw = bytes((kwargs["argument"] * 2, 1, 1, 0, 0x28, 1, value))
            parity = 0
            for byte in raw:
                parity ^= byte
            return SimpleNamespace(data=raw + bytes((parity,)))
        return SimpleNamespace()


class PRBSTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def dialog(self, client, value=0):
        dialog = pop_prbs(client, [value])
        self.addCleanup(dialog.close)
        return dialog

    def test_raw_prbs_missing_ic_reply_still_configures_checker(self):
        for link in range(4):
            for selection, checker in enumerate((1, 3, 4, 5), start=1):
                with self.subTest(link=link, selection=selection):
                    client = PRBSClient(EthernetControlError(
                        "MiniDAQ reply timeout", status=3, opcode=LPGBT_WRITE, detail=0))
                    dialog = self.dialog(client, 0x1111)
                    dialog.mode_controls[link].setCurrentIndex(selection)
                    # PRBS-7 may already be selected on construction.
                    if not client.requests:
                        dialog.set_prbs_mode(link // 2, 115 if link % 2 else 117,
                                             "prbs option", selection)
                    self.assertEqual(client.requests[0][1]["target"], link)
                    opcode, write = client.requests[-1]
                    self.assertEqual((opcode, write["address"]), (FPGA_WRITE, 36))
                    expected = (0x1111 & ~(15 << (4*link))) | (checker << (4*link))
                    self.assertEqual(int.from_bytes(write["payload"], "big"), expected)
                    self.assertEqual(dialog.rxprbssel[0], expected)
                    self.assertIn("verify PRBS lock", dialog.message_label.text())

    def test_unrelated_failures_are_reported_without_configuring_checker(self):
        for error in (
            EthernetControlError("Ethernet transport timeout"),
            EthernetControlError("busy", status=2, opcode=LPGBT_WRITE),
            EthernetControlError("timeout", status=3, opcode=FPGA_WRITE),
        ):
            client = PRBSClient(error)
            dialog = self.dialog(client)
            dialog.mode_controls[0].setCurrentIndex(1)
            self.assertEqual(len(client.requests), 1)
            self.assertEqual(dialog.rxprbssel[0], 0)
            self.assertEqual(dialog.mode_controls[0].currentIndex(), 0)
            self.assertIn("failed", dialog.message_label.text())

    def test_disabling_prbs_requires_a_reply(self):
        client = PRBSClient(EthernetControlError("timeout", status=3, opcode=LPGBT_WRITE))
        dialog = self.dialog(client, 1)
        dialog.mode_controls[0].setCurrentIndex(0)
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(dialog.rxprbssel[0], 1)
        self.assertIn("failed", dialog.message_label.text())

    def test_normal_reply_allows_enable_and_disable(self):
        client = PRBSClient()
        dialog = self.dialog(client)
        dialog.mode_controls[3].setCurrentIndex(4)
        self.assertEqual(dialog.rxprbssel[0], 0x5000)
        dialog.mode_controls[3].setCurrentIndex(0)
        self.assertEqual(dialog.rxprbssel[0], 0)
        self.assertNotIn("failed", dialog.message_label.text())

    def test_reopening_restores_modes_without_hardware_writes(self):
        client = PRBSClient()
        dialog = self.dialog(client, 0x5431)
        self.assertEqual([c.currentIndex() for c in dialog.mode_controls], [1, 2, 3, 4])
        self.assertEqual(client.requests, [])

    def test_incomplete_status_is_reported_without_raising_from_qt_slot(self):
        dialog = self.dialog(PRBSClient())
        with patch("pop_prbs.fpga_readback", return_value=0):
            dialog.update_prbs_status()
        self.assertIn("Incomplete FPGA PRBS status", dialog.message_label.text())
        self.assertEqual([label.text() for label in dialog.bit_error], ["-"] * 4)

    def test_status_and_counters_keep_logical_link_order(self):
        dialog = self.dialog(PRBSClient())
        status = format((0b1010 << 72) | (0b0101 << 64), "0160b")
        low = format((4 << 48) | (3 << 32) | (2 << 16) | 1, "0160b")
        with patch("pop_prbs.fpga_readback", side_effect=(status, low, "0"*160)):
            dialog.update_prbs_status()
        self.assertEqual([label.text() for label in dialog.bit_error],
                         ["00000001", "00000002", "00000003", "00000004"])
        self.assertEqual(dialog.led_locked[0].styleSheet(), dialog.led_locked[2].styleSheet())
        self.assertNotEqual(dialog.led_locked[0].styleSheet(), dialog.led_locked[1].styleSheet())
        self.assertEqual(dialog.message_label.text(), "PRBS status updated.")


if __name__ == "__main__":
    unittest.main()
