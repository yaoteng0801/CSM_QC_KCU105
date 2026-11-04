"""Automated CSM QC sequence for CSM0.

The sequence drives the existing tabs, whose functions touch widgets and so must
run on the GUI thread.  ``CsmQcRun.run`` is a generator that yields the seconds
to wait before it is resumed: the GUI stays live during the long BER waits, and
Stop takes effect at the next wait.  Programming a mezzanine still blocks the GUI
for as long as the matching button does.
"""

import csv
import datetime as dt
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass

from PyQt5.QtCore import Qt

from TDC_config_low_level_function import (
    ethernet_exclusive_session,
    fpga_config,
    fpga_readback,
    fpga_readback_BER,
    lpgbt_config_write,
    value_to_list,
)
from ethernet_control_protocol import EthernetControlError, LPGBT_WRITE
from firmware_links import detect_uplink_count
from lpgbt_register_map_v1 import LpgbtRegisterMapV1
from Worker_read_CSM_idcode_ethernet import EXPECTED_CSM_FPGA_IDCODE


WHICH_CSM = 0
MEZZ_PER_CSM = 20
MASTER_ADDR, SLAVE_ADDR = 117, 115
MASTER_LINK, SLAVE_LINK = 0, 1
# CSM0 only, so the check also holds on firmware with more links.
UPLINK_MASK, DOWNLINK_MASK = 0b11, 0b1

# Set by the QC procedure.  The firmware's transceivers run at 10.24 Gb/s
# (ip/xlx_ku_mgt_ip_10g24_1); the report states the rate that was used.
PRBS_LINE_RATE_BPS = 12.8e9
DLINE_BITS_PER_FRAME = 40

PRBS_NONE, PRBS_31 = 0, 4  # lpGBT ULDATASOURCE0 values
_PRBS_CHECKER = {PRBS_NONE: 0, PRBS_31: 5}  # GTH rxprbssel values
_REG_DRPEN, _REG_DRPADDR, _REG_PRBS_RESET, _REG_PRBS_SEL = 31, 33, 35, 36
_DRP_ERR_LOW, _DRP_ERR_HIGH = 0x15E, 0x15F
_STATUS_TIMEOUT = 3

LINK_TIMEOUT_S = 5.0
IDCODE_TIMEOUT_S = 60.0
PROGRAM_TIMEOUT_S = 30.0
PRBS_LOCK_TIMEOUT_S = 10.0
BER_POLL_S = 2.0
DLINE_STALL_S = 30.0
MEZZ_RETRIES = 10
MONITOR_INTERVAL_S = 5.0
MONITOR_SCANS = 20
MONITOR_TIMEOUT_S = 1800.0
CAPTURE_MIN_S, CAPTURE_MAX_S = 30.0, 60.0
CAPTURE_MIN_TRIGGERS = 20

_INDICATOR_NAMES = ("TDC config", "ASD config", "D-line lock")
_INDICATOR_UNCHECKED = "background-color: lightgray; border: 1px solid black;"

STEPS = (
    ("master", "1. Load master lpGBT"),
    ("slave", "2. Toggle slave link, load slave lpGBT"),
    ("links", "3. Check link status"),
    ("fpga", "3b. Read IDCODE, program FPGA"),
    ("prbs", "4. PRBS test"),
    ("mezz", "5. Scan and configure mezzanines"),
    ("ber", "6. D-line BER monitor"),
    ("enable", "7. Enable TDC inputs and ASD channels"),
    ("monitor", "8. Monitoring"),
    ("capture", "9. Capture and ADC plots"),
)


class QcFailure(Exception):
    """The board failed a check; the run stops and raises the alarm."""


class QcStopped(Exception):
    """The operator pressed Stop QC."""


@dataclass
class QcSettings:
    serial: str
    operator: str
    bitstream: str
    output_dir: str
    prbs_target: float = 1e-13
    dline_target: float = 1e-11
    asd_threshold: int = 114


def prbs_ber_limit(seconds, line_rate=PRBS_LINE_RATE_BPS):
    return 1.0 / (line_rate * seconds) if seconds > 0 else float("inf")


def dline_ber_limit(frames):
    return 1.0 / (frames * DLINE_BITS_PER_FRAME) if frames > 0 else float("inf")


def decode_ber_info(bits):
    """Return (rec_dline1, rec_dline0, err_dline1, err_dline0) from a BER page."""
    if not isinstance(bits, str) or len(bits) != 160:
        raise ValueError("incomplete BER readback")
    return int(bits[:44], 2), int(bits[44:88], 2), int(bits[88:124], 2), int(bits[124:], 2)


def valid_path_component(text):
    """True when text can be one folder name on Windows and Linux."""
    return bool(re.fullmatch(r"[\w-](?:[\w .-]*[\w-])?", text or ""))


