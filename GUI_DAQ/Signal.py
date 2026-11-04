# Signal.py
# MiniDAQ signal definitions + decoder
# Hit includes spatial info; Overflow / DecodeError include tdcid

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Iterator, Protocol, Tuple

WORD_SIZE = 5


class SignalType(IntEnum):
    HIT = 1
    TRIGGER = 2
    EVENT_HEADER = 3
    EVENT_TRAILER = 4
    OVERFLOW = 5
    DECODE_ERROR = 6
    ABORT = 7
    TDC_HEADER = 8
    TDC_TRAILER = 9
    NOISE_COUNTER_HEADER = 10
    NOISE_COUNTER = 11
    NOISE_COUNTER_TRAILER = 12
    NOISE_ERROR_COUNTER = 13
    UNKNOWN = 99


# ---- geometry hook ----

class GeometryLike(Protocol):
    def wire_center_from_hit(
        self, tdc_id: int, channel_id: int
    ) -> Tuple[float, float, int, int]:
        ...


# ---------------- payloads ----------------

@dataclass(frozen=True)
class Hit:
    csmid: int
    tdcid: int
    ch: int
    mode: int
    ledge: int
    width: int

    x: float
    y: float
    layer: int
    col: int
    chamber_id: int


@dataclass(frozen=True)
class EventHeader:
    event_id20: int
    rd_bank_sel: int
    event_id12: int = 0
    chamber_id: int = 0
    chamber_event_id: int = 0
    event_id_ext: int = 0
    trigger_overflow: int = 0
    trigger_ledge: Optional[int] = None


@dataclass(frozen=True)
class EventTrailer:
    event_id20: int
    trigger_count: int
    hit_count: int
    event_id12: int = 0
    chamber_id: int = 0
    chamber_event_id: int = 0
    tdc_header_count: int = 0
    tdc_trailer_count: int = 0
    header_count_error: int = 0
    trailer_count_error: int = 0


@dataclass(frozen=True)
class Trigger:
    raw: int
    overflow: int
    event_count: int
    ledge: int


@dataclass(frozen=True)
class TDCHeader:
    tdcid: int
    event_id: int
    trigger_bcid: int
    raw: int


@dataclass(frozen=True)
class TDCTrailer:
    tdcid: int
    trigger_lost: int
    timeout: int
    hit_count: int
    raw: int


@dataclass(frozen=True)
class Overflow:
    tdcid: int
    raw: int


@dataclass(frozen=True)
class DecodeError:
    tdcid: int
    raw: int
    reason: str = "decode_error"
    channel: Optional[int] = None
    mode: Optional[int] = None
    ledge: Optional[int] = None
    width: Optional[int] = None


@dataclass(frozen=True)
class AbortMarker:
    raw: int
    kind: str
    threshold: Optional[int] = None
    watchdog_count: Optional[int] = None
    watchdog_state_bits: Optional[int] = None
    watchdog_state_name: Optional[str] = None


@dataclass(frozen=True)
class NoiseCounterHeader:
    csmid: int
    tdcid: int
    tdc_local: int
    seconds_elapsed: int


@dataclass(frozen=True)
class NoiseCounter:
    csmid: int
    tdcid: int
    tdc_local: int
    ch: int
    total_count: int


@dataclass(frozen=True)
class NoiseErrorCounter:
    csmid: int
    tdcid: int
    tdc_local: int
    kind: int
    total_count: int


@dataclass(frozen=True)
class NoiseCounterTrailer:
    csmid: int
    tdcid: int
    tdc_local: int
    total_count_this_tdc: int


# ---------------- Signal ----------------

@dataclass(frozen=True)
class Signal:
    type: SignalType
    raw40: int

    hit: Optional[Hit] = None
    trigger: Optional[Trigger] = None
    header: Optional[EventHeader] = None
    trailer: Optional[EventTrailer] = None
    tdc_header: Optional[TDCHeader] = None
    tdc_trailer: Optional[TDCTrailer] = None
    overflow: Optional[Overflow] = None
    error: Optional[DecodeError] = None
    abort: Optional[AbortMarker] = None
    noise_header: Optional[NoiseCounterHeader] = None
    noise_counter: Optional[NoiseCounter] = None
    noise_error: Optional[NoiseErrorCounter] = None
    noise_trailer: Optional[NoiseCounterTrailer] = None


