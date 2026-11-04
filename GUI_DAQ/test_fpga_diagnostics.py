"""Offline DIA protocol, display, polling and run-artifact regressions."""
import json
import os
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtCore, QtWidgets
from backend import Backend
from fpga_diagnostics import COUNTERS, SIGNATURE, CLOCK_HZ, DiagnosticSnapshot, read_snapshot
from fpga_diagnostics_widget import DiagnosticWidget, SnapshotWorker
from tab_capture import tab_capture
from tab_lpgbt import tab_lpgbt
from MiniDAQ_reg import MiniDAQ_reg
from ethernet_control_protocol import FPGA_READ, FPGA_WRITE


def snapshot(number, total=0, running=False, epoch=0, cycles=None):
    values = [total, total, 0] + [0]*(len(COUNTERS)-3)
    return DiagnosticSnapshot(number, epoch, number*CLOCK_HZ if cycles is None else cycles,
                              running, (tuple(values), tuple(values)), "2026-09-14T12:00:00+00:00")


class DiagnosticFPGA:
    def __init__(self):
        self._lock = threading.RLock()
        self.sequence = 0
        self.epoch = 3
        self.running = False
        self.valid = False
        self.signature = SIGNATURE
        self.width = 64
        self.live = [list(snapshot(1, total=(1 << 40)+ch).chambers[0]) for ch in range(2)]
        self.frozen = None
        self.reads = []
        self.writes = []
        self.corrupt = None

    def read(self, address, selector=0):
        self.reads.append((address, selector))
        if address == 1:
            return int(self.running) << 25
        if address == 68:
            return (self.signature | self.sequence << 32 | self.epoch << 64 |
                    len(COUNTERS) << 96 | self.width << 104 | int(self.valid) << 112 |
                    int(self.running) << 113)
        if address == 70:
            return CLOCK_HZ*self.sequence | self.epoch << 64 | self.sequence << 96
        if self.corrupt == "timeout":
            raise RuntimeError("injected timeout")
        if self.corrupt == "mid_read" and selector == 0x82:
            self.sequence += 1
        chamber, pair = selector >> 7, selector & 127
        if self.corrupt == "clear" and selector == 0x86:
            self.epoch += 1
        if self.corrupt == "live_only":
            self.live[chamber][0] += 1
            self.live[chamber][1] += 1
        values = self.frozen[chamber]
        return values[pair*2] | values[pair*2+1] << 64 | self.sequence << 128

    def write(self, address, value):
        self.writes.append((address, value))
        if address == 40:
            self.running = bool(value)
            return
        assert (address, value) == (68, 1), "GUI must never clear counters"
        if self.corrupt == "ignored":
            return
        self.sequence += 1
        self.valid = True
        self.frozen = [list(row) for row in self.live]

    def request(self, opcode, *, address, payload=b"", subtarget=0, **kwargs):
        if opcode == FPGA_WRITE:
            self.write(address, int.from_bytes(payload, "big"))
            return SimpleNamespace(address=address, subtarget=subtarget, data=b"")
        assert opcode == FPGA_READ
        value = self.read(address, subtarget)
        data = value.to_bytes(20, "big")
        if self.corrupt == "short":
            data = data[:-1]
        if self.corrupt == "selector":
            subtarget ^= 1
        return SimpleNamespace(address=address, subtarget=subtarget, data=data)


class ProtocolTest(unittest.TestCase):
    def controller(self):
        obj = object.__new__(tab_lpgbt)
        obj.eth = DiagnosticFPGA()
        obj.miniDAQ_reg = MiniDAQ_reg()
        return obj

    def test_full_width_both_chambers_freeze_and_no_clear(self):
        obj = self.controller()
        obj.eth.corrupt = "live_only"
        value = obj.read_diagnostic_snapshot()
        self.assertEqual(value.chambers[0][0], 1 << 40)
        self.assertEqual(value.chambers[1][0], (1 << 40)+1)
        self.assertEqual(value.epoch, 3)
        self.assertFalse(value.running)
        self.assertEqual(obj.eth.writes, [(68, 1)])
        self.assertEqual([sel for addr, sel in obj.eth.reads if addr == 69],
                         list(range(7)) + list(range(128, 135)))

    def test_legacy_and_wrong_layout_do_not_write(self):
        for field, value in (("signature", 0), ("width", 32)):
            obj = self.controller()
            setattr(obj.eth, field, value)
            with self.assertRaises(RuntimeError):
                obj.read_diagnostic_snapshot()
            self.assertEqual(obj.eth.writes, [])

    def test_mixed_incomplete_and_unacknowledged_reads_are_not_returned(self):
        for corruption in ("mid_read", "clear", "timeout", "ignored", "short", "selector"):
            with self.subTest(corruption=corruption):
                obj = self.controller()
                obj.eth.corrupt = corruption
                with self.assertRaises(RuntimeError):
                    obj.read_diagnostic_snapshot()

    def test_counter_invariant_validated(self):
        obj = self.controller()
        obj.eth.live[1][2] = 1
        with self.assertRaisesRegex(RuntimeError, "accounting"):
            obj.read_diagnostic_snapshot()

    def test_cancellation_and_deadline(self):
        obj = self.controller()
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            obj.read_diagnostic_snapshot(cancelled=lambda: True)
        self.assertEqual(obj.eth.writes, [])
        with patch("fpga_diagnostics.time.monotonic", side_effect=[0, 3]):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                read_snapshot(obj.eth.read, obj.eth.write)

    def test_cancellation_while_transport_is_busy(self):
        obj = self.controller()
        obj.eth._lock.acquire()
        try:
            worker = SnapshotWorker(obj.read_diagnostic_snapshot)
            worker.start()
            worker.requestInterruption()
            self.assertTrue(worker.wait(1000))
            self.assertIn("cancelled", worker.error)
            self.assertEqual(obj.eth.writes, [])
        finally:
            obj.eth._lock.release()

    def test_run_delta_and_reset_detection(self):
        base, current = snapshot(1, 100), snapshot(2, 107)
        self.assertEqual(current.delta(base)[0][0], 7)
        for changed in (replace(current, epoch=1), replace(current, cycles=0), snapshot(2, 90)):
            with self.assertRaises(RuntimeError):
                changed.delta(base)


class DiagnosticGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="minidaq_diagnostic_test_")
        self.old_cwd = os.getcwd()
        os.chdir(self.directory.name)
        self.backend = Backend()
        self.messages = []
        self.backend.message.connect(self.messages.append)
        self.parent = QtWidgets.QWidget()
        with patch.object(tab_capture, "refresh_devices"):
            self.capture = tab_capture(self.parent, self.backend)

    def tearDown(self):
        self.capture._pause_diagnostic_polling()
        self.parent.deleteLater()
        self.backend.deleteLater()
        self.app.processEvents()
        os.chdir(self.old_cwd)
        self.directory.cleanup()

    def finish_poll(self):
        deadline = time.monotonic() + 2
        while self.capture._diagnostic_worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            QtCore.QThread.msleep(1)
        self.assertIsNone(self.capture._diagnostic_worker)

    def test_display_run_totals_rates_and_final(self):
        widget = DiagnosticWidget()
        base, current = snapshot(1, 100), snapshot(2, 107, True)
        widget.show_snapshot(current, base, base)
        self.assertEqual(widget.table.item(0, 1).text(), "7")
        self.assertEqual(widget.table.item(0, 2).text(), "7.0")
        widget.show_snapshot(snapshot(3, 110), base, current, final=True)
        self.assertEqual(widget.table.item(0, 1).text(), "10")
        self.assertEqual(widget.table.item(0, 2).text(), "—")
        self.assertIn("Final", widget.status.text())
        widget.resize(1100, widget.minimumSizeHint().height())
        widget.show(); self.app.processEvents()
        self.assertGreater(widget.note.geometry().top(), widget.table.geometry().bottom())
        last_cell = widget.table.visualItemRect(widget.table.item(len(COUNTERS)-1, 0))
        self.assertLessEqual(last_cell.bottom(), widget.table.viewport().height())
        widget.close()

    def test_poll_background_thread_and_failure_is_stale_not_zero(self):
        self.capture.set_daq_run_control(diagnostic_snapshot_callback=lambda: snapshot(1, 100))
        self.capture._begin_diagnostics(1, 0)
        seen_threads = []

        def read(cancelled=None):
            seen_threads.append(QtCore.QThread.currentThread())
            return snapshot(2, 107, True)

        self.capture._diagnostic_snapshot_callback = read
        self.capture._poll_diagnostics()
        worker = self.capture._diagnostic_worker
        self.capture._poll_diagnostics()
        self.assertIs(worker, self.capture._diagnostic_worker)
        self.finish_poll()
        self.assertNotEqual(seen_threads[0], self.app.thread())
        self.assertEqual(self.capture.fpga_diagnostics.table.item(0, 1).text(), "7")

        def fail(cancelled=None):
            raise RuntimeError("injected link failure")

        self.capture._diagnostic_snapshot_callback = fail
        self.capture._poll_diagnostics(); self.finish_poll()
        self.assertEqual(self.capture.fpga_diagnostics.table.item(0, 1).text(), "7")
        self.assertIn("STALE", self.capture.fpga_diagnostics.status.text())
        self.assertIn("latest_error", self.backend._fpga_diagnostics)
        self.capture._diagnostic_snapshot_callback = lambda cancelled=None: snapshot(3, 112, True)
        self.capture._poll_diagnostics(); self.finish_poll()
        self.assertNotIn("latest_error", self.backend._fpga_diagnostics)
        self.assertEqual(self.capture.fpga_diagnostics.table.item(0, 1).text(), "12")

    def test_old_firmware_is_unavailable_and_noise_does_not_poll(self):
        def read():
            raise RuntimeError("old firmware")

        self.capture._diagnostic_snapshot_callback = read
        self.capture._begin_diagnostics(1, 0)
        self.assertFalse(self.capture._diagnostic_active)
        self.assertIn("Unavailable", self.capture.fpga_diagnostics.status.text())
        self.assertEqual(self.capture.fpga_diagnostics.table.item(0, 1).text(), "—")
        self.assertIn("start_error", self.backend._fpga_diagnostics)
        with patch.object(self.capture, "_diagnostic_snapshot_callback") as reader:
            for modes in ((0, 0), (1, 1), (1, 2)):
                self.capture._begin_diagnostics(*modes)
            reader.assert_not_called()

    def test_reset_invalidates_totals_for_the_rest_of_the_run(self):
        self.capture._diagnostic_snapshot_callback = lambda: snapshot(1, 100)
        self.capture._begin_diagnostics(1, 0)
        self.capture._diagnostic_snapshot_callback = lambda cancelled=None: snapshot(2, 0, True)
        self.capture._poll_diagnostics(); self.finish_poll()
        self.assertIsNotNone(self.capture._diagnostic_continuity_error)
        # Counts recovering above the baseline must not disguise a detected reset.
        self.capture._diagnostic_snapshot_callback = lambda cancelled=None: snapshot(3, 200, True)
        self.capture._poll_diagnostics(); self.finish_poll()
        self.assertIn("STALE", self.capture.fpga_diagnostics.status.text())
        self.capture._finish_diagnostics()
        self.assertNotIn("final", self.backend._fpga_diagnostics)
        self.assertIn("final_error", self.backend._fpga_diagnostics)

    def test_automatic_stop_collects_before_summary_and_log_close(self):
        capture, backend = self.capture, self.backend
        data_path = os.path.join(self.directory.name, "run0001.dat")
        backend.prepare_run_artifacts(data_path, {"mode": "capture"})
        summary_path = backend._current_summary_path
        log_path = backend._current_log_path

        def log(text):
            with open(log_path, "a") as stream:
                stream.write(text)

        backend.message.connect(log)
        reads = iter((snapshot(1, 100), snapshot(2, 109)))
        order = []
        capture.set_daq_run_control(
            diagnostic_snapshot_callback=lambda: next(reads),
            stop_callback=lambda: order.append("hardware stop"),
        )
        capture._begin_diagnostics(1, 0)
        capture._hardware_run_active = True
        backend.run_finished.connect(lambda: order.append("log close"))
        backend._cap_thread = SimpleNamespace(stop=lambda: order.append("capture stop"), wait=lambda ms: True)
        backend.stop_capture()  # Same entry point used by decode-error auto-stop.
        self.assertEqual(order, ["hardware stop", "capture stop", "log close"])
        self.assertEqual(backend._fpga_diagnostics["final"]["run_totals"][0]["accepted"], 9)
        summary = Path(summary_path).read_text()
        log_text = Path(log_path).read_text()
        self.assertIn("[fpga_triggerless_diagnostics]", summary)
        self.assertIn('"accepted": 9', summary)
        self.assertIn("[FPGA diagnostics start]", log_text)
        self.assertIn("[FPGA diagnostics final]", log_text)
        self.assertFalse(capture._diagnostic_active)

    def test_failed_final_snapshot_does_not_claim_run_totals_are_final(self):
        self.capture._diagnostic_snapshot_callback = lambda: snapshot(1, 100)
        self.capture._begin_diagnostics(1, 0)
        self.capture._diagnostic_snapshot_callback = lambda: snapshot(2, 110, True)
        self.capture._finish_diagnostics()
        self.assertNotIn("final", self.backend._fpga_diagnostics)
        self.assertIn("final_error", self.backend._fpga_diagnostics)
        self.assertIn("STALE", self.capture.fpga_diagnostics.status.text())

    def test_start_then_stop_while_poll_is_waiting_for_control_lock(self):
        controller = object.__new__(tab_lpgbt)
        controller.eth = DiagnosticFPGA()
        self.capture._diagnostic_snapshot_callback = controller.read_diagnostic_snapshot
        self.capture._begin_diagnostics(1, 0)
        controller.eth._lock.acquire()
        try:
            self.capture._poll_diagnostics()
            worker = self.capture._diagnostic_worker
            self.capture._pause_diagnostic_polling()
            self.assertFalse(worker.isRunning())
        finally:
            controller.eth._lock.release()
        self.capture._finish_diagnostics()
        self.app.processEvents()
        self.assertIn("Final", self.capture.fpga_diagnostics.status.text())


if __name__ == "__main__":
    unittest.main()
