"""Readback pages 6, 7 and 8 decode for every MiniDAQ build, with all columns kept."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PyQt5 import QtWidgets

from StyleSheet import LedGray, LedGreen, LedRed
from ethernet_control_protocol import EthernetControlError, LPGBT_READ
from firmware_links import detect_uplink_count, downlink_count
from pop_link_setup import pop_link_setup
from pop_prbs import pop_prbs


class Client:
    """Answers lpGBT requests the way ethernet_control_engine.sv does."""

    def __init__(self, uplinks, other_status=None):
        self._lock = threading.RLock()
        self.uplinks = uplinks
        self.other_status = other_status
        self.targets = []

    def request(self, opcode, **kwargs):
        if opcode == LPGBT_READ:
            self.targets.append(kwargs["target"])
            if kwargs["target"] >= self.uplinks:
                raise EthernetControlError("invalid request", status=1, opcode=opcode)
            if self.other_status is not None:
                raise EthernetControlError("other", status=self.other_status, opcode=opcode)
        return SimpleNamespace()


def bits(value):
    return format(value, "0160b")


def pack(*fields):
    """Concatenate (value, width) fields from bit 0, as MiniDAQ_reg.sv does."""
    value, shift = 0, 0
    for field, width in fields:
        value |= field << shift
        shift += width
    return value


class DetectionTests(unittest.TestCase):
    def test_counts_follow_the_targets_the_firmware_accepts(self):
        for uplinks, downlinks in ((1, 1), (2, 1), (4, 2)):
            self.assertEqual(detect_uplink_count(Client(uplinks)), uplinks)
            self.assertEqual(downlink_count(uplinks), downlinks)

    def test_no_ic_reply_still_proves_the_link_exists(self):
        # CSM1 not cabled on 4-uplink firmware; slave in raw PRBS on the KCU105.
        self.assertEqual(detect_uplink_count(Client(4, other_status=3)), 4)
        self.assertEqual(detect_uplink_count(Client(2, other_status=3)), 2)

    def test_absent_targets_are_probed_before_any_link_is_read(self):
        client = Client(2)
        detect_uplink_count(client)
        self.assertEqual(client.targets, [3, 2, 1])

    def test_busy_or_transport_failure_is_not_mistaken_for_a_count(self):
        with self.assertRaises(EthernetControlError):
            detect_uplink_count(Client(4, other_status=2))

        class Dead(Client):
            def request(self, opcode, **kwargs):
                raise EthernetControlError("Ethernet transport timeout")
        with self.assertRaises(EthernetControlError):
            detect_uplink_count(Dead(4))


class DialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def prbs(self, uplinks):
        dialog = pop_prbs(Client(uplinks), [0x55])
        self.addCleanup(dialog.close)
        return dialog

    def test_prbs_two_uplink_status_keeps_csm1_columns(self):
        dialog = self.prbs(2)
        self.assertEqual(len(dialog.mode_controls), 4)
        status = bits(pack((0, 32), (0b01, 8), (0b10, 8)))
        low = bits(pack((0x1111, 16), (0x2222, 16)))
        high = bits(pack((0x000A, 16), (0x000B, 16)))
        with patch("pop_prbs.fpga_readback", side_effect=(status, low, high)):
            dialog.update_prbs_status()
        self.assertEqual([led.styleSheet() for led in dialog.led_locked],
                         [LedGreen, LedRed, LedGray, LedGray])
        self.assertEqual([led.styleSheet() for led in dialog.led_error],
                         [LedGreen, LedRed, LedGray, LedGray])
        self.assertEqual([label.text() for label in dialog.bit_error],
                         ["000A1111", "000B2222", "n/a", "n/a"])
        self.assertIn("2 uplinks", dialog.message_label.text())

    def test_prbs_reading_seen_on_the_board(self):
        # The old fixed decode showed "03000300" under CSM1 master for this page.
        dialog = self.prbs(2)
        page = bits(pack((0, 32), (0x00, 8), (0x03, 8)))
        with patch("pop_prbs.fpga_readback", side_effect=(page, page, page)):
            dialog.update_prbs_status()
        self.assertEqual([led.styleSheet() for led in dialog.led_locked][:2], [LedRed, LedRed])
        self.assertEqual([led.styleSheet() for led in dialog.led_error][:2], [LedRed, LedRed])
        self.assertEqual(dialog.bit_error[2].text(), "n/a")

    def test_prbs_four_uplink_status(self):
        dialog = self.prbs(4)
        status = bits(pack((0, 64), (0b0101, 8), (0b1010, 8)))
        low = bits(pack((1, 16), (2, 16), (3, 16), (4, 16)))
        with patch("pop_prbs.fpga_readback", side_effect=(status, low, "0"*160)):
            dialog.update_prbs_status()
        self.assertEqual([led.styleSheet() for led in dialog.led_locked],
                         [LedGreen, LedRed, LedGreen, LedRed])
        self.assertEqual([led.styleSheet() for led in dialog.led_error],
                         [LedGreen, LedRed, LedGreen, LedRed])
        self.assertEqual([label.text() for label in dialog.bit_error],
                         ["00000001", "00000002", "00000003", "00000004"])
        self.assertEqual(dialog.message_label.text(), "PRBS status updated.")

    def test_counts_are_detected_once_per_dialog(self):
        dialog = self.prbs(2)
        with patch("pop_prbs.fpga_readback", return_value="0"*160):
            dialog.update_prbs_status()
            first = list(dialog.eth.targets)
            dialog.update_prbs_status()
        self.assertEqual(dialog.eth.targets, first)

    def link_setup(self, uplinks, status, uplink, downlink):
        dialog = pop_link_setup(Client(uplinks))
        self.addCleanup(dialog.close)
        dialog._select_fpga_mapping = lambda: None
        with patch("pop_link_setup.fpga_readback",
                   side_effect=(bits(status), bits(uplink), bits(downlink))):
            dialog.refresh_from_fpga()
        return dialog

    def test_link_setup_two_uplinks_keeps_csm1_disabled(self):
        uplink = pack((0b01, 2), (0b10, 2), (0b11, 2), (0b10, 2), (0, 2), (0b01, 2),
                      (pack((5, 3), (2, 3)), 6), (0b10, 2), (pack((3, 3), (6, 3)), 6))
        downlink = pack((1, 1), (0, 1), (1, 1), (0x55, 7), (1, 1), (0, 1), (0x2AB, 10),
                        (1, 1), (1, 1), (0x123, 10), (1, 1), (0x44, 7))
        dialog = self.link_setup(2, 0b11 << 8 | 0b1, uplink, downlink)

        controls = dialog.uplink_controls
        self.assertEqual([c.isChecked() for c in controls["interleaver_bypass"]],
                         [True, False, False, False])
        self.assertEqual([c.isChecked() for c in controls["fec_bypass"]],
                         [False, True, False, False])
        self.assertEqual([c.isChecked() for c in controls["rx_polarity"]],
                         [False, True, False, False])
        self.assertEqual([c.isChecked() for c in controls["phase_force"]],
                         [True, False, False, False])
        self.assertEqual([c.value() for c in controls["phase_calib"]], [5, 2, 0, 0])
        self.assertEqual([c.isEnabled() for c in controls["rx_polarity"]],
                         [True, True, False, False])
        self.assertEqual([l.text() for l in dialog.uplink_status["ready"]],
                         ["Yes", "Yes", "—", "—"])
        self.assertEqual([l.text() for l in dialog.uplink_status["fec_corrected"]],
                         ["No", "Yes", "—", "—"])
        self.assertEqual([l.text() for l in dialog.uplink_status["phase"]],
                         ["3", "6", "—", "—"])

        down = dialog.downlink_controls
        self.assertEqual([c.value() for c in down["tx_pi_calib"]], [0x55, 0])
        self.assertEqual([c.value() for c in down["phase_calib"]], [0x2AB, 0])
        self.assertEqual([c.isChecked() for c in down["phase_force"]], [True, False])
        self.assertEqual([c.isEnabled() for c in down["phase_force"]], [True, False])
        self.assertEqual(dialog.downlink_status["tx_pi_phase"][0].text(), str(0x44))

        writes = {}
        dialog._write_register = writes.__setitem__
        dialog.apply_uplinks()
        self.assertEqual(writes, {46: 0b01, 47: 0b10, 48: 0b11, 49: 0b10,
                                  51: pack((5, 3), (2, 3)), 52: 0b01})

    def test_link_setup_four_uplinks_matches_upstream_layout(self):
        # Bit positions from the comments above pages 7 and 8 in MiniDAQ_reg.sv.
        uplink = (0b0101 << 12) | (0b1000 << 20) | (0o7654 << 24) | (0b0100 << 36) | (0o1234 << 40)
        downlink = (0b10 << 22) | (0b01 << 44) | (0b11 << 68)
        dialog = self.link_setup(4, 0b1111 << 8 | 0b11, uplink, downlink)
        controls = dialog.uplink_controls
        self.assertEqual([c.isChecked() for c in controls["rx_polarity"]],
                         [True, False, True, False])
        self.assertEqual([c.isChecked() for c in controls["phase_force"]],
                         [False, False, False, True])
        self.assertEqual([c.value() for c in controls["phase_calib"]], [4, 5, 6, 7])
        self.assertTrue(all(c.isEnabled() for c in controls["rx_polarity"]))
        self.assertEqual([l.text() for l in dialog.uplink_status["phase"]], ["4", "3", "2", "1"])
        self.assertEqual([l.text() for l in dialog.uplink_status["fec_corrected"]],
                         ["No", "No", "Yes", "No"])
        down = dialog.downlink_controls
        self.assertEqual([c.isChecked() for c in down["tx_polarity"]], [False, True])
        self.assertEqual([c.isChecked() for c in down["phase_force"]], [True, False])
        self.assertEqual([l.text() for l in dialog.downlink_status["tx_aligned"]], ["Yes", "Yes"])


if __name__ == "__main__":
    unittest.main()