# ---------------- decoder ----------------

_HDR = 0xA
_TRL = 0xC
_TRG = 0xE
_OVF_MAGIC = 0xE8
_TDC_HDR_MAGIC = 0xF8
_TDC_TRL_MAGIC = 0xF0
_NOISE_HDR = 0xD
_NOISE_COUNTER = 0x9
_NOISE_ERROR = 0xF
_NOISE_TRL = 0xE
_NOISE_TDC_PER_CSM = 20
_ERR_IDENT = 0xF7
_ERR_MAGIC = 0xF7411111
_ABORT_TAG = 0xB
_ABORT_SUBTYPE_SHIFT = 32
_ABORT_SUBTYPE_MASK = 0xF
_BURST_ABORT_SUBTYPE = 0xA
_WATCHDOG_ABORT_SUBTYPE = 0xD
_BURST_ABORT_MAGIC_SHIFT = 10
_BURST_ABORT_MAGIC_MASK = (1 << 22) - 1
_BURST_ABORT_MAGIC = 0x2AAAAA
_BURST_ABORT_THRESHOLD_MASK = (1 << 10) - 1
_WATCHDOG_ABORT_STATE_SHIFT = 21
_WATCHDOG_ABORT_STATE_MASK = (1 << 11) - 1
_WATCHDOG_ABORT_COUNT_MASK = (1 << 21) - 1
_WATCHDOG_ABORT_LEGACY_MAGIC = 0x6DB
_MAX_TDC_CHANNELS = 24

_WATCHDOG_STATE_NAMES = {
    1 << 0: "IDLE",
    1 << 1: "TRIG_ONLY",
    1 << 2: "START_EVENT",
    1 << 3: "CAPTURE_PRE",
    1 << 4: "SEND_HEAD",
    1 << 5: "FLUSH_BUF",
    1 << 6: "STREAM_LIVE",
    1 << 7: "SEND_TRAIL",
    1 << 8: "ABORT_MARK",
    1 << 9: "ABORT_TRAIL",
    1 << 10: "ABORT_CLEAN",
}


def _decode_tdcid(w: int) -> int:
    """Shared TDC ID extraction."""
    csmid = (w >> 37) & 0x7
    tdc_local = (w >> 32) & 0x1F
    return tdc_local + csmid * 20


def _decode_watchdog_state_name(state_bits: int) -> Optional[str]:
    return _WATCHDOG_STATE_NAMES.get(state_bits)


def _decode_noise_counter_header(w: int) -> Signal:
    csmid = (w >> 35) & 0x1
    tdc_local = (w >> 30) & 0x1F
    return Signal(
        SignalType.NOISE_COUNTER_HEADER,
        w,
        noise_header=NoiseCounterHeader(
            csmid=csmid,
            tdcid=tdc_local + csmid * _NOISE_TDC_PER_CSM,
            tdc_local=tdc_local,
            seconds_elapsed=w & ((1 << 30) - 1),
        ),
    )


def _decode_noise_counter(w: int, csmid: int, tdc_local: int) -> Signal:
    return Signal(
        SignalType.NOISE_COUNTER,
        w,
        noise_counter=NoiseCounter(
            csmid=csmid,
            tdcid=tdc_local + csmid * _NOISE_TDC_PER_CSM,
            tdc_local=tdc_local,
            ch=(w >> 31) & 0x1F,
            total_count=w & ((1 << 31) - 1),
        ),
    )


