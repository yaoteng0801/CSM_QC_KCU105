import os
from pathlib import Path
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from replay_format import replay_modes
from native_decoder.benchmark_decoder import triggerless_event, triggered_event


class ReplayFormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="minidaq_replay_")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "run.dat"
        self.config = self.path.with_name("run_configuration.txt")

    def test_capture_metadata_controls_all_profiles(self):
        self.path.write_bytes(b"")
        for mode, noise in ((0, 0), (1, 0), (1, 1), (1, 2)):
            self.config.write_text(f"[run_context]\nmode: capture\nacquisition_mode: {mode}\nnoise_test_mode: {noise}\n")
            self.assertEqual(replay_modes(self.path, (0, 0))[:2], (mode, noise))

    def test_framing_without_sidecar_and_after_old_replay_overwrite(self):
        for mode, build in ((0, triggered_event), (1, triggerless_event)):
            self.path.write_bytes(b"".join(build(i, 3) for i in (5, 8, 21, 0x80009)))
            self.assertEqual(replay_modes(self.path, (1-mode, 0))[:2], (mode, 0))
            self.config.write_text(f"[run_context]\nmode: replay\nacquisition_mode: {1-mode}\nnoise_test_mode: 0\n")
            self.assertEqual(replay_modes(self.path, (1-mode, 0))[:2], (mode, 0))
            self.config.unlink()

    def test_ambiguous_stream_preserves_explicit_fallback(self):
        self.path.write_bytes(b"")
        self.assertEqual(replay_modes(self.path, (1, 2))[:2], (1, 2))
        self.config.write_text("[run_context]\nmode: capture\nacquisition_mode: 7\nnoise_test_mode: 9\n")
        self.assertEqual(replay_modes(self.path, (1, 0))[:2], (1, 0))

    def test_backend_replay_selects_recorded_mode_and_preserves_original_artifacts(self):
        from PyQt5 import QtWidgets
        from backend import Backend
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self.path.write_bytes(b"".join(triggerless_event(i, 4) for i in (10, 11, 12)))
        self.config.write_text("[run_context]\nmode: capture\nacquisition_mode: 1\nnoise_test_mode: 0\n")
        summary = self.path.with_name("run_summary.txt")
        summary.write_text("hit_rate_duration_s: 123\n")
        original = {p: p.read_bytes() for p in (self.path, self.config, summary)}
        backend = Backend()
        done = []
        backend.run_finished.connect(lambda: done.append(True))
        self.assertEqual(backend.acquisition_mode, 0)
        backend.start_replay(str(self.path))
        try:
            deadline = time.monotonic() + 10
            while not done and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(.01)
            self.assertTrue(done)
            snap = backend._last_decode_snapshot
            self.assertEqual(snap.valid_events, 3)
            self.assertEqual(snap.hits_total, 12)
            self.assertEqual(snap.err_event_id, 0)
            self.assertEqual(backend._hit_rate_duration_override_s, 123)
            self.assertIn("replays", Path(backend.current_artifact_dir()).parts)
            self.assertTrue((Path(backend.current_artifact_dir()) / "run_summary.txt").exists())
            for path, data in original.items():
                self.assertEqual(path.read_bytes(), data)
        finally:
            if backend.is_running():
                backend.stop_capture()
