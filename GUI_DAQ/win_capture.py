"""Detector-data capture for Windows: an in-process port of native_capture/minidaq_capture.cpp.

The Linux GUI runs ``minidaq_capture`` as a subprocess (libpcap, poll, signals).
On Windows ``CaptureThread`` uses ``CaptureEngine`` + ``run_live`` from this
module instead, through Npcap (win_pcap.py).  The output is the same:

* the .dat file: non-empty 5-byte words of every captured frame, in order,
  optionally passed through the isolated-hit filter,
* the same ``MINIDAQ_STATUS`` / ``MINIDAQ_STATS`` / ``MINIDAQ_ERROR`` lines,
  which CaptureThread parses exactly as it parses the native helper's stderr.

The module is also a command-line tool with the native helper's options, so the
native end-to-end tests can run against it (test_win_capture.py):

    python win_capture.py (--device DEV | --input-pcap FILE) --output FILE
                          [--filter BPF] [--isolation-map FILE] [--dispatch-limit N]
"""

from __future__ import annotations

import argparse
import ctypes
import struct
import sys
import time
from typing import BinaryIO, Callable, Iterator, Optional, Tuple

from isolated_hit_filter import IsolatedHitFilter

try:
    import numpy as _np
except Exception:  # pragma: no cover - numpy is a GUI requirement
    _np = None

WORD_SIZE = 5
DATA_START = 14
POSTLOAD = 4
FLUSH_THRESHOLD = 256 * 1024
DEFAULT_SNAPLEN = 65536
DEFAULT_TIMEOUT_MS = 100
DEFAULT_RING_BUFFER_BYTES = 64 << 20
DEFAULT_DISPATCH_LIMIT = 4096
DEFAULT_STATS_INTERVAL_MS = 5000

Line = Callable[[str], None]
Sink = Callable[[bytes], None]


def _is_empty_word(word: bytes) -> bool:
    if word == b"\xff\xff\xff\xff\xff":
        return True
    return word[0] < 0x20 and word[1:] == b"\x00\x00\x00\x00"


class CaptureEngine:
    """Per-packet processing shared by live and offline capture."""

    def __init__(self, isolation_map_path: Optional[str] = None):
        self.isolation = IsolatedHitFilter()
        if isolation_map_path and not self.isolation.load(isolation_map_path):
            raise ValueError(f"invalid_isolation_map path={isolation_map_path}")
        self.batch = bytearray()
        self.total_packets = 0
        self.lost_packets = 0
        self.total_bytes = 0
        self.analysis_dropped_chunks = 0
        self.analysis_dropped_bytes = 0
        self.last_packet = -1

    def handle_packet(self, packet: bytes, wire_length: int) -> None:
        caplen = len(packet)
        if caplen < DATA_START + POSTLOAD + 2:
            return
        packet_number = (packet[caplen - 2] << 8) | packet[caplen - 1]
        if self.last_packet != -1:
            expected = (self.last_packet + 1) & 0xFFFF
            if packet_number != expected:
                self.isolation.packet_loss()
                self.lost_packets += (packet_number - expected) & 0xFFFF
        self.last_packet = packet_number
        self.total_packets += 1

        end = caplen - POSTLOAD
        count = (end - DATA_START) // WORD_SIZE if end > DATA_START else 0
        before = len(self.batch)
        if count:
            payload = packet[DATA_START:DATA_START + count * WORD_SIZE]
            if self.isolation.enabled:
                for offset in range(0, len(payload), WORD_SIZE):
                    word = payload[offset:offset + WORD_SIZE]
                    if not _is_empty_word(word):
                        self.isolation.feed(word, self.batch)
            elif _np is not None:
                words = _np.frombuffer(payload, dtype=_np.uint8).reshape(count, WORD_SIZE)
                idle = (words == 0xFF).all(axis=1)
                filler = (words[:, 0] < 0x20) & (words[:, 1:] == 0).all(axis=1)
                self.batch += words[~(idle | filler)].tobytes()
            else:
                for offset in range(0, len(payload), WORD_SIZE):
                    word = payload[offset:offset + WORD_SIZE]
                    if not _is_empty_word(word):
                        self.batch += word
        self.total_bytes += len(self.batch) - before
        if wire_length != caplen:
            self.isolation.packet_loss()

    def take_batch(self) -> bytes:
        data = bytes(self.batch)
        self.batch.clear()
        return data

    def finish(self) -> bytes:
        before = len(self.batch)
        self.isolation.finish(self.batch)
        self.total_bytes += len(self.batch) - before
        return self.take_batch()

    def stats_line(self, kernel: Tuple[int, int, int] = (0, 0, 0)) -> str:
        iso = self.isolation
        return (
            f"MINIDAQ_STATS packets={self.total_packets} lost={self.lost_packets} "
            f"bytes={self.total_bytes} analysis_dropped_chunks={self.analysis_dropped_chunks} "
            f"analysis_dropped_bytes={self.analysis_dropped_bytes} "
            f"isolated_dropped={iso.dropped_hits} filtered_events={iso.filtered_events} "
            f"preserved_events={iso.preserved_events} filter_rejected_events={iso.rejected_events} "
            f"kernel_received={kernel[0]} kernel_dropped={kernel[1]} interface_dropped={kernel[2]}"
        )


