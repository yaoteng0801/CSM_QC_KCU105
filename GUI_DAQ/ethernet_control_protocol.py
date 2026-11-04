"""MiniDAQ raw-Ethernet register, lpGBT IC and SCA protocol.

0x88B5/MDC1 carries programming and active control.  0x88B6/MDM1 carries
readback and monitoring.  A single client lock serializes requests, while the
FPGA keeps separate request/result FIFOs for the two traffic classes.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import struct
import threading
import time
from typing import Callable, Optional
from sca_transaction_ids import validate_sca_transaction_id

from ethernet_jtag_protocol import (
    EthernetProgrammingError,
    FPGA_MAC,
    NativeEthernetPort,
    interface_mac,
)


CONTROL_ETHERTYPE = 0x88B5
MONITOR_ETHERTYPE = 0x88B6
CONTROL_MAGIC = b"MDC1"
MONITOR_MAGIC = b"MDM1"
PROTOCOL_VERSION = 2

FPGA_WRITE = 0x10
FPGA_READ = 0x11
FPGA_RESET = 0x12
LPGBT_WRITE = 0x20
LPGBT_READ = 0x21
SCA_COMMAND = 0x30
SCA_CONNECT = 0x31
SCA_RESET = 0x32

STATUS_NAMES = {
    0x00: "ok",
    0x01: "invalid request",
    0x02: "resource busy",
    0x03: "reply timeout",
    0x04: "reply overflow",
}

_ETHERNET_HEADER = struct.Struct("!6s6sH")
class EthernetControlError(RuntimeError):
    def __init__(self, message, *, status=None, opcode=None, detail=None):
        super().__init__(message)
        self.status = status
        self.opcode = opcode
        self.detail = detail


@dataclass(frozen=True)
class ControlResponse:
    destination_mac: bytes
    source_mac: bytes
    ethertype: int
    opcode: int
    status: int
    target: int
    subtarget: int
    request_id: int
    address: int
    detail: int
    data: bytes


def build_request_frame(
    source_mac: bytes,
    *,
    ethertype: int,
    request_id: int,
    opcode: int,
    flags: int = 0,
    target: int = 0,
    subtarget: int = 0,
    address: int = 0,
    trans_id: int = 0,
    channel: int = 0,
    command: int = 0,
    sca_address: int = 0,
    argument: int = 0,
    payload: bytes = b"",
) -> bytes:
    if opcode == SCA_COMMAND:
        trans_id = validate_sca_transaction_id(trans_id)
    payload = bytes(payload)
    if len(source_mac) != 6:
        raise ValueError("source_mac must contain six bytes")
    if len(payload) > 20:
        raise ValueError("Ethernet control payload is limited to 20 bytes")
    if ethertype == CONTROL_ETHERTYPE:
        magic = CONTROL_MAGIC
    elif ethertype == MONITOR_ETHERTYPE:
        magic = MONITOR_MAGIC
    else:
        raise ValueError(f"unsupported MiniDAQ EtherType 0x{ethertype:04X}")

    frame = bytearray(_ETHERNET_HEADER.pack(FPGA_MAC, source_mac, ethertype))
    frame.extend(magic)
    frame.extend(
        bytes(
            (
                PROTOCOL_VERSION,
                opcode & 0xFF,
                flags & 0xFF,
                target & 0xFF,
                subtarget & 0xFF,
                len(payload),
            )
        )
    )
    frame.extend(struct.pack("!I", request_id & 0xFFFFFFFF))
    frame.extend(struct.pack("!H", address & 0xFFFF))
    frame.extend(
        bytes(
            (
                trans_id & 0xFF,
                channel & 0xFF,
                command & 0xFF,
                sca_address & 0xFF,
            )
        )
    )
    frame.extend(struct.pack("!I", argument & 0xFFFFFFFF))
    frame.extend(b"\x00\x00")
    frame.extend(payload)
    return bytes(frame).ljust(60, b"\x00")


def parse_response(frame: bytes) -> Optional[ControlResponse]:
    if len(frame) < 60:
        return None
    destination, source, ethertype = _ETHERNET_HEADER.unpack_from(frame, 0)
    expected_magic = {
        CONTROL_ETHERTYPE: CONTROL_MAGIC,
        MONITOR_ETHERTYPE: MONITOR_MAGIC,
    }.get(ethertype)
    if expected_magic is None or frame[14:18] != expected_magic:
        return None
    if frame[18] != PROTOCOL_VERSION or not (frame[19] & 0x80):
        return None
    data_len = frame[23]
    if data_len > 36 or len(frame) < max(60, 36 + data_len):
        return None
    return ControlResponse(
        destination_mac=destination,
        source_mac=source,
        ethertype=ethertype,
        opcode=frame[19] & 0x7F,
        status=frame[20],
        target=frame[21],
        subtarget=frame[22],
        request_id=int.from_bytes(frame[24:28], "big"),
        address=int.from_bytes(frame[28:30], "big"),
        detail=frame[30],
        data=bytes(frame[36 : 36 + data_len]),
    )


class EthernetControlClient:
    """Thread-safe synchronous client shared by every GUI hardware tab."""

    def __init__(
        self,
        device_callback: Callable[[], str],
        *,
        response_timeout_s: float = 0.25,
        attempts: int = 3,
    ):
        self._device_callback = device_callback
        self.response_timeout_s = float(response_timeout_s)
        self.attempts = max(1, int(attempts))
        self._lock = threading.RLock()
        self._ids = itertools.count(int(time.time_ns()) & 0xFFFFFFFF)
        self._port: Optional[NativeEthernetPort] = None
        self._device = ""
        self._source_mac = b""

    def close(self) -> None:
        with self._lock:
            if self._port is not None:
                self._port.close()
            self._port = None
            self._device = ""
            self._source_mac = b""

    def _ensure_port(self) -> NativeEthernetPort:
        device = str(self._device_callback() or "").strip()
        if not device:
            raise EthernetControlError("No Ethernet interface is selected")
        if self._port is not None and device == self._device:
            return self._port
        self.close()
        port = NativeEthernetPort(device)
        try:
            port.open()
            source_mac = interface_mac(device)
        except Exception:
            port.close()
            raise
        self._port = port
        self._device = device
        self._source_mac = source_mac
        return port

    def request(
        self,
        opcode: int,
        *,
        monitor: bool = False,
        flags: int = 0,
        target: int = 0,
        subtarget: int = 0,
        address: int = 0,
        trans_id: int = 0,
        channel: int = 0,
        command: int = 0,
        sca_address: int = 0,
        argument: int = 0,
        payload: bytes = b"",
        timeout_s: Optional[float] = None,
    ) -> ControlResponse:
        with self._lock:
            port = self._ensure_port()
            request_id = next(self._ids) & 0xFFFFFFFF
            ethertype = MONITOR_ETHERTYPE if monitor else CONTROL_ETHERTYPE
            frame = build_request_frame(
                self._source_mac,
                ethertype=ethertype,
                request_id=request_id,
                opcode=opcode,
                flags=flags,
                target=target,
                subtarget=subtarget,
                address=address,
                trans_id=trans_id,
                channel=channel,
                command=command,
                sca_address=sca_address,
                argument=argument,
                payload=payload,
            )
            timeout = self.response_timeout_s if timeout_s is None else float(timeout_s)
            for _attempt in range(self.attempts):
                port.send_frame(frame)
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    received = port.receive_frame(deadline - time.monotonic())
                    if received is None:
                        break
                    response = parse_response(received)
                    if response is None:
                        continue
                    if (
                        response.destination_mac == self._source_mac
                        and response.source_mac == FPGA_MAC
                        and response.ethertype == ethertype
                        and response.request_id == request_id
                        and response.opcode == opcode
                    ):
                        if response.status:
                            name = STATUS_NAMES.get(
                                response.status, f"status 0x{response.status:02X}"
                            )
                            raise EthernetControlError(
                                f"MiniDAQ {name}; opcode=0x{opcode:02X}, "
                                f"detail=0x{response.detail:02X}",
                                status=response.status, opcode=opcode,
                                detail=response.detail,
                            )
                        return response
            raise EthernetControlError(
                f"MiniDAQ Ethernet reply timeout; opcode=0x{opcode:02X}, "
                f"request_id=0x{request_id:08X}"
            )
