import unittest

from Signal import SignalType, decode_word5


def word5(value: int) -> bytes:
    return int(value & ((1 << 40) - 1)).to_bytes(5, "big")


class ChamberEventIdTest(unittest.TestCase):
    def test_triggerless_header_and_trailer_expose_chamber(self):
        sequence = 0x12345
        event_id = (1 << 19) | sequence
        header = decode_word5(
            word5((0xA << 36) | (event_id << 16)), acquisition_mode=1
        )
        trailer = decode_word5(
            word5((0xC << 36) | (event_id << 16) | 3), acquisition_mode=1
        )

        self.assertEqual(header.type, SignalType.EVENT_HEADER)
        self.assertEqual(header.header.event_id20, event_id)
        self.assertEqual(header.header.chamber_id, 1)
        self.assertEqual(header.header.chamber_event_id, sequence)
        self.assertEqual(trailer.type, SignalType.EVENT_TRAILER)
        self.assertEqual(trailer.trailer.chamber_id, 1)
        self.assertEqual(trailer.trailer.chamber_event_id, sequence)


if __name__ == "__main__":
    unittest.main()
