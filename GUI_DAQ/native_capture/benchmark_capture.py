#!/usr/bin/env python3
"""Compare native and Python MiniDAQ packet extraction on the same pcap."""

from __future__ import annotations

import argparse
import hashlib
import os
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator, Tuple


NATIVE_DIR = Path(__file__).resolve().parent
GUI_DAQ_DIR = NATIVE_DIR.parent
sys.path.insert(0, str(GUI_DAQ_DIR))

from pcap_session import PacketData, PCapSessionHandlerPy  # noqa: E402


PCAP_GLOBAL_HEADER_SIZE = 24
PCAP_PACKET_HEADER_SIZE = 16
PYTHON_DISPATCH_PACKET_LIMIT = 4096


def generate_pcap(path: Path, packet_count: int, words_per_packet: int) -> None:
    with path.open("wb") as output:
        output.write(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
        words = b"".join(
            bytes((0x20 + (index % 32), index & 0xFF, index >> 8, 0x55, 0xAA))
            for index in range(words_per_packet)
        )
        for packet_number in range(packet_count):
            packet = (
                b"\x00" * 14
                + words
                + b"\x00\x00"
                + struct.pack(">H", packet_number & 0xFFFF)
            )
            output.write(
                struct.pack(
                    "<IIII",
                    packet_number,
                    0,
                    len(packet),
                    len(packet),
                )
            )
            output.write(packet)


def pcap_packets(path: Path) -> Iterator[bytes]:
    with path.open("rb") as source:
        global_header = source.read(PCAP_GLOBAL_HEADER_SIZE)
        if len(global_header) != PCAP_GLOBAL_HEADER_SIZE:
            raise RuntimeError(f"{path} is not a complete pcap file")

        magic = global_header[:4]
        if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
            endian = "<"
        elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
            endian = ">"
        else:
            raise RuntimeError("Only classic pcap files are supported, not pcapng")

        packet_header = struct.Struct(f"{endian}IIII")
        while True:
            raw_header = source.read(PCAP_PACKET_HEADER_SIZE)
            if not raw_header:
                return
            if len(raw_header) != PCAP_PACKET_HEADER_SIZE:
                raise RuntimeError("Truncated pcap packet header")
            _, _, captured_length, _ = packet_header.unpack(raw_header)
            packet = source.read(captured_length)
            if len(packet) != captured_length:
                raise RuntimeError("Truncated pcap packet")
            yield packet


def new_python_session() -> PCapSessionHandlerPy:
    session = PCapSessionHandlerPy.__new__(PCapSessionHandlerPy)
    session.checkPackets = True
    session.data = PacketData()
    session.totalPackets = 0
    session.totalBufferedBytes = 0
    return session


def run_python(pcap_path: Path, output_path: Path) -> Tuple[float, int, int]:
    session = new_python_session()
    started = time.perf_counter()
    with output_path.open("wb") as output:
        for packet_index, packet in enumerate(pcap_packets(pcap_path), start=1):
            session._handle_one_packet(packet)
            if packet_index % PYTHON_DISPATCH_PACKET_LIMIT == 0:
                output.write(session.data.packetBuffer)
                session.data.packetBuffer.clear()
        output.write(session.data.packetBuffer)
    elapsed = time.perf_counter() - started
    return elapsed, session.totalPackets, session.totalBufferedBytes


def run_native(
    executable: Path, pcap_path: Path, output_path: Path
) -> Tuple[float, int, int]:
    started = time.perf_counter()
    result = subprocess.run(
        [
            str(executable),
            "--input-pcap",
            str(pcap_path),
            "--output",
            str(output_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(
            f"Native capture exited with {result.returncode}:\n{result.stderr}"
        )

    stats_line = next(
        line for line in reversed(result.stderr.splitlines())
        if line.startswith("MINIDAQ_STATS ")
    )
    stats = {}
    for field in stats_line.split()[1:]:
        key, separator, value = field.partition("=")
        if separator:
            stats[key] = int(value)
    return elapsed, stats["packets"], stats["bytes"]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def format_result(
    label: str, elapsed_values: list[float], packets: int, output_bytes: int
) -> str:
    elapsed = statistics.median(elapsed_values)
    return (
        f"{label:8} {elapsed:8.3f} s  "
        f"{packets / elapsed:12,.0f} packets/s  "
        f"{output_bytes / elapsed / 1_000_000:9.2f} MB/s"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcap", type=Path, help="Classic pcap input file")
    parser.add_argument("--packets", type=int, default=200_000)
    parser.add_argument("--words-per-packet", type=int, default=50)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument(
        "--native",
        type=Path,
        default=NATIVE_DIR / "minidaq_capture",
    )
    args = parser.parse_args()

    if args.iterations < 1:
        parser.error("--iterations must be at least 1")
    if not args.native.is_file():
        parser.error(f"native helper not found: {args.native}; run make first")

    with tempfile.TemporaryDirectory(prefix="minidaq_capture_bench_") as temp_dir:
        temp = Path(temp_dir)
        pcap_path = args.pcap
        if pcap_path is None:
            pcap_path = temp / "benchmark.pcap"
            print(
                f"Generating {args.packets:,} packets with "
                f"{args.words_per_packet} words/packet..."
            )
            generate_pcap(pcap_path, args.packets, args.words_per_packet)

        native_times = []
        python_times = []
        native_packets = python_packets = 0
        native_bytes = python_bytes = 0
        native_output = temp / "native.dat"
        python_output = temp / "python.dat"

        for iteration in range(args.iterations):
            native_elapsed, native_packets, native_bytes = run_native(
                args.native, pcap_path, native_output
            )
            python_elapsed, python_packets, python_bytes = run_python(
                pcap_path, python_output
            )
            native_times.append(native_elapsed)
            python_times.append(python_elapsed)
            print(
                f"Iteration {iteration + 1}: native={native_elapsed:.3f}s "
                f"python={python_elapsed:.3f}s"
            )

        if (
            native_packets != python_packets
            or native_bytes != python_bytes
            or file_hash(native_output) != file_hash(python_output)
        ):
            print("ERROR: native and Python outputs do not match", file=sys.stderr)
            return 1

        print("\nOutput parity: PASS")
        print(format_result("Native", native_times, native_packets, native_bytes))
        print(format_result("Python", python_times, python_packets, python_bytes))
        speedup = statistics.median(python_times) / statistics.median(native_times)
        print(f"Native speedup: {speedup:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
