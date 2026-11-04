"""Qt worker that reads a CSM FPGA IDCODE through MiniDAQ raw Ethernet."""

from __future__ import annotations

import secrets
import time

from PyQt5.QtCore import QObject, pyqtSignal

from ethernet_jtag_protocol import (
    ERR_BUSY,
    MSG_IDCODE_ACK,
    MSG_IDCODE_NACK,
    MSG_RX_ACK,
    MSG_RX_NACK,
    EthernetProgrammingError,
    NativeEthernetPort,
    build_idcode_read_frame,
    parse_response_frame,
)


EXPECTED_CSM_FPGA_IDCODE = 0x0362D093


class Worker_read_CSM_idcode_ethernet(QObject):
    finished = pyqtSignal()
    message_out = pyqtSignal(str)
    # Use object for the value so unexpected 32-bit IDs above signed INT_MAX
    # are still reported without PyQt integer conversion overflow.
    idcode_signal = pyqtSignal(int, object, bool)

    RX_ACK_TIMEOUT_S = 1.0
    IDCODE_ACK_TIMEOUT_S = 10.0
    MAX_FRAME_RETRIES = 3

    def __init__(self, which_csm, ethernet_device, target_sca=0):
        super().__init__()
        self.which_csm = int(which_csm)
        self.ethernet_device = str(ethernet_device or "").strip()
        self.target_sca = int(target_sca)
        self._session_id = secrets.randbits(32) or 1
        self._sequence = 0
        self._port = None

    def _matching_response(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
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

    def _read_idcode(self, frame):
        last_problem = "no FPGA response"

        for attempt in range(self.MAX_FRAME_RETRIES + 1):
            if attempt:
                self.message_out.emit(
                    f"CSM{self.which_csm} Ethernet IDCODE retry "
                    f"{attempt}/{self.MAX_FRAME_RETRIES}: {last_problem}"
                )

            self._port.send_frame(frame)
            rx_ack_seen = False
            deadline = time.monotonic() + self.RX_ACK_TIMEOUT_S

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    last_problem = (
                        "IDCODE_ACK timeout"
                        if rx_ack_seen else "RX_ACK timeout"
                    )
                    break

                response = self._matching_response(remaining)
                if response is None:
                    last_problem = (
                        "IDCODE_ACK timeout"
                        if rx_ack_seen else "RX_ACK timeout"
                    )
                    break

                if response.message_type == MSG_RX_ACK:
                    if response.status not in (0, ERR_BUSY):
                        last_problem = (
                            f"RX_ACK status 0x{response.status:02X}"
                        )
                        break
                    if not rx_ack_seen:
                        rx_ack_seen = True
                        deadline = (
                            time.monotonic() + self.IDCODE_ACK_TIMEOUT_S
                        )
                    continue

                if response.message_type == MSG_IDCODE_ACK:
                    return response

                if response.message_type == MSG_IDCODE_NACK:
                    raise EthernetProgrammingError(
                        f"IDCODE_NACK status=0x{response.status:02X}, "
                        f"command=0x{response.failed_command:02X}, "
                        f"detail=0x{response.error_code:02X}"
                    )

                if response.message_type == MSG_RX_NACK:
                    last_problem = (
                        f"RX_NACK: {response.error_name} "
                        f"(status=0x{response.status:02X})"
                    )
                    if response.error_code != ERR_BUSY:
                        raise EthernetProgrammingError(last_problem)
                    break

        raise EthernetProgrammingError(
            f"IDCODE read failed after {self.MAX_FRAME_RETRIES} retries: "
            f"{last_problem}"
        )

    def run(self):
        start_time = time.monotonic()
        try:
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

            self._port = NativeEthernetPort(self.ethernet_device)
            self._port.open()
            frame = build_idcode_read_frame(
                self._port.source_mac,
                session_id=self._session_id,
                sequence=self._sequence,
                target_csm=self.which_csm,
                target_sca=self.target_sca,
            )
            response = self._read_idcode(frame)
            idcode = response.result_data
            expected = idcode == EXPECTED_CSM_FPGA_IDCODE
            ir_status_known = response.captured_ir is not None
            configured = (
                expected
                and (
                    not ir_status_known
                    or (
                        response.jtag_ir_valid
                        and response.jtag_done
                        and response.jtag_init
                    )
                )
            )
            self.idcode_signal.emit(self.which_csm, idcode, configured)

            if ir_status_known:
                status_text = (
                    f", DONE={int(response.jtag_done)}, "
                    f"INIT={int(response.jtag_init)}"
                )
            else:
                status_text = ", DONE=unknown, INIT=unknown (older firmware)"

            if expected:
                self.message_out.emit(
                    f"CSM{self.which_csm} FPGA present: "
                    f"IDCODE=0x{idcode:08X}{status_text}"
                )
            else:
                self.message_out.emit(
                    f"CSM{self.which_csm} unexpected FPGA IDCODE "
                    f"0x{idcode:08X}; expected "
                    f"0x{EXPECTED_CSM_FPGA_IDCODE:08X}{status_text}"
                )
        except Exception as error:
            self.message_out.emit(
                f"CSM{self.which_csm} Ethernet IDCODE read failed: {error}"
            )
        finally:
            if self._port is not None:
                self._port.close()
                self._port = None
            self.message_out.emit(
                f"Ethernet IDCODE runtime: "
                f"{time.monotonic() - start_time:.2f}s"
            )
            self.finished.emit()
