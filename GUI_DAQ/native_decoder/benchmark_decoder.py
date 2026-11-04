#!/usr/bin/env python3
"""Check Python/C++ decoder parity and compare ordered decode throughput."""

from __future__ import annotations

import argparse
import os
import queue
import sys
import time
from pathlib import Path

import numpy as np


GUI_DAQ_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUI_DAQ_DIR))

from DecodeThread import DecodeThread, EventBuffer  # noqa: E402


ARRAY_FIELDS = (
    "adc_hist",
    "tdc_hist",
    "adc_ch_hist",
    "tdc_ch_hist",
    "raw_hit_ch_count",
    "event_hit_count_hist",
    "overflow_cnt",
    "decode_err_cnt",
    "noise_counter_total",
    "noise_counter_rate",
    "noise_decode_error_count",
    "noise_invalid_channel_count",
)

COUNTER_FIELDS = (
    "headers",
    "events_fifoA",
    "events_fifoB",
    "trailers",
    "triggers",
    "hits_total",
    "valid_events",
    "decode_error_total",
    "err_event_id",
    "err_hit_count",
    "err_missing_trailer",
    "err_missing_header",
    "abort_burst",
    "abort_watchdog",
    "noise_headers",
    "noise_counters",
    "noise_error_words",
    "noise_trailers",
    "noise_last_seconds",
    "noise_last_total",
)


class BenchmarkGeometry:
    def chamber_id_from_tdcid(self, tdc_id: int) -> int:
        return int(tdc_id) // 2

    def wire_center_from_hit(self, tdc_id: int, channel_id: int):
        return float(tdc_id), float(channel_id), int(tdc_id) % 8, int(channel_id)


def word(value: int) -> bytes:
    return int(value & ((1 << 40) - 1)).to_bytes(5, "big")


def hit(tdc: int, channel: int, ledge: int, width: int, mode: int = 0) -> bytes:
    return word(
        ((tdc & 0x1F) << 32)
        | ((channel & 0x1F) << 27)
        | ((mode & 0x3) << 25)
        | ((ledge & 0x1FFFF) << 8)
        | (width & 0xFF)
    )


def tdc_header(tdc: int, event_id: int) -> bytes:
    return word(((tdc & 0x1F) << 32) | (0xF8 << 24) | ((event_id & 0xFFF) << 12))


def tdc_trailer(tdc: int, hit_count: int) -> bytes:
    return word(((tdc & 0x1F) << 32) | (0xF0 << 24) | (hit_count & 0x3FF))


def triggered_event(event_id: int, event_hits: int) -> bytes:
    trigger_ledge = (1000 + event_id * 3) & 0x1FFFF
    output = [
        word((0xA << 36) | ((event_id & 0xFFF) << 17) | trigger_ledge),
        tdc_header(0, event_id),
    ]
    for index in range(event_hits):
        output.append(
            hit(
                tdc=index % 4,
                channel=index % 24,
                ledge=(trigger_ledge + 20 + index) & 0x1FFFF,
                width=30 + index,
            )
        )
    output.extend(
        (
            tdc_trailer(0, event_hits),
            word(
                (0xC << 36)
                | (1 << 32)
                | (1 << 28)
                | ((event_id & 0xFFF) << 16)
                | event_hits
            ),
        )
    )
    return b"".join(output)


def triggerless_event(event_id: int, event_hits: int) -> bytes:
    output = [word((0xA << 36) | ((event_id & 0xFFFFF) << 16))]
    for index in range(event_hits):
        output.append(
            hit(
                tdc=index % 4,
                channel=index % 24,
                ledge=(2000 + event_id * 5 + index) & 0x1FFFF,
                width=40 + index,
            )
        )
    output.append(
        word(
            (0xC << 36)
            | ((event_id & 0xFFFFF) << 16)
            | (1 << 10)
            | event_hits
        )
    )
    return b"".join(output)


def noise_packet(seconds: int, total: int, decode_errors: int = 0, invalid_channels: int = 0) -> bytes:
    return b"".join(
        (
            word((0xD << 36) | (seconds & ((1 << 30) - 1))),
            word((0x9 << 36) | (3 << 31) | total),
            word((0xF << 36) | decode_errors),
            word((0xF << 36) | (1 << 31) | invalid_channels),
            word((0xE << 36) | total),
        )
    )


def diagnostics(mode: int) -> bytes:
    output = []
    if mode == 1:
        header = lambda event_id: word((0xA << 36) | ((event_id & 0xFFFFF) << 16))
        trailer = lambda event_id, count: word(
            (0xC << 36) | ((event_id & 0xFFFFF) << 16) | count
        )
    else:
        header = lambda event_id: word(
            (0xA << 36) | ((event_id & 0xFFF) << 17) | 1000
        )
        trailer = lambda event_id, count: word(
            (0xC << 36) | ((event_id & 0xFFF) << 16) | count
        )

    output.append(trailer(800, 0))  # missing header
    output.append(header(801))
    output.append(header(802))  # missing trailer
    output.append(trailer(803, 0))  # event-id mismatch
    output.extend((header(804), hit(0, 0, 1020, 20), trailer(804, 0)))
    output.append(word(0xE8 << 24))  # overflow
    output.append(word(0xF7411111))  # decode error
    output.append(hit(0, 24, 100, 10))  # invalid channel decode error
    output.append(word((0xB << 36) | (0xA << 32) | (0x2AAAAA << 10) | 12))
    output.append(word((0xB << 36) | (0xD << 32) | ((1 << 4) << 21) | 34))
    return b"".join(output)


