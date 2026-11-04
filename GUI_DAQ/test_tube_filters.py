"""Offline regression tests; no raw sockets, FPGA writes, or hardware access."""
import os
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets, QtCore
from geometry import Geometry
from MiniDAQ_reg import MiniDAQ_reg
from triggerless_filters import TubeFilterSettings, SIGNATURE, build_geometry_image
from tube_filter_widget import TubeFilterWidget, GeometryUploadDialog
from tab_lpgbt import tab_lpgbt
from tab_capture import tab_capture
from pop_miniDAQ_setup import pop_miniDAQ_setup
from MainWindow import Ui_MainWindow
from ethernet_control_protocol import FPGA_READ, FPGA_WRITE


def geometry(chamber=0, tdcs=(0, 20), mls=(0, 1), columns=(0, 0)):
    geo = Geometry(chamber_id=chamber, _skip_autoload=True)
    geo.configure_tdc_map(list(tdcs), list(mls), list(columns))
    return geo


class FakeFPGA:
    """Register-transport fake independent of the uploader's helpers."""
    def __init__(self):
        self._lock = threading.RLock()
        self.regs = {37: 20, 38: 4, 39: 128, 40: 0, 42: 0, 44: 1, 61: 0, 66: 65, 67: 65}
        self.mapping, self.writes, self.reads = {}, [], []
        self.index = self.generation = self.error = 0
        self.ready = False
        self.signature = SIGNATURE
        self.fail_read = None
        self.corrupt_index = False
        self.corrupt_mask = False
        self.force_busy = False
        self.apply_error = 0

    def request(self, opcode, *, address, payload=b"", subtarget=0, **_kwargs):
        if opcode == FPGA_WRITE:
            value = int.from_bytes(payload, "big")
            self.writes.append((address, value))
            if address == 62:
                self.index = value
            elif address == 63:
                self.mapping[self.index] = value
            elif address == 64:
                if value == 1:
                    self.mapping.clear(); self.ready = False; self.error = 0
                elif value == 2:
                    self.error = self.apply_error
                    self.ready = not self.error
                    self.generation += int(self.ready)
            else:
                if address == 40 and value and self.regs[44] and not self.regs[42] and not self.ready:
                    value = 0
                self.regs[address] = value
                if address in (38, 61, 66, 67):
                    self.ready = False
            return SimpleNamespace(address=address, data=b"", subtarget=subtarget)
        assert opcode == FPGA_READ
        self.reads.append((address, subtarget))
        if self.fail_read == (address, self.index):
            raise RuntimeError("injected transport failure")
        if address == 1:
            value = (self.regs[40] << 25) | (self.regs[42] << 26) | (self.regs[44] << 28)
        elif address == 2:
            value = 0
        elif address == 4:
            value = self.regs[37] << 56 | self.regs[38] << 40 | self.regs[39] << 24
        elif address == 62:
            value = self.index + int(self.corrupt_index)
        elif address == 63:
            value = self.mapping.get(self.index, 0)
        elif address == 64:
            value = (int(self.ready) | int(self.force_busy) << 1 | self.error << 8 |
                     self.generation << 32 | self.signature << 64 | 1280 << 96 | 960 << 112)
        elif address == 65:
            chamber, part = subtarget >> 2, subtarget & 3
            positions = [v for v in self.mapping.values() if v & 1 and (v >> 1) & 1 == chamber]
            mls = sum(1 << ml for ml in {(v >> 2) & 15 for v in positions})
            layers = sum(1 << layer for layer in {(v >> 6) & 255 for v in positions})
            value = mls if part == 0 else (layers >> (128*(part-1))) & ((1 << 128)-1)
            value ^= int(self.corrupt_mask)
        else:
            value = self.regs[address]
        return SimpleNamespace(address=address, data=value.to_bytes(20, "big"), subtarget=subtarget)


def controller():
    obj = object.__new__(tab_lpgbt)
    obj.eth, obj.miniDAQ_reg = FakeFPGA(), MiniDAQ_reg()
    return obj


