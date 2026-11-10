"""CSM QC sequence against simulated hardware, plus the page and its real-tab hooks."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import csv
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from PyQt5 import QtWidgets

import csm_qc
from Worker_Monitor import Worker_Monitor
from ethernet_control_protocol import EthernetControlError, LPGBT_WRITE
from tab_lpgbt import tab_lpgbt
from tab_mezz import tab_mezz
from tab_monitor import tab_monitor
from tab_qc import tab_qc


GOOD_ID, WRONG_ID = 0x0362D093, 0x12345678


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class Hardware:
    def __init__(self, clock, log):
        self.clock, self.log = clock, log
        self.links = (0b11, 0b1)
        self.links_after_prbs = None
        self.pattern = {}
        self.resets = 0
        self.lock_after_resets = 1
        self.prbs_errors_at = None
        self.lock_lost_at = None
        self.frame_rate = 8e6
        self.ber_error_at = None
        self.stalled_tdc = None
        self.prbs_started = None
        self.prbs_reads = 0
        self.ber_reads = 0
        self.prbs_burst_times = []  # One error burst each; a counter reset clears it.
        self.ber_burst_times = []   # Each adds 2 errors to TDC 5's cumulative dline1 count.

    def read_links(self):
        if self.links_after_prbs is not None and self.resets:
            return self.links_after_prbs
        return self.links

    def uplink_count(self):
        return 2

    def set_prbs(self, addr, link, selection):
        self.log.append(("prbs", addr, selection))
        self.pattern[link] = selection

    def reset_prbs_counters(self, mask):
        self.log.append(("prbs_reset", mask))
        self.resets += 1
        self.prbs_started = self.clock()

    def read_prbs(self, uplinks):
        running = all(self.pattern.get(link) == csm_qc.PRBS_31 for link in (0, 1))
        locked = 0b11 if running and self.resets >= self.lock_after_resets else 0
        if self.lock_lost_at is not None and self.clock() >= self.lock_lost_at:
            locked = 0b10
        self.prbs_reads += 1
        errors = 7 if self.prbs_errors_at is not None and self.clock() >= self.prbs_errors_at else 0
        if any(self.prbs_started < t <= self.clock() for t in self.prbs_burst_times):
            errors = 5
        return locked, [errors, 0]

    def read_ber(self, tdc):
        frames = 1000 + int(self.frame_rate * self.clock())
        if tdc == self.stalled_tdc:
            return 1000, frames, 0, 0
        self.ber_reads += 1
        errors = 3 if self.ber_error_at is not None and self.clock() >= self.ber_error_at else 0
        if tdc == 5:
            errors += 2 * sum(1 for t in self.ber_burst_times if t <= self.clock())
        return frames, frames, errors, 0


class Checkbox:
    def __init__(self, log, on_change=None):
        self.checked, self.log, self.on_change = True, log, on_change
        self.blocked = False

    def blockSignals(self, value):
        previous, self.blocked = self.blocked, value
        return previous

    def setChecked(self, value):
        changed = value != self.checked
        self.checked = value
        if changed and not self.blocked and self.on_change:
            self.on_change(value)

    def isChecked(self):
        return self.checked


class Lpgbt:
    def __init__(self, clock, log):
        self.clock, self.log = clock, log
        self._link_ready_poll = None
        self.rxprbssel = [0]
        self.idcode_results = []  # None means the read gave no answer.
        self.idcode_default = GOOD_ID
        self.program_seconds = 12.0
        self.program_ok = True
        self.program_end = None
        self.cancelled = False
        self.worker_read_CSM_idcode = None
        self.file_path_box = SimpleNamespace(text=lambda: "x.bit", setText=lambda text: log.append(("bitfile", text)))
        slave = Checkbox(log, lambda value: self.slave_control(0, "enable" if value else "disable"))
        self.uplink_status_component = [None, slave, None, None]

    @property
    def worker_load_CSM_bit(self):
        return object() if self.program_end is not None and self.clock() < self.program_end else None

    def load_lpgbt(self, csm, is_master):
        self.log.append(("load", "master" if is_master else "slave"))

    def slave_control(self, csm, state):
        self.log.append(("slave", "enable" if state == "enable" else "disable"))

    def update_status(self):
        self.log.append(("update_status",))

    def read_fpga_id(self, csm, on_result=None):
        self.log.append(("idcode",))
        idcode = self.idcode_results.pop(0) if self.idcode_results else self.idcode_default
        if idcode is not None:
            on_result(csm, idcode, False)  # QC must not depend on DONE and INIT.
        return True

    def load_fpga_bit_ethernet(self, csm, on_programmed=None):
        self.log.append(("program",))
        self.program_end = self.clock() + self.program_seconds
        if self.program_ok:
            on_programmed(csm)
        return True

    def cancel_load_CSM_bit(self):
        self.cancelled = True
        self.program_end = None

    def fpga_physical_rx_reset(self):
        self.log.append(("rx_reset",))


class Indicator:
    def __init__(self):
        self.style = "gray"

    def setStyleSheet(self, style):
        self.style = style

    def styleSheet(self):
        return self.style


class Mezz:
    def __init__(self, log):
        self.log = log
        self.detected = set(range(20))
        self.detect_by_scan = []
        self.csm_indicator_list = [[[Indicator() for _ in range(3)] for _ in range(20)] for _ in range(2)]
        self.selected = {0: set(), 1: set()}
        self.bad_rounds = 0
        self.enable_bad_rounds = 0
        self.raise_in_write = 0
        self.thresholds = []
        self.spinBox_ASD_main_thr = SimpleNamespace(setValue=self.thresholds.append)
        self.scans = 0

    def check_all_checkboxes(self, csm, state):
        self.selected[csm] = set(range(20)) if state == csm_qc.Qt.Checked else set()

    def mezz_scan(self):
        self.scans += 1
        self.log.append(("mezz_scan",))
        detected = self.detect_by_scan.pop(0) if self.detect_by_scan else self.detected
        self.selected[0] &= set(detected)

    def selected_mezz_indices(self):
        return [(csm, mezz) for csm in (0, 1) for mezz in sorted(self.selected[csm])]

    def _set(self, which, ok=True):
        for mezz in self.selected[0]:
            self.csm_indicator_list[0][mezz][which].style = "background-color: green" if ok else "background-color: red"

    def _set_all_asd_main_thr(self, value):
        pass

    def write_TDC_all(self):
        self.log.append(("write_tdc",))
        if self.raise_in_write:
            self.raise_in_write -= 1
            raise RuntimeError("SCA timeout")
        self._set(0, self.bad_rounds == 0)
        if self.bad_rounds:
            self.bad_rounds -= 1

    def write_ASD_all(self):
        self.log.append(("write_asd",))
        self._set(1)

    def TDC_input_config(self, enable):
        self.log.append(("tdc_inputs", enable))
        self._set(0, not (enable and self.enable_bad_rounds))

    def ASD_channel_mode_config(self, active):
        self.log.append(("asd_channels", active))
        self._set(1)

    def fpga_global_reset(self):
        self.log.append(("global_reset",))

    def get_dline_status(self):
        self.log.append(("dline",))
        self._set(2)
        if self.enable_bad_rounds:
            self.enable_bad_rounds -= 1


class Monitor:
    def __init__(self, clock, log, folder_box_text="old"):
        self.clock, self.log = clock, log
        self.end_time = None
        self.interval = SimpleNamespace(value=lambda: self._interval, setValue=lambda value: setattr(self, "_interval", value))
        self._interval = 60.0
        self._folder = folder_box_text
        self.lineEdit_csv_directory = SimpleNamespace(
            text=lambda: self._folder, setText=lambda text: setattr(self, "_folder", text))
        self.checkBox_monitor_mezz = Checkbox(log)
        self.checkBox_monitor_csm = Checkbox(log)
        self.csm = SimpleNamespace(
            checkbox_list=[Checkbox(log), Checkbox(log)],
            _monitor_metrics=lambda: [((0, -1, 0), "CSM0 Temp", "C", "CSM0_SCA_Temp_display_C")],
            _monitor_limits={(0, -1, 0): (0.0, 50.0)})
        self.mezz = SimpleNamespace(select_scanned_mezz=lambda selected: None,
                                    get_monitor_limits=lambda: {"AVDD": (2.9, 3.1)})
        self.status = SimpleNamespace(text=lambda: "Completed scan")
        self.csv_path = None
        self.scan_limit = 0
        self.rows = 20
        self.avdd = "3.0"
        self.seen_interval = self.seen_limit = None

    @property
    def worker(self):
        return object() if self.end_time is not None and self.clock() < self.end_time else None

    def start(self):
        self.end_time = self.clock() + self.rows * self._interval
        self.seen_interval, self.seen_limit = self._interval, self.scan_limit
        self.log.append(("monitor_start",))
        self.csv_path = Path(self._folder) / "monitor_1.csv"
        with open(self.csv_path, "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["timestamp", "scan", "CSM0_Mezz0_AVDD_display_V", "CSM0_SCA_Temp_display_C"])
            for scan in range(self.rows):
                writer.writerow(["t", scan + 1, self.avdd, "30"])

    def stop(self):
        self.end_time = None

    def plot_csv(self):
        self.log.append(("plot_csv",))
        Path(self.csv_path).with_suffix(".png").write_bytes(b"png")


class Signal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def disconnect(self, slot):
        self.slots.remove(slot)

    def emit(self, value):
        for slot in list(self.slots):
            slot(value)


class Backend:
    def __init__(self):
        self.running = False
        self.decode_status = Signal()

    def is_running(self):
        return self.running


class Capture:
    def __init__(self, clock, backend, log):
        self.clock, self.backend, self.log = clock, backend, log
        self.folder = "last-operator-folder"
        self.edit_outdir = SimpleNamespace(text=lambda: self.folder, setText=lambda text: setattr(self, "folder", text))
        self._daq_preflight_callback = "preflight"
        self.selections = []
        self._plot_selection_callback = lambda live, save: self.selections.append((set(live), set(save)))
        self.trigger_rate = 10.0
        self.errors_at = None
        self.overflow = 0
        self.tdc_hits = 5
        self.dies_at = None
        self.begun = None
        self.seen = {}

    def run_plot_live_labels(self):
        return {"TDC overall"}

    def run_plot_save_labels(self):
        return set()

    def _apply_plot_selection(self):
        self.selections.append("restored")

    def _save_settings(self):
        self.log.append(("save_settings", self.folder))

    def snapshot(self):
        elapsed = self.clock() - self.begun
        errors = np.zeros(40, dtype=int)
        if self.errors_at is not None and elapsed >= self.errors_at:
            errors[3] = 2
        overflow = np.zeros(40, dtype=int)
        overflow[1] = self.overflow
        histogram = np.zeros((40, 8), dtype=int)
        histogram[:, 0] = self.tdc_hits
        return SimpleNamespace(triggers=int(self.trigger_rate * elapsed), decode_err_cnt=errors,
                               overflow_cnt=overflow, adc_hist=histogram, hits_total=100,
                               decode_error_total=int(errors.sum()))

    def start(self):
        self.seen = dict(folder=self.folder, preflight=self._daq_preflight_callback)
        self.log.append(("capture_start",))
        self.backend.running = True
        self.begun = self.clock()

    def stop(self):
        self.log.append(("capture_stop",))
        self.backend.running = False
        self.backend.decode_status.emit(self.snapshot())


class Adc:
    def __init__(self):
        self.fit_only = True
        self.fit_only_when_saved = None
        self.chk_fit_only = SimpleNamespace(isChecked=lambda: self.fit_only,
                                            setChecked=lambda value: setattr(self, "fit_only", value))
        self.saved = []
        self.drop = 0

    def save_plots(self, folder, active_tdcs=None):
        self.fit_only_when_saved = self.fit_only
        self.saved = list(active_tdcs)
        return [f"{folder}/{tdc}.png" for tdc in active_tdcs[self.drop:]]


class Ui:
    def __init__(self):
        self.steps = []
        self.questions = []
        self.answer = True
        self.result = None
        self.redo_answers = []  # Answers to the step-failure pop-up; Stop QC once they run out.
        self.redo_asked = []

    def status(self, text):
        pass

    def step(self, key, state):
        self.steps.append((key, state))

    def confirm(self, title, text):
        self.questions.append(text)
        return self.answer

    def ask_redo(self, step, reason):
        self.redo_asked.append((step, reason))
        return self.redo_answers.pop(0) if self.redo_answers else False

    def finished(self, verdict, reason, folder):
        self.result = (verdict, reason, folder)


class Sim:
    def __init__(self, test, **settings):
        self.directory = tempfile.TemporaryDirectory()
        test.addCleanup(self.directory.cleanup)
        self.clock = Clock()
        self.log = []
        self.hw = Hardware(self.clock, self.log)
        self.lpgbt = Lpgbt(self.clock, self.log)
        self.mezz = Mezz(self.log)
        self.monitor = Monitor(self.clock, self.log)
        self.backend = Backend()
        self.capture = Capture(self.clock, self.backend, self.log)
        self.adc = Adc()
        self.ui = Ui()
        self.mismatch = ([], [])
        tabs = SimpleNamespace(eth=None, lpgbt=self.lpgbt, mezz=self.mezz, monitor=self.monitor,
                               capture=self.capture, adc=self.adc, backend=self.backend,
                               tdc_mismatch=lambda: self.mismatch,
                               show_adc_plots=lambda: self.log.append(("show_adc_plots",)))
        self.settings = csm_qc.QcSettings("SN 42", "Ana", "fw.bit", self.directory.name, **settings)
        self.run = csm_qc.CsmQcRun(tabs, self.settings, self.ui, hardware=self.hw, clock=self.clock,
                                   now=lambda: dt.datetime(2026, 11, 4, 13, 46))
        self.on_tick = None

    def drive(self):
        for delay in self.run.run():
            self.clock.t += delay
            if self.backend.running:
                self.backend.decode_status.emit(self.capture.snapshot())
            if self.on_tick:
                self.on_tick(self)
        return self.ui.result

    def actions(self):
        return [entry[0] for entry in self.log]

    def summary(self):
        return json.loads((Path(self.ui.result[2]) / "qc_summary.json").read_text())


class CalculationTests(unittest.TestCase):
    def test_ber_formulas(self):
        self.assertAlmostEqual(csm_qc.prbs_ber_limit(781.25), 1e-13)
        self.assertEqual(csm_qc.prbs_ber_limit(0), float("inf"))
        self.assertAlmostEqual(csm_qc.dline_ber_limit(2.5e9), 1e-11)
        self.assertEqual(csm_qc.dline_ber_limit(0), float("inf"))

    def test_ber_page_layout_matches_the_dialog(self):
        bits = format(5, "044b") + format(6, "044b") + format(7, "036b") + format(8, "036b")
        self.assertEqual(csm_qc.decode_ber_info(bits), (5, 6, 7, 8))
        with self.assertRaises(ValueError):
            csm_qc.decode_ber_info(0)

    def test_folder_is_output_serial_operator_time(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = csm_qc.QcSettings("S1", "Ana", "b", directory)
            now = dt.datetime(2026, 11, 4, 13, 46)
            first = csm_qc.create_run_folder(settings, now)
            self.assertEqual(Path(first), Path(directory, "S1", "Ana", "202611041346"))
            self.assertTrue(Path(first).is_dir())
            second = csm_qc.create_run_folder(settings, now)
            self.assertEqual(Path(second).name, "202611041346_2")

    def test_path_component_rules(self):
        for good in ("CSM-042", "A B", "a.b_c"):
            self.assertTrue(csm_qc.valid_path_component(good), good)
        for bad in ("", "..", "a/b", "a\\b", "a:", "a.", " a", 'a"'):
            self.assertFalse(csm_qc.valid_path_component(bad), bad)


class FullRunTests(unittest.TestCase):
    def test_good_board_runs_every_step_in_order(self):
        sim = Sim(self)
        verdict, reason, folder = sim.drive()
        self.assertEqual((verdict, reason), ("PASS", ""))
        self.assertEqual([state for _key, state in sim.ui.steps].count("pass"), len(csm_qc.STEPS))

        actions = sim.actions()
        order = ["load", "slave", "slave", "load", "update_status", "idcode", "program", "idcode",
                 "prbs", "mezz_scan", "write_tdc", "write_asd", "tdc_inputs", "global_reset",
                 "dline", "tdc_inputs", "asd_channels", "monitor_start", "plot_csv",
                 "capture_start", "capture_stop"]
        position = -1
        for action in order:
            position = actions.index(action, position + 1)
        self.assertEqual([e for e in sim.log if e[0] == "load"], [("load", "master"), ("load", "slave")])
        self.assertEqual([e for e in sim.log if e[0] == "slave"], [("slave", "disable"), ("slave", "enable")])
        self.assertEqual([e for e in sim.log if e[0] == "tdc_inputs"], [("tdc_inputs", False), ("tdc_inputs", True)])
        self.assertIn(("bitfile", "fw.bit"), sim.log)

        run_files = {path.name for path in Path(folder).iterdir()}
        self.assertTrue({"qc_log.txt", "qc_summary.txt", "qc_summary.json", "monitor_1.csv", "monitor_1.png"} <= run_files)
        self.assertEqual(Path(folder).relative_to(sim.directory.name), Path("SN 42", "Ana", "202611041346"))
        summary = sim.summary()
        self.assertEqual(summary["csm_serial"], "SN 42")
        self.assertEqual(summary["flags"], [])

    def test_operator_settings_come_back_after_the_run(self):
        sim = Sim(self)
        sim.drive()
        self.assertEqual(sim.capture.folder, "last-operator-folder")
        self.assertEqual(sim.capture._daq_preflight_callback, "preflight")
        self.assertTrue(sim.adc.fit_only)
        self.assertEqual(sim.capture.selections[-1], "restored")
        self.assertEqual(sim.backend.decode_status.slots, [])
        self.assertEqual(sim.monitor.interval.value(), 60.0)
        self.assertEqual(sim.monitor.lineEdit_csv_directory.text(), "old")
        self.assertEqual(sim.monitor.scan_limit, 0)


class LinkAndFpgaTests(unittest.TestCase):
    def test_link_failure_alarms_with_the_bits_read(self):
        sim = Sim(self)
        sim.hw.links = (0b01, 0b1)
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("00000001", reason)
        self.assertNotIn("idcode", sim.actions())

    def test_extra_links_on_larger_firmware_still_pass(self):
        sim = Sim(self)
        sim.hw.links = (0b1111, 0b11)
        self.assertEqual(sim.drive()[0], "PASS")

    def test_idcode_failure_rechecks_links_then_retries(self):
        sim = Sim(self)
        sim.lpgbt.idcode_results = [None, GOOD_ID, GOOD_ID]
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(sim.actions().count("idcode"), 3)

    def test_idcode_failure_with_bad_links_alarms_without_programming(self):
        sim = Sim(self)
        sim.lpgbt.idcode_results = [WRONG_ID]
        original = sim.lpgbt.read_fpga_id

        def drop_links(csm, on_result=None):
            result = original(csm, on_result=on_result)
            sim.hw.links = (0, 0)
            return result
        sim.lpgbt.read_fpga_id = drop_links
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("links are not ready", reason)
        self.assertNotIn("program", sim.actions())

    def test_idcode_failing_twice_alarms_without_programming(self):
        sim = Sim(self)
        sim.lpgbt.idcode_default = WRONG_ID
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("0x0362D093", reason)
        self.assertNotIn("DONE", reason)
        self.assertNotIn("program", sim.actions())

    def test_programming_past_30_seconds_is_cancelled(self):
        sim = Sim(self)
        sim.lpgbt.program_seconds = 45.0
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("30 s", reason)
        self.assertTrue(sim.lpgbt.cancelled)
        self.assertNotIn(("prbs", 117, 4), sim.log)

    def test_programming_failure_alarms(self):
        sim = Sim(self)
        sim.lpgbt.program_ok = False
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("programming", reason)

    def test_correct_id_with_done_0_goes_on_to_programming(self):
        sim = Sim(self)
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(sim.actions().count("idcode"), 2)

    def test_wrong_id_after_programming_alarms(self):
        sim = Sim(self)
        sim.lpgbt.idcode_results = [GOOD_ID, WRONG_ID]
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("after programming", reason)


class PrbsTests(unittest.TestCase):
    def test_none_comes_before_prbs31_and_framing_returns_afterwards(self):
        sim = Sim(self)
        sim.drive()
        calls = [e for e in sim.log if e[0] == "prbs"]
        self.assertEqual(calls, [("prbs", 117, 0), ("prbs", 115, 0),
                                 ("prbs", 117, 4), ("prbs", 115, 4),
                                 ("prbs", 117, 0), ("prbs", 115, 0)])
        self.assertLess(sim.actions().index("prbs_reset"), sim.actions().index("mezz_scan"))

    def test_stops_once_the_target_is_reached(self):
        sim = Sim(self)
        sim.drive()
        result = sim.summary()["results"]["prbs"]
        self.assertGreaterEqual(result["seconds"], 781.25)
        self.assertLess(result["seconds"], 781.25 + 2 * csm_qc.BER_POLL_S)
        self.assertLessEqual(result["ber_limit"], 1e-13)
        self.assertEqual(result["line_rate_bps"], 12.8e9)

    def test_target_is_operator_settable(self):
        sim = Sim(self, prbs_target=1e-11)
        sim.drive()
        self.assertLess(sim.summary()["results"]["prbs"]["seconds"], 10.0)

    def test_errors_that_keep_coming_fail_after_three_clears(self):
        sim = Sim(self)
        sim.hw.prbs_errors_at = 100.0
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("master 7", reason)
        self.assertIn("3 times", reason)
        self.assertNotIn("mezz_scan", sim.actions())
        self.assertEqual(sim.hw.pattern, {0: 0, 1: 0})
        # Lock-up reset, measurement start, then one clear per error, never a link reset.
        self.assertEqual(sim.actions().count("prbs_reset"), 2 + 3)
        self.assertNotIn("rx_reset", sim.actions())
        self.assertEqual(len(sim.ui.redo_asked), 1)

    def test_an_error_burst_is_cleared_and_the_ber_counted_again(self):
        sim = Sim(self)
        sim.hw.prbs_burst_times = [300.0]
        self.assertEqual(sim.drive()[0], "PASS")
        result = sim.summary()["results"]["prbs"]
        self.assertEqual(len(result["error_clears"]), 1)
        self.assertIn("master 5", result["error_clears"][0])
        # The BER is counted from the clear, so the test runs on for the full time after it.
        self.assertGreaterEqual(result["seconds"], 781.25)
        self.assertGreater(result["total_seconds"], result["seconds"] + 200)
        self.assertTrue(any("PRBS error count cleared 1 time" in flag for flag in sim.summary()["flags"]))
        self.assertEqual(sim.ui.redo_asked, [])

    def test_three_bursts_still_pass(self):
        sim = Sim(self)
        sim.hw.prbs_burst_times = [100.0, 200.0, 300.0]
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(len(sim.summary()["results"]["prbs"]["error_clears"]), 3)

    def test_a_fourth_burst_fails(self):
        sim = Sim(self)
        sim.hw.prbs_burst_times = [100.0, 200.0, 300.0, 400.0]
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("3 times", reason)

    def test_zero_target_switches_the_pattern_but_measures_nothing(self):
        sim = Sim(self, prbs_target=0.0)
        self.assertEqual(sim.drive()[0], "PASS")
        calls = [e for e in sim.log if e[0] == "prbs"]
        self.assertEqual(calls, [("prbs", 117, 0), ("prbs", 115, 0), ("prbs", 117, 4), ("prbs", 115, 4),
                                 ("prbs", 117, 0), ("prbs", 115, 0)])
        self.assertEqual(sim.hw.prbs_reads, 0)
        self.assertIn(("prbs", "skip"), sim.ui.steps)
        summary = sim.summary()
        self.assertEqual(summary["results"]["prbs"], {"skipped": True})
        step = next(s for s in summary["steps"] if s["name"].startswith("4."))
        self.assertEqual(step["result"], "SKIPPED")

    def test_no_lock_never_passes_on_zero_errors(self):
        sim = Sim(self)
        sim.hw.lock_after_resets = 10**6
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("did not lock", reason)
        self.assertEqual(sim.hw.pattern, {0: 0, 1: 0})

    def test_lock_lost_during_the_test_fails(self):
        sim = Sim(self)
        sim.hw.lock_lost_at = 200.0
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("lost lock", reason)

    def test_second_counter_reset_recovers_a_late_lock(self):
        sim = Sim(self)
        sim.hw.lock_after_resets = 3
        self.assertEqual(sim.drive()[0], "PASS")

    def test_links_not_returning_after_prbs_alarm(self):
        sim = Sim(self)
        sim.hw.links_after_prbs = (0b10, 0b1)
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("rx_reset", sim.actions())
        self.assertIn("links are not ready", reason)


class MezzTests(unittest.TestCase):
    def test_missing_mezz_asks_once_and_continues_without_it(self):
        sim = Sim(self)
        sim.mezz.detected = set(range(20)) - {7, 12}
        sim.mezz.bad_rounds = 2
        verdict, _reason, _folder = sim.drive()
        self.assertEqual(verdict, "PASS")
        self.assertEqual(len(sim.ui.questions), 1)
        self.assertIn("7, 12", sim.ui.questions[0])
        self.assertNotIn(7, sim.adc.saved)
        self.assertTrue(any("[7, 12]" in flag for flag in sim.summary()["flags"]))

    def test_declining_ends_the_run(self):
        sim = Sim(self)
        sim.mezz.detected = set(range(19))
        sim.ui.answer = False
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("[19]", reason)
        self.assertEqual(sim.mezz.scans, 1)
        self.assertEqual(sim.ui.redo_asked, [])

    def test_all_detected_never_asks(self):
        sim = Sim(self)
        sim.drive()
        self.assertEqual(sim.ui.questions, [])

    def test_csm1_is_left_out(self):
        sim = Sim(self)
        sim.mezz.selected[1] = set(range(20))
        sim.drive()
        self.assertEqual(sim.mezz.selected[1], set())

    def test_threshold_reaches_the_mezz_page(self):
        sim = Sim(self, asd_threshold=99)
        sim.drive()
        self.assertEqual(set(sim.mezz.thresholds), {99})

    def test_retries_then_passes(self):
        sim = Sim(self)
        sim.mezz.bad_rounds = 10
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(sim.summary()["results"]["mezz_attempts"], 11)

    def test_gives_up_after_ten_retries(self):
        sim = Sim(self)
        sim.mezz.bad_rounds = 11
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("TDC config", reason)
        self.assertEqual(sim.mezz.scans, 11)
        self.assertNotIn("monitor_start", sim.actions())

    def test_program_exception_counts_as_a_failed_attempt(self):
        sim = Sim(self)
        sim.mezz.raise_in_write = 2
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(sim.summary()["results"]["mezz_attempts"], 3)

    def test_mezz_vanishing_on_a_retry_is_not_asked_again(self):
        sim = Sim(self)
        everything = set(range(20))
        sim.mezz.detect_by_scan = [everything] + [everything - {4}] * 15
        sim.mezz.bad_rounds = 1
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("Mezz4 no longer detected", reason)
        self.assertEqual(sim.ui.questions, [])

    def test_disabling_inputs_cannot_hide_a_failed_tdc_configuration(self):
        sim = Sim(self)
        sim.mezz.bad_rounds = 11  # The fake's TDC_input_config turns the indicator green.
        self.assertEqual(sim.drive()[0], "FAIL")
        self.assertNotIn("global_reset", sim.actions())

    def test_stale_green_indicators_do_not_hide_a_failed_attempt(self):
        sim = Sim(self)
        original = sim.mezz.write_TDC_all
        calls = []

        def stop_early_on_retry():
            calls.append(1)
            if len(calls) == 1:
                original()  # All green from a first pass that fails on D-line only.
                sim.mezz.csm_indicator_list[0][5][0].style = "background-color: red"
            # Later attempts return early, as write_TDC_all does after a bad readback.
        sim.mezz.write_TDC_all = stop_early_on_retry
        verdict, _reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")

    def test_enable_failure_repeats_scan_and_program(self):
        sim = Sim(self)
        sim.mezz.enable_bad_rounds = 2
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertGreater(sim.mezz.scans, 1)
        self.assertEqual([e for e in sim.log if e[0] == "tdc_inputs"][-1], ("tdc_inputs", True))


class DlineBerTests(unittest.TestCase):
    def test_stops_at_target_using_frames_counted_in_this_step(self):
        sim = Sim(self)
        sim.drive()
        result = sim.summary()["results"]["dline_ber"]
        self.assertGreaterEqual(result["frames"], 2.5e9)
        self.assertLess(result["frames"], 2.5e9 + 8e6 * 2 * csm_qc.BER_POLL_S)
        self.assertLessEqual(result["ber_limit"], 1e-11)

    def ber_step_start(self, sim):
        # The time the D-line step starts in a good run, so bursts can be placed inside it.
        probe = Sim(self)
        probe.drive()
        return next(s for s in probe.summary()["steps"] if s["name"].startswith("5."))

    def test_an_error_burst_is_cleared_and_the_ber_counted_again(self):
        sim = Sim(self)
        sim.hw.ber_burst_times = [1000.0]
        self.assertEqual(sim.drive()[0], "PASS")
        result = sim.summary()["results"]["dline_ber"]
        self.assertEqual(len(result["error_clears"]), 1)
        self.assertIn("TDC 5 dline1 2", result["error_clears"][0])
        self.assertGreaterEqual(result["frames"], 2.5e9)
        self.assertNotIn("global_reset", sim.actions()[sim.actions().index("dline"):sim.actions().index("tdc_inputs", sim.actions().index("dline"))])

    def test_errors_that_keep_coming_fail_after_three_clears_and_name_the_tdc(self):
        sim = Sim(self)
        sim.hw.ber_burst_times = [1000.0 + 4 * n for n in range(200)]
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("TDC 5", reason)
        self.assertIn("3 times", reason)
        self.assertNotIn("monitor_start", sim.actions())

    def test_zero_target_skips_the_step(self):
        sim = Sim(self, dline_target=0.0)
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(sim.hw.ber_reads, 0)
        self.assertIn(("ber", "skip"), sim.ui.steps)
        self.assertEqual(sim.summary()["results"]["dline_ber"], {"skipped": True})

    def test_counts_older_than_the_step_are_ignored(self):
        sim = Sim(self)
        original = sim.hw.read_ber
        sim.hw.read_ber = lambda tdc: tuple(value + 50 if i >= 2 else value
                                            for i, value in enumerate(original(tdc)))
        self.assertEqual(sim.drive()[0], "PASS")

    def test_dead_dline_fails_instead_of_running_forever(self):
        sim = Sim(self)
        sim.hw.stalled_tdc = 2
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("TDC 2 dline1 stopped", reason)


class MonitorTests(unittest.TestCase):
    def test_runs_twenty_scans_every_five_seconds_in_the_run_folder(self):
        sim = Sim(self)
        folder = sim.drive()[2]
        self.assertEqual((sim.monitor.seen_interval, sim.monitor.seen_limit), (5.0, 20))
        self.assertTrue((Path(folder) / "monitor_1.csv").is_file())
        self.assertFalse(sim.monitor.csm.checkbox_list[1].isChecked())

    def test_out_of_range_is_flagged_not_failed(self):
        sim = Sim(self)
        sim.monitor.avdd = "3.4"
        self.assertEqual(sim.drive()[0], "PASS")
        flags = sim.summary()["flags"]
        self.assertTrue(any("Mezz0_AVDD" in flag and "20/20" in flag for flag in flags), flags)

    def test_unreadable_values_are_flagged_not_failed(self):
        sim = Sim(self)
        sim.monitor.avdd = "NA"
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertTrue(any("no valid reading" in flag for flag in sim.summary()["flags"]))

    def test_too_few_scans_fail(self):
        sim = Sim(self)
        sim.monitor.rows = 19
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("19/20", reason)

    def test_real_worker_stops_at_the_scan_limit(self):
        worker = Worker_Monitor.__new__(Worker_Monitor)
        QtObject = Worker_Monitor.__mro__[1]
        QtObject.__init__(worker)
        worker.scan_limit, worker.interval_seconds = 3, 0
        worker.stop_requested = SimpleNamespace(is_set=lambda: False, wait=lambda _delay: False)
        worker.mezz_reader = worker.csm_reader = None
        worker.monitor_csv = Mock()
        scans = []
        worker._scan = scans.append
        worker.run()
        self.assertEqual(scans, [1, 2, 3])

    def test_real_worker_without_a_limit_runs_until_stop(self):
        worker = Worker_Monitor.__new__(Worker_Monitor)
        QtObject = Worker_Monitor.__mro__[1]
        QtObject.__init__(worker)
        scans = []
        worker.scan_limit, worker.interval_seconds = 0, 0
        worker.stop_requested = SimpleNamespace(is_set=lambda: len(scans) >= 7, wait=lambda _delay: len(scans) >= 7)
        worker.mezz_reader = worker.csm_reader = None
        worker.monitor_csv = Mock()
        worker._scan = scans.append
        worker.run()
        self.assertEqual(len(scans), 7)


class CaptureTests(unittest.TestCase):
    def capture_seconds(self, sim):
        return sim.summary()["results"]["capture"]["seconds"]

    def test_stops_at_30_seconds_with_enough_triggers(self):
        sim = Sim(self)
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertLess(self.capture_seconds(sim), 31.0)

    def test_extends_past_30_seconds_until_20_triggers(self):
        sim = Sim(self)
        sim.capture.trigger_rate = 0.5
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertAlmostEqual(self.capture_seconds(sim), 40.0, delta=1.0)

    def test_fewer_than_20_triggers_by_60_seconds_fails(self):
        sim = Sim(self)
        sim.capture.trigger_rate = 0.3
        verdict, reason, folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("need at least 20.", reason)
        self.assertLess(self.capture_seconds(sim), 61.0)
        self.assertEqual(len(sim.adc.saved), 20)

    def test_error_stops_at_once_saves_plots_and_fails(self):
        sim = Sim(self)
        sim.capture.errors_at = 5.0
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("TDC 03 err=2", reason)
        self.assertLess(self.capture_seconds(sim), 7.0)
        self.assertEqual(len(sim.adc.saved), 20)
        self.assertFalse(sim.backend.running)

    def test_adc_page_is_showing_before_the_capture_starts(self):
        sim = Sim(self)
        sim.drive()
        self.assertLess(sim.actions().index("show_adc_plots"), sim.actions().index("capture_start"))

    def test_uses_the_run_folder_and_skips_the_preflight_popup(self):
        sim = Sim(self)
        folder = sim.drive()[2]
        self.assertEqual(sim.capture.seen, {"folder": folder, "preflight": None})

    def test_plots_are_raw_adc_even_if_fit_only_was_ticked(self):
        sim = Sim(self)
        sim.adc.fit_only = True
        sim.drive()
        self.assertIs(sim.adc.fit_only_when_saved, False)
        self.assertEqual(sim.capture.selections[0], ({"TDC overall", "ADC overall"}, set()))

    def test_geometry_mismatch_is_flagged(self):
        sim = Sim(self)
        sim.mismatch = ([], [1, 2, 3])
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertTrue(any("[1, 2, 3]" in flag for flag in sim.summary()["flags"]))

    def test_dead_tdc_and_overflow_are_flagged(self):
        sim = Sim(self)
        sim.capture.tdc_hits = 0
        sim.capture.overflow = 4
        self.assertEqual(sim.drive()[0], "PASS")
        flags = " ".join(sim.summary()["flags"])
        self.assertIn("no hits", flags)
        self.assertIn("overflow", flags)

    def test_missing_plots_fail(self):
        sim = Sim(self)
        sim.adc.drop = 1
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("19 of 20", reason)

    def test_capture_that_will_not_start_fails(self):
        sim = Sim(self)
        sim.capture.start = lambda: None
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("did not start", reason)
        self.assertEqual(sim.capture.folder, "last-operator-folder")

    def test_capture_stopping_itself_fails(self):
        sim = Sim(self)
        def die(run_sim):
            if sim.backend.running and sim.clock.t - sim.capture.begun > 10:
                sim.backend.running = False
        sim.on_tick = die
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("stopped by itself", reason)


class RedoTests(unittest.TestCase):
    def test_redo_runs_only_the_failed_step_again(self):
        sim = Sim(self)
        sim.hw.links = (0b01, 0b1)

        def repair(run_sim):
            if sim.ui.redo_asked:
                sim.hw.links = (0b11, 0b1)
        sim.on_tick = repair
        sim.ui.redo_answers = [True]
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(len(sim.ui.redo_asked), 1)
        self.assertIn("00000001", sim.ui.redo_asked[0][1])
        self.assertEqual([e for e in sim.log if e[0] == "load"], [("load", "master"), ("load", "slave")])
        summary = sim.summary()
        step = next(s for s in summary["steps"] if s["name"].startswith("3."))
        self.assertEqual(step["attempts"], 2)
        self.assertEqual(len(step["failed_attempts"]), 1)
        self.assertTrue(any("redone after" in flag for flag in summary["flags"]))
        text = (Path(sim.ui.result[2]) / "qc_summary.txt").read_text()
        self.assertIn("2 attempts", text)
        self.assertIn("failed attempt:", text)

    def test_stop_qc_in_the_pop_up_ends_the_run(self):
        sim = Sim(self)
        sim.hw.links = (0b01, 0b1)
        verdict, reason, _folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertEqual(len(sim.ui.redo_asked), 1)
        self.assertNotIn("idcode", sim.actions())

    def test_failing_again_asks_again(self):
        sim = Sim(self)
        sim.hw.links = (0b01, 0b1)
        sim.ui.redo_answers = [True, True]
        self.assertEqual(sim.drive()[0], "FAIL")
        self.assertEqual(len(sim.ui.redo_asked), 3)

    def test_capture_is_stopped_and_settings_restored_before_the_pop_up(self):
        sim = Sim(self)
        sim.capture.errors_at = 5.0
        seen = []
        original = sim.ui.ask_redo

        def check(step, reason):
            seen.append((sim.backend.running, sim.capture.folder, sim.capture._daq_preflight_callback))
            sim.capture.errors_at = None
            return original(step, reason)
        sim.ui.ask_redo = check
        sim.ui.redo_answers = [True]
        self.assertEqual(sim.drive()[0], "PASS")
        self.assertEqual(seen, [(False, "last-operator-folder", "preflight")])
        self.assertEqual(sim.actions().count("capture_start"), 2)
        self.assertEqual(sim.capture.folder, "last-operator-folder")

    def test_prbs_redo_starts_from_framed_links(self):
        sim = Sim(self)
        sim.hw.lock_after_resets = 10**6
        def allow_lock(run_sim):
            if sim.ui.redo_asked:
                sim.hw.lock_after_resets = 0
        sim.on_tick = allow_lock
        sim.ui.redo_answers = [True]
        self.assertEqual(sim.drive()[0], "PASS")
        calls = [e[2] for e in sim.log if e[0] == "prbs"]
        # Fail: none, PRBS-31, safe state none; redo: none, PRBS-31, none.
        self.assertEqual(calls, [0, 0, 4, 4, 0, 0, 0, 0, 4, 4, 0, 0])


class StopTests(unittest.TestCase):
    def test_stop_during_prbs_restores_framing_and_writes_a_report(self):
        sim = Sim(self)
        def stop(run_sim):
            if sim.clock.t > 100 and not run_sim.run.stop_requested:
                run_sim.run.request_stop()
        sim.on_tick = stop
        verdict, _reason, folder = sim.drive()
        self.assertEqual(verdict, "STOPPED")
        self.assertEqual(sim.hw.pattern, {0: 0, 1: 0})
        self.assertTrue((Path(folder) / "qc_summary.txt").is_file())
        self.assertIn("STOPPED", (Path(folder) / "qc_summary.txt").read_text())
        self.assertNotIn("mezz_scan", sim.actions())

    def test_stop_during_capture_stops_the_capture(self):
        sim = Sim(self)
        def stop(run_sim):
            if sim.backend.running:
                run_sim.run.request_stop()
        sim.on_tick = stop
        self.assertEqual(sim.drive()[0], "STOPPED")
        self.assertFalse(sim.backend.running)
        self.assertEqual(sim.capture.folder, "last-operator-folder")

    def test_log_captures_prints_and_stdout_is_returned(self):
        import sys
        sim = Sim(self)
        before = sys.stdout
        folder = sim.drive()[2]
        self.assertIs(sys.stdout, before)
        self.assertIn("[QC] Output folder", (Path(folder) / "qc_log.txt").read_text())

    def test_unexpected_exception_still_gives_a_safe_state_and_report(self):
        sim = Sim(self)
        sim.lpgbt.load_lpgbt = Mock(side_effect=RuntimeError("boom"))
        verdict, reason, folder = sim.drive()
        self.assertEqual(verdict, "FAIL")
        self.assertIn("boom", reason)
        self.assertTrue((Path(folder) / "qc_summary.json").is_file())


class HardwareTests(unittest.TestCase):
    """Register access, against a client that answers as the firmware does."""

    class Client:
        def __init__(self):
            self.writes = []

    def setUp(self):
        self.written = []
        self.hw = csm_qc.QcHardware(self.Client(), [0x00])

    def test_prbs_status_and_counts_for_two_uplinks(self):
        status = (0b11 << 32) | (0b00 << 40)
        low = (0x0002 << 16) | 0x0001
        high = (0x0000 << 16) | 0x0003
        pages = [format(page, "0160b") for page in (status, low, high)]
        with patch("csm_qc.fpga_readback", side_effect=pages), patch("csm_qc.fpga_config"):
            locked, counts = self.hw.read_prbs(2)
        self.assertEqual(locked, 0b11)
        self.assertEqual(counts, [0x00030001, 0x00000002])

    def test_prbs_status_for_four_uplinks(self):
        status = 0b0101 << 64
        pages = [format(page, "0160b") for page in (status, 0, 0)]
        with patch("csm_qc.fpga_readback", side_effect=pages), patch("csm_qc.fpga_config"):
            locked, counts = self.hw.read_prbs(4)
        self.assertEqual(locked, 0b0101)
        self.assertEqual(len(counts), 4)

    def test_drp_address_is_repeated_for_each_channel(self):
        page = "0" * 160
        with patch("csm_qc.fpga_readback", return_value=page), patch("csm_qc.fpga_config") as config:
            self.hw.read_prbs(2)
        addresses = [call.args[2] for call in config.call_args_list if call.args[1] == 33]
        expected = 0x15E | 0x15E << 9 | 0x15E << 18 | 0x15E << 27
        self.assertEqual(int.from_bytes(bytes(addresses[0]), "big"), expected)

    def test_links_read_from_page_3(self):
        bits = format((0b11 << 8) | 0b1, "0160b")
        with patch("csm_qc.fpga_readback", return_value=bits):
            self.assertEqual(self.hw.read_links(), (0b11, 0b1))

    def test_prbs_selection_keeps_other_links_and_shares_state(self):
        with patch("csm_qc.lpgbt_config_write"), patch("csm_qc.fpga_config") as config:
            self.hw.set_prbs(117, 0, csm_qc.PRBS_31)
            self.hw.set_prbs(115, 1, csm_qc.PRBS_31)
        self.assertEqual(self.hw.rxprbssel[0], 0x55)
        self.assertEqual(config.call_args_list[-1].args[1:], (36, [0x55]))

    def test_lost_reply_is_accepted_when_switching_either_way(self):
        lost = EthernetControlError("timeout", status=3, opcode=LPGBT_WRITE)
        with patch("csm_qc.lpgbt_config_write", side_effect=lost), patch("csm_qc.fpga_config") as config:
            self.hw.rxprbssel[0] = 0x55
            self.hw.set_prbs(117, 0, csm_qc.PRBS_NONE)
        self.assertEqual(self.hw.rxprbssel[0], 0x50)
        config.assert_called_once()

    def test_other_errors_still_raise(self):
        busy = EthernetControlError("busy", status=2, opcode=LPGBT_WRITE)
        with patch("csm_qc.lpgbt_config_write", side_effect=busy), patch("csm_qc.fpga_config") as config:
            with self.assertRaises(EthernetControlError):
                self.hw.set_prbs(117, 0, csm_qc.PRBS_31)
        config.assert_not_called()


class RealTabTests(unittest.TestCase):
    """The attributes the sequence relies on exist on the real tabs."""

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.host = QtWidgets.QWidget()
        self.addCleanup(self.host.close)

    def test_real_mezz_tab_selection_and_indicators(self):
        mezz = tab_mezz(self.host, object())
        run = csm_qc.CsmQcRun(SimpleNamespace(eth=None, lpgbt=SimpleNamespace(rxprbssel=[0]), mezz=mezz),
                              csm_qc.QcSettings("s", "o", "b", "d"), Ui())
        mezz.check_all_checkboxes(0, csm_qc.Qt.Checked)
        mezz.check_all_checkboxes(1, csm_qc.Qt.Unchecked)
        self.assertEqual(run._selected_mezz(), list(range(20)))
        self.assertEqual(mezz.selected_csm_indices(), [0])
        run._clear_indicators()
        self.assertEqual(len(run._indicator_errors()), 60)
        for indicators in mezz.csm_indicator_list[0]:
            for indicator in indicators:
                indicator.setStyleSheet("background-color: green; border: 1px solid black;")
        self.assertEqual(run._indicator_errors(), [])
        mezz.csm_indicator_list[0][7][2].setStyleSheet("background-color: red; border: 1px solid black;")
        self.assertEqual(run._indicator_errors(), ["Mezz7 D-line lock"])

    def test_real_mezz_threshold_control(self):
        mezz = tab_mezz(self.host, object())
        mezz.spinBox_ASD_main_thr.setValue(99)
        self.assertEqual(mezz.asd_main_thr_value(), 99)
        self.assertEqual(mezz.CSM_list[0].TDC_list[0].ASD_list[0].main_thr[0], format(99, "08b"))

    def test_real_lpgbt_callbacks_and_refusals(self):
        lpgbt = tab_lpgbt(self.host, object(), ethernet_device_callback=lambda: "")
        self.assertIsNotNone(lpgbt.uplink_status_component[1].blockSignals)
        self.assertFalse(lpgbt.read_fpga_id(0, on_result=print))
        self.assertFalse(lpgbt.load_fpga_bit_ethernet(0, on_programmed=print))
        self.assertIsNone(lpgbt.worker_read_CSM_idcode)
        self.assertIsNone(lpgbt.worker_load_CSM_bit)

    def test_real_monitor_controls(self):
        monitor = tab_monitor(self.host, object())
        self.assertEqual(monitor.scan_limit, 0)
        self.assertEqual(sorted(monitor.mezz.get_monitor_limits()), ["AVDD", "DVDD", "Temp"])
        metrics = monitor.csm._monitor_metrics()
        monitor.csm._prepare_monitor_limits()
        self.assertTrue(all(key in monitor.csm._monitor_limits for key, *_rest in metrics))


class RealCaptureTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_real_capture_controls_the_sequence_changes_and_restores(self):
        from tab_capture import tab_capture
        with tempfile.TemporaryDirectory() as directory, patch(
            "tab_capture.SETTINGS_FILE", str(Path(directory) / "settings.ini")
        ), patch("tab_capture.pcapy.findalldevs", return_value=[]):
            host = QtWidgets.QWidget()
            self.addCleanup(host.close)
            capture = tab_capture(host)
            adc = SimpleNamespace(chk_fit_only=QtWidgets.QCheckBox())
            adc.chk_fit_only.setChecked(True)
            backend = Backend()
            selection = Mock()
            capture.set_run_plot_saving_control(selection_callback=selection, plot_labels_callback=lambda: ["ADC overall"])
            preflight = capture._daq_preflight_callback = Mock()
            folder = capture.edit_outdir.text()
            run = csm_qc.CsmQcRun(
                SimpleNamespace(eth=None, lpgbt=SimpleNamespace(rxprbssel=[0]), capture=capture, adc=adc, backend=backend),
                csm_qc.QcSettings("s", "o", "b", directory), Ui())
            run.folder = directory

            run._prepare_capture()
            self.assertEqual(capture.edit_outdir.text(), directory)
            self.assertIsNone(capture._daq_preflight_callback)
            self.assertFalse(adc.chk_fit_only.isChecked())
            self.assertIn("ADC overall", selection.call_args.args[0])

            run._run_restores()
            self.assertEqual(capture.edit_outdir.text(), folder)
            self.assertIs(capture._daq_preflight_callback, preflight)
            self.assertTrue(adc.chk_fit_only.isChecked())
            self.assertEqual(run.flags, [])


class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def page(self, device="eth0"):
        self.host = QtWidgets.QWidget()
        self.addCleanup(self.host.close)
        tabs = SimpleNamespace(
            lpgbt=SimpleNamespace(file_path_box=SimpleNamespace(text=lambda: "default.bit"),
                                  current_ethernet_device=lambda: device),
            backend=SimpleNamespace(is_running=lambda: False),
            monitor=SimpleNamespace(worker=None))
        page = tab_qc(self.host, tabs)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.bit = Path(self.directory.name) / "fw.bit"
        self.bit.write_bytes(b"x")
        page.edit_serial.setText("S1")
        page.edit_operator.setText("Ana")
        page.edit_bitstream.setText(str(self.bit))
        page.edit_output.setText(self.directory.name)
        return page

    def test_defaults_match_the_procedure(self):
        page = self.page()
        settings, problem = page.read_inputs()
        self.assertIsNone(problem)
        self.assertEqual((settings.prbs_target, settings.dline_target, settings.asd_threshold), (1e-13, 1e-11, 114))

    def test_bad_inputs_are_refused(self):
        for widget, value, expect in (("edit_serial", "", "serial"), ("edit_serial", "a/b", "serial"),
                                      ("edit_operator", "", "operator"),
                                      ("edit_bitstream", "missing.bit", "not found"),
                                      ("edit_output", "", "output"),
                                      ("edit_prbs_target", "abc", "PRBS"),
                                      ("edit_prbs_target", "-1", "PRBS"),
                                      ("edit_dline_target", "1.5", "BER monitor")):
            page = self.page()
            getattr(page, widget).setText(value)
            settings, problem = page.read_inputs()
            self.assertIsNone(settings)
            self.assertIn(expect, problem)

    def test_zero_targets_are_accepted_as_skip(self):
        page = self.page()
        page.edit_prbs_target.setText("0")
        page.edit_dline_target.setText("0")
        settings, problem = page.read_inputs()
        self.assertIsNone(problem)
        self.assertEqual((settings.prbs_target, settings.dline_target), (0.0, 0.0))

    def test_redo_pop_up_buttons(self):
        page = self.page()
        for button, expected in (("Redo this step", True), ("Stop QC", False)):
            shown = []

            def press(box, text=button):
                shown.append(box.text())
                next(b for b in box.buttons() if b.text() == text).click()
                return 0
            with patch.object(QtWidgets.QMessageBox, "exec_", press):
                self.assertIs(page.ask_redo("3. Check link status", "links are not ready"), expected)
            self.assertIn("links are not ready", shown[0])

    def test_needs_an_ethernet_interface(self):
        settings, problem = self.page(device="").read_inputs()
        self.assertIsNone(settings)
        self.assertIn("Ethernet", problem)

    def test_folder_hint_follows_the_inputs(self):
        page = self.page()
        self.assertIn(os.path.join("S1", "Ana", "YYYYMMDDHHMM"), page.label_folder.text())


if __name__ == "__main__":
    unittest.main()