def _decode_noise_error(w: int, csmid: int, tdc_local: int) -> Signal:
    return Signal(
        SignalType.NOISE_ERROR_COUNTER,
        w,
        noise_error=NoiseErrorCounter(
            csmid=csmid,
            tdcid=tdc_local + csmid * _NOISE_TDC_PER_CSM,
            tdc_local=tdc_local,
            kind=(w >> 31) & 0x1F,
            total_count=w & ((1 << 31) - 1),
        ),
    )


def _decode_noise_counter_trailer(w: int) -> Signal:
    csmid = (w >> 35) & 0x1
    tdc_local = (w >> 30) & 0x1F
    return Signal(
        SignalType.NOISE_COUNTER_TRAILER,
        w,
        noise_trailer=NoiseCounterTrailer(
            csmid=csmid,
            tdcid=tdc_local + csmid * _NOISE_TDC_PER_CSM,
            tdc_local=tdc_local,
            total_count_this_tdc=w & ((1 << 30) - 1),
        ),
    )


def _decode_hit_word(w: int, geo: Optional[GeometryLike] = None) -> Signal:
    low32 = w & 0xFFFFFFFF
    if low32 == 0:
        return Signal(SignalType.UNKNOWN, w)

    csmid = (w >> 37) & 0x7
    tdcid = _decode_tdcid(w)
    ch = (w >> 27) & 0x1F
    mode = (w >> 25) & 0x3
    ledge = (w >> 8) & 0x1FFFF
    width = w & 0xFF

    if ch >= _MAX_TDC_CHANNELS:
        return Signal(
            SignalType.DECODE_ERROR,
            w,
            error=DecodeError(
                tdcid=tdcid,
                raw=w,
                reason="invalid_hit_channel",
                channel=ch,
                mode=mode,
                ledge=ledge,
                width=width,
            ),
        )

    x = -1.0
    y = -1.0
    layer = -1
    col = -1
    cid = -1
    if geo is not None:
        try:
            x, y, layer, col = geo.wire_center_from_hit(tdcid, ch)
        except Exception:
            pass

    if geo is not None and hasattr(geo, "chamber_id_from_tdcid"):
        try:
            cid = int(geo.chamber_id_from_tdcid(tdcid))
        except Exception:
            cid = -1

    return Signal(
        SignalType.HIT,
        w,
        hit=Hit(
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
            chamber_id=cid,
        ),
    )


