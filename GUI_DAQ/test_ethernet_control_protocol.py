import unittest
from unittest.mock import Mock

from ethernet_control_protocol import (
    CONTROL_ETHERTYPE,
    CONTROL_MAGIC,
    FPGA_READ,
    FPGA_WRITE,
    LPGBT_WRITE,
    EthernetControlClient,
    EthernetControlError,
    MONITOR_ETHERTYPE,
    MONITOR_MAGIC,
    PROTOCOL_VERSION,
    build_request_frame,
    parse_response,
)
from ethernet_jtag_protocol import FPGA_MAC


HOST_MAC = bytes.fromhex("e8393563c6c1")


class EthernetControlProtocolTest(unittest.TestCase):
    def test_fpga_timeout_preserves_status_and_opcode(self):
        client = EthernetControlClient(lambda: "test")
        client._source_mac = HOST_MAC
        client._ids = iter([42])
        port = Mock()
        client._ensure_port = lambda: port
        frame = bytearray(build_request_frame(
            HOST_MAC, ethertype=CONTROL_ETHERTYPE, request_id=42,
            opcode=LPGBT_WRITE))
        frame[0:6] = HOST_MAC
        frame[6:12] = FPGA_MAC
        frame[19] |= 0x80
        frame[20] = 3
        frame[23] = 0
        port.receive_frame.return_value = bytes(frame)
        with self.assertRaises(EthernetControlError) as caught:
            client.request(LPGBT_WRITE)
        self.assertEqual(caught.exception.status, 3)
        self.assertEqual(caught.exception.opcode, LPGBT_WRITE)
        self.assertEqual(caught.exception.detail, 0)

    def test_control_request_layout(self):
        payload = bytes.fromhex(
            "a55ac300112233445566778899aabbccddeeffab"
        )
        frame = build_request_frame(
            HOST_MAC,
            ethertype=CONTROL_ETHERTYPE,
            request_id=0x12345678,
            opcode=FPGA_WRITE,
            target=2,
            subtarget=3,
            address=0x0035,
            trans_id=0x5A,
            channel=0x13,
            command=0x07,
            sca_address=0x22,
            argument=0xCAFEBABE,
            payload=payload,
        )
        self.assertEqual(len(frame), 60)
        self.assertEqual(frame[0:6], FPGA_MAC)
        self.assertEqual(frame[6:12], HOST_MAC)
        self.assertEqual(frame[12:14], CONTROL_ETHERTYPE.to_bytes(2, "big"))
        self.assertEqual(frame[14:18], CONTROL_MAGIC)
        self.assertEqual(frame[18], PROTOCOL_VERSION)
        self.assertEqual(frame[19], FPGA_WRITE)
        self.assertEqual(frame[21:24], bytes((2, 3, 20)))
        self.assertEqual(frame[24:28], bytes.fromhex("12345678"))
        self.assertEqual(frame[28:38], bytes.fromhex("00355a130722cafebabe"))
        self.assertEqual(frame[40:60], payload)

    def test_monitor_response_layout(self):
        data = bytes(range(20))
        frame = bytearray(60)
        frame[0:6] = HOST_MAC
        frame[6:12] = FPGA_MAC
        frame[12:14] = MONITOR_ETHERTYPE.to_bytes(2, "big")
        frame[14:18] = MONITOR_MAGIC
        frame[18] = PROTOCOL_VERSION
        frame[19] = 0x80 | FPGA_READ
        frame[20:24] = bytes((0, 1, 9, len(data)))
        frame[24:28] = bytes.fromhex("89abcdef")
        frame[28:31] = bytes.fromhex("000500")
        frame[36:56] = data

        response = parse_response(bytes(frame))
        self.assertIsNotNone(response)
        self.assertEqual(response.ethertype, MONITOR_ETHERTYPE)
        self.assertEqual(response.opcode, FPGA_READ)
        self.assertEqual(response.request_id, 0x89ABCDEF)
        self.assertEqual(response.target, 1)
        self.assertEqual(response.subtarget, 9)
        self.assertEqual(response.address, 5)
        self.assertEqual(response.data, data)

    def test_class_magic_must_match(self):
        frame = bytearray(
            build_request_frame(
                HOST_MAC,
                ethertype=MONITOR_ETHERTYPE,
                request_id=1,
                opcode=FPGA_READ,
            )
        )
        frame[19] |= 0x80
        frame[14:18] = CONTROL_MAGIC
        self.assertIsNone(parse_response(bytes(frame)))


if __name__ == "__main__":
    unittest.main()
