import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tab_csm import tab_csm
from tab_mezz import tab_mezz
from tab_sca import tab_sca
from sca_transaction_ids import validate_sca_transaction_id
from TDC_config_low_level_function import (
    SCA_config, SCA_JTAG_go, SCA_enable_adc, SCAReplyMismatchError, sca_reply_retry_reporting,
)
from ethernet_control_protocol import (
    build_request_frame, CONTROL_ETHERTYPE, SCA_COMMAND, SCA_CONNECT, SCA_RESET, FPGA_READ,
)
from TDCreg import TDCreg
from SCA_share import SCA_share
from crc8_D81 import crc_cal


class SCATransactionIDTests(unittest.TestCase):
    def test_all_controllers_skip_reserved_ids_across_repeated_wraps(self):
        for cls in (tab_csm, tab_mezz, tab_sca):
            with self.subTest(controller=cls.__name__):
                controller = object.__new__(cls)
                controller.transID = 0
                values = [controller.get_transID() for _ in range(254 * 4)]
                self.assertEqual(values, list(range(1, 255)) * 4)

    def test_wrap_recovers_from_old_reserved_counter_value(self):
        for cls in (tab_csm, tab_mezz, tab_sca):
            with self.subTest(controller=cls.__name__):
                controller = object.__new__(cls)
                controller.transID = 0xFF
                self.assertEqual(controller.get_transID(), 1)

    def test_invalid_ids_are_rejected_without_byte_truncation(self):
        for value in (-1, 0, 255, 256, 257, 511):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Invalid SCA transaction ID"):
                    validate_sca_transaction_id(value)
                eth = SimpleNamespace(request=Mock())
                with self.assertRaises(ValueError):
                    SCA_config(eth, 2, 0, 0, value, 19, 4, 0x80, 0)
                eth.request.assert_not_called()
                with self.assertRaises(ValueError):
                    build_request_frame(bytes(6), ethertype=CONTROL_ETHERTYPE,
                                        request_id=1, opcode=SCA_COMMAND, trans_id=value)

    def test_connect_reset_and_non_sca_frames_allow_unused_zero_id(self):
        for opcode in (SCA_CONNECT, SCA_RESET, FPGA_READ):
            frame = build_request_frame(bytes(6), ethertype=CONTROL_ETHERTYPE,
                                        request_id=1, opcode=opcode)
            self.assertEqual(frame[30], 0)

    @staticmethod
    def _reply(trans_id=1, channel=19, error=0, data=0x1234):
        return bytes((0, trans_id, channel, error, 4)) + data.to_bytes(4, "big")

    def test_successful_sca_read_and_write_keep_return_format(self):
        for command in (0x80, 0x81):
            eth = SimpleNamespace(request=Mock())
            eth.request.return_value = SimpleNamespace(data=self._reply())
            self.assertEqual(SCA_config(eth, 2, 0, 0, 1, 19, 4, command, 0),
                             [19, 0, 0x1234])

    def test_sca_errors_propagate_for_reads_writes_and_broadcasts(self):
        for command in (0x80, 0x81):
            for prefix in (b"", self._reply()):
                with self.subTest(command=command, broadcast=bool(prefix)):
                    eth = SimpleNamespace(request=Mock())
                    eth.request.return_value = SimpleNamespace(
                        data=prefix + self._reply(error=8))
                    with self.assertRaisesRegex(RuntimeError, "error=0x08.*transaction=0x01"):
                        SCA_config(eth, 15, 0, 0, 1, 19, 4, command, 0)

    def test_unmatched_reply_cannot_look_like_success(self):
        for raw in (b"", self._reply(trans_id=2), self._reply(channel=0)):
            eth = SimpleNamespace(request=Mock())
            eth.request.return_value = SimpleNamespace(data=raw)
            with self.assertRaisesRegex(RuntimeError, "no matching Ethernet reply"):
                SCA_config(eth, 2, 0, 0, 1, 19, 4, 0x80, 0)

    def test_jtag_write_error_stops_before_go(self):
        eth = SimpleNamespace(request=Mock())
        eth.request.return_value = SimpleNamespace(data=self._reply(error=8))
        with self.assertRaisesRegex(RuntimeError, "SCA command failed"):
            SCA_JTAG_go(eth, 1, 2, 0, "10010", "0" * 115, verbose=False)
        self.assertEqual(eth.request.call_count, 1)

    def test_adc_enable_ignores_unmatched_acknowledgement_without_retries_or_logs(self):
        for raw in (b"", self._reply(trans_id=0, channel=0)):
            eth = SimpleNamespace(request=Mock(return_value=SimpleNamespace(data=raw)))
            messages = []
            with sca_reply_retry_reporting(messages.append), patch("builtins.print") as output:
                self.assertIsNone(SCA_enable_adc(eth, Mock(return_value=1), 1, 0))
            eth.request.assert_called_once()
            self.assertEqual(messages, [])
            output.assert_not_called()

    def test_normal_adc_enable_ignores_ack_but_next_adc_reply_is_checked(self):
        eth = SimpleNamespace(request=Mock(return_value=SimpleNamespace(
            data=self._reply(trans_id=0, channel=0))))
        self.assertIsNone(SCA_config(eth, 1, 0, 0, 1, SCA_share.CR_CHANNEL, 4,
                                     SCA_share.CTRL_W_CRD, SCA_share.ENADC_DATA))
        eth.request.assert_called_once()
        eth.request.reset_mock()
        with sca_reply_retry_reporting(lambda message: None), self.assertRaises(SCAReplyMismatchError):
            SCA_config(eth, 1, 0, 0, 2, SCA_share.ADC_CHANNEL, 4, SCA_share.ADC_GO, 1)
        self.assertEqual(eth.request.call_count, 3)

    def test_adc_enable_does_not_retry_real_sca_errors_or_transport_timeouts(self):
        for failure in (SimpleNamespace(data=self._reply(trans_id=1, channel=0, error=8)),
                        RuntimeError("Ethernet reply timeout")):
            eth = SimpleNamespace(request=Mock())
            if isinstance(failure, Exception):
                eth.request.side_effect = failure
            else:
                eth.request.return_value = failure
            with self.assertRaises(RuntimeError):
                SCA_enable_adc(eth, Mock(return_value=1), 1, 0)
            self.assertEqual(eth.request.call_count, 1)

    def test_normal_adc_commands_retry_with_fresh_ids_and_report_recovery(self):
        for channel, command, data in (
            (SCA_share.ADC_CHANNEL, SCA_share.ADC_W_MUX, 12),
            (SCA_share.ADC_CHANNEL, SCA_share.ADC_R_MUX, 0),
            (SCA_share.ADC_CHANNEL, SCA_share.ADC_GO, SCA_share.ADC_GO_DATA),
        ):
            with self.subTest(channel=channel, command=command):
                eth = SimpleNamespace(request=Mock(side_effect=[
                    SimpleNamespace(data=self._reply(trans_id=0, channel=0)),
                    SimpleNamespace(data=self._reply(trans_id=1, channel=channel)),
                ]))
                messages = []
                with sca_reply_retry_reporting(messages.append):
                    result = SCA_config(eth, 1, 0, 0, 254, channel, 4, command, data)
                self.assertEqual(result, [channel, 0, 0x1234])
                self.assertEqual([c.kwargs["trans_id"] for c in eth.request.call_args_list], [254, 1])
                self.assertEqual(len(messages), 1)
                self.assertIn("retrying with transaction=0x01", messages[0])

    def test_normal_adc_recovery_is_bounded_and_real_errors_are_not_retried(self):
        cases = (
            (SimpleNamespace(data=self._reply(trans_id=0, channel=0)), 3),
            (SimpleNamespace(data=self._reply(trans_id=1, channel=SCA_share.ADC_CHANNEL, error=8)), 1),
            (RuntimeError("Ethernet reply timeout"), 1),
        )
        for response, expected_calls in cases:
            eth = SimpleNamespace(request=Mock())
            if isinstance(response, Exception):
                eth.request.side_effect = response
            else:
                eth.request.return_value = response
            with sca_reply_retry_reporting(lambda message: None), self.assertRaises(RuntimeError):
                SCA_config(eth, 1, 0, 0, 1, SCA_share.ADC_CHANNEL, 4, SCA_share.ADC_GO, 1)
            self.assertEqual(eth.request.call_count, expected_calls)

    def test_jtag_gpio_and_other_control_commands_remain_single_attempt(self):
        for channel, command, data in (
            (SCA_share.CR_CHANNEL, SCA_share.CTRL_W_CRD, SCA_share.ENJTAG_DATA),
            (SCA_share.CR_CHANNEL, SCA_share.CTRL_W_CRB, SCA_share.ENGPIO_DATA),
            (SCA_share.GPIO_CHANNEL, SCA_share.GPIO_W_DATAOUT, 0),
            (SCA_share.JTAG_CHANNEL, SCA_share.JTAG_W_FREQ, 10),
            (SCA_share.JTAG_CHANNEL, SCA_share.JTAG_GO, 0),
            (SCA_share.JTAG_CHANNEL, SCA_share.JTAG_R_TDI0, 0),
        ):
            with self.subTest(channel=channel, command=command):
                eth = SimpleNamespace(request=Mock(return_value=SimpleNamespace(
                    data=self._reply(trans_id=0, channel=0))))
                with self.assertRaises(SCAReplyMismatchError):
                    SCA_config(eth, 1, 0, 0, 1, channel, 4, command, data)
                eth.request.assert_called_once()

    def test_normal_configuration_survives_multiple_id_wraps(self):
        controller = object.__new__(tab_mezz)
        controller.eth = object()
        controller.transID = 0xFC
        tdc = TDCreg()
        ids = []

        def jtag(*args, **kwargs):
            ids.append(validate_sca_transaction_id(kwargs["transID"]))
            ir = int(kwargs["ir_value"], 2)
            if ir == SCA_share.TDC_STATUS0:
                return ("0" + f"{int(crc_cal(tdc), 16):032b}")[::-1]
            return kwargs["dr_value"][::-1]

        with patch("tab_mezz.SCA_JTAG_go", side_effect=jtag), patch("builtins.print"):
            for _ in range(100):
                self.assertTrue(controller._write_tdc_once(tdc, which_csm=0))
                self.assertTrue(controller._write_asd_once(tdc, 0, 0))
        self.assertEqual(len(ids), 800)
        self.assertEqual(ids[:4], [253, 254, 1, 2])
        self.assertGreater(ids.count(1), 3)


if __name__ == "__main__":
    unittest.main()
