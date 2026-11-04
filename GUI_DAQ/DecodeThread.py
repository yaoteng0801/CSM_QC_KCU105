from __future__ import annotations

from collections import Counter
import os
import sys
import time
import queue
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PyQt5 import QtCore

from Signal import SignalType, Hit, StreamDecoder, GeometryLike
from Event import Event, ChamberBlock  # UPDATED

_NATIVE_DECODER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "native_decoder")
if _NATIVE_DECODER_DIR not in sys.path:
    sys.path.insert(0, _NATIVE_DECODER_DIR)
try:
    import native_decoder_cpp
except Exception:
    native_decoder_cpp = None


_WATCHDOG_TYPE_ORDER = (
    "IDLE",
    "TRIG_ONLY",
    "START_EVENT",
    "CAPTURE_PRE",
    "SEND_HEAD",
    "FLUSH_BUF",
    "STREAM_LIVE",
    "SEND_TRAIL",
    "ABORT_MARK",
    "ABORT_TRAIL",
    "ABORT_CLEAN",
    "legacy/unknown",
)

_TDC_LSB_NS = 0.78125
MAX_CHAMBERS = 2
EVENT_HIT_COUNT_MAX = 20
EVENT_HIT_COUNT_BINS = EVENT_HIT_COUNT_MAX + 2  # 0..20 plus >20 overflow
ANALYSIS_UPDATE_INTERVAL_SEC = 5.0
DECODE_BATCH_MAX_BYTES = 256 * 1024
DECODE_BATCH_MAX_CHUNKS = 64
_DEFAULT_SNAPSHOT_FIELDS = object()


@dataclass(frozen=True)
class DecodeSnapshot:
    adc_hist: Optional[np.ndarray]
    tdc_hist: Optional[np.ndarray]

    adc_ch_hist: Optional[np.ndarray]
    tdc_ch_hist: Optional[np.ndarray]

    adc_bins: int
    tdc_bins: int
    ch_adc_bins: int
    ch_tdc_bins: int

    headers: int
    events_fifoA: int
    events_fifoB: int
    trailers: int
    triggers: int
    hits_total: int
    valid_events: int
    raw_hit_ch_count: Optional[np.ndarray]
    event_hit_count_hist: Optional[np.ndarray]

    overflow_cnt: np.ndarray
    decode_err_cnt: np.ndarray
    decode_error_total: int

    err_event_id: int
    err_hit_count: int
    err_missing_trailer: int
    err_missing_header: int
    abort_burst: int
    abort_watchdog: int
    abort_watchdog_types: tuple[tuple[str, int], ...]
    noise_headers: int
    noise_counters: int
    noise_error_words: int
    noise_trailers: int
    noise_last_seconds: int
    noise_last_total: int
    noise_counter_total: Optional[np.ndarray]
    noise_counter_rate: Optional[np.ndarray]
    noise_decode_error_count: np.ndarray
    noise_invalid_channel_count: np.ndarray

    events_buffered: int
    decoded_bytes_total: int
    decode_rate_bytes_s: float
    decode_rate_words_s: float
    queue_backlog_chunks: int
    queue_backlog_peak_chunks: int
    queue_capacity_chunks: int
    decode_backend: str
    tdc_shift: int
    ch_tdc_shift: int
    tdc_min_ns: float
    tdc_max_ns: float
    ch_tdc_min_ns: float
    ch_tdc_max_ns: float
    tdc_binw_ns: float
    ch_tdc_binw_ns: float


class EventBuffer:
    def __init__(self, max_events: int = 256, min_hits: int = 0):
        self._q: "queue.Queue[Event]" = queue.Queue(maxsize=max_events)
        self.max_events = int(max_events)
        self.min_hits = max(0, int(min_hits))
        self.dropped = 0

    def push(self, ev: Event):
        if int(getattr(ev, "hit_count_expected", 0)) < self.min_hits:
            return
        try:
            self._q.put_nowait(ev)
        except queue.Full:
            self.dropped += 1

    def pop(self) -> Optional[Event]:
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        return self._q.qsize()

    def available(self) -> int:
        return max(0, self.max_events - self._q.qsize())

    def account_dropped(self, count: int):
        self.dropped += max(0, int(count))

    def clear(self):
        try:
            while True:
                self._q.get_nowait()
        except queue.Empty:
            pass


