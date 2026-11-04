import unittest

from Worker_lpGBT import _is_missing_reply_error


class WorkerLpGBTReplyClassificationTests(unittest.TestCase):
    def test_minidaq_reply_timeout_is_missing_reply(self):
        self.assertTrue(
            _is_missing_reply_error(
                "EthernetControlError: MiniDAQ reply timeout; "
                "opcode=0x20, detail=0x00"
            )
        )

    def test_minidaq_ethernet_reply_timeout_is_missing_reply(self):
        self.assertTrue(
            _is_missing_reply_error(
                "EthernetControlError: MiniDAQ Ethernet reply timeout; "
                "opcode=0x20, request_id=0x12345678"
            )
        )

    def test_protocol_failure_with_reply_is_not_missing_reply(self):
        self.assertFalse(
            _is_missing_reply_error(
                "EthernetControlError: MiniDAQ reply overflow; "
                "opcode=0x20, detail=0x00"
            )
        )


if __name__ == "__main__":
    unittest.main()