def decode_word5(
    word5: bytes,
    geo: Optional[GeometryLike] = None,
    acquisition_mode: int = 0,
    noise_test_mode: int = 0,
) -> Signal:
    if len(word5) != WORD_SIZE:
        raise ValueError("invalid word size")

    w = int.from_bytes(word5, "big")
    top4 = (w >> 36) & 0xF

    if int(noise_test_mode) & 0x1:
        return _decode_hit_word(w, geo)

    if top4 == _NOISE_HDR and int(acquisition_mode) == 1:
        return _decode_noise_counter_header(w)

    # ---------- Abort marker ----------
    if top4 == _ABORT_TAG:
        abort_subtype = (w >> _ABORT_SUBTYPE_SHIFT) & _ABORT_SUBTYPE_MASK
        if (
            abort_subtype == _BURST_ABORT_SUBTYPE
            and ((w >> _BURST_ABORT_MAGIC_SHIFT) & _BURST_ABORT_MAGIC_MASK) == _BURST_ABORT_MAGIC
        ):
            return Signal(
                SignalType.ABORT,
                w,
                abort=AbortMarker(
                    raw=w,
                    kind="burst",
                    threshold=w & _BURST_ABORT_THRESHOLD_MASK,
                ),
            )

        if (
            abort_subtype == _WATCHDOG_ABORT_SUBTYPE
        ):
            watchdog_state_bits = (w >> _WATCHDOG_ABORT_STATE_SHIFT) & _WATCHDOG_ABORT_STATE_MASK
            watchdog_state_name = _decode_watchdog_state_name(watchdog_state_bits)
            if watchdog_state_bits == _WATCHDOG_ABORT_LEGACY_MAGIC:
                watchdog_state_bits = None
                watchdog_state_name = None
            return Signal(
                SignalType.ABORT,
                w,
                abort=AbortMarker(
                    raw=w,
                    kind="watchdog",
                    watchdog_count=w & _WATCHDOG_ABORT_COUNT_MASK,
                    watchdog_state_bits=watchdog_state_bits,
                    watchdog_state_name=watchdog_state_name,
                ),
            )

    # ---------- Event header ----------
    if top4 == _HDR:
        if int(acquisition_mode) == 1:
            event_id20 = (w >> 16) & 0xFFFFF
            chamber_id = (event_id20 >> 19) & 0x1
            chamber_event_id = event_id20 & 0x7FFFF
            return Signal(
                SignalType.EVENT_HEADER,
                w,
                header=EventHeader(
                    event_id20=event_id20,
                    rd_bank_sel=(w >> 15) & 0x1,
                    event_id12=event_id20 & 0xFFF,
                    chamber_id=chamber_id,
                    chamber_event_id=chamber_event_id,
                    event_id_ext=(event_id20 >> 12) & 0xFF,
                ),
            )

        # Triggered-format MiniDAQ header:
        #   39..36 type, 35 trigger overflow, 34..29 EventIDext,
        #   28..17 EventID, 16..0 trigger leading edge.
        event_id12 = (w >> 17) & 0xFFF
        event_id_ext = (w >> 29) & 0x3F
        return Signal(
            SignalType.EVENT_HEADER,
            w,
            header=EventHeader(
                event_id20=(w >> 17) & 0x3FFFF,
                rd_bank_sel=0,
                event_id12=event_id12,
                event_id_ext=event_id_ext,
                trigger_overflow=(w >> 35) & 0x1,
                trigger_ledge=w & 0x1FFFF,
            ),
        )

    # ---------- Event trailer ----------
    if top4 == _TRL:
        if int(acquisition_mode) == 1:
            event_id20 = (w >> 16) & 0xFFFFF
            chamber_id = (event_id20 >> 19) & 0x1
            chamber_event_id = event_id20 & 0x7FFFF
            return Signal(
                SignalType.EVENT_TRAILER,
                w,
                trailer=EventTrailer(
                    event_id20=event_id20,
                    trigger_count=(w >> 10) & 0x3F,
                    hit_count=w & 0x3FF,
                    event_id12=event_id20 & 0xFFF,
                    chamber_id=chamber_id,
                    chamber_event_id=chamber_event_id,
                ),
            )

        # Triggered-format MiniDAQ trailer:
        #   35..32 TDC header count, 31..28 TDC trailer count,
        #   27..16 EventID, 15/14 count error flags, 9..0 hit count.
        event_id12 = (w >> 16) & 0xFFF
        return Signal(
            SignalType.EVENT_TRAILER,
            w,
            trailer=EventTrailer(
                event_id20=event_id12,
                trigger_count=0,
                hit_count=w & 0x3FF,
                event_id12=event_id12,
                tdc_header_count=(w >> 32) & 0xF,
                tdc_trailer_count=(w >> 28) & 0xF,
                header_count_error=(w >> 15) & 0x1,
                trailer_count_error=(w >> 14) & 0x1,
            ),
        )

    # ---------- Trigger ----------
    if top4 == _TRG and ((w >> 30) & 0x3F) == 0:
        return Signal(
            SignalType.TRIGGER,
            w,
            trigger=Trigger(
                raw=w,
                overflow=(w >> 29) & 0x1,
                event_count=(w >> 17) & 0xFFF,
                ledge=w & 0x1FFFF,
            ),
        )

    low32 = w & 0xFFFFFFFF
    ident = (w >> 24) & 0xFF

    # ---------- TDC header / trailer ----------
    if ident == _TDC_HDR_MAGIC:
        tdcid = _decode_tdcid(w)
        return Signal(
            SignalType.TDC_HEADER,
            w,
            tdc_header=TDCHeader(
                tdcid=tdcid,
                event_id=(w >> 12) & 0xFFF,
                trigger_bcid=w & 0xFFF,
                raw=w,
            ),
        )

    if ident == _TDC_TRL_MAGIC:
        tdcid = _decode_tdcid(w)
        return Signal(
            SignalType.TDC_TRAILER,
            w,
            tdc_trailer=TDCTrailer(
                tdcid=tdcid,
                trigger_lost=(w >> 11) & 0x1,
                timeout=(w >> 10) & 0x1,
                hit_count=w & 0x3FF,
                raw=w,
            ),
        )

    # ---------- Decode error ----------
    if low32 == _ERR_MAGIC or ident == _ERR_IDENT:
        tdcid = _decode_tdcid(w)
        return Signal(
            SignalType.DECODE_ERROR,
            w,
            error=DecodeError(tdcid=tdcid, raw=w),
        )

    # ---------- Overflow ----------
    if ident == _OVF_MAGIC:
        tdcid = _decode_tdcid(w)
        return Signal(
            SignalType.OVERFLOW,
            w,
            overflow=Overflow(tdcid=tdcid, raw=w),
        )

    # ---------- Empty TDC filler ----------
    # Triggered-mode packets can contain one empty word per TDC, e.g.
    # 0000000000, 0100000000, 0200000000, 0300000000. These carry only the
    # TDC id bits and have channel/mode/ledge/width all zero, so they are not
    # physical hits and must not enter ADC/TDC spectra.
    if low32 == 0:
        return Signal(SignalType.UNKNOWN, w)

    # ---------- Hit ----------
    return _decode_hit_word(w, geo)


