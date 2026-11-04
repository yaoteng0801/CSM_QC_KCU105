"""DIA v1 request-driven FPGA counters (no data-stream format changes)."""
from dataclasses import dataclass
from datetime import datetime, timezone
import time

SIGNATURE = 0x44494101
CLOCK_HZ = 40_000_000
MASK64 = (1 << 64) - 1
COUNTERS = (
    ("processed", "Candidates processed"),
    ("accepted", "Candidates accepted (committed)"),
    ("rejected", "Candidates rejected"),
    ("fail_min_tubes_event", "Fail: min tubes / event"),
    ("fail_min_tubes_ml", "Fail: min tubes / every ML"),
    ("fail_min_tubes_layer", "Fail: min tubes / every layer"),
    ("fail_min_layers_ml", "Fail: min hit layers / every ML"),
    ("discard_prebuffer", "Discard: prebuffer limit"),
    ("discard_raw_limit", "Discard: raw-word limit"),
    ("fifo_lost_words", "Hit FIFO overflow: lost writes"),
    ("watchdog_aborts", "Watchdog aborts"),
    ("unmapped_hits", "Unmapped hits read"),
    ("interrupted_candidates", "Undecided candidates lost at stop/reset"),
    ("raw_limit_aborts", "Committed events: raw-limit aborts"),
)


class DiagnosticContinuityError(RuntimeError):
    """The run baseline can no longer be used, even if later counts recover."""


@dataclass(frozen=True)
class DiagnosticSnapshot:
    sequence: int
    epoch: int
    cycles: int
    running: bool
    chambers: tuple
    sampled_at: str

    def as_dict(self):
        return {
            "sequence": self.sequence, "epoch": self.epoch,
            "fpga_cycles": self.cycles, "running": self.running,
            "sampled_at_utc": self.sampled_at,
            "chambers": [dict(zip((key for key, _ in COUNTERS), values))
                         for values in self.chambers],
        }

    def delta(self, earlier):
        if self.epoch != earlier.epoch or self.cycles < earlier.cycles:
            raise DiagnosticContinuityError("FPGA counters were cleared/reset; run totals are unavailable")
        # A 64-bit event counter cannot legitimately wrap during a GUI run.
        if any(a < b for cur, old in zip(self.chambers, earlier.chambers)
               for a, b in zip(cur, old)):
            raise DiagnosticContinuityError("FPGA counters decreased; run totals are unavailable")
        return tuple(tuple(a-b for a, b in zip(cur, old))
                     for cur, old in zip(self.chambers, earlier.chambers))


def read_snapshot(read, write, cancelled=None):
    """Caller holds the Ethernet lock across the entire transaction.

    Sequence tags on every page plus final status catch competing readers too.
    No counter reset is performed. A failed transaction is never partly returned.
    """
    deadline = time.monotonic() + 2.0

    def check_request():
        if cancelled is not None and cancelled():
            raise RuntimeError("FPGA diagnostic read cancelled")
        if time.monotonic() > deadline:
            raise RuntimeError("FPGA diagnostic snapshot timed out")

    def read_page(address, selector=0):
        check_request()
        return read(address, selector)

    def validate(status):
        if status & 0xffffffff != SIGNATURE:
            raise RuntimeError("FPGA diagnostics unavailable: load DIA v1 firmware")
        if (status >> 96) & 255 != len(COUNTERS) or (status >> 104) & 255 != 64:
            raise RuntimeError("Unsupported FPGA diagnostic counter layout")

    before = read_page(68)
    validate(before)
    check_request()
    write(68, 1)
    status = read_page(68)
    validate(status)
    sequence = (status >> 32) & 0xffffffff
    epoch = (status >> 64) & 0xffffffff
    if not (status >> 112) & 1 or sequence == (before >> 32) & 0xffffffff:
        raise RuntimeError("FPGA did not acknowledge a fresh diagnostic snapshot")
    if epoch != (before >> 64) & 0xffffffff:
        raise RuntimeError("FPGA diagnostic epoch changed during snapshot request")
    stamp = read_page(70)
    if (stamp >> 64) & 0xffffffff != epoch or stamp >> 96 != sequence:
        raise RuntimeError("FPGA diagnostic timestamp snapshot mismatch")
    chambers = []
    for chamber in range(2):
        values = []
        for pair in range(len(COUNTERS)//2):
            page = read_page(69, (chamber << 7) | pair)
            if page >> 128 != sequence:
                raise RuntimeError("FPGA diagnostic snapshot changed during readback")
            values.extend((page & MASK64, (page >> 64) & MASK64))
        if values[0] != (values[1] + values[2]) & MASK64:
            raise RuntimeError("Inconsistent FPGA candidate accounting")
        chambers.append(tuple(values))
    if read_page(68) != status:
        raise RuntimeError("FPGA diagnostic snapshot changed during readback")
    return DiagnosticSnapshot(sequence, epoch, stamp & MASK64,
                              bool((status >> 113) & 1), tuple(chambers),
                              datetime.now(timezone.utc).isoformat())