class TubeWireTest(unittest.TestCase):
    def test_pack_boundaries_and_all_enable_masks(self):
        for mask in range(16):
            cfg = TubeFilterSettings(mask, 256, 256, 256, 256)
            self.assertEqual(cfg.pack(), mask | 256 << 4 | 256 << 14 | 256 << 24 | 256 << 34)
            self.assertEqual(TubeFilterSettings.unpack(cfg.pack()), cfg)
        self.assertEqual(TubeFilterSettings().pack(), 0x41)
        for value in (-1, 1 << 43, 257 << 4, 257 << 34):
            with self.assertRaises(ValueError):
                TubeFilterSettings.unpack(value)

    def test_uses_actual_geometry_channels_and_cross_csm_chambers(self):
        geos = [geometry(), geometry(1, (1, 21))]
        geos[0].hit_layer_map[0] = 3
        image = build_geometry_image(geos)
        self.assertEqual(len(image.entries), 96)
        self.assertEqual(image.enabled_mask, 3 | 3 << 20)
        self.assertEqual(image.chamber1_mask, 2 | 2 << 20)
        for geo in geos:
            for tdc, active in enumerate(geo.isActiveTDC):
                if active:
                    for ch in range(24):
                        v = dict(image.entries)[tdc*32+ch]
                        layer, col = geo.get_hit_layer_column(tdc, ch)
                        self.assertEqual(((v >> 1) & 1, (v >> 2) & 15, (v >> 6) & 255, (v >> 14) & 511),
                                         (geo.chamber_id, geo.TDC_ML[tdc], layer, col))

    def test_aliases_share_ids_and_disabled_channels_explicit(self):
        geo = geometry(0, (0, 20), (0, 0))
        geo.MAX_TDC_CHANNEL = 20
        image = build_geometry_image([geo])
        self.assertEqual(len(image.positions), 20)
        entries = dict(image.entries)
        for ch in range(20):
            self.assertEqual(entries[ch], entries[640+ch])
        self.assertEqual(entries[23], 0)
        self.assertEqual(entries[663], 0)

    def test_duplicate_tdc_and_invalid_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError, "multiply assigned"):
            build_geometry_image([geometry(), geometry(1)])
        geo = geometry(); geo.TDC_COL[0] = 511
        with self.assertRaisesRegex(ValueError, "out of range"):
            build_geometry_image([geo])
        with self.assertRaisesRegex(ValueError, "Assign mezzanine"):
            build_geometry_image([])

    def test_feasibility_every_ml_layer_and_buffer(self):
        image = build_geometry_image([geometry()])
        defaults = TubeFilterSettings()
        for cfg, message in (
            (TubeFilterSettings(1, 49), "event cut"),
            (TubeFilterSettings(2, 0, 25), "ML cut"),
            (TubeFilterSettings(4, 0, 0, 7), "too few mapped tubes"),
            (TubeFilterSettings(8, 0, 0, 0, 5), "too few mapped layers"),
        ):
            with self.assertRaisesRegex(ValueError, message):
                image.validate_filters((cfg, defaults))
        cfg = TubeFilterSettings(15, 8, 4, 1, 3)
        image.validate_filters((cfg, defaults), 8)
        with self.assertRaisesRegex(ValueError, "raw-word limit"):
            image.validate_filters((cfg, defaults), 7)

    def test_model_reset_and_packed_registers(self):
        registers = MiniDAQ_reg()
        registers.set_tube_filter_settings((TubeFilterSettings(15, 8, 4, 1, 3), TubeFilterSettings(0)))
        self.assertEqual([r[0] for r in registers.register_table if r[1].startswith("tube_filters")], [66, 67])
        registers.reset()
        self.assertEqual(registers.tube_filter_settings(), (TubeFilterSettings(),)*2)