def create_run_folder(settings, now):
    base = os.path.join(settings.output_dir, settings.serial, settings.operator,
                        now.strftime("%Y%m%d%H%M"))
    folder, suffix = base, 1
    while True:
        try:
            os.makedirs(folder)
            return folder
        except FileExistsError:
            suffix += 1
            folder = f"{base}_{suffix}"


def monitor_flags(csv_path, mezz_limits, csm_metrics, csm_limits):
    """List out-of-range and unreadable monitor values; they do not fail the QC."""
    limits = {column: csm_limits.get(key) for key, _name, _unit, column in csm_metrics}
    with open(csv_path, newline="") as stream:
        rows = list(csv.DictReader(stream))
    flags = []
    for column in (rows[0] if rows else ()):
        if "_display_" not in column:
            continue
        bounds = limits.get(column)
        match = re.search(r"_Mezz\d+_(\w+?)_display_", column)
        if match:
            bounds = mezz_limits.get(match.group(1))
        out_of_range = unreadable = 0
        worst = []
        for row in rows:
            try:
                value = float(row[column])
            except (TypeError, ValueError):
                unreadable += 1
                continue
            if bounds is not None and not bounds[0] <= value <= bounds[1]:
                out_of_range += 1
                worst.append(value)
        name = column.replace("_display_", " ")
        if out_of_range:
            flags.append(f"{name}: {out_of_range}/{len(rows)} scans outside "
                         f"{bounds[0]:g} to {bounds[1]:g} "
                         f"(seen {min(worst):g} to {max(worst):g})")
        if unreadable:
            flags.append(f"{name}: {unreadable}/{len(rows)} scans had no valid reading")
    return flags


