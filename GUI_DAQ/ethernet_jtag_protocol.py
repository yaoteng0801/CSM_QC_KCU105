"""Host side of the MiniDAQ raw-Ethernet FPGA programming protocol.

The firmware accepts one 1408-byte bitstream chunk at a time.  Each DATA frame
is protected by an application CRC32 in addition to the Ethernet FCS.  The host
does not advance until it receives an SCA_ACK, which means the chunk has been
shifted through the GBT-SCA JTAG controller and its rolling file CRC agrees.

Raw packet I/O is delegated to ``native_capture/ethernet_frame_io``.  That
small helper can be granted CAP_NET_RAW/CAP_NET_ADMIN without granting those
capabilities to the Python interpreter or the entire GUI.

On Windows the helper is not built; ``interface_mac`` and ``NativeEthernetPort``
are replaced at the end of this module by the in-process Npcap implementation
in ``win_pcap.py`` (same interface).
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import selectors
import socket
import struct
import subprocess
import sys
import time
from typing import List, Optional
import zlib

if sys.platform != "win32":
    import fcntl


FPGA_MAC = bytes.fromhex("020000c70501")
PROGRAM_ETHERTYPE = 0x88B5
PROTOCOL_MAGIC = b"MDJ1"
PROTOCOL_VERSION = 0x01
MAX_CHUNK_BYTES = 1408

MSG_DATA = 0x01
MSG_ABORT = 0x02
MSG_IDCODE_READ = 0x03
MSG_RX_ACK = 0x81
MSG_SCA_ACK = 0x82
MSG_IDCODE_ACK = 0x83
MSG_RX_NACK = 0xE1
MSG_SCA_NACK = 0xE2
MSG_IDCODE_NACK = 0xE3

ERR_NONE = 0x00
ERR_HEADER = 0x01
ERR_SEQUENCE = 0x02
ERR_BUSY = 0x03
ERR_CHUNK_CRC = 0x04
ERR_FILE_CRC = 0x05
ERR_FIFO = 0x06
ERR_ABORTED = 0x07

MESSAGE_NAMES = {
    MSG_RX_ACK: "RX_ACK",
    MSG_SCA_ACK: "SCA_ACK",
    MSG_IDCODE_ACK: "IDCODE_ACK",
    MSG_RX_NACK: "RX_NACK",
    MSG_SCA_NACK: "SCA_NACK",
    MSG_IDCODE_NACK: "IDCODE_NACK",
}

ERROR_NAMES = {
    ERR_NONE: "none",
    ERR_HEADER: "invalid header",
    ERR_SEQUENCE: "session/sequence mismatch",
    ERR_BUSY: "programmer busy",
    ERR_CHUNK_CRC: "chunk CRC mismatch",
    ERR_FILE_CRC: "complete-file CRC mismatch",
    ERR_FIFO: "FPGA receive FIFO error",
    ERR_ABORTED: "session aborted",
}

_ETHERNET_HEADER = struct.Struct("!6s6sH")
_DATA_HEADER = struct.Struct("!4s6BH5I")
_RESPONSE_HEADER = struct.Struct("!4s8B5I")
_LENGTH_PREFIX = struct.Struct("!I")


class EthernetProgrammingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProgramResponse:
    destination_mac: bytes
    source_mac: bytes
    message_type: int
    status: int
    target_csm: int
    target_sca: int
    failed_command: int
    error_code: int
    session_id: int
    sequence: int
    expected_sequence: int
    completed_offset: int
    rolling_crc32: int

    @property
    def message_name(self) -> str:
        return MESSAGE_NAMES.get(self.message_type, f"0x{self.message_type:02X}")

    @property
    def error_name(self) -> str:
        return ERROR_NAMES.get(self.error_code, f"0x{self.error_code:02X}")

    @property
    def result_data(self) -> int:
        """Message-dependent 32-bit result: rolling CRC or FPGA IDCODE."""
        return self.rolling_crc32

    @property
    def captured_ir(self) -> Optional[int]:
        """Return FPGA Capture-IR status for a new-format IDCODE_ACK.

        IDCODE_ACK has no bit-file offset, so firmware places captured IR[5:0]
        in the otherwise-unused completed-offset field.  A zero field identifies
        older firmware that returned no JTAG status.
        """
        if self.message_type != MSG_IDCODE_ACK or self.completed_offset == 0:
            return None
        return self.completed_offset & 0x3F

    @property
    def jtag_done(self) -> Optional[bool]:
        ir = self.captured_ir
        return None if ir is None else bool(ir & 0x20)

    @property
    def jtag_init(self) -> Optional[bool]:
        ir = self.captured_ir
        return None if ir is None else bool(ir & 0x10)

    @property
    def jtag_ir_valid(self) -> Optional[bool]:
        ir = self.captured_ir
        return None if ir is None else (ir & 0x03) == 0x01


def crc32(data: bytes, initial: int = 0) -> int:
    """Return the reflected CRC32 used by zlib and the FPGA transport."""

    return zlib.crc32(data, initial) & 0xFFFFFFFF


def interface_mac(device: str) -> bytes:
    """Read a Linux interface MAC address without requiring raw-I/O privilege."""

    device_bytes = str(device or "").strip().encode("ascii", errors="strict")
    if not device_bytes or len(device_bytes) >= 16:
        raise EthernetProgrammingError(
            f"Invalid Ethernet interface name: {device!r}"
        )

    request = struct.pack("256s", device_bytes)
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        result = fcntl.ioctl(control_socket.fileno(), 0x8927, request)
    except OSError as error:
        raise EthernetProgrammingError(
            f"Cannot read the MAC address for interface {device!r}: {error}"
        ) from error
    finally:
        control_socket.close()

    mac = result[18:24]
    if len(mac) != 6 or mac == b"\x00" * 6:
        raise EthernetProgrammingError(
            f"Interface {device!r} does not have a usable Ethernet MAC address"
        )
    return mac


def build_data_frame(
    source_mac: bytes,
    payload: bytes,
    *,
    session_id: int,
    sequence: int,
    file_offset: int,
    total_length: int,
    file_crc32: int,
    target_csm: int,
    target_sca: int = 0,
    first: bool = False,
    last: bool = False,
) -> bytes:
    if len(source_mac) != 6:
        raise ValueError("source_mac must contain six bytes")
    if not 1 <= len(payload) <= MAX_CHUNK_BYTES:
        raise ValueError(
            f"DATA payload must contain 1..{MAX_CHUNK_BYTES} bytes"
        )
    if not last and len(payload) != MAX_CHUNK_BYTES:
        raise ValueError("Every non-final DATA payload must be 1408 bytes")
    if target_csm not in range(2) or target_sca not in range(4):
        raise ValueError("target CSM/SCA is outside the firmware range")
    if file_offset + len(payload) > total_length:
        raise ValueError("chunk extends beyond the announced bitstream length")

    flags = (0x01 if first else 0) | (0x02 if last else 0)
    ethernet_header = _ETHERNET_HEADER.pack(
        FPGA_MAC,
        source_mac,
        PROGRAM_ETHERTYPE,
    )
    protocol_header = _DATA_HEADER.pack(
        PROTOCOL_MAGIC,
        PROTOCOL_VERSION,
        MSG_DATA,
        flags,
        target_csm,
        target_sca,
        0,
        len(payload),
        session_id & 0xFFFFFFFF,
        sequence & 0xFFFFFFFF,
        file_offset & 0xFFFFFFFF,
        total_length & 0xFFFFFFFF,
        file_crc32 & 0xFFFFFFFF,
    )
    return (
        ethernet_header
        + protocol_header
        + payload
        + struct.pack("!I", crc32(payload))
    )


def build_abort_frame(
    source_mac: bytes,
    *,
    session_id: int,
    sequence: int,
    file_offset: int,
    total_length: int,
    file_crc32: int,
    target_csm: int,
    target_sca: int = 0,
) -> bytes:
    """Build a minimum-size ABORT frame.

    The byte at frame offset 46 is padding, but it is required because the
    firmware selects ABORT mode on that first post-header byte.
    """

    if len(source_mac) != 6:
        raise ValueError("source_mac must contain six bytes")
    ethernet_header = _ETHERNET_HEADER.pack(
        FPGA_MAC,
        source_mac,
        PROGRAM_ETHERTYPE,
    )
    protocol_header = _DATA_HEADER.pack(
        PROTOCOL_MAGIC,
        PROTOCOL_VERSION,
        MSG_ABORT,
        0,
        target_csm,
        target_sca,
        0,
        0,
        session_id & 0xFFFFFFFF,
        sequence & 0xFFFFFFFF,
        file_offset & 0xFFFFFFFF,
        total_length & 0xFFFFFFFF,
        file_crc32 & 0xFFFFFFFF,
    )
    frame = ethernet_header + protocol_header
    return frame.ljust(60, b"\x00")


def build_idcode_read_frame(
    source_mac: bytes,
    *,
    session_id: int,
    sequence: int,
    target_csm: int,
    target_sca: int = 0,
) -> bytes:
    """Build a standalone FPGA IDCODE request padded to 60 Ethernet bytes."""

    if len(source_mac) != 6:
        raise ValueError("source_mac must contain six bytes")
    if target_csm not in range(2) or target_sca not in range(4):
        raise ValueError("target CSM/SCA is outside the firmware range")

    ethernet_header = _ETHERNET_HEADER.pack(
        FPGA_MAC,
        source_mac,
        PROGRAM_ETHERTYPE,
    )
    protocol_header = _DATA_HEADER.pack(
        PROTOCOL_MAGIC,
        PROTOCOL_VERSION,
        MSG_IDCODE_READ,
        0,
        target_csm,
        target_sca,
        0,
        0,
        session_id & 0xFFFFFFFF,
        sequence & 0xFFFFFFFF,
        0,
        0,
        0,
    )
    return (ethernet_header + protocol_header).ljust(60, b"\x00")


def parse_response_frame(
    frame: bytes,
    *,
    expected_host_mac: Optional[bytes] = None,
) -> ProgramResponse:
    if len(frame) < 46:
        raise ValueError(f"programming response is too short ({len(frame)} bytes)")

    destination, source, ethertype = _ETHERNET_HEADER.unpack_from(frame, 0)
    if source != FPGA_MAC:
        raise ValueError("response source MAC is not the MiniDAQ FPGA")
    if expected_host_mac is not None and destination != expected_host_mac:
        raise ValueError("response is addressed to another host")
    if ethertype != PROGRAM_ETHERTYPE:
        raise ValueError(f"unexpected EtherType 0x{ethertype:04X}")

    (
        magic,
        version,
        message_type,
        status,
        target_csm,
        target_sca,
        failed_command,
        error_code,
        _reserved,
        session_id,
        sequence,
        expected_sequence,
        completed_offset,
        rolling_crc,
    ) = _RESPONSE_HEADER.unpack_from(frame, 14)

    if magic != PROTOCOL_MAGIC or version != PROTOCOL_VERSION:
        raise ValueError("response protocol magic/version mismatch")
    if message_type not in MESSAGE_NAMES:
        raise ValueError(f"unknown programming response 0x{message_type:02X}")

    return ProgramResponse(
        destination_mac=destination,
        source_mac=source,
        message_type=message_type,
        status=status,
        target_csm=target_csm,
        target_sca=target_sca,
        failed_command=failed_command,
        error_code=error_code,
        session_id=session_id,
        sequence=sequence,
        expected_sequence=expected_sequence,
        completed_offset=completed_offset,
        rolling_crc32=rolling_crc,
    )


class NativeEthernetPort:
    """Length-prefixed pipe connection to the capability-enabled pcap helper."""

    START_TIMEOUT_S = 3.0
    MAX_FRAME_BYTES = 65535

    def __init__(self, device: str):
        self.device = str(device or "").strip()
        self.source_mac = interface_mac(self.device)
        self._process: Optional[subprocess.Popen] = None
        self._selector: Optional[selectors.BaseSelector] = None
        self._stdout_buffer = bytearray()
        self._stderr_buffer = bytearray()
        self._stderr_lines: List[str] = []

    @staticmethod
    def helper_path() -> str:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "native_capture",
            "ethernet_frame_io",
        )

    def open(self) -> None:
        if self._process is not None:
            return

        helper = self.helper_path()
        if not os.path.isfile(helper) or not os.access(helper, os.X_OK):
            raise EthernetProgrammingError(
                "Ethernet programming helper is not built. Run:\n"
                f"  make -C {os.path.dirname(helper)}\n"
                "then apply the capabilities documented in README.md."
            )

        try:
            process = subprocess.Popen(
                [helper, "--device", self.device],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
            )
        except OSError as error:
            raise EthernetProgrammingError(
                f"Could not start Ethernet programming helper: {error}"
            ) from error

        assert process.stdout is not None
        assert process.stderr is not None
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        self._process = process
        self._selector = selector

        try:
            deadline = time.monotonic() + self.START_TIMEOUT_S
            while time.monotonic() < deadline:
                self._read_available(min(0.1, deadline - time.monotonic()))
                if any(
                    line.startswith("MINIDAQ_ETH_STATUS started")
                    for line in self._stderr_lines
                ):
                    return
                if process.poll() is not None:
                    break
        except Exception:
            self.close()
            raise

        detail = self._error_detail()
        self.close()
        raise EthernetProgrammingError(
            "Ethernet programming helper did not initialize"
            + (f": {detail}" if detail else "")
        )

    def close(self) -> None:
        selector = self._selector
        self._selector = None
        if selector is not None:
            selector.close()

        process = self._process
        self._process = None
        if process is None:
            return

        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def __enter__(self) -> "NativeEthernetPort":
        self.open()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def _error_detail(self) -> str:
        errors = [
            line
            for line in self._stderr_lines
            if "ERROR" in line or "WARN" in line
        ]
        return "; ".join(errors[-3:])

    def _consume_stderr(self) -> None:
        while b"\n" in self._stderr_buffer:
            raw_line, _, remainder = self._stderr_buffer.partition(b"\n")
            self._stderr_buffer[:] = remainder
            line = raw_line.decode(errors="replace").strip()
            if line:
                self._stderr_lines.append(line)

    def _read_available(self, timeout: float) -> None:
        if self._selector is None or self._process is None:
            raise EthernetProgrammingError("Ethernet helper is not open")

        for key, _events in self._selector.select(max(0.0, timeout)):
            try:
                block = os.read(key.fileobj.fileno(), 65536)
            except BlockingIOError:
                continue
            if not block:
                try:
                    self._selector.unregister(key.fileobj)
                except Exception:
                    pass
                continue
            if key.data == "stdout":
                self._stdout_buffer.extend(block)
            else:
                self._stderr_buffer.extend(block)
                self._consume_stderr()

        if self._process.poll() is not None:
            self._consume_stderr()
            detail = self._error_detail()
            if "Operation not permitted" in detail:
                detail += (
                    ". Grant packet-I/O capabilities with: sudo setcap "
                    "cap_net_raw,cap_net_admin=eip "
                    f"{self.helper_path()}"
                )
            raise EthernetProgrammingError(
                "Ethernet programming helper exited"
                + (f": {detail}" if detail else "")
            )

    def send_frame(self, frame: bytes) -> None:
        if not 14 <= len(frame) <= self.MAX_FRAME_BYTES:
            raise ValueError(f"invalid raw Ethernet frame length {len(frame)}")
        if self._process is None or self._process.stdin is None:
            raise EthernetProgrammingError("Ethernet helper is not open")

        packet = _LENGTH_PREFIX.pack(len(frame)) + frame
        try:
            self._process.stdin.write(packet)
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            detail = self._error_detail()
            raise EthernetProgrammingError(
                f"Ethernet frame injection failed: {error}"
                + (f" ({detail})" if detail else "")
            ) from error

    def receive_frame(self, timeout: float) -> Optional[bytes]:
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            if len(self._stdout_buffer) >= _LENGTH_PREFIX.size:
                frame_length = _LENGTH_PREFIX.unpack_from(
                    self._stdout_buffer, 0
                )[0]
                if not 14 <= frame_length <= self.MAX_FRAME_BYTES:
                    raise EthernetProgrammingError(
                        f"helper returned invalid frame length {frame_length}"
                    )
                record_length = _LENGTH_PREFIX.size + frame_length
                if len(self._stdout_buffer) >= record_length:
                    frame = bytes(
                        self._stdout_buffer[_LENGTH_PREFIX.size:record_length]
                    )
                    del self._stdout_buffer[:record_length]
                    return frame

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            self._read_available(min(0.05, remaining))


if sys.platform == "win32":
    # Windows: Npcap in-process instead of the setcap'd native helper.
    import win_pcap as _win_pcap

    def interface_mac(device: str) -> bytes:  # noqa: F811 - platform override
        """Read an interface MAC address (Windows: NPF or friendly name)."""
        try:
            return _win_pcap.interface_mac(device)
        except _win_pcap.PcapError as error:
            raise EthernetProgrammingError(str(error)) from error

    class NativeEthernetPort(_win_pcap.PcapEthernetPort):  # noqa: F811
        """Raw-Ethernet port through Npcap; same interface as the Linux helper."""

        error_class = EthernetProgrammingError
