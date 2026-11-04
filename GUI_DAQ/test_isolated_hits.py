"""End-to-end PCAP -> native capture -> DAT tests, without detector hardware."""
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from geometry import Geometry
from isolated_hits import neighbor_map_text
from triggerless_filters import TubeFilterSettings

ROOT = Path(__file__).resolve().parent


def word(value):
    return value.to_bytes(5, "big")


def hit(channel, tdc=0, ledge=100):
    return word((tdc // 20 << 37) | (tdc % 20 << 32) | (channel << 27) | (ledge << 8) | 30)


def event(hits, event_id=1, controls=b"", count=None):
    return (word((0xa << 36) | (event_id << 16)) + b"".join(hits) + controls +
            word((0xc << 36) | (event_id << 16) | (len(hits) if count is None else count)))


def parse_map(text):
    rows = {}
    for line in text.splitlines()[1:]:
        index, chamber, tube, count, *neighbors = map(int, line.split())
        assert len(neighbors) == count
        rows[index] = (chamber, tube, set(neighbors))
    return rows


class NeighborMapTests(unittest.TestCase):
    def test_six_physical_neighbors_and_no_cross_ml(self):
        geo = Geometry(chamber_id=0, _skip_autoload=True)
        geo.configure_tdc_map([0, 1, 20], [0, 0, 1], [0, 6, 0])
        rows = parse_map(neighbor_map_text([geo]))
        # Find an interior tube with all six neighbors and check actual centers.
        interior = [(idx, value) for idx, value in rows.items() if len(value[2]) == 6]
        self.assertTrue(interior)
        tube_positions = {}
        for index, (_, tube, _) in rows.items():
            tdc, channel = divmod(index, 32)
            layer, col = geo.get_hit_layer_column(tdc, channel)
            tube_positions[tube] = (geo.TDC_ML[tdc], layer, *geo.get_hit_xy(layer, col))
        for index, (_, tube, neighbors) in interior:
            ml, layer, x, y = tube_positions[tube]
            for n in neighbors:
                nml, nl, nx, ny = tube_positions[n]
                self.assertEqual(ml, nml)
                self.assertLessEqual(abs(nl-layer), 1)
                expected = geo.column_distance if nl == layer else geo.column_distance / 2
                self.assertAlmostEqual(abs(nx-x), expected)

    def test_geo_import_uses_centers_and_reassigned_tdcs(self):
        from test_geometry_geo import small_geometry
        geo = small_geometry()
        rows = parse_map(neighbor_map_text([geo]))
        self.assertIn(rows[9][1], rows[17][2])
        self.assertNotIn(rows[32+16][1], rows[17][2])
        slots = geo.assignment_by_ml()
        slots[1][0] = (21, 1)
        geo.set_assignment(geo.slots_per_ml, ml_slots=slots, apply_map=True)
        moved = parse_map(neighbor_map_text([geo]))
        self.assertIn(21*32+16, moved)
        self.assertNotIn(32+16, moved)


class NativeIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="minidaq_isolation_test_")
        cls.root = Path(cls.temp.name)
        cls.helper = cls.root / "capture"
        subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Wpedantic",
                        str(ROOT / "native_capture/minidaq_capture.cpp"), "-lpcap",
                        "-o", str(cls.helper)], check=True, capture_output=True)
        # channel 0 and alias 3 share tube 0; channel 1 neighbors tube 0;
        # channel 2 is isolated. Chamber 1 has its own adjacent pair.
        cls.mapping = cls.root / "neighbors.txt"
        cls.mapping.write_text("MINIDAQ_NEIGHBORS_V1\n"
                               "0 0 0 1 1\n1 0 1 1 0\n2 0 2 0\n3 0 0 1 1\n"
                               "640 1 3 1 4\n641 1 4 1 3\n")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def capture(self, chunks, *, enabled=True, sequence=None, mapping=None):
        path, output = self.root / "test.pcap", self.root / "test.dat"
        with path.open("wb") as f:
            f.write(struct.pack("<IHHIIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
            for i, chunk in enumerate(chunks):
                seq = i if sequence is None else sequence[i]
                packet = bytes(14) + chunk + bytes(2) + struct.pack(">H", seq)
                f.write(struct.pack("<IIII", i, 0, len(packet), len(packet)))
                f.write(packet)
        cmd = [str(self.helper), "--input-pcap", str(path), "--output", str(output),
               "--dispatch-limit", "1"]
        if enabled:
            cmd += ["--isolation-map", str(mapping or self.mapping)]
        result = subprocess.run(cmd, check=True, capture_output=True)
        data = output.read_bytes()
        self.assertEqual(data, result.stdout)  # live stream equals saved stream
        return data, result.stderr.decode()

    def test_late_neighbor_aliases_order_count_and_event_boundaries(self):
        a, b, isolated, alias = hit(0), hit(1), hit(2), hit(3)
        trigger = word((0xe << 36) | 321)
        raw = event([a, isolated, alias, b], controls=trigger)
        chunks = [raw[:10], raw[10:20], raw[20:]]
        data, stats = self.capture(chunks)
        self.assertEqual(data, event([a, alias, b], controls=trigger))
        self.assertIn("isolated_dropped=1", stats)
        raw = event([a], 1) + event([b], 2)
        data, _ = self.capture([raw])
        self.assertEqual(data, event([], 1) + event([], 2))

    def test_duplicates_are_not_neighbors_unmapped_hits_are_kept(self):
        data, stats = self.capture([event([hit(0), hit(3), hit(0), hit(10)])])
        self.assertEqual(data, event([hit(10)]))
        self.assertIn("isolated_dropped=3", stats)

    def test_both_chambers_and_wrong_chamber_preservation(self):
        raw = event([hit(0), hit(1), hit(2)]) + event([hit(0, 20), hit(1, 20)], 0x80001)
        data, _ = self.capture([raw])
        self.assertEqual(data, event([hit(0), hit(1)]) + event([hit(0, 20), hit(1, 20)], 0x80001))
        wrong = event([hit(0, 20), hit(2)], 1)
        self.assertEqual(self.capture([wrong])[0], wrong)

    def test_disabled_is_byte_identical(self):
        raw = event([hit(0), hit(2)]) + event([hit(0), hit(1)])
        data, stats = self.capture([raw], enabled=False)
        self.assertEqual(data, raw)
        self.assertIn("isolated_dropped=0", stats)

    def test_damaged_aborted_incomplete_and_oversized_events_preserved(self):
        cases = [event([hit(2)], count=2), event([hit(2)])[:-5],
                 event([hit(2)], controls=word((0xb << 36) | (0xd << 32))),
                 event([hit(2)])[:-5] + word((0xc << 36) | (5 << 16) | 1),
                 event([hit(2)])[:-5] + event([hit(0), hit(1)], 2),
                 event([hit(2)] * 8200, count=8)]
        for raw in cases:
            with self.subTest(size=len(raw)):
                # Keep each Ethernet packet smaller than the PCAP snaplen.
                chunks = [raw[i:i+1000] for i in range(0, len(raw), 1000)]
                self.assertEqual(self.capture(chunks)[0], raw)

    def test_packet_loss_preserves_affected_event_and_recovers(self):
        raw = event([hit(0), hit(2), hit(1)])
        chunks = [raw[:10], raw[10:], event([hit(2)], 2)]
        data, stats = self.capture(chunks, sequence=[0, 2, 3])
        self.assertEqual(data, raw + event([], 2))
        self.assertIn("lost=1", stats)
        self.assertIn("preserved_events=1", stats)

    def test_real_geo_map_end_to_end(self):
        from test_geometry_geo import small_geometry
        mapping = self.root / "geo.txt"
        mapping.write_text(neighbor_map_text([small_geometry()]))
        raw = event([hit(17), hit(9), hit(16, 1)])
        self.assertEqual(self.capture([raw], mapping=mapping)[0], event([hit(17), hit(9)]))

    def filter_map(self, cfg0, cfg1=None):
        """Two adjacent pairs in different MLs, two isolated tubes and an alias."""
        cfg1 = cfg1 or TubeFilterSettings(enabled=0)
        lines = ["MINIDAQ_NEIGHBORS_V2"]
        for cid, cfg in enumerate((cfg0, cfg1)):
            lines.append(f"FILTER {cid} {cfg.enabled} {cfg.min_tubes} {cfg.min_tubes_per_ml} "
                         f"{cfg.min_tubes_per_layer} {cfg.min_layers_per_ml}")
        lines += ["0 0 0 0 0 1 1", "1 0 1 0 1 1 0",
                  "2 0 2 1 2 1 3", "3 0 3 1 3 1 2",
                  "4 0 4 0 0 0", "5 0 5 1 3 0", "6 0 0 0 0 1 1",
                  "640 1 6 0 0 1 7", "641 1 7 0 1 1 6"]
        path = self.root / "filters.txt"
        path.write_text("\n".join(lines) + "\n")
        return path

    def test_all_filter_enable_masks_after_isolation(self):
        # Before isolation: 6 distinct tubes, 3/ML. Afterwards: 4, 2/ML,
        # 1/layer, and 2 hit layers/ML. Repeated words/aliases add no tubes.
        raw = event([hit(c) for c in (0, 4, 6, 1, 2, 5, 3, 0)])
        retained = event([hit(c) for c in (0, 6, 1, 2, 3, 0)])
        for mask in range(16):
            for thresholds in ((4, 2, 1, 2), (5, 2, 1, 2), (4, 3, 1, 2),
                               (4, 2, 2, 2), (4, 2, 1, 3)):
                cfg = TubeFilterSettings(mask, *thresholds)
                passed = all(not mask & (1 << i) or value >= thresholds[i]
                             for i, value in enumerate((4, 2, 1, 2)))
                with self.subTest(mask=mask, thresholds=thresholds):
                    data, stats = self.capture([raw], mapping=self.filter_map(cfg))
                    self.assertEqual(data, retained if passed else b"")
                    self.assertIn(f"filter_rejected_events={int(not passed)}", stats)
                    self.assertIn("isolated_dropped=2", stats)

    def test_empty_configured_layers_and_multilayers_fail(self):
        for bit in (2, 4, 8):
            cfg = TubeFilterSettings(bit, 0, 1, 1, 1)
            data, _ = self.capture([event([hit(0), hit(1)])], mapping=self.filter_map(cfg))
            self.assertEqual(data, b"")
        # No enabled cuts: retain a nonempty mapped event, but reject an empty
        # one or one containing only unknown channels, exactly as firmware.
        mapping = self.filter_map(TubeFilterSettings(enabled=0))
        raw = event([hit(4)]) + event([hit(10)], 2) + event([hit(0), hit(1)], 3)
        self.assertEqual(self.capture([raw], mapping=mapping)[0], event([hit(0), hit(1)], 3))

    def test_chambers_have_independent_thresholds_and_event_ids(self):
        mapping = self.filter_map(TubeFilterSettings(min_tubes=3), TubeFilterSettings(min_tubes=2))
        chamber1 = event([hit(0, 20), hit(1, 20)], 0x80009)
        raw = event([hit(0), hit(1)]) + chamber1
        self.assertEqual(self.capture([raw], mapping=mapping)[0], chamber1)

    def test_filter_snapshot_from_geo_and_damaged_events_kept(self):
        from test_geometry_geo import small_geometry
        mapping = self.root / "snapshot.txt"
        configs = (TubeFilterSettings(min_tubes=3), TubeFilterSettings(enabled=0))
        text = neighbor_map_text([small_geometry()], configs)
        self.assertTrue(text.startswith("MINIDAQ_NEIGHBORS_V2\nFILTER 0 1 3 0 0 0\n"))
        mapping.write_text(text)
        raw = event([hit(17), hit(9), hit(16, 1)])
        self.assertEqual(self.capture([raw], mapping=mapping)[0], b"")
        damaged = event([hit(17)], count=7)
        self.assertEqual(self.capture([damaged], mapping=mapping)[0], damaged)

    def test_every_neighbor_and_cross_mezzanine_with_generated_map(self):
        geo = Geometry(chamber_id=0, _skip_autoload=True)
        geo.configure_tdc_map([0, 1, 20], [0, 0, 1], [0, 6, 0])
        text = neighbor_map_text([geo])
        mapping = self.root / "all_neighbors.txt"
        mapping.write_text(text)
        rows = parse_map(text)
        channels = {value[1]: divmod(index, 32) for index, value in rows.items()}
        events = []
        across_mezzanine = False
        for index, (_, tube, neighbors) in rows.items():
            if len(neighbors) != 6:
                continue
            tdc, channel = divmod(index, 32)
            for neighbor in neighbors:
                nt, nc = channels[neighbor]
                across_mezzanine |= nt != tdc
                events.append(event([hit(channel, tdc), hit(nc, nt)], len(events)))
        self.assertTrue(across_mezzanine)
        raw = b"".join(events)
        self.assertEqual(self.capture([raw], mapping=mapping)[0], raw)

    def test_full_trailer_capacity_and_trigger_bits(self):
        hits = [hit(0)] * 511 + [hit(2)] * 511 + [hit(1)]
        raw = event(hits)[:-5] + word((0xc << 36) | (1 << 16) | (37 << 10) | 1023)
        expected = event([hit(0)] * 511 + [hit(1)])[:-5] + word(
            (0xc << 36) | (1 << 16) | (37 << 10) | 512)
        self.assertEqual(self.capture([raw])[0], expected)

    def test_filtered_stream_replays_in_python_and_native_decoders(self):
        from native_decoder.benchmark_decoder import run_decoder
        raw = event([hit(0), hit(2), hit(1)]) + event([hit(2)], 2)
        data, _ = self.capture([raw])
        for native in (False, True):
            with self.subTest(native=native):
                result = run_decoder(data, 1, 2, native)
                snapshot = result[1]
                self.assertEqual(snapshot.valid_events, 2)
                self.assertEqual(snapshot.hits_total, 2)
                self.assertEqual(snapshot.err_hit_count, 0)
                self.assertEqual(snapshot.err_event_id, 0)


class IsolationControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt5 import QtWidgets
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_default_persistence_modes_and_run_lock(self):
        from PyQt5 import QtWidgets
        from tab_capture import tab_capture, RUN_PROFILE_TRIGGERLESS, RUN_PROFILE_TRIGGERLESS_NOISE_RAW
        with tempfile.TemporaryDirectory() as directory, patch("tab_capture.os.getcwd", return_value=directory), \
                patch.object(tab_capture, "refresh_devices"):
            parent = QtWidgets.QWidget()
            tab = tab_capture(parent)
            self.assertFalse(tab.check_remove_isolated_hits.isChecked())
            tab.combo_acquisition_mode.setCurrentIndex(tab.combo_acquisition_mode.findData(RUN_PROFILE_TRIGGERLESS))
            self.assertTrue(tab.check_remove_isolated_hits.isEnabled())
            tab.check_remove_isolated_hits.setChecked(True)
            self.assertFalse(tab.save_isolated_hits())
            tab.btn_start.setEnabled(False)
            tab._update_isolated_hit_control()
            self.assertFalse(tab.check_remove_isolated_hits.isEnabled())
            tab.btn_start.setEnabled(True)
            tab.combo_acquisition_mode.setCurrentIndex(tab.combo_acquisition_mode.findData(RUN_PROFILE_TRIGGERLESS_NOISE_RAW))
            self.assertFalse(tab.check_remove_isolated_hits.isEnabled())
            self.assertTrue(tab.save_isolated_hits())
            parent2 = QtWidgets.QWidget()
            restored = tab_capture(parent2)
            self.assertTrue(restored.check_remove_isolated_hits.isChecked())
            parent.close()
            parent2.close()

    def test_post_filter_rejections_update_live_status_without_logging(self):
        import queue
        from PyQt5 import QtWidgets
        from CaptureThread import CaptureThread
        from tab_capture import tab_capture
        with tempfile.TemporaryDirectory() as directory, patch("tab_capture.os.getcwd", return_value=directory), \
                patch.object(tab_capture, "refresh_devices"):
            parent = QtWidgets.QWidget()
            tab = tab_capture(parent)
            capture = CaptureThread("test", "", "/tmp/test.dat", queue.Queue())
            messages = []
            capture.message.connect(messages.append)
            capture.isolation_stats.connect(tab.update_isolation_stats)
            capture._handle_native_line("MINIDAQ_STATS isolated_dropped=50 filtered_events=250 "
                                        "preserved_events=3 filter_rejected_events=17")
            self.assertEqual(tab.lab_isolated_dropped.text(), "50")
            self.assertEqual(tab.lab_filter_rejected_events.text(), "17")
            self.assertEqual(messages, [])
            tab.update_isolation_stats((0, 0, 0, 0))
            self.assertEqual(tab.lab_filter_rejected_events.text(), "0")
            parent.close()