def _write(output: BinaryIO, data: bytes, sink: Optional[Sink]) -> None:
    if not data:
        return
    output.write(data)
    if sink is not None:
        sink(data)


def read_pcap(path: str) -> Iterator[Tuple[bytes, int]]:
    """Yield (captured bytes, original length) from a classic pcap file."""
    with open(path, "rb") as handle:
        header = handle.read(24)
        if len(header) < 24:
            raise ValueError(f"{path} is not a pcap file")
        magic = struct.unpack("<I", header[:4])[0]
        if magic in (0xA1B2C3D4, 0xA1B23C4D):
            endian = "<"
        elif magic in (0xD4C3B2A1, 0x4D3CB2A1):
            endian = ">"
        else:
            raise ValueError("Only classic pcap files are supported, not pcapng")
        record = struct.Struct(endian + "IIII")
        while True:
            raw = handle.read(record.size)
            if not raw:
                return
            if len(raw) < record.size:
                raise ValueError("Truncated pcap packet header")
            _sec, _usec, caplen, length = record.unpack(raw)
            data = handle.read(caplen)
            if len(data) < caplen:
                raise ValueError("Truncated pcap packet")
            yield data, length


def run_offline(pcap_path: str, output_path: str, *, isolation_map: Optional[str] = None,
                line: Line = print, sink: Optional[Sink] = None,
                dispatch_limit: int = DEFAULT_DISPATCH_LIMIT) -> int:
    """Replay a pcap file through the capture pipeline (tests, benchmarks)."""
    try:
        engine = CaptureEngine(isolation_map)
    except ValueError as error:
        line(f"MINIDAQ_ERROR {error}")
        return 2
    with open(output_path, "wb") as output:
        line(f"MINIDAQ_STATUS started source={pcap_path} output={output_path}")
        in_dispatch = 0
        for packet, length in read_pcap(pcap_path):
            engine.handle_packet(packet, length)
            in_dispatch += 1
            if in_dispatch >= dispatch_limit or len(engine.batch) >= FLUSH_THRESHOLD:
                _write(output, engine.take_batch(), sink)
                in_dispatch = 0
        _write(output, engine.take_batch(), sink)
        _write(output, engine.finish(), sink)
    line(engine.stats_line())
    line("MINIDAQ_STATUS stopped exit_code=0")
    return 0


