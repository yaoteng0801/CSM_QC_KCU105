"""Run the native capture end-to-end tests against the Windows Python port.

test_isolated_hits.NativeIsolationTests compiles native_capture/minidaq_capture.cpp
with g++/libpcap and checks the .dat bytes and MINIDAQ_STATS lines it produces.
Here the same cases run against ``python win_capture.py`` (CaptureEngine +
isolated_hit_filter.py), so the Windows path is held to the native behavior.
Runs on any OS; needs no capture driver (offline pcap input).
"""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import test_isolated_hits as native_tests
from test_isolated_hits import event, hit

ROOT = Path(__file__).resolve().parent
HAVE_QT = importlib.util.find_spec("PyQt5") is not None


class WindowsCaptureParityTests(native_tests.NativeIsolationTests):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="minidaq_win_capture_test_")
        cls.root = Path(cls.temp.name)
        cls.mapping = cls.root / "neighbors.txt"
        cls.mapping.write_text("MINIDAQ_NEIGHBORS_V1\n"
                               "0 0 0 1 1\n1 0 1 1 0\n2 0 2 0\n3 0 0 1 1\n"
                               "640 1 3 1 4\n641 1 4 1 3\n")

    def capture(self, chunks, *, enabled=True, sequence=None, mapping=None):
        path, output = self.root / "test.pcap", self.root / "test.dat"
        with path.open("wb") as f:
            f.write(struct.pack("<IHHIIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
            for i, chunk in enumerate(chunks):
                seq = i if sequence is None else sequence[i]
                packet = bytes(14) + chunk + bytes(2) + struct.pack(">H", seq)
                f.write(struct.pack("<IIII", i, 0, len(packet), len(packet)))
                f.write(packet)
        cmd = [sys.executable, str(ROOT / "win_capture.py"), "--input-pcap", str(path),
               "--output", str(output), "--dispatch-limit", "1"]
        if enabled:
            cmd += ["--isolation-map", str(mapping or self.mapping)]
        result = subprocess.run(cmd, check=True, capture_output=True)
        data = output.read_bytes()
        self.assertEqual(data, result.stdout)  # live stream equals saved stream
        return data, result.stderr.decode()

    @unittest.skipUnless(HAVE_QT, "DecodeThread needs PyQt5")
    def test_filtered_stream_replays_in_python_and_native_decoders(self):
        from native_decoder.benchmark_decoder import run_decoder
        raw = event([hit(0), hit(2), hit(1)]) + event([hit(2)], 2)
        data, _ = self.capture([raw])
        natives = [False]
        if importlib.util.find_spec("native_decoder_cpp") is not None:
            natives.append(True)
        for native in natives:
            with self.subTest(native=native):
                snapshot = run_decoder(data, 1, 2, native)[1]
                self.assertEqual(snapshot.valid_events, 2)
                self.assertEqual(snapshot.hits_total, 2)


class CaptureEngineTests(unittest.TestCase):
    def test_idle_and_filler_words_are_dropped_and_loss_is_counted(self):
        from win_capture import CaptureEngine
        engine = CaptureEngine()
        data = hit(0) + b"\xff" * 5 + bytes([0x05, 0, 0, 0, 0]) + hit(1)
        engine.handle_packet(bytes(14) + data + bytes(2) + struct.pack(">H", 7), 14 + len(data) + 4)
        engine.handle_packet(bytes(14) + hit(2) + bytes(2) + struct.pack(">H", 10), 23)
        self.assertEqual(engine.take_batch(), hit(0) + hit(1) + hit(2))
        self.assertEqual(engine.lost_packets, 2)
        self.assertIn("packets=2 lost=2 bytes=15", engine.stats_line())


if __name__ == "__main__":
    unittest.main()
