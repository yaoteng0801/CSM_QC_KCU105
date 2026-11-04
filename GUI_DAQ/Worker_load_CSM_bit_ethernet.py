"""Qt worker that programs a CSM FPGA through MiniDAQ raw Ethernet."""

from __future__ import annotations

import os
import secrets
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from ethernet_jtag_protocol import (
    ERR_BUSY,
    ERR_CHUNK_CRC,
    ERR_FIFO,
    MAX_CHUNK_BYTES,
    MSG_RX_ACK,
    MSG_RX_NACK,
    MSG_SCA_ACK,
    MSG_SCA_NACK,
    EthernetProgrammingError,
    NativeEthernetPort,
    build_abort_frame,
    build_data_frame,
    crc32,
    parse_response_frame,
)


class _ProgrammingCancelled(Exception):
    pass


class Worker_load_CSM_bit_ethernet(QObject):
    finished = pyqtSignal()
    message_out = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    programmed_signal = pyqtSignal(int)

    RX_ACK_TIMEOUT_S = 1.0
    SCA_ACK_TIMEOUT_S = 30.0
    MAX_FRAME_RETRIES = 3

    def __init__(
        self,
        which_csm,
        file_name,
        ethernet_device,
        target_sca=0,
    ):
        super().__init__()
        self.which_csm = int(which_csm)
        self.file_name = str(file_name)
        self.ethernet_device = str(ethernet_device or "").strip()
        self.target_sca = int(target_sca)
        self._cancel_event = threading.Event()
        self._port = None
        self._session_id = 0
        self._sequence = 0
        self._file_offset = 0
        self._total_length = 0
        self._file_crc32 = 0

    def request_cancel(self):
        self._cancel_event.set()

    def _check_cancelled(self):
        if self._cancel_event.is_set():
            raise _ProgrammingCancelled()

    def _send_abort(self):
        if self._port is None or self._session_id == 0:
            return
        try:
            self._port.send_frame(
                build_abort_frame(
                    self._port.source_mac,
                    session_id=self._session_id,
                    sequence=self._sequence,
                    file_offset=self._file_offset,
                    total_length=self._total_length,
                    file_crc32=self._file_crc32,
                    target_csm=self.which_csm,
                    target_sca=self.target_sca,
                )
            )
            # Give the helper enough time to inject the frame before it exits.
            time.sleep(0.02)
        except Exception as error:
            self.message_out.emit(
                f"Could not send Ethernet programming ABORT: {error}"
            )

    def _matching_response(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            self._check_cancelled()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            frame = self._port.receive_frame(min(0.1, remaining))
            if frame is None:
                continue
            try:
                response = parse_response_frame(
                    frame,
                    expected_host_mac=self._port.source_mac,
                )
            except ValueError:
                continue
            if (
                response.session_id != self._session_id
                or response.sequence != self._sequence
                or response.target_csm != self.which_csm
                or response.target_sca != self.target_sca
            ):
                continue
            return response

    def _transfer_chunk(self, frame, expected_offset, expected_crc):
        last_problem = "no FPGA response"
        for attempt in range(self.MAX_FRAME_RETRIES + 1):
            self._check_cancelled()
            if attempt:
                self.message_out.emit(
                    f"CSM{self.which_csm} Ethernet chunk {self._sequence} "
                    f"retry {attempt}/{self.MAX_FRAME_RETRIES}: {last_problem}"
                )

            self._port.send_frame(frame)
            rx_ack_seen = False
            deadline = time.monotonic() + self.RX_ACK_TIMEOUT_S

            while True:
                self._check_cancelled()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    last_problem = (
                        "SCA_ACK timeout" if rx_ack_seen else "RX_ACK timeout"
                    )
                    break

                response = self._matching_response(remaining)
                if response is None:
                    last_problem = (
                        "SCA_ACK timeout" if rx_ack_seen else "RX_ACK timeout"
                    )
                    break

                if response.message_type == MSG_RX_ACK:
                    # ERR_BUSY is the intentional response to a retransmitted
                    # chunk that the SCA is still executing.
                    if response.status not in (0, ERR_BUSY):
                        last_problem = (
                            f"RX_ACK status 0x{response.status:02X}"
                        )
                        break
                    if not rx_ack_seen:
                        rx_ack_seen = True
                        deadline = time.monotonic() + self.SCA_ACK_TIMEOUT_S
                    continue

                if response.message_type == MSG_SCA_ACK:
                    if response.completed_offset != expected_offset:
                        raise EthernetProgrammingError(
                            "SCA_ACK offset mismatch: "
                            f"got {response.completed_offset}, "
                            f"expected {expected_offset}"
                        )
                    if response.expected_sequence != self._sequence + 1:
                        raise EthernetProgrammingError(
                            "SCA_ACK next-sequence mismatch: "
                            f"got {response.expected_sequence}, "
                            f"expected {self._sequence + 1}"
                        )
                    if response.rolling_crc32 != expected_crc:
                        raise EthernetProgrammingError(
                            "SCA_ACK rolling CRC mismatch: "
                            f"got 0x{response.rolling_crc32:08X}, "
                            f"expected 0x{expected_crc:08X}"
                        )
                    return

                if response.message_type == MSG_SCA_NACK:
                    raise EthernetProgrammingError(
                        f"SCA_NACK status=0x{response.status:02X}, "
                        f"command=0x{response.failed_command:02X}, "
                        f"detail=0x{response.error_code:02X}"
                    )

                if response.message_type == MSG_RX_NACK:
                    last_problem = (
                        f"RX_NACK: {response.error_name} "
                        f"(status=0x{response.status:02X})"
                    )
                    # Header/sequence/file errors are deterministic.  CRC and
                    # FIFO errors can be recovered by sending the exact frame.
                    if response.error_code not in (
                        ERR_BUSY,
                        ERR_CHUNK_CRC,
                        ERR_FIFO,
                    ):
                        raise EthernetProgrammingError(last_problem)
                    break

        raise EthernetProgrammingError(
            f"chunk {self._sequence} failed after "
            f"{self.MAX_FRAME_RETRIES} retries: {last_problem}"
        )

    def run(self):
        start_time = time.monotonic()
        cancelled = False
        completed = False

        try:
            self._check_cancelled()
            if not self.ethernet_device:
                raise EthernetProgrammingError(
                    "No Ethernet interface is selected in the Ethernet Capture tab"
                )
            if self.which_csm not in range(2):
                raise EthernetProgrammingError(
                    f"Unsupported CSM target {self.which_csm}"
                )
            if self.target_sca not in range(4):
                raise EthernetProgrammingError(
                    f"Unsupported SCA target {self.target_sca}"
                )
            if not os.path.isfile(self.file_name):
                raise EthernetProgrammingError(
                    f"Bitstream file does not exist: {self.file_name}"
                )

            with open(self.file_name, "rb") as bit_file:
                bitstream = bit_file.read()
            if not bitstream:
                raise EthernetProgrammingError(
                    f"Bitstream file is empty: {self.file_name}"
                )

            self._total_length = len(bitstream)
            self._file_crc32 = crc32(bitstream)
            self._session_id = secrets.randbits(32) or 1
            total_chunks = (
                self._total_length + MAX_CHUNK_BYTES - 1
            ) // MAX_CHUNK_BYTES

            self.message_out.emit(
                f"CSM{self.which_csm} Ethernet programming: "
                f"{self._total_length} bytes, {total_chunks} chunks, "
                f"file CRC32=0x{self._file_crc32:08X}, "
                f"interface={self.ethernet_device}, SCA{self.target_sca}"
            )
            self.progress_signal.emit(0)

            rolling_crc = 0
            self._port = NativeEthernetPort(self.ethernet_device)
            self._port.open()

            while self._file_offset < self._total_length:
                self._check_cancelled()
                chunk = bitstream[
                    self._file_offset:
                    self._file_offset + MAX_CHUNK_BYTES
                ]
                first = self._file_offset == 0
                last = self._file_offset + len(chunk) == self._total_length
                rolling_crc = crc32(chunk, rolling_crc)

                frame = build_data_frame(
                    self._port.source_mac,
                    chunk,
                    session_id=self._session_id,
                    sequence=self._sequence,
                    file_offset=self._file_offset,
                    total_length=self._total_length,
                    file_crc32=self._file_crc32,
                    target_csm=self.which_csm,
                    target_sca=self.target_sca,
                    first=first,
                    last=last,
                )
                next_offset = self._file_offset + len(chunk)
                self._transfer_chunk(frame, next_offset, rolling_crc)
                self._file_offset = next_offset
                self._sequence += 1
                self.progress_signal.emit(
                    (self._file_offset * 100) // self._total_length
                )

            if rolling_crc != self._file_crc32:
                raise EthernetProgrammingError(
                    "local rolling CRC did not match the complete-file CRC"
                )

            completed = True
            self.progress_signal.emit(100)
            self.programmed_signal.emit(self.which_csm)
            self.message_out.emit(
                f"CSM{self.which_csm} bit file programmed over Ethernet."
            )
        except _ProgrammingCancelled:
            cancelled = True
            self._send_abort()
        except Exception as error:
            self.message_out.emit(
                f"CSM{self.which_csm} Ethernet bit load failed: {error}"
            )
            self._send_abort()
        finally:
            if self._port is not None:
                self._port.close()
                self._port = None
            if cancelled or (self._cancel_event.is_set() and not completed):
                self.message_out.emit(
                    f"CSM{self.which_csm} Ethernet bit load cancelled."
                )
            self.message_out.emit(
                f"Ethernet programming runtime: "
                f"{time.monotonic() - start_time:.2f}s"
            )
            self.finished.emit()