def run_live(device: str, bpf: str, output_path: str, *, isolation_map: Optional[str] = None,
             line: Line = print, sink: Optional[Sink] = None,
             should_stop: Callable[[], bool] = lambda: False,
             timeout_ms: int = DEFAULT_TIMEOUT_MS,
             ring_buffer_bytes: int = DEFAULT_RING_BUFFER_BYTES,
             dispatch_limit: int = DEFAULT_DISPATCH_LIMIT,
             stats_interval_ms: int = DEFAULT_STATS_INTERVAL_MS) -> int:
    """Capture from a live interface until ``should_stop()`` returns True."""
    import win_pcap

    try:
        engine = CaptureEngine(isolation_map)
    except ValueError as error:
        line(f"MINIDAQ_ERROR {error}")
        return 2
    try:
        lib, handle = win_pcap.open_live(device, snaplen=DEFAULT_SNAPLEN, timeout_ms=timeout_ms,
                                         kernel_buffer_bytes=ring_buffer_bytes)
    except win_pcap.PcapError as error:
        line(f"MINIDAQ_ERROR pcap_activate_failed message={error}")
        return 1
    exit_code = 0
    try:
        try:
            win_pcap.set_filter(lib, handle, bpf)
        except win_pcap.PcapError as error:
            line(f"MINIDAQ_ERROR pcap_compile_failed message={error}")
            return 1
        try:
            output = open(output_path, "wb", buffering=4 * 1024 * 1024)
        except OSError as error:
            line(f"MINIDAQ_ERROR output_open_failed errno={error.errno} message={error.strerror} path={output_path}")
            return 1

        def on_packet(_user, header_p, data_p):
            header = header_p.contents
            engine.handle_packet(ctypes.string_at(data_p, header.caplen), header.len)

        callback = win_pcap.PCAP_HANDLER(on_packet)  # keep a reference while capturing
        with output:
            line(f"MINIDAQ_STATUS started source={device} output={output_path}")
            last_stats = time.monotonic()
            while not should_stop():
                result = lib.pcap_dispatch(handle, dispatch_limit, callback, None)
                try:
                    _write(output, engine.take_batch(), sink)
                except OSError as error:
                    line(f"MINIDAQ_ERROR file_write_failed errno={error.errno} message={error.strerror}")
                    exit_code = 1
                    break
                if result < 0:
                    if result != -2:  # PCAP_ERROR_BREAK
                        line(f"MINIDAQ_ERROR pcap_dispatch_failed message={win_pcap._err(lib, handle)}")
                        exit_code = 1
                    break
                now = time.monotonic()
                if (now - last_stats) * 1000.0 >= stats_interval_ms:
                    line(engine.stats_line(win_pcap.stats(lib, handle)))
                    last_stats = now
            _write(output, engine.finish(), sink)
        line(engine.stats_line(win_pcap.stats(lib, handle)))
    finally:
        lib.pcap_close(handle)
    line(f"MINIDAQ_STATUS stopped exit_code={exit_code}")
    return exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--device")
    source.add_argument("--input-pcap")
    parser.add_argument("--output", required=True)
    parser.add_argument("--filter", default="")
    parser.add_argument("--isolation-map")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--ring-buffer-bytes", type=int, default=DEFAULT_RING_BUFFER_BYTES)
    parser.add_argument("--dispatch-limit", type=int, default=DEFAULT_DISPATCH_LIMIT)
    parser.add_argument("--stats-interval-ms", type=int, default=DEFAULT_STATS_INTERVAL_MS)
    args = parser.parse_args(argv)

    def line(text: str) -> None:
        sys.stderr.write(text + "\n")
        sys.stderr.flush()

    stdout = sys.stdout.buffer

    def sink(data: bytes) -> None:
        stdout.write(data)
        stdout.flush()

    if args.input_pcap:
        return run_offline(args.input_pcap, args.output, isolation_map=args.isolation_map,
                           line=line, sink=sink, dispatch_limit=args.dispatch_limit)
    try:
        return run_live(args.device, args.filter, args.output, isolation_map=args.isolation_map,
                        line=line, sink=sink, timeout_ms=args.timeout_ms,
                        ring_buffer_bytes=args.ring_buffer_bytes,
                        dispatch_limit=args.dispatch_limit,
                        stats_interval_ms=args.stats_interval_ms)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
