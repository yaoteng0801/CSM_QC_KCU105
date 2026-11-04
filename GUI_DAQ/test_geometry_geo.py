"""Offline tests for explicit GEO wiring, six-layer UI, and geometry consumers."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from geometry import Geometry
from triggerless_filters import build_geometry_image

GEO_FILE = Path(__file__).resolve().parents[1] / 'EML1A05.geo'
SMALL_GEO = '''MZ MezzCh locY locZ Layer Tube_y ML
0 117 14.985 14.985 1 1 1
0 109 40.9961 30.0025 2 1 1
0 101 67.0072 14.985 3 1 1
1 216 266.9772 165.16 1 6 2
1 208 292.9883 180.1775 2 6 2
1 200 318.9994 165.16 3 6 2
'''


def small_geometry():
    geo = Geometry.from_text(SMALL_GEO, apply_map=True)
    geo.chamber_id = 0
    return geo


class GeoTableTests(unittest.TestCase):
    def test_exact_coordinates_and_local_channel_encoding(self):
        geo = small_geometry()
        self.assertEqual((geo.MAX_TUBE_LAYER, geo.MAX_TDC_LAYER), (6, 3))
        self.assertEqual(geo.wire_center_from_hit(1, 16), (165.16, 266.9772, 3, 5))
        self.assertEqual(geo.wire_center_from_hit(0, 17), (14.985, 14.985, 0, 0))
        self.assertEqual(geo.get_hit_xy(3, 5), (165.16, 266.9772))
        self.assertEqual(geo.tdc_channel_for_tube(3, 5), (1, 16))
        direct = Geometry.from_text(SMALL_GEO.replace('0 117', '0 17'))
        self.assertEqual(direct.wire_center_from_hit(0, 17), geo.wire_center_from_hit(0, 17))

    def test_save_reload_and_copy_preserve_explicit_map(self):
        geo = small_geometry()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.txt'
            geo.save(path)
            loaded = Geometry.load(path, apply_map=True)
        clone = Geometry(chamber_id=1)
        clone._copy_from(loaded)
        self.assertEqual(clone.chamber_id, 1)
        self.assertEqual(clone.tube_map, geo.tube_map)
        for tdc, ch in geo._channel_tubes:
            self.assertEqual(clone.wire_center_from_hit(tdc, ch), geo.wire_center_from_hit(tdc, ch))

    def test_slot_reassignment_and_clear_preserve_physical_wiring(self):
        geo = small_geometry()
        before = geo.wire_center_from_hit(1, 16)
        slots = geo.assignment_by_ml()
        slots[1][0] = (21, 1)
        geo.set_assignment(1, ml_slots=slots, apply_map=True)
        self.assertEqual(geo.wire_center_from_hit(21, 16), before)
        self.assertFalse(geo.isActiveTDC[1])
        slots[1][0] = (-1, 1)
        geo.set_assignment(1, ml_slots=slots, apply_map=True)
        self.assertIsNone(geo.tdc_channel_for_tube(3, 5))
        slots[1][0] = (21, 1)
        geo.set_assignment(1, ml_slots=slots, apply_map=True)
        self.assertEqual(geo.wire_center_from_hit(21, 16), before)

    def test_rejects_malformed_and_ambiguous_rows(self):
        cases = {
            'duplicate channel': SMALL_GEO + '0 117 14.985 45.02 1 2 1\n',
            'duplicate tube': SMALL_GEO + '0 119 14.985 14.985 1 1 1\n',
            'bad encoded MZ': SMALL_GEO.replace('0 117', '0 217'),
            'nonfinite coordinate': SMALL_GEO.replace('14.985', 'nan', 1),
            'wrong row length': SMALL_GEO.replace('0 117 14.985', '0 117'),
            'missing header': 'not a geometry\n',
            'missing layer': SMALL_GEO.replace('0 109 40.9961 30.0025 2 1 1\n', ''),
        }
        for name, text in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                Geometry.from_text(text)

    def test_missing_channels_remain_unmapped_in_firmware_image(self):
        geo = small_geometry()
        with self.assertRaisesRegex(ValueError, 'No GEO mapping'):
            geo.get_hit_layer_column(0, 0)
        image = build_geometry_image([geo])
        entries = dict(image.entries)
        self.assertEqual(entries[0], 0)
        word = entries[(1 << 5) | 16]
        self.assertEqual((word >> 2) & 15, 1)
        self.assertEqual((word >> 6) & 255, 3)
        self.assertEqual((word >> 14) & 511, 5)
        self.assertEqual(image.layer_masks, (63, 0))

    def test_decoded_hits_receive_explicit_coordinates(self):
        from DecodeThread import DecodeThread
        from GeoRouter import GeoRouter
        geo = small_geometry()
        decoder = SimpleNamespace(acquisition_mode=0, geo=GeoRouter({0: geo, 1: geo}))
        raw = dict(event_id20=1, rd_bank_sel=0, trigger_count=1, hit_count_expected=2,
                   event_id12=1, trigger_overflow=0, tdc_header_count=0, tdc_trailer_count=0,
                   header_count_error=0, trailer_count_error=0,
                   hits=[(0,0,17,0,50,20),(0,1,16,0,100,20)])
        event = DecodeThread._materialize_native_event(decoder, raw)
        hit = event.chambers[0].hits[1]
        self.assertEqual((hit.x, hit.y, hit.layer, hit.col), (165.16,266.9772,3,5))

    def test_quality_and_nrt_mapping_use_three_layers_per_ml(self):
        from EventQuality import EventQualityChecker
        from rt_function import hit_multilayers
        geo = small_geometry()
        hits = [SimpleNamespace(layer=layer, col=0 if layer < 3 else 10,
                                ledge=100+layer*10, width=30) for layer in range(6)]
        quality = EventQualityChecker(checkTime=False, min_layer_hit=6)
        self.assertFalse(quality._chamber_hit_check(hits))  # legacy four-layer split
        event = SimpleNamespace(chambers={0:SimpleNamespace(hits=hits)})
        result = quality.compute_for_event(event, geometries={0:geo})
        self.assertTrue(result.valid_by_chamber[0])
        self.assertEqual(hit_multilayers(hits, geo).tolist(), [0,0,0,1,1,1])

    @unittest.skipUnless(GEO_FILE.is_file(), 'local EML1A05.geo not available')
    def test_all_336_eml_channels_match_file_and_firmware(self):
        geo = Geometry.load(GEO_FILE, apply_map=True)
        geo.chamber_id = 0
        self.assertEqual((geo.MAX_TUBE_LAYER,geo.MAX_TUBE_COLUMN,geo.slots_per_ml), (6,56,7))
        self.assertEqual(len(geo.tube_map), 336)
        self.assertTrue(all(ncol == 8 for slots in geo.assignment_by_ml() for _,ncol in slots))
        words = dict(build_geometry_image([geo]).entries)
        for line in GEO_FILE.read_text().splitlines()[1:]:
            mz, code, y, x, layer, col, ml = line.split()
            tdc, ch = int(mz), int(code) % 100
            ll, cc = (int(ml)-1)*3+int(layer)-1, int(col)-1
            with self.subTest(tdc=tdc, channel=ch):
                self.assertEqual(geo.wire_center_from_hit(tdc,ch), (float(x),float(y),ll,cc))
                self.assertEqual(geo.tdc_channel_for_tube(ll,cc), (tdc,ch))
                word = words[(tdc << 5) | ch]
                self.assertEqual(((word>>2)&15,(word>>6)&255,(word>>14)&511), (int(ml)-1,ll,cc))


class GeometryEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt5 import QtWidgets
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_manual_six_layers_and_eight_columns(self):
        from geometry_dialog import GeometryConfigDialog
        editor = GeometryConfigDialog(geo=Geometry(), embedded=True)
        editor.sb_MAX_TUBE_LAYER.setValue(6)
        self.assertEqual(editor.sb_MAX_TDC_LAYER.value(), 3)
        for combo in editor._slot_count_spins:
            combo.setCurrentIndex(combo.findData(8))
        self.assertEqual(editor.result_geometry().MAX_TUBE_LAYER, 6)
        self.assertEqual(editor.result_ml_slots()[0][0][1], 8)
        editor.sb_MAX_TDC_LAYER.setValue(4)
        self.assertEqual(editor.sb_MAX_TUBE_LAYER.value(), 8)
        self.assertEqual(editor._slot_count_spins[0].findData(8), -1)
        editor.close()

    def test_editor_keeps_map_when_reassigning_and_saving(self):
        from geometry_dialog import GeometryConfigDialog
        geo = small_geometry()
        editor = GeometryConfigDialog(geo=geo, slots_per_ml=geo.slots_per_ml, embedded=True)
        row = next(row for row in editor._rows if row['ml']==1 and row['slot']==0)
        row['combo'].setCurrentIndex(row['combo'].findData(21))
        result = editor.result_geometry()
        self.assertEqual(result.tube_map, geo.tube_map)
        self.assertEqual(result.wire_center_from_hit(21,16), (165.16,266.9772,3,5))
        self.assertFalse(editor.sb_MAX_TUBE_LAYER.isEnabled())
        self.assertFalse(editor._slot_count_spins[0].isEnabled())
        editor.close()

    @unittest.skipUnless(GEO_FILE.is_file(), 'local EML1A05.geo not available')
    def test_load_button_applies_full_eml_display_and_channel_labels(self):
        from PyQt5 import QtWidgets
        from tab_geometry import tab_geometry
        parent = QtWidgets.QWidget()
        geo = Geometry(chamber_id=0)
        tab = tab_geometry(parent, geo, backend=None, chamber_id=0)
        with patch('geometry_dialog.QtWidgets.QFileDialog.getOpenFileName', return_value=(str(GEO_FILE),'')):
            tab.settings_editor._on_load()
        self.app.processEvents()
        self.assertEqual(len(tab._tube_items), 336)
        self.assertEqual(tab.geo.MAX_TUBE_LAYER, 6)
        self.assertEqual(tab.geo.MAX_TUBE_COLUMN, 56)
        self.assertEqual(tab._tdc_channel_for_layer_col(3,5), (1,16))
        tab._show_channel_ids = True
        tab._update_channel_labels()
        self.assertEqual(len(tab._ch_text_items), 336)
        for item in tab._tube_items:
            self.assertEqual((item.tdc_id,item.ch_id), geo.tdc_channel_for_tube(item.layer,item.col))
        self.assertFalse(tab.sync_from_mezz_state([{'ml':0,'slot':0,'tdc_id':0,'ncol':6}]))
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory)/'saved.txt')
            with patch('geometry_dialog.QtWidgets.QFileDialog.getSaveFileName', return_value=(path,'')):
                tab.settings_editor._on_save()
            restored = Geometry.load(path,apply_map=True)
            self.assertEqual(restored.tube_map,geo.tube_map)
        parent.close()


if __name__ == '__main__':
    unittest.main()