def make_stream(mode: int, event_count: int, event_hits: int) -> bytes:
    event_builder = triggerless_event if mode == 1 else triggered_event
    if mode == 1:
        # Alternate chamber IDs while keeping a monotonic sequence within each chamber.
        event_ids = [((index & 0x1) << 19) | (index >> 1) for index in range(event_count)]
    else:
        event_ids = range(event_count)
    output = [event_builder(event_id, event_hits) for event_id in event_ids]
    output.append(diagnostics(mode))
    if mode == 1:
        output.append(noise_packet(10, 1234, 2, 1))
        output.append(noise_packet(12, 1434, 5, 3))
    return b"".join(output)


def run_decoder(data: bytes, mode: int, event_count: int, use_native: bool):
    analysis_q: "queue.Queue[bytes]" = queue.Queue(maxsize=4096)
    event_buffer = EventBuffer(max_events=event_count + 10)
    decoder = DecodeThread(
        analysis_q=analysis_q,
        event_buffer=event_buffer,
        geo=BenchmarkGeometry(),
        acquisition_mode=mode,
        use_native_decoder=use_native,
    )

    started = time.perf_counter()
    decoder.start()
    offsets = (17, 511, 4099, 65537)
    cursor = 0
    split_index = 0
    while cursor < len(data):
        size = offsets[split_index % len(offsets)]
        analysis_q.put(data[cursor : cursor + size])
        cursor += size
        split_index += 1

    deadline = time.monotonic() + 120.0
    while time.monotonic() < deadline:
        snapshot = decoder.make_snapshot(copy_arrays=True)
        if int(snapshot.valid_events) == event_count:
            break
        time.sleep(0.005)
    else:
        decoder.stop()
        decoder.wait(5000)
        raise RuntimeError(
            f"decoder timeout: backend={snapshot.decode_backend} "
            f"valid={snapshot.valid_events}/{event_count}"
        )

    elapsed = time.perf_counter() - started
    decoder.stop()
    if not decoder.wait(5000):
        raise RuntimeError(f"decoder did not stop: backend={snapshot.decode_backend}")
    snapshot = decoder.make_snapshot(copy_arrays=True)

    events = []
    while True:
        event = event_buffer.pop()
        if event is None:
            break
        events.append(
            (
                event.event_id20,
                event.event_id12,
                event.chamber_id,
                event.chamber_event_id,
                event.trigger_count,
                event.hit_count_expected,
                event.trigger_ledge,
                tuple(
                    (
                        chamber_id,
                        tuple(
                            (
                                hit.csmid,
                                hit.tdcid,
                                hit.ch,
                                hit.mode,
                                hit.ledge,
                                hit.width,
                                hit.x,
                                hit.y,
                                hit.layer,
                                hit.col,
                                hit.chamber_id,
                            )
                            for hit in block.hits
                        ),
                    )
                    for chamber_id, block in sorted(event.chambers.items())
                ),
            )
        )
    return elapsed, snapshot, events


def check_parity(python_snapshot, native_snapshot, python_events, native_events) -> None:
    for field in ARRAY_FIELDS:
        left = np.asarray(getattr(python_snapshot, field))
        right = np.asarray(getattr(native_snapshot, field))
        if not np.array_equal(left, right):
            difference = int(np.count_nonzero(left != right))
            raise RuntimeError(f"array mismatch: {field}, differing_bins={difference}")

    for field in COUNTER_FIELDS:
        left = int(getattr(python_snapshot, field))
        right = int(getattr(native_snapshot, field))
        if left != right:
            raise RuntimeError(f"counter mismatch: {field}, python={left}, native={right}")

    if python_events != native_events:
        raise RuntimeError("completed event metadata mismatch")
    if sorted(python_snapshot.abort_watchdog_types) != sorted(native_snapshot.abort_watchdog_types):
        raise RuntimeError("watchdog abort type mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=20_000)
    parser.add_argument("--hits-per-event", type=int, default=8)
    parser.add_argument("--mode", choices=("both", "triggered", "triggerless"), default="both")
    args = parser.parse_args()

    modes = []
    if args.mode in ("both", "triggered"):
        modes.append((0, "triggered"))
    if args.mode in ("both", "triggerless"):
        modes.append((1, "triggerless"))

    for mode, label in modes:
        data = make_stream(mode, args.events, args.hits_per_event)
        python_time, python_snapshot, python_events = run_decoder(
            data, mode, args.events, use_native=False
        )
        native_time, native_snapshot, native_events = run_decoder(
            data, mode, args.events, use_native=True
        )
        check_parity(python_snapshot, native_snapshot, python_events, native_events)
        print(
            f"{label}: parity=PASS bytes={len(data):,} events={args.events:,} "
            f"python={python_time:.3f}s native={native_time:.3f}s "
            f"speedup={python_time / native_time:.2f}x"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