class DecodeThread(QtCore.QThread):
    analysis_1hz = QtCore.pyqtSignal(object)
    event_ready = QtCore.pyqtSignal(object)
    decode_issue = QtCore.pyqtSignal(str)
    decode_error_limit_exceeded = QtCore.pyqtSignal(int, int)

    def __init__(
        self,
        analysis_q: "queue.Queue[bytes]",
        event_buffer: EventBuffer,
        geo: Optional["GeometryLike"] = None,
        max_tdcs: int = 40,
        max_channels: int = 24,
        adc_bins: int = 256,
        tdc_bins: int = 4096,
        tdc_shift: int = 5,
        ch_tdc_bins: int = 1024,
        ch_tdc_shift: int = 7,
        tdc_min_ns: float = 0.0,
        tdc_max_ns: Optional[float] = None,
        ch_tdc_min_ns: Optional[float] = None,
        ch_tdc_max_ns: Optional[float] = None,
        decode_error_stop_threshold: int = 1000,
        acquisition_mode: int = 0,
        noise_test_mode: int = 0,
        use_native_decoder: Optional[bool] = None,
        retain_all_native_events: bool = False,
        snapshot_fields=None,
        parent: Optional[QtCore.QObject] = None,
    ):
        super().__init__(parent)

        self.q = analysis_q
        self.buf = event_buffer
        self.geo = geo
        self._stop = False
        self.acquisition_mode = int(acquisition_mode)
        self.noise_test_mode = int(noise_test_mode)
        self.raw_hit_mode = bool(self.noise_test_mode & 0x1)
        self.retain_all_native_events = bool(retain_all_native_events)
        self._snapshot_fields = (
            None if snapshot_fields is None else frozenset(str(field) for field in snapshot_fields)
        )

        self.max_tdcs = int(max_tdcs)
        self.max_channels = int(max_channels)

        self.adc_bins = int(adc_bins)
        self.tdc_bins = int(tdc_bins)
        self.tdc_shift = int(tdc_shift)
        self.tdc_binw_ns = float(_TDC_LSB_NS * (1 << self.tdc_shift))
        self.tdc_min_ns = float(tdc_min_ns)
        self.tdc_max_ns = (
            float(tdc_max_ns)
            if tdc_max_ns is not None
            else float(self.tdc_min_ns + self.tdc_bins * self.tdc_binw_ns)
        )
        self.tdc_min_count = int(round(self.tdc_min_ns / _TDC_LSB_NS))

        self.ch_adc_bins = int(adc_bins)
        self.ch_tdc_bins = int(ch_tdc_bins)
        self.ch_tdc_shift = int(ch_tdc_shift)
        self.ch_tdc_binw_ns = float(_TDC_LSB_NS * (1 << self.ch_tdc_shift))
        self.ch_tdc_min_ns = float(self.tdc_min_ns if ch_tdc_min_ns is None else ch_tdc_min_ns)
        self.ch_tdc_max_ns = (
            float(ch_tdc_max_ns)
            if ch_tdc_max_ns is not None
            else float(self.ch_tdc_min_ns + self.ch_tdc_bins * self.ch_tdc_binw_ns)
        )
        self.ch_tdc_min_count = int(round(self.ch_tdc_min_ns / _TDC_LSB_NS))

        # histograms (VALID EVENTS ONLY)
        self._adc = np.zeros((self.max_tdcs, self.adc_bins), dtype=np.uint32)
        self._tdc = np.zeros((self.max_tdcs, self.tdc_bins), dtype=np.uint32)

        self._adc_ch = np.zeros((self.max_tdcs, self.max_channels, self.ch_adc_bins), dtype=np.uint32)
        self._tdc_ch = np.zeros((self.max_tdcs, self.max_channels, self.ch_tdc_bins), dtype=np.uint32)
        self._hit_ch_all = np.zeros((self.max_tdcs, self.max_channels), dtype=np.uint32)
        self._event_hit_count_hist = np.zeros(
            (MAX_CHAMBERS, EVENT_HIT_COUNT_BINS), dtype=np.uint64
        )

        self._tdc_chamber_ids = np.full((self.max_tdcs,), -1, dtype=np.int32)
        if self.geo is not None:
            chamber_lookup = getattr(self.geo, "chamber_id_from_tdcid", None)
            if callable(chamber_lookup):
                for tdc_id in range(self.max_tdcs):
                    try:
                        chamber_id = int(chamber_lookup(tdc_id))
                    except Exception:
                        chamber_id = -1
                    if 0 <= chamber_id < MAX_CHAMBERS:
                        self._tdc_chamber_ids[tdc_id] = chamber_id
        self._configured_chamber_ids = tuple(
            int(chamber_id)
            for chamber_id in sorted(set(self._tdc_chamber_ids.tolist()))
            if 0 <= int(chamber_id) < MAX_CHAMBERS
        )

        self._ovf = np.zeros((self.max_tdcs,), dtype=np.uint32)
        self._derr = np.zeros((self.max_tdcs,), dtype=np.uint32)
        self._noise_total = np.zeros((self.max_tdcs, self.max_channels), dtype=np.uint64)
        self._noise_rate = np.zeros((self.max_tdcs, self.max_channels), dtype=np.float64)
        self._noise_prev_total = np.zeros((self.max_tdcs, self.max_channels), dtype=np.uint64)
        self._noise_prev_seconds = np.zeros((self.max_tdcs, self.max_channels), dtype=np.uint64)
        self._noise_decode_error_count = np.zeros((self.max_tdcs,), dtype=np.uint64)
        self._noise_invalid_channel_count = np.zeros((self.max_tdcs,), dtype=np.uint64)
        self._decode_error_total = 0
        self.decode_error_stop_threshold = int(decode_error_stop_threshold)
        self._decode_error_limit_emitted = False

        self._hdr = 0
        self._events_fifoA = 0
        self._events_fifoB = 0
        self._trl = 0
        self._trg = 0
        self._hit_total = 0
        self._valid_events = 0

        self._err_eid = 0
        self._err_hit = 0
        self._err_missing_trailer = 0
        self._err_missing_header = 0
        self._abort_burst = 0
        self._abort_watchdog = 0
        self._abort_watchdog_types: Counter[str] = Counter()
        self._noise_hdr = 0
        self._noise_ctr = 0
        self._noise_err = 0
        self._noise_trl = 0
        self._noise_last_seconds = 0
        self._noise_last_total = 0
        self._noise_counter_modulus = 1 << 31

        # current event state
        self._cur_open = False
        self._cur_event_id20 = 0
        self._cur_event_id12 = 0
        self._cur_header_raw40 = 0
        self._cur_rd_bank_sel = 0
        self._cur_trigger_ledge: Optional[int] = None
        self._cur_trigger_overflow = 0
        self._cur_trigger_count = 0
        self._cur_tdc_header_count = 0
        self._cur_tdc_trailer_count = 0

        # Keep for histogram updates (fast flat loop)
        self._cur_hits: list[Hit] = []

        # Chamber grouping for Event payload (no mixing)
        self._cur_hits_by_ch: dict[int, list[Hit]] = {}

        self._cur_hit_count = 0
        self._last_emit = time.time()
        self._decoded_bytes_total = 0
        self._decode_rate_bytes_s = 0.0
        self._decode_rate_words_s = 0.0
        self._decode_rate_last_time = time.monotonic()
        self._decode_rate_last_bytes = 0
        self._queue_backlog_peak_chunks = 0
        self._stream_decoder = StreamDecoder(
            geo=geo,
            acquisition_mode=self.acquisition_mode,
            noise_test_mode=self.noise_test_mode,
        )
        native_requested = (
            native_decoder_cpp is not None
            if use_native_decoder is None
            else bool(use_native_decoder)
        )
        if native_requested and native_decoder_cpp is None:
            raise RuntimeError(
                "Native decoder requested but native_decoder_cpp is not built. "
                f"Build it with: cd {_NATIVE_DECODER_DIR} && ../.venv/bin/python setup.py build_ext --inplace"
            )
        self._native_decoder = None
        if native_requested:
            self._native_decoder = native_decoder_cpp.NativeDecoder(
                self.acquisition_mode,
                self.noise_test_mode,
                self.max_tdcs,
                self.max_channels,
                self._tdc_chamber_ids.tolist(),
                self.adc_bins,
                self.tdc_bins,
                self.tdc_shift,
                self.ch_tdc_bins,
                self.ch_tdc_shift,
                self.tdc_min_ns,
                self.tdc_max_ns,
                self.ch_tdc_min_ns,
                self.ch_tdc_max_ns,
                self.decode_error_stop_threshold,
            )

    def stop(self):
        self._stop = True

    def set_snapshot_fields(self, fields) -> None:
        self._snapshot_fields = (
            None if fields is None else frozenset(str(field) for field in fields)
        )

    def _reset_event(self):
        self._cur_open = False
        self._cur_event_id20 = 0
        self._cur_event_id12 = 0
        self._cur_header_raw40 = 0
        self._cur_rd_bank_sel = 0
        self._cur_trigger_ledge = None
        self._cur_trigger_overflow = 0
        self._cur_trigger_count = 0
        self._cur_tdc_header_count = 0
        self._cur_tdc_trailer_count = 0
        self._cur_hits.clear()
        self._cur_hits_by_ch.clear()
        self._cur_hit_count = 0

    def _fill_raw_hit_adc(self, hit) -> None:
        tdc = int(hit.tdcid)
        channel = int(hit.ch)
        width = int(hit.width)
        if not (0 <= tdc < self.max_tdcs):
            return
        if 0 <= width < self.adc_bins:
            self._adc[tdc, width] += 1
        if 0 <= channel < self.max_channels and 0 <= width < self.ch_adc_bins:
            self._adc_ch[tdc, channel, width] += 1

    def _record_event_hit_count(self, event_id20: int, hit_count: int) -> None:
        """Accumulate one valid event into its geometry hit-multiplicity histogram."""
        if self.acquisition_mode == 1:
            chamber_id = (int(event_id20) >> 19) & 0x1
            count = max(0, min(EVENT_HIT_COUNT_MAX + 1, int(hit_count)))
            self._event_hit_count_hist[chamber_id, count] += 1
            return

        # A triggered event is shared by all configured geometries. Count mapped
        # hits independently, including the zero-hit bin for a geometry.
        if self._configured_chamber_ids:
            for chamber_id in self._configured_chamber_ids:
                count = len(self._cur_hits_by_ch.get(chamber_id, ()))
                count = max(0, min(EVENT_HIT_COUNT_MAX + 1, count))
                self._event_hit_count_hist[chamber_id, count] += 1
            return

        # Preserve the historical single-geometry behavior when no map exists.
        count = max(0, min(EVENT_HIT_COUNT_MAX + 1, int(hit_count)))
        self._event_hit_count_hist[0, count] += 1

    def _start_event(
        self,
        event_id20: int,
        event_id12: int,
        rd_bank_sel: int,
        trigger_ledge: Optional[int],
        trigger_overflow: int,
        header_raw40: int = 0,
    ):
        self._cur_open = True
        self._cur_event_id20 = int(event_id20)
        self._cur_event_id12 = int(event_id12)
        self._cur_header_raw40 = int(header_raw40)
        self._cur_rd_bank_sel = int(rd_bank_sel)
        self._cur_trigger_ledge = None if trigger_ledge is None else int(trigger_ledge)
        self._cur_trigger_overflow = int(trigger_overflow)
        self._cur_trigger_count = 0
        self._cur_tdc_header_count = 0
        self._cur_tdc_trailer_count = 0
        self._cur_hits.clear()
        self._cur_hits_by_ch.clear()
        self._cur_hit_count = 0

    @staticmethod
    def _rollover_diff_17bit(a: int, b: int) -> int:
        rollover = 1 << 17
        half = rollover >> 1
        d = int(a) - int(b)
        if d > half:
            d -= rollover
        elif d < -half:
            d += rollover
        return int(d)

    @staticmethod
    def _watchdog_type_name(abort_marker) -> str:
        state_name = str(getattr(abort_marker, "watchdog_state_name", "") or "").strip()
        if state_name:
            return state_name

        state_bits = getattr(abort_marker, "watchdog_state_bits", None)
        if state_bits is None:
            return "legacy/unknown"

        return f"state 0x{int(state_bits):03x}"

    def _ordered_watchdog_types(self) -> tuple[tuple[str, int], ...]:
        order = {name: idx for idx, name in enumerate(_WATCHDOG_TYPE_ORDER)}
        items = sorted(
            self._abort_watchdog_types.items(),
            key=lambda item: (order.get(item[0], len(order)), item[0]),
        )
        return tuple((str(name), int(count)) for name, count in items if int(count) > 0)

    @staticmethod
    def _fmt_raw40(raw: int) -> str:
        return f"0x{(int(raw) & ((1 << 40) - 1)):010x}"

    def _event_context(self) -> str:
        if not self._cur_open:
            return "event_open=0"
        return (
            "event_open=1 "
            f"event_id12={int(self._cur_event_id12)} "
            f"event_id20={int(self._cur_event_id20)} "
            f"hits_seen={int(self._cur_hit_count)} "
            f"header_raw={self._fmt_raw40(self._cur_header_raw40)}"
        )

    def _emit_issue(self, level: str, detail: str) -> None:
        self.decode_issue.emit(f"[{str(level).upper()}] {detail}\n")

    def _record_noise_error_counter(self, noise_error, raw40: int) -> bool:
        self._noise_err += 1
        tdc = int(noise_error.tdcid)
        kind = int(noise_error.kind)
        total = int(noise_error.total_count)
        if not (0 <= tdc < self.max_tdcs):
            self._emit_issue(
                "ERROR",
                f"noise error counter has invalid TDC: tdc={tdc} kind={kind} total={total}",
            )
            return False

        if kind == 0:
            totals = self._noise_decode_error_count
            kind_name = "KERR/DErr"
        elif kind == 1:
            totals = self._noise_invalid_channel_count
            kind_name = "invalid_channel"
        else:
            self._emit_issue(
                "ERROR",
                f"unknown noise error counter kind: tdc={tdc} kind={kind} total={total}",
            )
            return False

        previous = int(totals[tdc])
        if total >= previous:
            delta = total - previous
        else:
            wrapped = (total - previous) & (self._noise_counter_modulus - 1)
            delta = wrapped if wrapped <= (self._noise_counter_modulus // 2) else total
        totals[tdc] = total

        if delta <= 0:
            return False

        self._decode_error_total += delta
        self._derr[tdc] += delta
        self._emit_issue(
            "ERROR",
            f"noise error counter: reason={kind_name} tdc={tdc} "
            f"delta={delta} total={total} raw={self._fmt_raw40(raw40)}",
        )
        threshold = int(self.decode_error_stop_threshold)
        if (
            threshold > 0
            and self._decode_error_total > threshold
            and not self._decode_error_limit_emitted
        ):
            self._decode_error_limit_emitted = True
            self._emit_issue(
                "ERROR",
                "decode error limit exceeded: "
                f"count={int(self._decode_error_total)} threshold={threshold}; stopping DAQ",
            )
            self.decode_error_limit_exceeded.emit(int(self._decode_error_total), threshold)
            self._stop = True
            return True
        return False

    def _finalize_event(
        self,
        trailer_event_id20: int,
        trailer_event_id12: int,
        trigger_count: int,
        hit_expected: int,
        tdc_header_count: int,
        tdc_trailer_count: int,
        header_count_error: int,
        trailer_count_error: int,
        trailer_raw40: int,
    ):
        event_id_mismatch = self._cur_event_id12 != int(trailer_event_id12)
        if self.acquisition_mode == 1:
            event_id_mismatch = self._cur_event_id20 != int(trailer_event_id20)

        if event_id_mismatch:
            self._err_eid += 1
            self._emit_issue(
                "ERROR",
                "event_id mismatch: "
                f"header_event_id12={int(self._cur_event_id12)} "
                f"trailer_event_id12={int(trailer_event_id12)} "
                f"header_event_id20={int(self._cur_event_id20)} "
                f"trailer_event_id20={int(trailer_event_id20)} "
                f"hits_seen={int(self._cur_hit_count)} "
                f"trailer_hit_count={int(hit_expected)} "
                f"header_raw={self._fmt_raw40(self._cur_header_raw40)} "
                f"trailer_raw={self._fmt_raw40(trailer_raw40)}",
            )
            self._reset_event()
            return

        if self._cur_hit_count != int(hit_expected):
            self._err_hit += 1
            self._emit_issue(
                "ERROR",
                "hit_count mismatch: "
                f"event_id12={int(self._cur_event_id12)} "
                f"event_id20={int(self._cur_event_id20)} "
                f"hits_seen={int(self._cur_hit_count)} "
                f"trailer_hit_count={int(hit_expected)} "
                f"tdc_header_count={int(tdc_header_count)} "
                f"tdc_trailer_count={int(tdc_trailer_count)} "
                f"header_raw={self._fmt_raw40(self._cur_header_raw40)} "
                f"trailer_raw={self._fmt_raw40(trailer_raw40)}",
            )
            self._reset_event()
            return

        if int(header_count_error) or int(trailer_count_error):
            self._emit_issue(
                "WARN",
                "TDC count flag in event trailer: "
                f"event_id12={int(self._cur_event_id12)} "
                f"event_id20={int(self._cur_event_id20)} "
                f"header_count_error={int(header_count_error)} "
                f"trailer_count_error={int(trailer_count_error)} "
                f"tdc_header_count={int(tdc_header_count)} "
                f"tdc_trailer_count={int(tdc_trailer_count)} "
                f"hit_count={int(hit_expected)} "
                f"trailer_raw={self._fmt_raw40(trailer_raw40)}",
            )

        self._record_event_hit_count(self._cur_event_id20, hit_expected)

        # VALID: update histograms (keep locals for speed)
        adc = self._adc
        tdc = self._tdc
        adc_ch = self._adc_ch
        tdc_ch = self._tdc_ch

        max_tdcs = self.max_tdcs
        max_channels = self.max_channels
        adc_bins = self.adc_bins
        tdc_bins = self.tdc_bins
        tdc_shift = self.tdc_shift
        tdc_min_count = self.tdc_min_count
        ch_adc_bins = self.ch_adc_bins
        ch_tdc_bins = self.ch_tdc_bins
        ch_tdc_shift = self.ch_tdc_shift
        ch_tdc_min_count = self.ch_tdc_min_count

        trigger_ledge = self._cur_trigger_ledge

        for h in self._cur_hits:
            t = int(h.tdcid)
            if not (0 <= t < max_tdcs):
                continue

            ch = int(h.ch)
            w = int(h.width)
            ledge_for_hist = int(h.ledge)
            if trigger_ledge is not None:
                ledge_for_hist = self._rollover_diff_17bit(ledge_for_hist, trigger_ledge)

            if 0 <= w < adc_bins:
                adc[t, w] += 1

            b = (int(ledge_for_hist) - tdc_min_count) >> tdc_shift
            if 0 <= b < tdc_bins:
                tdc[t, b] += 1

            if 0 <= ch < max_channels:
                if 0 <= w < ch_adc_bins:
                    adc_ch[t, ch, w] += 1

                bc = (int(ledge_for_hist) - ch_tdc_min_count) >> ch_tdc_shift
                if 0 <= bc < ch_tdc_bins:
                    tdc_ch[t, ch, bc] += 1

        # Freeze chamber-separated hits into ChamberBlocks
        chambers = {
            int(cid): ChamberBlock(chamber_id=int(cid), hits=tuple(hlist))
            for cid, hlist in self._cur_hits_by_ch.items()
            if hlist
        }

        ev = Event(
            event_id20=int(self._cur_event_id20),
            rd_bank_sel=int(self._cur_rd_bank_sel),
            trigger_count=int(max(trigger_count, self._cur_trigger_count)),
            hit_count_expected=int(hit_expected),
            event_id12=int(self._cur_event_id12),
            chamber_id=(int(self._cur_event_id20) >> 19) & 0x1
            if self.acquisition_mode == 1 else 0,
            chamber_event_id=int(self._cur_event_id20) & 0x7FFFF
            if self.acquisition_mode == 1 else int(self._cur_event_id20),
            trigger_ledge=trigger_ledge,
            trigger_overflow=int(self._cur_trigger_overflow),
            tdc_header_count=int(tdc_header_count),
            tdc_trailer_count=int(tdc_trailer_count),
            header_count_error=int(header_count_error),
            trailer_count_error=int(trailer_count_error),
            chambers=chambers,
        )
        self._valid_events += 1
        self.buf.push(ev)
        self.event_ready.emit(ev)
        self._reset_event()

    def _materialize_native_event(self, raw_event):
        event_id20 = int(raw_event["event_id20"])
        default_chamber_id = (event_id20 >> 19) & 0x1 if self.acquisition_mode == 1 else 0
        default_chamber_event_id = (
            event_id20 & 0x7FFFF if self.acquisition_mode == 1 else event_id20
        )
        hits_by_ch: dict[int, list[Hit]] = {}
        for raw_hit in raw_event.get("hits", ()):
            csmid, tdcid, ch, mode, ledge, width = (int(v) for v in raw_hit)
            x = -1.0
            y = -1.0
            layer = -1
            col = -1
            chamber_id = -1
            if self.geo is not None:
                try:
                    x, y, layer, col = self.geo.wire_center_from_hit(tdcid, ch)
                except Exception:
                    pass
                try:
                    chamber_id = int(self.geo.chamber_id_from_tdcid(tdcid))
                except Exception:
                    chamber_id = -1

            hit = Hit(
                csmid=csmid,
                tdcid=tdcid,
                ch=ch,
                mode=mode,
                ledge=ledge,
                width=width,
                x=float(x),
                y=float(y),
                layer=int(layer),
                col=int(col),
                chamber_id=chamber_id,
            )
            if chamber_id >= 0:
                hits_by_ch.setdefault(chamber_id, []).append(hit)

        chambers = {
            chamber_id: ChamberBlock(chamber_id=chamber_id, hits=tuple(hits))
            for chamber_id, hits in hits_by_ch.items()
        }
        trigger_ledge = raw_event.get("trigger_ledge")
        return Event(
            event_id20=event_id20,
            rd_bank_sel=int(raw_event["rd_bank_sel"]),
            trigger_count=int(raw_event["trigger_count"]),
            hit_count_expected=int(raw_event["hit_count_expected"]),
            event_id12=int(raw_event["event_id12"]),
            chamber_id=int(raw_event.get("chamber_id", default_chamber_id)),
            chamber_event_id=int(
                raw_event.get("chamber_event_id", default_chamber_event_id)
            ),
            trigger_ledge=None if trigger_ledge is None else int(trigger_ledge),
            trigger_overflow=int(raw_event["trigger_overflow"]),
            tdc_header_count=int(raw_event["tdc_header_count"]),
            tdc_trailer_count=int(raw_event["tdc_trailer_count"]),
            header_count_error=int(raw_event["header_count_error"]),
            trailer_count_error=int(raw_event["trailer_count_error"]),
            chambers=chambers,
        )

    def _run_native(self):
        q_get = self.q.get
        q_get_nowait = self.q.get_nowait
        emit_periodic_analysis = self._emit_periodic_analysis_if_needed

        while not self._stop:
            try:
                chunk = q_get(timeout=0.01)
            except queue.Empty:
                emit_periodic_analysis()
                continue

            self._queue_backlog_peak_chunks = max(
                self._queue_backlog_peak_chunks,
                int(self.q.qsize()),
            )
            chunks = [chunk]
            batch_bytes = len(chunk)
            while (
                len(chunks) < DECODE_BATCH_MAX_CHUNKS
                and batch_bytes < DECODE_BATCH_MAX_BYTES
            ):
                try:
                    next_chunk = q_get_nowait()
                except queue.Empty:
                    break
                chunks.append(next_chunk)
                batch_bytes += len(next_chunk)

            batch = chunk if len(chunks) == 1 else b"".join(chunks)
            self._decoded_bytes_total += len(batch)
            event_slots = -1 if self.retain_all_native_events else self.buf.available()
            native_min_hits = 0 if self.retain_all_native_events else self.buf.min_hits
            result = self._native_decoder.process(
                batch,
                event_slots,
                native_min_hits,
            )

            for detail in result.get("issues", ()):
                text = str(detail)
                self.decode_issue.emit(text if text.endswith("\n") else f"{text}\n")

            for raw_event in result.get("events", ()):
                event = self._materialize_native_event(raw_event)
                self.buf.push(event)
                self.event_ready.emit(event)
            completed_total = int(result.get("completed_events_total", 0))
            returned_events = len(result.get("events", ()))
            if completed_total > returned_events:
                self.buf.account_dropped(completed_total - returned_events)

            if bool(result.get("decode_error_limit_exceeded", False)):
                count = int(result.get("decode_error_total", 0))
                self.decode_error_limit_exceeded.emit(
                    count,
                    int(self.decode_error_stop_threshold),
                )
                self._stop = True

            emit_periodic_analysis()

    def run(self):
        if self._native_decoder is not None:
            self._run_native()
            return

        q_get = self.q.get
        q_get_nowait = self.q.get_nowait
        emit_periodic_analysis = self._emit_periodic_analysis_if_needed

        while not self._stop:
            try:
                chunk = q_get(timeout=0.01)
            except queue.Empty:
                emit_periodic_analysis()
                continue

            self._queue_backlog_peak_chunks = max(
                self._queue_backlog_peak_chunks,
                int(self.q.qsize()),
            )
            chunks = [chunk]
            batch_bytes = len(chunk)
            while (
                len(chunks) < DECODE_BATCH_MAX_CHUNKS
                and batch_bytes < DECODE_BATCH_MAX_BYTES
            ):
                try:
                    next_chunk = q_get_nowait()
                except queue.Empty:
                    break
                chunks.append(next_chunk)
                batch_bytes += len(next_chunk)

            batch = chunk if len(chunks) == 1 else b"".join(chunks)
            self._decoded_bytes_total += len(batch)
            for s in self._stream_decoder.decode(batch):
                st = s.type

                if st == SignalType.NOISE_COUNTER_HEADER and s.noise_header is not None:
                    self._noise_hdr += 1
                    seconds = int(s.noise_header.seconds_elapsed)
                    if seconds != self._noise_last_seconds:
                        self._noise_rate.fill(0.0)
                        self._noise_last_total = 0
                        self._noise_last_seconds = seconds
                    if self._cur_open:
                        self._err_missing_trailer += 1
                        self._reset_event()
                    continue

                if st == SignalType.NOISE_COUNTER and s.noise_counter is not None:
                    self._noise_ctr += 1
                    t = int(s.noise_counter.tdcid)
                    ch = int(s.noise_counter.ch)
                    if 0 <= t < self.max_tdcs and 0 <= ch < self.max_channels:
                        total = int(s.noise_counter.total_count)
                        prev_total = int(self._noise_prev_total[t, ch])
                        prev_seconds = int(self._noise_prev_seconds[t, ch])
                        seconds = int(self._noise_last_seconds)

                        if prev_seconds > 0 and seconds > prev_seconds:
                            delta = (total - prev_total) & (self._noise_counter_modulus - 1)
                            if total < prev_total and delta > (self._noise_counter_modulus // 2):
                                rate = 0.0
                            else:
                                rate = float(delta) / float(seconds - prev_seconds)
                            self._noise_rate[t, ch] = rate

                        self._noise_total[t, ch] = total
                        self._noise_prev_total[t, ch] = total
                        self._noise_prev_seconds[t, ch] = seconds
                    continue

                if st == SignalType.NOISE_ERROR_COUNTER and s.noise_error is not None:
                    if self._record_noise_error_counter(s.noise_error, s.raw40):
                        break
                    continue

                if st == SignalType.NOISE_COUNTER_TRAILER and s.noise_trailer is not None:
                    self._noise_trl += 1
                    self._noise_last_total += int(s.noise_trailer.total_count_this_tdc)
                    continue

                if st == SignalType.EVENT_HEADER and s.header is not None:
                    self._hdr += 1
                    if self.acquisition_mode == 0:
                        # Triggered-mode headers carry the trigger timestamp.
                        self._trg += 1
                    if int(s.header.rd_bank_sel) == 0:
                        self._events_fifoA += 1
                    else:
                        self._events_fifoB += 1
                    if self._cur_open:
                        self._err_missing_trailer += 1
                        self._emit_issue(
                            "ERROR",
                            "missing trailer before new header: "
                            f"previous_event_id12={int(self._cur_event_id12)} "
                            f"previous_event_id20={int(self._cur_event_id20)} "
                            f"hits_seen={int(self._cur_hit_count)} "
                            f"previous_header_raw={self._fmt_raw40(self._cur_header_raw40)} "
                            f"new_header_event_id12={int(getattr(s.header, 'event_id12', s.header.event_id20 & 0xFFF))} "
                            f"new_header_event_id20={int(s.header.event_id20)} "
                            f"new_header_raw={self._fmt_raw40(s.raw40)}",
                        )
                        self._reset_event()
                    self._start_event(
                        event_id20=int(s.header.event_id20),
                        event_id12=int(getattr(s.header, "event_id12", s.header.event_id20 & 0xFFF)),
                        rd_bank_sel=int(s.header.rd_bank_sel),
                        trigger_ledge=getattr(s.header, "trigger_ledge", None),
                        trigger_overflow=int(getattr(s.header, "trigger_overflow", 0)),
                        header_raw40=int(s.raw40),
                    )
                    continue

                if st == SignalType.HIT and s.hit is not None:
                    self._hit_total += 1
                    t = int(s.hit.tdcid)
                    ch = int(s.hit.ch)
                    if 0 <= t < self.max_tdcs and 0 <= ch < self.max_channels:
                        self._hit_ch_all[t, ch] += 1
                    if self._cur_open:
                        self._cur_hits.append(s.hit)
                        self._cur_hit_count += 1

                        cid = int(getattr(s.hit, "chamber_id", -1))
                        if cid >= 0:
                            self._cur_hits_by_ch.setdefault(cid, []).append(s.hit)
                    elif self.raw_hit_mode:
                        self._fill_raw_hit_adc(s.hit)
                    continue

                if st == SignalType.EVENT_TRAILER and s.trailer is not None:
                    self._trl += 1
                    if not self._cur_open:
                        self._err_missing_header += 1
                        self._emit_issue(
                            "ERROR",
                            "missing header before trailer: "
                            f"trailer_event_id12={int(getattr(s.trailer, 'event_id12', s.trailer.event_id20 & 0xFFF))} "
                            f"trailer_event_id20={int(s.trailer.event_id20)} "
                            f"trailer_hit_count={int(s.trailer.hit_count)} "
                            f"tdc_header_count={int(getattr(s.trailer, 'tdc_header_count', 0))} "
                            f"tdc_trailer_count={int(getattr(s.trailer, 'tdc_trailer_count', 0))} "
                            f"trailer_raw={self._fmt_raw40(s.raw40)}",
                        )
                        continue

                    self._finalize_event(
                        trailer_event_id20=int(s.trailer.event_id20),
                        trailer_event_id12=int(getattr(s.trailer, "event_id12", s.trailer.event_id20 & 0xFFF)),
                        trigger_count=int(s.trailer.trigger_count),
                        hit_expected=int(s.trailer.hit_count),
                        tdc_header_count=int(getattr(s.trailer, "tdc_header_count", 0)),
                        tdc_trailer_count=int(getattr(s.trailer, "tdc_trailer_count", 0)),
                        header_count_error=int(getattr(s.trailer, "header_count_error", 0)),
                        trailer_count_error=int(getattr(s.trailer, "trailer_count_error", 0)),
                        trailer_raw40=int(s.raw40),
                    )
                    continue

                if st == SignalType.TRIGGER and s.trigger is not None:
                    self._trg += 1
                    if self._cur_open:
                        self._cur_trigger_ledge = int(s.trigger.ledge)
                        self._cur_trigger_overflow = int(s.trigger.overflow)
                        self._cur_trigger_count += 1
                    continue

                if st == SignalType.TDC_HEADER:
                    if self._cur_open:
                        self._cur_tdc_header_count += 1
                    continue

                if st == SignalType.TDC_TRAILER:
                    if self._cur_open:
                        self._cur_tdc_trailer_count += 1
                    if s.tdc_trailer is not None and (
                        int(getattr(s.tdc_trailer, "trigger_lost", 0))
                        or int(getattr(s.tdc_trailer, "timeout", 0))
                    ):
                        self._emit_issue(
                            "WARN",
                            "TDC trailer flag: "
                            f"tdc={int(s.tdc_trailer.tdcid)} "
                            f"trigger_lost={int(s.tdc_trailer.trigger_lost)} "
                            f"timeout={int(s.tdc_trailer.timeout)} "
                            f"tdc_hit_count={int(s.tdc_trailer.hit_count)} "
                            f"raw={self._fmt_raw40(s.raw40)} "
                            f"{self._event_context()}",
                        )
                    continue

                if st == SignalType.ABORT and s.abort is not None:
                    abort_kind = str(getattr(s.abort, "kind", "burst"))
                    if abort_kind == "watchdog":
                        self._abort_watchdog += 1
                        watchdog_type = self._watchdog_type_name(s.abort)
                        self._abort_watchdog_types[watchdog_type] += 1
                        self._emit_issue(
                            "WARN",
                            "watchdog abort marker: "
                            f"state={watchdog_type} "
                            f"state_bits={getattr(s.abort, 'watchdog_state_bits', None)} "
                            f"count={getattr(s.abort, 'watchdog_count', None)} "
                            f"raw={self._fmt_raw40(s.raw40)} "
                            f"{self._event_context()}",
                        )
                    else:
                        self._abort_burst += 1
                        self._emit_issue(
                            "WARN",
                            "burst abort marker: "
                            f"threshold={getattr(s.abort, 'threshold', None)} "
                            f"raw={self._fmt_raw40(s.raw40)} "
                            f"{self._event_context()}",
                        )
                    continue

                if st == SignalType.OVERFLOW and s.overflow is not None:
                    t = int(s.overflow.tdcid)
                    if 0 <= t < self.max_tdcs:
                        self._ovf[t] += 1
                    self._emit_issue(
                        "WARN",
                        "TDC overflow word: "
                        f"tdc={t} "
                        f"raw={self._fmt_raw40(s.raw40)} "
                        f"{self._event_context()}",
                    )
                    continue

                if st == SignalType.DECODE_ERROR and s.error is not None:
                    self._decode_error_total += 1
                    t = int(s.error.tdcid)
                    if 0 <= t < self.max_tdcs:
                        self._derr[t] += 1
                    reason = str(getattr(s.error, "reason", "decode_error") or "decode_error")
                    channel = getattr(s.error, "channel", None)
                    mode = getattr(s.error, "mode", None)
                    ledge = getattr(s.error, "ledge", None)
                    width = getattr(s.error, "width", None)
                    extra = ""
                    if channel is not None:
                        extra += f"ch={int(channel)} "
                    if mode is not None:
                        extra += f"mode={int(mode)} "
                    if ledge is not None:
                        extra += f"ledge={int(ledge)} "
                    if width is not None:
                        extra += f"width={int(width)} "
                    self._emit_issue(
                        "ERROR",
                        "decode error word: "
                        f"reason={reason} "
                        f"tdc={t} "
                        f"{extra}"
                        f"raw={self._fmt_raw40(s.raw40)} "
                        f"{self._event_context()}",
                    )
                    threshold = int(self.decode_error_stop_threshold)
                    if (
                        threshold > 0
                        and self._decode_error_total > threshold
                        and not self._decode_error_limit_emitted
                    ):
                        self._decode_error_limit_emitted = True
                        self._emit_issue(
                            "ERROR",
                            "decode error limit exceeded: "
                            f"count={int(self._decode_error_total)} "
                            f"threshold={threshold}; stopping DAQ",
                        )
                        self.decode_error_limit_exceeded.emit(
                            int(self._decode_error_total),
                            threshold,
                        )
                        self._stop = True
                        break
                    continue

            emit_periodic_analysis()

    def _emit_periodic_analysis_if_needed(self):
        now = time.time()
        if now - self._last_emit < ANALYSIS_UPDATE_INTERVAL_SEC:
            return

        snap = self.make_snapshot(copy_arrays=False)
        self.analysis_1hz.emit(snap)
        self._last_emit = now

    def make_snapshot(
        self,
        copy_arrays: bool = False,
        snapshot_fields=_DEFAULT_SNAPSHOT_FIELDS,
    ):
        fields = self._snapshot_fields if snapshot_fields is _DEFAULT_SNAPSHOT_FIELDS else snapshot_fields
        fields = None if fields is None else frozenset(str(field) for field in fields)

        now = time.monotonic()
        elapsed = now - self._decode_rate_last_time
        if elapsed > 0.0:
            decoded_delta = self._decoded_bytes_total - self._decode_rate_last_bytes
            self._decode_rate_bytes_s = float(decoded_delta) / elapsed
            self._decode_rate_words_s = self._decode_rate_bytes_s / 5.0
            self._decode_rate_last_time = now
            self._decode_rate_last_bytes = self._decoded_bytes_total

        queue_backlog = int(self.q.qsize())
        self._queue_backlog_peak_chunks = max(
            self._queue_backlog_peak_chunks,
            queue_backlog,
        )
        if self._native_decoder is not None:
            native = self._native_decoder.snapshot(
                None if fields is None else sorted(fields)
            )
            return DecodeSnapshot(
                adc_hist=native["adc_hist"],
                tdc_hist=native["tdc_hist"],
                adc_ch_hist=native["adc_ch_hist"],
                tdc_ch_hist=native["tdc_ch_hist"],
                adc_bins=self.adc_bins,
                tdc_bins=self.tdc_bins,
                ch_adc_bins=self.ch_adc_bins,
                ch_tdc_bins=self.ch_tdc_bins,
                headers=int(native["headers"]),
                events_fifoA=int(native["events_fifoA"]),
                events_fifoB=int(native["events_fifoB"]),
                trailers=int(native["trailers"]),
                triggers=int(native["triggers"]),
                hits_total=int(native["hits_total"]),
                valid_events=int(native["valid_events"]),
                raw_hit_ch_count=native["raw_hit_ch_count"],
                event_hit_count_hist=native["event_hit_count_hist"],
                overflow_cnt=native["overflow_cnt"],
                decode_err_cnt=native["decode_err_cnt"],
                decode_error_total=int(native["decode_error_total"]),
                err_event_id=int(native["err_event_id"]),
                err_hit_count=int(native["err_hit_count"]),
                err_missing_trailer=int(native["err_missing_trailer"]),
                err_missing_header=int(native["err_missing_header"]),
                abort_burst=int(native["abort_burst"]),
                abort_watchdog=int(native["abort_watchdog"]),
                abort_watchdog_types=tuple(native["abort_watchdog_types"]),
                noise_headers=int(native["noise_headers"]),
                noise_counters=int(native["noise_counters"]),
                noise_error_words=int(native["noise_error_words"]),
                noise_trailers=int(native["noise_trailers"]),
                noise_last_seconds=int(native["noise_last_seconds"]),
                noise_last_total=int(native["noise_last_total"]),
                noise_counter_total=native["noise_counter_total"],
                noise_counter_rate=native["noise_counter_rate"],
                noise_decode_error_count=native["noise_decode_error_count"],
                noise_invalid_channel_count=native["noise_invalid_channel_count"],
                events_buffered=self.buf.size(),
                decoded_bytes_total=int(self._decoded_bytes_total),
                decode_rate_bytes_s=float(self._decode_rate_bytes_s),
                decode_rate_words_s=float(self._decode_rate_words_s),
                queue_backlog_chunks=queue_backlog,
                queue_backlog_peak_chunks=int(self._queue_backlog_peak_chunks),
                queue_capacity_chunks=int(getattr(self.q, "maxsize", 0)),
                decode_backend="C++",
                tdc_shift=int(self.tdc_shift),
                ch_tdc_shift=int(self.ch_tdc_shift),
                tdc_min_ns=float(self.tdc_min_ns),
                tdc_max_ns=float(self.tdc_max_ns),
                ch_tdc_min_ns=float(self.ch_tdc_min_ns),
                ch_tdc_max_ns=float(self.ch_tdc_max_ns),
                tdc_binw_ns=float(self.tdc_binw_ns),
                ch_tdc_binw_ns=float(self.ch_tdc_binw_ns),
            )

        arr = np.array if copy_arrays else (lambda value, copy=False: value)

        def selected(field, value):
            if fields is not None and field not in fields:
                return None
            return arr(value, copy=True)

        snap = DecodeSnapshot(
            adc_hist=selected("adc", self._adc),
            tdc_hist=selected("tdc", self._tdc),
            adc_ch_hist=selected("adc_ch", self._adc_ch),
            tdc_ch_hist=selected("tdc_ch", self._tdc_ch),
            adc_bins=self.adc_bins,
            tdc_bins=self.tdc_bins,
            ch_adc_bins=self.ch_adc_bins,
            ch_tdc_bins=self.ch_tdc_bins,
            headers=self._hdr,
            events_fifoA=self._events_fifoA,
            events_fifoB=self._events_fifoB,
            trailers=self._trl,
            triggers=self._trg,
            hits_total=self._hit_total,
            valid_events=self._valid_events,
            raw_hit_ch_count=selected("ch_hits", self._hit_ch_all),
            event_hit_count_hist=selected("event_hits", self._event_hit_count_hist),
            overflow_cnt=arr(self._ovf, copy=True),
            decode_err_cnt=arr(self._derr, copy=True),
            decode_error_total=int(self._decode_error_total),
            err_event_id=self._err_eid,
            err_hit_count=self._err_hit,
            err_missing_trailer=self._err_missing_trailer,
            err_missing_header=self._err_missing_header,
            abort_burst=self._abort_burst,
            abort_watchdog=self._abort_watchdog,
            abort_watchdog_types=self._ordered_watchdog_types(),
            noise_headers=self._noise_hdr,
            noise_counters=self._noise_ctr,
            noise_error_words=self._noise_err,
            noise_trailers=self._noise_trl,
            noise_last_seconds=self._noise_last_seconds,
            noise_last_total=self._noise_last_total,
            noise_counter_total=selected("ch_hits", self._noise_total),
            noise_counter_rate=selected("ch_hits", self._noise_rate),
            noise_decode_error_count=arr(self._noise_decode_error_count, copy=True),
            noise_invalid_channel_count=arr(self._noise_invalid_channel_count, copy=True),
            events_buffered=self.buf.size(),
            decoded_bytes_total=int(self._decoded_bytes_total),
            decode_rate_bytes_s=float(self._decode_rate_bytes_s),
            decode_rate_words_s=float(self._decode_rate_words_s),
            queue_backlog_chunks=queue_backlog,
            queue_backlog_peak_chunks=int(self._queue_backlog_peak_chunks),
            queue_capacity_chunks=int(getattr(self.q, "maxsize", 0)),
            decode_backend="Python",
            tdc_shift=int(self.tdc_shift),
            ch_tdc_shift=int(self.ch_tdc_shift),
            tdc_min_ns=float(self.tdc_min_ns),
            tdc_max_ns=float(self.tdc_max_ns),
            ch_tdc_min_ns=float(self.ch_tdc_min_ns),
            ch_tdc_max_ns=float(self.ch_tdc_max_ns),
            tdc_binw_ns=float(self.tdc_binw_ns),
            ch_tdc_binw_ns=float(self.ch_tdc_binw_ns),
        )
        return snap