class QcHardware:
    """Direct register access the QC needs but the tabs only offer through dialogs."""

    def __init__(self, eth, rxprbssel):
        self.eth = eth
        self.rxprbssel = rxprbssel  # Shared with the PRBS dialog.

    def read_links(self):
        bits = fpga_readback(self.eth, 3)
        if not isinstance(bits, str) or len(bits) < 24:
            raise RuntimeError("Incomplete FPGA link-status readback")
        return int(bits[-16:-8], 2), int(bits[-8:], 2)

    def uplink_count(self):
        return detect_uplink_count(self.eth)

    def set_prbs(self, lpgbt_addr, link, selection):
        """Select the lpGBT pattern and matching FPGA checker for one uplink.

        The pattern switch takes the framed uplink away or brings it back, so the
        IC reply can be lost in either direction.  Other errors still raise, and
        the caller verifies the outcome through lock or link-ready status.
        """
        with ethernet_exclusive_session(self.eth):
            try:
                lpgbt_config_write(
                    self.eth, reg_addr=LpgbtRegisterMapV1.ULDATASOURCE0.address,
                    value_list=[selection], which_csm=link // 2, lpgbt_addr=lpgbt_addr)
            except EthernetControlError as error:
                if error.status != _STATUS_TIMEOUT or error.opcode != LPGBT_WRITE:
                    raise
            value = self.rxprbssel[0] & ~(0xF << (link * 4))
            value |= _PRBS_CHECKER[selection] << (link * 4)
            fpga_config(self.eth, _REG_PRBS_SEL, value_to_list(value))
            self.rxprbssel[0] = value

    def reset_prbs_counters(self, link_mask):
        with ethernet_exclusive_session(self.eth):
            fpga_config(self.eth, _REG_PRBS_RESET, value_to_list(link_mask))
            fpga_config(self.eth, _REG_PRBS_RESET, value_to_list(0))

    def _prbs_page(self):
        bits = fpga_readback(self.eth, 6)
        if not isinstance(bits, str) or len(bits) != 160:
            raise RuntimeError("Incomplete FPGA PRBS readback")
        return int(bits, 2)

    def _prbs_drp_word(self, address):
        for _channel in range(3):
            address |= address << 9
        fpga_config(self.eth, _REG_DRPADDR, value_to_list(address))
        fpga_config(self.eth, _REG_DRPEN, value_to_list(0b1111))
        fpga_config(self.eth, _REG_DRPEN, value_to_list(0))
        return self._prbs_page()

    def read_prbs(self, uplinks):
        """Return (locked mask, error count per uplink), laid out as MiniDAQ_reg.sv packs them."""
        with ethernet_exclusive_session(self.eth):
            status = self._prbs_page()
            low = self._prbs_drp_word(_DRP_ERR_LOW)
            high = self._prbs_drp_word(_DRP_ERR_HIGH)
        locked = (status >> (uplinks * 16)) & ((1 << uplinks) - 1)
        counts = [((high >> (link * 16)) & 0xFFFF) << 16 | ((low >> (link * 16)) & 0xFFFF)
                  for link in range(uplinks)]
        return locked, counts

    def read_ber(self, tdc):
        return decode_ber_info(fpga_readback_BER(self.eth, tdc))


class _LogTee:
    """Copy everything the GUI prints during a run into the run's log file."""

    def __init__(self, real, path):
        self._real = real
        self._file = open(path, "w", encoding="utf-8")
        self._lock = threading.Lock()

    def write(self, text):
        self._real.write(text)
        with self._lock:
            if not self._file.closed:
                self._file.write(text)
                self._file.flush()

    def flush(self):
        self._real.flush()

    def close(self):
        with self._lock:
            self._file.close()


class CsmQcRun:
    """One QC run.  ``tabs`` holds the existing tabs; ``ui`` shows progress and pop-ups."""

    def __init__(self, tabs, settings, ui, hardware=None,
                 clock=time.monotonic, now=dt.datetime.now):
        self.tabs = tabs
        self.settings = settings
        self.ui = ui
        self.hw = hardware or QcHardware(tabs.eth, tabs.lpgbt.rxprbssel)
        self.clock = clock
        self.now = now
        self.folder = ""
        self.verdict = "NOT RUN"
        self.failure = ""
        self.flags = []
        self.results = {}
        self.step_log = []
        self.stop_requested = False
        self._accepted_missing = None
        self._prbs_active = False
        self._programmed = False
        self._idcode = None
        self._snapshot = None
        self._restores = []
        self._tee = None

    # ------------------------------------------------------------- run control
    def request_stop(self):
        self.stop_requested = True

    def _say(self, text):
        print(f"[QC] {text}")
        self.ui.status(text)

    def _sleep(self, seconds):
        end = self.clock() + seconds
        while True:
            yield max(0.0, min(end - self.clock(), 0.25))
            if self.stop_requested:
                raise QcStopped()
            if self.clock() >= end:
                return

    def run(self):
        """The whole QC.  Every outcome ends in a safe state, a report and a pop-up."""
        started = self.now()
        self.folder = create_run_folder(self.settings, started)
        self._tee = _LogTee(sys.stdout, os.path.join(self.folder, "qc_log.txt"))
        real_stdout, sys.stdout = sys.stdout, self._tee
        current = None
        try:
            self._say(f"Output folder: {self.folder}")
            try:
                for key, name in STEPS:
                    current = {"name": name, "result": "RUNNING", "detail": ""}
                    self.step_log.append(current)
                    self.ui.step(key, "running")
                    begun = self.clock()
                    yield from getattr(self, f"_step_{key}")()
                    current.update(result="PASS", seconds=round(self.clock() - begun, 1))
                    self.ui.step(key, "pass")
                self.verdict = "PASS"
            except QcStopped:
                self.verdict = "STOPPED"
                self.failure = "Stopped by the operator."
            except QcFailure as error:
                self.verdict, self.failure = "FAIL", str(error)
            except Exception as error:
                self.verdict, self.failure = "FAIL", f"{type(error).__name__}: {error}"
            if self.verdict != "PASS":
                current.update(result=self.verdict, detail=self.failure)
                self.ui.step(key, "fail")
                self._say(f"{self.verdict} at {current['name']}: {self.failure}")
            self.stop_requested = False
            yield from self._safe_state()
            self._write_report(started)
            self._say(f"QC {self.verdict}. Results in {self.folder}")
        finally:
            sys.stdout = real_stdout
            self._tee.close()
        self.ui.finished(self.verdict, self.failure, self.folder)

    def _safe_state(self):
        attempts = (self._stop_programming, self._stop_capture, self._stop_monitor,
                    self._stop_prbs)
        for attempt in attempts:
            try:
                yield from attempt()
            except Exception as error:
                self.flags.append(f"Cleanup problem ({attempt.__name__}): {error}")
                self._say(self.flags[-1])
        self._run_restores()

    def _run_restores(self):
        while self._restores:
            restore = self._restores.pop()
            try:
                restore()
            except Exception as error:
                self.flags.append(f"Could not restore a setting: {error}")

    def _stop_programming(self):
        lpgbt = self.tabs.lpgbt
        if lpgbt.worker_load_CSM_bit is not None:
            lpgbt.cancel_load_CSM_bit()
        deadline = self.clock() + 5.0
        while (lpgbt.worker_load_CSM_bit is not None or lpgbt.worker_read_CSM_idcode is not None) \
                and self.clock() < deadline:
            yield from self._sleep(0.1)

    def _stop_capture(self):
        if self.tabs.backend.is_running():
            self.tabs.capture.stop()
        return
        yield

    def _stop_monitor(self):
        monitor = self.tabs.monitor
        if monitor.worker is not None:
            monitor.stop()
        deadline = self.clock() + 60.0
        while monitor.worker is not None and self.clock() < deadline:
            yield from self._sleep(0.1)

    def _stop_prbs(self):
        if not self._prbs_active:
            return
        self.hw.set_prbs(MASTER_ADDR, MASTER_LINK, PRBS_NONE)
        self.hw.set_prbs(SLAVE_ADDR, SLAVE_LINK, PRBS_NONE)
        self._prbs_active = False
        yield from self._sleep(0.1)

    # ------------------------------------------------------------ steps 1 to 3
    def _wait_for_link_poll(self):
        deadline = self.clock() + LINK_TIMEOUT_S
        while self.tabs.lpgbt._link_ready_poll is not None and self.clock() < deadline:
            yield from self._sleep(0.1)

    def _step_master(self):
        self.tabs.lpgbt.load_lpgbt(WHICH_CSM, 1)
        yield from self._wait_for_link_poll()

    def _step_slave(self):
        lpgbt = self.tabs.lpgbt
        checkbox = lpgbt.uplink_status_component[WHICH_CSM * 2 + 1]
        # Send the disable even when the box already looks unchecked.
        blocked = checkbox.blockSignals(True)
        checkbox.setChecked(False)
        checkbox.blockSignals(blocked)
        lpgbt.slave_control(WHICH_CSM, Qt.Unchecked)
        yield from self._sleep(0.5)
        checkbox.setChecked(True)  # The checkbox's own handler sends the enable.
        yield from self._sleep(0.5)
        lpgbt.load_lpgbt(WHICH_CSM, 0)
        yield from self._wait_for_link_poll()

    def _links_ready(self):
        uplink, downlink = self.hw.read_links()
        ready = (uplink & UPLINK_MASK) == UPLINK_MASK and (downlink & DOWNLINK_MASK) == DOWNLINK_MASK
        return ready, uplink, downlink

    def _require_links(self):
        """Pass after three good reads in a row, as the LpGBT Config page confirms a link."""
        deadline = self.clock() + LINK_TIMEOUT_S
        good = 0
        while True:
            ready, uplink, downlink = self._links_ready()
            good = good + 1 if ready else 0
            if good >= 3:
                self.tabs.lpgbt.update_status()
                return
            if self.clock() >= deadline:
                self.tabs.lpgbt.update_status()
                raise QcFailure(
                    f"CSM{WHICH_CSM} links are not ready: uplink ready = {uplink:08b}, "
                    f"downlink ready = {downlink:08b}.")
            yield from self._sleep(0.1)

    def _step_links(self):
        yield from self._require_links()

    # ---------------------------------------------------------------- step 3b
    def _on_idcode(self, _csm, idcode, _configured):
        self._idcode = idcode

    def _on_programmed(self, _csm):
        self._programmed = True

    def _read_idcode(self):
        """Return True for the expected IDCODE.

        DONE and INIT are deliberately not checked: the log shows them, and a CSM
        may arrive unconfigured.  The firmware itself rejects a programming run
        that ends without them.
        """
        lpgbt = self.tabs.lpgbt
        self._idcode = None
        if not lpgbt.read_fpga_id(WHICH_CSM, on_result=self._on_idcode):
            raise QcFailure("Could not start the IDCODE read; check the Ethernet interface.")
        deadline = self.clock() + IDCODE_TIMEOUT_S
        while lpgbt.worker_read_CSM_idcode is not None:
            if self.clock() >= deadline:
                raise QcFailure("The IDCODE read did not finish.")
            yield from self._sleep(0.1)
        return self._idcode == EXPECTED_CSM_FPGA_IDCODE

    def _step_fpga(self):
        lpgbt = self.tabs.lpgbt
        present = yield from self._read_idcode()
        if not present:
            self._say("IDCODE check failed; rechecking the links.")
            yield from self._require_links()
            present = yield from self._read_idcode()
        if not present:
            raise QcFailure(
                f"CSM0 JTAG ID check failed: expected IDCODE=0x{EXPECTED_CSM_FPGA_IDCODE:08X}. "
                "The links are ready; see the log for what was read.")

        self._say("Programming the CSM0 FPGA over Ethernet.")
        lpgbt.file_path_box.setText(self.settings.bitstream)
        self._programmed = False
        if not lpgbt.load_fpga_bit_ethernet(WHICH_CSM, on_programmed=self._on_programmed):
            raise QcFailure("Could not start FPGA programming; check the Ethernet interface.")
        begun = self.clock()
        while lpgbt.worker_load_CSM_bit is not None:
            if self.clock() - begun >= PROGRAM_TIMEOUT_S:
                lpgbt.cancel_load_CSM_bit()
                raise QcFailure(f"FPGA programming did not finish within {PROGRAM_TIMEOUT_S:.0f} s.")
            yield from self._sleep(0.2)
        if not self._programmed:
            raise QcFailure("FPGA programming over Ethernet failed; see the log for the reason.")
        self.results["fpga_program_s"] = round(self.clock() - begun, 1)

        # JTAG must still answer after the new design has loaded.
        yield from self._sleep(1.0)
        present = yield from self._read_idcode()
        if not present:
            raise QcFailure("The JTAG ID could not be read correctly after programming.")

    # ----------------------------------------------------------------- step 4
    def _step_prbs(self):
        target = self.settings.prbs_target
        uplinks = self.hw.uplink_count()
        for selection in (PRBS_NONE, PRBS_31):
            self._prbs_active = True
            self.hw.set_prbs(MASTER_ADDR, MASTER_LINK, selection)
            self.hw.set_prbs(SLAVE_ADDR, SLAVE_LINK, selection)
            yield from self._sleep(1.0)

        # The checker only locks after a counter reset once the pattern is running.
        link_mask = (1 << MASTER_LINK) | (1 << SLAVE_LINK)
        deadline = self.clock() + PRBS_LOCK_TIMEOUT_S
        while True:
            self.hw.reset_prbs_counters(link_mask)
            yield from self._sleep(1.0)
            locked, _counts = self.hw.read_prbs(uplinks)
            if locked & link_mask == link_mask:
                break
            if self.clock() >= deadline:
                raise QcFailure(f"PRBS-31 did not lock: locked = {locked:0{uplinks}b}.")

        # A counter with no lock also reads zero, so lock must hold for the whole test.
        self.hw.reset_prbs_counters(link_mask)
        begun = self.clock()
        limit = float("inf")
        while limit > target:
            yield from self._sleep(BER_POLL_S)
            locked, counts = self.hw.read_prbs(uplinks)
            elapsed = self.clock() - begun
            if locked & link_mask != link_mask:
                raise QcFailure(f"PRBS-31 lost lock after {elapsed:.0f} s: locked = {locked:0{uplinks}b}.")
            errors = counts[MASTER_LINK] + counts[SLAVE_LINK]
            if errors:
                raise QcFailure(
                    f"PRBS-31 errors after {elapsed:.0f} s: master {counts[MASTER_LINK]}, "
                    f"slave {counts[SLAVE_LINK]}.")
            limit = prbs_ber_limit(elapsed)
            self.ui.status(f"PRBS: {elapsed:.0f} s, no errors, BER = {limit:.2e}, target {target:.2e}")
        self.results["prbs"] = {"seconds": round(elapsed, 1), "ber_limit": limit,
                                "target": target, "line_rate_bps": PRBS_LINE_RATE_BPS}

        # IC and SCA need framed data again before anything else can run.
        yield from self._stop_prbs()
        yield from self._sleep(1.0)
        ready, _uplink, _downlink = self._links_ready()
        if not ready:
            self._say("Links not ready after PRBS; sending the physical uplink reset.")
            self.tabs.lpgbt.fpga_physical_rx_reset()
            yield from self._sleep(1.0)
        yield from self._require_links()

    # ------------------------------------------------------------- steps 5 to 7
    def _selected_mezz(self):
        return sorted(mezz for csm, mezz in self.tabs.mezz.selected_mezz_indices()
                      if csm == WHICH_CSM)

    def _clear_indicators(self):
        for indicators in self.tabs.mezz.csm_indicator_list[WHICH_CSM]:
            for indicator in indicators:
                indicator.setStyleSheet(_INDICATOR_UNCHECKED)

    def _indicator_errors(self, which=(0, 1, 2)):
        """Selected mezzanines whose indicator is not green.  Gray counts: it was never checked."""
        indicators = self.tabs.mezz.csm_indicator_list[WHICH_CSM]
        return [f"Mezz{mezz} {_INDICATOR_NAMES[index]}"
                for mezz in self._selected_mezz() for index in which
                if "green" not in indicators[mezz][index].styleSheet()]

    def _scan_and_program(self):
        """Steps 5(a) and 5(b) once.  Return the problems found, empty when all is good."""
        mezz = self.tabs.mezz
        self._clear_indicators()
        mezz.check_all_checkboxes(WHICH_CSM, Qt.Checked)
        mezz.check_all_checkboxes(1 - WHICH_CSM, Qt.Unchecked)
        yield from self._sleep(0)
        mezz.mezz_scan()
        selected = self._selected_mezz()
        if not selected:
            return ["no mezzanine detected"]
        missing = [index for index in range(MEZZ_PER_CSM) if index not in selected]
        if self._accepted_missing is None:
            if missing and not self.ui.confirm(
                    "Mezzanines not detected",
                    f"Mezz scan did not detect: {', '.join(map(str, missing))}.\n\n"
                    "Continue the QC without them?"):
                raise QcFailure(f"Operator ended the run: mezzanines not detected: {missing}.")
            self._accepted_missing = set(missing)
            if missing:
                self.flags.append(f"Run without mezzanines not detected: {missing}")
        unexpected = sorted(set(missing) - self._accepted_missing)
        if unexpected:
            return [f"Mezz{index} no longer detected" for index in unexpected]
        yield from self._sleep(0)

        mezz.spinBox_ASD_main_thr.setValue(self.settings.asd_threshold)
        mezz._set_all_asd_main_thr(self.settings.asd_threshold)
        # Check each result now: TDC_input_config rewrites the TDC indicator from one
        # register alone, which could turn a failed full configuration green.
        mezz.write_TDC_all()
        problems = self._indicator_errors((0,))
        if problems:
            return problems
        yield from self._sleep(0)
        mezz.write_ASD_all()
        problems = self._indicator_errors((1,))
        if problems:
            return problems
        yield from self._sleep(0)
        mezz.TDC_input_config(False)
        yield from self._sleep(0)
        mezz.fpga_global_reset()
        yield from self._sleep(1.0)
        mezz.get_dline_status()
        return self._indicator_errors()

    def _attempt_scan_and_program(self):
        try:
            return (yield from self._scan_and_program())
        except (QcFailure, QcStopped):
            raise
        except Exception as error:
            return [f"{type(error).__name__}: {error}"]

    def _step_mezz(self):
        for attempt in range(1 + MEZZ_RETRIES):
            problems = yield from self._attempt_scan_and_program()
            if not problems:
                self.results["mezz_attempts"] = attempt + 1
                self.results["mezz_selected"] = self._selected_mezz()
                return
            self._say(f"Mezzanine configuration attempt {attempt + 1} failed: {', '.join(problems)}")
        raise QcFailure(f"Mezzanine configuration failed after {MEZZ_RETRIES} retries: "
                        f"{', '.join(problems)}.")

    def _step_ber(self):
        target = self.settings.dline_target
        tdcs = [WHICH_CSM * MEZZ_PER_CSM + mezz for mezz in self._selected_mezz()]
        # Counted from here, whatever the counters held before this step.
        start = {tdc: self.hw.read_ber(tdc) for tdc in tdcs}
        progress = {(tdc, line): (0, self.clock()) for tdc in tdcs for line in (1, 0)}
        limit = float("inf")
        while limit > target:
            yield from self._sleep(BER_POLL_S)
            fewest = None
            for tdc in tdcs:
                rec1, rec0, err1, err0 = self.hw.read_ber(tdc)
                base = start[tdc]
                if err1 - base[2] or err0 - base[3]:
                    raise QcFailure(f"D-line errors on TDC {tdc}: dline1 {err1 - base[2]}, "
                                    f"dline0 {err0 - base[3]}.")
                for line, frames in ((1, rec1 - base[0]), (0, rec0 - base[1])):
                    seen, moved_at = progress[tdc, line]
                    if frames > seen:
                        progress[tdc, line] = (frames, self.clock())
                    elif self.clock() - moved_at >= DLINE_STALL_S:
                        raise QcFailure(f"TDC {tdc} dline{line} stopped receiving data.")
                    fewest = frames if fewest is None else min(fewest, frames)
            limit = dline_ber_limit(fewest)
            self.ui.status(f"D-line BER: {fewest:.3e} frames, no errors, BER = {limit:.2e}, target {target:.2e}")
        self.results["dline_ber"] = {"frames": fewest, "ber_limit": limit, "target": target}

    def _step_enable(self):
        mezz = self.tabs.mezz
        for attempt in range(1 + MEZZ_RETRIES):
            try:
                self._clear_indicators()
                mezz.TDC_input_config(True)
                yield from self._sleep(0)
                mezz.ASD_channel_mode_config(True)
                yield from self._sleep(1.0)
                mezz.get_dline_status()
                problems = self._indicator_errors()
            except Exception as error:
                problems = [f"{type(error).__name__}: {error}"]
            if not problems:
                self.results["enable_attempts"] = attempt + 1
                return
            self._say(f"Enable attempt {attempt + 1} failed: {', '.join(problems)}")
            if attempt < MEZZ_RETRIES:
                yield from self._attempt_scan_and_program()
        raise QcFailure(f"Enabling inputs failed after {MEZZ_RETRIES} retries: {', '.join(problems)}.")

    # ----------------------------------------------------------------- step 8
    def _step_monitor(self):
        monitor = self.tabs.monitor
        saved_interval = monitor.interval.value()
        saved_folder = monitor.lineEdit_csv_directory.text()
        saved_mezz = monitor.checkBox_monitor_mezz.isChecked()
        saved_csm = monitor.checkBox_monitor_csm.isChecked()

        def restore():
            monitor.scan_limit = 0
            monitor.interval.setValue(saved_interval)
            monitor.lineEdit_csv_directory.setText(saved_folder)
            monitor.checkBox_monitor_mezz.setChecked(saved_mezz)
            monitor.checkBox_monitor_csm.setChecked(saved_csm)
        self._restores.append(restore)

        monitor.interval.setValue(MONITOR_INTERVAL_S)
        monitor.lineEdit_csv_directory.setText(self.folder)
        monitor.checkBox_monitor_mezz.setChecked(True)
        monitor.checkBox_monitor_csm.setChecked(True)
        monitor.csm.checkbox_list[WHICH_CSM].setChecked(True)
        monitor.csm.checkbox_list[1 - WHICH_CSM].setChecked(False)
        monitor.mezz.select_scanned_mezz(self.tabs.mezz.selected_mezz_indices())
        monitor.scan_limit = MONITOR_SCANS
        monitor.start()
        if monitor.worker is None:
            raise QcFailure("Monitoring did not start; see the log.")

        deadline = self.clock() + MONITOR_TIMEOUT_S
        while monitor.worker is not None:
            if self.clock() >= deadline:
                raise QcFailure(f"Monitoring did not finish {MONITOR_SCANS} scans.")
            self.ui.status(f"Monitoring: {monitor.status.text()}")
            yield from self._sleep(0.5)

        csv_path = str(monitor.csv_path)
        with open(csv_path, newline="") as stream:
            scans = sum(1 for _row in csv.DictReader(stream))
        if scans < MONITOR_SCANS:
            raise QcFailure(f"Monitoring finished only {scans}/{MONITOR_SCANS} scans.")
        monitor.plot_csv()
        png_path = os.path.splitext(csv_path)[0] + ".png"
        if not os.path.isfile(png_path):
            self.flags.append("The monitoring plot was not saved.")
        self.results["monitor_csv"] = os.path.basename(csv_path)
        self.flags.extend(monitor_flags(
            csv_path, monitor.mezz.get_monitor_limits(),
            monitor.csm._monitor_metrics(), monitor.csm._monitor_limits))
        self._run_restores()

    # ----------------------------------------------------------------- step 9
    def _on_snapshot(self, snapshot):
        self._snapshot = snapshot

    def _tdc_errors(self, snapshot, tdcs):
        counts = getattr(snapshot, "decode_err_cnt", None)
        if counts is None:
            return {}
        return {tdc: int(counts[tdc]) for tdc in tdcs if int(counts[tdc])}

    def _prepare_capture(self):
        capture, backend, adc = self.tabs.capture, self.tabs.backend, self.tabs.adc
        saved_folder = capture.edit_outdir.text()
        saved_preflight = capture._daq_preflight_callback
        saved_fit_only = adc.chk_fit_only.isChecked()
        backend.decode_status.connect(self._on_snapshot)

        def restore():
            backend.decode_status.disconnect(self._on_snapshot)
            capture.edit_outdir.setText(saved_folder)
            capture._save_settings()
            capture._daq_preflight_callback = saved_preflight
            capture._apply_plot_selection()
            adc.chk_fit_only.setChecked(saved_fit_only)
        self._restores.append(restore)

        capture.edit_outdir.setText(self.folder)
        # An unattended run cannot answer this pop-up; the report records the mismatch.
        capture._daq_preflight_callback = None
        # "Fit data only" would show empty plots in a triggered run.
        adc.chk_fit_only.setChecked(False)
        # The ADC arrays only reach the plots while "ADC overall" is selected.
        if capture._plot_selection_callback is not None:
            capture._plot_selection_callback(
                capture.run_plot_live_labels() | {"ADC overall"},
                capture.run_plot_save_labels())

    def _flag_geometry_mismatch(self):
        unassigned, disabled = self.tabs.tdc_mismatch()[:2]
        if unassigned:
            self.flags.append(f"Enabled TDCs with no Geometry assignment: {unassigned}")
        if disabled:
            self.flags.append(f"TDCs in Geometry but not enabled: {disabled}")

    def _step_capture(self):
        capture, backend, adc = self.tabs.capture, self.tabs.backend, self.tabs.adc
        tdcs = [WHICH_CSM * MEZZ_PER_CSM + mezz for mezz in self._selected_mezz()]
        self._flag_geometry_mismatch()
        self._prepare_capture()
        self._snapshot = None
        # The operator sees the plots fill, and an exported plot needs its page laid out.
        self.tabs.show_adc_plots()
        capture.start()
        if not backend.is_running():
            raise QcFailure("Capture did not start; see the log.")

        begun = self.clock()
        while True:
            yield from self._sleep(0.5)
            elapsed = self.clock() - begun
            if not backend.is_running():
                raise QcFailure(f"Capture stopped by itself after {elapsed:.0f} s; see the log.")
            snapshot = self._snapshot
            triggers = int(getattr(snapshot, "triggers", 0))
            self.ui.status(f"Capture: {elapsed:.0f} s, {triggers} triggers")
            if self._tdc_errors(snapshot, tdcs):
                break
            if elapsed >= CAPTURE_MAX_S or (elapsed >= CAPTURE_MIN_S and triggers >= CAPTURE_MIN_TRIGGERS):
                break

        capture.stop()  # Publishes the final counts and the final histograms.
        snapshot = self._snapshot
        elapsed = self.clock() - begun
        plots = adc.save_plots(os.path.join(self.folder, "plots", "ADC_overall"), active_tdcs=tdcs)
        self._record_capture(snapshot, tdcs, elapsed, plots)
        self._run_restores()

        errors = self._tdc_errors(snapshot, tdcs)
        if errors:
            raise QcFailure("ADC plots show errors: " + ", ".join(
                f"TDC {tdc:02d} err={count}" for tdc, count in sorted(errors.items())) + ".")
        triggers = int(getattr(snapshot, "triggers", 0))
        if triggers < CAPTURE_MIN_TRIGGERS:
            raise QcFailure(f"Only {triggers} triggers in {elapsed:.0f} s; "
                            f"need at least {CAPTURE_MIN_TRIGGERS}.")
        if len(plots) < len(tdcs):
            raise QcFailure(f"Saved only {len(plots)} of {len(tdcs)} ADC plots.")

    def _record_capture(self, snapshot, tdcs, elapsed, plots):
        histograms = getattr(snapshot, "adc_hist", None)
        overflow = getattr(snapshot, "overflow_cnt", None)
        hits = {tdc: int(histograms[tdc].sum()) for tdc in tdcs} if histograms is not None else {}
        self.results["capture"] = {
            "seconds": round(elapsed, 1),
            "triggers": int(getattr(snapshot, "triggers", 0)),
            "hits_total": int(getattr(snapshot, "hits_total", 0)),
            "hits_in_adc_plot_by_tdc": hits,
            "plots_saved": len(plots),
        }
        no_hits = [tdc for tdc, count in hits.items() if count == 0]
        if no_hits:
            self.flags.append(f"TDCs with no hits in the ADC plot: {no_hits}")
        if overflow is not None:
            overflowed = {tdc: int(overflow[tdc]) for tdc in tdcs if int(overflow[tdc])}
            if overflowed:
                self.flags.append(f"TDC overflow counts: {overflowed}")
        total = int(getattr(snapshot, "decode_error_total", 0))
        if total:
            self.flags.append(f"Total decode errors in the run: {total}")

    # ----------------------------------------------------------------- report
    def _write_report(self, started):
        settings = self.settings
        report = {
            "verdict": self.verdict,
            "failure": self.failure,
            "csm_serial": settings.serial,
            "operator": settings.operator,
            "started": started.isoformat(timespec="seconds"),
            "finished": self.now().isoformat(timespec="seconds"),
            "bitstream": settings.bitstream,
            "prbs_target_ber": settings.prbs_target,
            "dline_target_ber": settings.dline_target,
            "asd_main_threshold": settings.asd_threshold,
            "steps": self.step_log,
            "results": self.results,
            "flags": self.flags,
        }
        with open(os.path.join(self.folder, "qc_summary.json"), "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, default=str)

        lines = [
            f"CSM QC result: {self.verdict}",
            f"CSM serial:    {settings.serial}",
            f"Operator:      {settings.operator}",
            f"Started:       {report['started']}",
            f"Finished:      {report['finished']}",
            f"Bitstream:     {settings.bitstream}",
            f"Targets:       PRBS BER {settings.prbs_target:.1e}, D-line BER {settings.dline_target:.1e}, "
            f"ASD main threshold {settings.asd_threshold}",
            f"PRBS BER uses a line rate of {PRBS_LINE_RATE_BPS:.3g} bit/s.",
        ]
        if self.failure:
            lines.append(f"Reason:        {self.failure}")
        lines += ["", "Steps:"]
        lines += [f"  {step['result']:8} {step['name']}"
                  + (f" ({step['seconds']} s)" if "seconds" in step else "")
                  for step in self.step_log]
        lines += ["", "Flagged, not failed:"] + [f"  {flag}" for flag in self.flags or ["none"]]
        lines += ["", "Results:"] + [f"  {key}: {value}" for key, value in self.results.items()]
        with open(os.path.join(self.folder, "qc_summary.txt"), "w", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
