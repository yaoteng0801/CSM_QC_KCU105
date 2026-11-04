"""Trigger counts follow the acquisition-mode wire format in both decoders."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from DecodeThread import native_decoder_cpp
from native_decoder.benchmark_decoder import run_decoder, triggered_event, triggerless_event, word


class DecoderTriggerCountTests(unittest.TestCase):
    def test_header_triggers_and_standalone_trigger_words(self):
        triggered = b"".join(triggered_event(i, 3) for i in range(3))
        triggerless = b"".join(triggerless_event(i, 3) for i in range(3))
        first = triggerless_event(0, 3)
        with_triggers = (word((0xE << 36) | 42) + first[:5] +
                         word((0xE << 36) | 77) + first[5:] +
                         b"".join(triggerless_event(i, 3) for i in (1, 2)))
        backends = [False, True] if native_decoder_cpp is not None else [False]
        for use_native in backends:
            for mode, data, expected in ((0, triggered, 3), (1, triggerless, 0), (1, with_triggers, 2)):
                with self.subTest(native=use_native, mode=mode, expected_triggers=expected):
                    _, snapshot, _ = run_decoder(data, mode, 3, use_native)
                    self.assertEqual(snapshot.headers, 3)
                    self.assertEqual(snapshot.trailers, 3)
                    self.assertEqual(snapshot.valid_events, 3)
                    self.assertEqual(snapshot.triggers, expected)


if __name__ == "__main__":
    unittest.main()