class TubeUploadTest(unittest.TestCase):
    def test_complete_upload_readbacks_and_start(self):
        ctl = controller()
        image = build_geometry_image([geometry(), geometry(1, (1, 21))])
        filters = (TubeFilterSettings(15, 8, 4, 1, 3), TubeFilterSettings(8, 0, 0, 0, 3))
        ctl.set_triggerless_event_settings(24, filters)
        ctl.configure_triggerless_geometry(image)
        self.assertTrue(ctl.eth.ready)
        self.assertEqual(ctl.eth.mapping, dict(image.entries))
        self.assertEqual(ctl.eth.regs[66], filters[0].pack())
        self.assertEqual(ctl.eth.regs[67], filters[1].pack())
        self.assertFalse(any(addr in (38, 40) for addr, _ in ctl.eth.writes))
        self.assertTrue(all((65, selector) in ctl.eth.reads for selector in (0, 1, 2, 4, 5, 6)))
        ctl.DAQ_start()
        self.assertEqual(ctl.eth.writes[-1], (40, 1))
        ctl.DAQ_stop()
        # Reupload changed geometry; no stale ready/map shortcut.
        geo = geometry(); geo.TDC_COL[0] = 6
        ctl.configure_triggerless_geometry(build_geometry_image([geo]))
        self.assertEqual(ctl.eth.generation, 2)

    def test_legacy_firmware_and_running_board_block_writes(self):
        for field in ("signature", "running", "busy"):
            ctl = controller()
            if field == "signature": ctl.eth.signature = 0
            if field == "running": ctl.eth.regs[40] = 1
            if field == "busy": ctl.eth.force_busy = True
            with self.assertRaises(RuntimeError):
                ctl.configure_triggerless_geometry(build_geometry_image([geometry()]))
            self.assertEqual(ctl.eth.writes, [])

    def test_partial_upload_bad_index_mask_and_apply_fail_closed(self):
        for fault in ("transport", "index", "mask", "apply"):
            ctl = controller()
            if fault == "transport": ctl.eth.fail_read = (63, 3)
            if fault == "index": ctl.eth.corrupt_index = True
            if fault == "mask": ctl.eth.corrupt_mask = True
            if fault == "apply": ctl.eth.apply_error = 7
            with self.assertRaises(RuntimeError):
                ctl.configure_triggerless_geometry(build_geometry_image([geometry()]))
            self.assertFalse(ctl.eth.ready)
            self.assertFalse(any(addr == 40 for addr, _ in ctl.eth.writes))
            self.assertEqual(ctl.eth.writes[-1], (64, 1))

    def test_fpga_refusal_does_not_report_running(self):
        ctl = controller()
        with self.assertRaisesRegex(RuntimeError, "refused"):
            ctl.DAQ_start()
        self.assertEqual(ctl.eth.regs[40], 0)
        self.assertEqual(ctl._current_minidaq_register("run_enable"), 0)

    def test_raw_noise_does_not_require_tube_firmware(self):
        ctl = controller(); ctl.eth.signature = 0
        ctl.miniDAQ_reg.set_named_value("acquisition_mode", 1)
        ctl.miniDAQ_reg.set_named_value("noise_test_mode", 1)
        ctl.eth.regs[42] = 1
        ui = Ui_MainWindow(); ui.tab_lpgbt_inst = ctl; ui.geos = [geometry()]
        ui._start_daq_with_chamber_map()
        self.assertEqual(ctl.eth.regs[40], 1)
        self.assertFalse(any(62 <= addr <= 67 for addr, _ in ctl.eth.writes))


class TubeWidgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory(prefix="minidaq_gui_test_")
        os.chdir(self.tmp.name)

    def tearDown(self):
        self.app.processEvents()
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def make_capture(self):
        parent = QtWidgets.QWidget()
        with patch.object(tab_capture, "refresh_devices"):
            capture = tab_capture(parent)
        return parent, capture

    def test_checkboxes_are_independent_and_disabled_values_preserved(self):
        widget = TubeFilterWidget()
        widget.spins[0][0].setValue(7)
        for bit in range(4): widget.checks[0][bit].setChecked(True)
        self.assertEqual(widget.values()[0].enabled, 15)
        widget.checks[0][0].setChecked(False)
        self.assertEqual(widget.values()[0].min_tubes, 7)
        self.assertEqual(widget.values()[0].enabled, 14)
        self.assertEqual(widget.values()[1], TubeFilterSettings())

    def test_capture_filters_sync_persist_and_lock_without_device_writes(self):
        parent, capture = self.make_capture()
        registers = MiniDAQ_reg(); capture.bind_minidaq_registers(registers)
        capture.tube_filters.checks[0][3].setChecked(True)
        capture.tube_filters.spins[0][3].setValue(3)
        registers.set_tube_filter_settings((TubeFilterSettings(), TubeFilterSettings(min_tubes_per_ml=7)))
        self.assertEqual(capture.tube_filters.values()[1].min_tubes_per_ml, 7)
        capture.spin_triggerless_window_cycles.setValue(31)
        self.assertEqual(capture.triggerless_window_cycles(), 31)
        expected = capture.triggerless_filter_settings()
        parent2, restored = self.make_capture()
        self.assertEqual(restored.triggerless_filter_settings(), expected)
        registers.set_named_value("run_enable", 1)
        self.assertFalse(capture.tube_filters.isEnabled())
        self.assertFalse(capture.spin_triggerless_window_cycles.isEnabled())
        registers.set_named_value("run_enable", 0)
        self.assertTrue(capture.tube_filters.isEnabled())
        parent.close(); parent2.close()

    def test_migrates_old_shared_threshold_to_tubes(self):
        settings = QtCore.QSettings("capture_settings.ini", QtCore.QSettings.IniFormat)
        settings.setValue("run/triggerless_hit_threshold", 9); settings.sync()
        parent, capture = self.make_capture()
        self.assertEqual(capture.triggerless_filter_settings(), (TubeFilterSettings(min_tubes=9),)*2)
        parent.close()

    def test_capture_readback_replaces_staged_filters(self):
        parent, capture = self.make_capture()
        ctl = controller()
        capture.bind_minidaq_registers(ctl.miniDAQ_reg)
        capture.set_daq_run_control(read_acquisition_registers_callback=ctl.read_acquisition_registers)
        capture.tube_filters.spins[0][0].setValue(8)
        capture.read_filters_button.click()
        self.assertEqual(ctl.miniDAQ_reg.tube_filter_settings(), (TubeFilterSettings(),)*2)
        self.assertEqual(ctl.eth.writes, [])
        parent.close()

    def test_capture_can_stage_filters_when_hardware_is_offline(self):
        parent, capture = self.make_capture()
        registers = MiniDAQ_reg()
        capture.bind_minidaq_registers(registers)
        capture.tube_filters.spins[0][0].setValue(6)
        self.assertEqual(registers.tube_filter_settings()[0].min_tubes, 6)
        parent.close()

    def test_upload_worker_propagates_failure_without_hanging(self):
        def upload(progress):
            progress(1, 2, "Test upload")
            raise RuntimeError("test upload failed")
        dialog = GeometryUploadDialog(upload)
        with self.assertRaisesRegex(RuntimeError, "test upload failed"):
            dialog.upload()
        self.assertFalse(dialog.worker.isRunning())

    def test_cancel_stops_upload_and_does_not_start_daq(self):
        def upload(progress):
            for i in range(1000):
                progress(i, 1000, "Test upload")
                time.sleep(0.001)
        dialog = GeometryUploadDialog(upload)
        QtCore.QTimer.singleShot(0, dialog.reject)
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            dialog.upload()
        self.assertFalse(dialog.worker.isRunning())

    def test_mainwindow_framed_start_uploads_before_run(self):
        ctl = controller()
        ctl.miniDAQ_reg.set_named_value("acquisition_mode", 1)
        ctl.miniDAQ_reg.set_tube_filter_settings((TubeFilterSettings(15, 8, 4, 1, 3),)*2)
        ui = Ui_MainWindow(); ui.tab_lpgbt_inst = ctl; ui.geos = [geometry()]
        ui._start_daq_with_chamber_map()
        self.assertEqual(ctl.eth.mapping, dict(build_geometry_image(ui.geos).entries))
        self.assertEqual(ctl.eth.writes[-1], (40, 1))
        ctl.DAQ_stop()
        ctl.eth.corrupt_index = True
        ctl.eth.writes.clear()
        with self.assertRaisesRegex(RuntimeError, "index readback mismatch"):
            ui._start_daq_with_chamber_map()
        self.assertFalse(any(addr == 40 for addr, _ in ctl.eth.writes))
        self.assertEqual(ctl.eth.regs[40], 0)


if __name__ == "__main__":
    unittest.main()