class StreamDecoder:
    def __init__(
        self,
        geo: Optional[GeometryLike] = None,
        acquisition_mode: int = 0,
        noise_test_mode: int = 0,
    ):
        self.geo = geo
        self.acquisition_mode = int(acquisition_mode)
        self.noise_test_mode = int(noise_test_mode)
        self._carry = b""
        self._in_noise_counter_packet = False
        self._noise_csmid = 0
        self._noise_tdc_local = 0

    def decode(self, buf: bytes) -> Iterator[Signal]:
        buf = self._carry + bytes(buf)
        n = len(buf) // WORD_SIZE
        n_take = n * WORD_SIZE
        self._carry = bytes(buf[n_take:])

        for i in range(n):
            word5 = buf[i * WORD_SIZE : (i + 1) * WORD_SIZE]
            w = int.from_bytes(word5, "big")
            top4 = (w >> 36) & 0xF

            if self.noise_test_mode & 0x1:
                yield _decode_hit_word(w, self.geo)
                continue

            if self._in_noise_counter_packet:
                if top4 == _NOISE_TRL:
                    self._in_noise_counter_packet = False
                    yield _decode_noise_counter_trailer(w)
                elif top4 == _NOISE_COUNTER:
                    yield _decode_noise_counter(w, self._noise_csmid, self._noise_tdc_local)
                elif top4 == _NOISE_ERROR:
                    yield _decode_noise_error(w, self._noise_csmid, self._noise_tdc_local)
                else:
                    yield Signal(SignalType.UNKNOWN, w)
                continue

            if self.acquisition_mode == 1 and top4 == _NOISE_HDR:
                self._in_noise_counter_packet = True
                sig = _decode_noise_counter_header(w)
                self._noise_csmid = int(sig.noise_header.csmid)
                self._noise_tdc_local = int(sig.noise_header.tdc_local)
                yield sig
                continue

            yield decode_word5(
                word5,
                geo=self.geo,
                acquisition_mode=self.acquisition_mode,
                noise_test_mode=self.noise_test_mode,
            )


def decode_stream(
    buf: bytes,
    geo: Optional[GeometryLike] = None,
    acquisition_mode: int = 0,
    noise_test_mode: int = 0,
) -> Iterator[Signal]:
    yield from StreamDecoder(
        geo=geo,
        acquisition_mode=acquisition_mode,
        noise_test_mode=noise_test_mode,
    ).decode(buf)
