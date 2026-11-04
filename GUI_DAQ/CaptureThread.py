# CaptureThread.py
from __future__ import annotations

import os
import queue
import selectors
import signal
import subprocess
import sys
import time
from typing import Dict, Optional

from PyQt5 import QtCore


WORD_SIZE = 5
READ_SIZE = 1024 * 1024
IS_WINDOWS = sys.platform == "win32"
ANALYSIS_DROP_REPORT_INTERVAL_SEC = 5.0


class CaptureThread(QtCore.QThread):
    """
    Run native libpcap capture without putting per-packet work on the Python GIL.

    The native process always writes extracted data to the .dat file first.
    Its stdout is a best-effort, non-blocking stream for live decoding.

    On Windows the native helper is not built; the same capture runs in this
    thread through Npcap (win_capture.run_live) and reports the same
    MINIDAQ_* status lines.
    """

    message = QtCore.pyqtSignal(str)
    isolation_stats = QtCore.pyqtSignal(object)  # dropped hits, filtered, preserved, rejected events
    stats = QtCore.pyqtSignal(
        int,  # total_packets
        int,  # lost_packets
        int,  # total_bytes
        str,  # output filename
    )

    def __init__(
        self,
        dev: str,
        bpf: str,
        out_path: str,
        analysis_q: "queue.Queue[bytes]",
        parent: Optional[QtCore.QObject] = None,
        isolation_map_path: Optional[str] = None,
    ):
        super().__init__(parent)
        self.dev = dev
        self.bpf = bpf
        self.out_path = out_path
        self.analysis_q = analysis_q
        self.isolation_map_path = isolation_map_path

        self._stop = False
        self._process: Optional[subprocess.Popen] = None
        self._analysis_drop_count = 0
        self._last_drop_report = 0.0
        self._last_native_dropped_chunks = 0
        self._last_kernel_dropped = 0

    @staticmethod
    def _helper_path() -> str:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "native_capture",
            "minidaq_capture",
        )

    def stop(self):
        """Request native capture stop without blocking the GUI thread."""
        self._stop = True
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass

    def _emit_queue_drop_warning(self, chunk_bytes: int):
        self._analysis_drop_count += 1
        now = time.monotonic()
        if now - self._last_drop_report >= ANALYSIS_DROP_REPORT_INTERVAL_SEC:
            self.message.emit(
                "[WARN] Analysis queue full: "
                f"dropped_decode_chunks={self._analysis_drop_count} "
                f"last_chunk_bytes={chunk_bytes} "
                f"dat_file_still_complete={self.out_path}\n"
            )
            self._last_drop_report = now

    def _queue_analysis(self, data: bytes, carry: bytes) -> bytes:
        combined = carry + data
        aligned_size = len(combined) - (len(combined) % WORD_SIZE)
        if aligned_size == 0:
            return combined

        chunk = combined[:aligned_size]
        try:
            self.analysis_q.put_nowait(chunk)
        except queue.Full:
            self._emit_queue_drop_warning(len(chunk))
        return combined[aligned_size:]

    @staticmethod
    def _parse_values(line: str) -> Dict[str, int]:
        values: Dict[str, int] = {}
        for field in line.split()[1:]:
            key, separator, value = field.partition("=")
            if not separator:
                continue
            try:
                values[key] = int(value)
            except ValueError:
                continue
        return values

    def _handle_native_line(self, line: str):
        if line.startswith("MINIDAQ_STATS "):
            values = self._parse_values(line)
            self.stats.emit(
                values.get("packets", 0),
                values.get("lost", 0),
                values.get("bytes", 0),
                os.path.basename(self.out_path),
            )
            self.isolation_stats.emit((
                values.get("isolated_dropped", 0),
                values.get("filtered_events", 0),
                values.get("preserved_events", 0),
                values.get("filter_rejected_events", 0),
            ))

            native_drops = values.get("analysis_dropped_chunks", 0)
            if native_drops > self._last_native_dropped_chunks:
                self.message.emit(
                    "[WARN] Native analysis stream could not keep up: "
                    f"dropped_decode_chunks={native_drops} "
                    f"dropped_decode_bytes={values.get('analysis_dropped_bytes', 0)} "
                    f"dat_file_still_complete={self.out_path}\n"
                )
                self._last_native_dropped_chunks = native_drops

            kernel_drops = values.get("kernel_dropped", 0)
            if kernel_drops > self._last_kernel_dropped:
                self.message.emit(
                    "[WARN] libpcap kernel drops: "
                    f"dropped_delta={kernel_drops - self._last_kernel_dropped} "
                    f"dropped_total={kernel_drops} device={self.dev}\n"
                )
                self._last_kernel_dropped = kernel_drops
            return

        if line.startswith("MINIDAQ_STATUS started"):
            self.message.emit(f"Native pcap initialized on {self.dev}\n")
            kind = "filtered triggerless data" if self.isolation_map_path else "raw data"
            self.message.emit(f"Writing {kind} to: {self.out_path}\n")
        elif line.startswith("MINIDAQ_STATUS stopped"):
            self.message.emit("Capture stopped\n")
        elif line.startswith("MINIDAQ_WARN "):
            self.message.emit(f"[WARN] Native capture: {line[13:]}\n")
        elif line.startswith("MINIDAQ_ERROR "):
            self.message.emit(f"[ERROR] Native capture: {line[14:]}\n")
            if IS_WINDOWS and "pcap_activate_failed" in line:
                self.message.emit(
                    "Install Npcap from https://npcap.com. If it was installed with "
                    "'Restrict Npcap driver's access to Administrators only', "
                    "start the GUI as administrator.\n"
                )
            elif "pcap_activate_failed" in line and "Operation not permitted" in line:
                self.message.emit(
                    "Grant packet-capture privileges to the native helper:\n"
                    f"  sudo setcap cap_net_raw,cap_net_admin=eip {self._helper_path()}\n"
                )
        else:
            self.message.emit(f"[Native capture] {line}\n")

    def _start_process(self) -> Optional[subprocess.Popen]:
        helper = self._helper_path()
        if not os.path.isfile(helper) or not os.access(helper, os.X_OK):
            self.message.emit(
                "[ERROR] Native capture helper is not built. Run:\n"
                f"  make -C {os.path.dirname(helper)}\n"
            )
            return None

        out_dir = os.path.dirname(os.path.abspath(self.out_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        command = [
            helper,
            "--device",
            self.dev,
            "--filter",
            self.bpf,
            "--output",
            self.out_path,
        ]
        if self.isolation_map_path:
            command.extend(["--isolation-map", self.isolation_map_path])
        try:
            return subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
            )
        except Exception as error:
            self.message.emit(
                "[ERROR] Failed to start native capture: "
                f"device={self.dev} filter={self.bpf} error={error!r}\n"
            )
            return None

    def _run_windows(self):
        import win_capture

        out_dir = os.path.dirname(os.path.abspath(self.out_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        carry = [b""]

        def sink(data: bytes) -> None:
            carry[0] = self._queue_analysis(data, carry[0])

        try:
            return_code = win_capture.run_live(
                self.dev,
                self.bpf,
                self.out_path,
                isolation_map=self.isolation_map_path,
                line=self._handle_native_line,
                sink=sink,
                should_stop=lambda: self._stop,
            )
        except Exception as error:
            self.message.emit(
                "[ERROR] Failed to start capture: "
                f"device={self.dev} filter={self.bpf} error={error!r}\n"
            )
            return
        if return_code != 0 and not self._stop:
            self.message.emit(f"[ERROR] Native capture exited with code {return_code}\n")

    def run(self):
        if IS_WINDOWS:
            self._run_windows()
            return
        self._process = self._start_process()
        if self._process is None:
            return

        process = self._process
        selector = selectors.DefaultSelector()
        assert process.stdout is not None
        assert process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")

        analysis_carry = b""
        stderr_buffer = b""
        signal_sent = False
        try:
            while selector.get_map() or process.poll() is None:
                if self._stop and not signal_sent and process.poll() is None:
                    process.send_signal(signal.SIGINT)
                    signal_sent = True

                for key, _ in selector.select(timeout=0.1):
                    try:
                        data = os.read(key.fileobj.fileno(), READ_SIZE)
                    except BlockingIOError:
                        continue
                    if not data:
                        selector.unregister(key.fileobj)
                        continue

                    if key.data == "stdout":
                        analysis_carry = self._queue_analysis(data, analysis_carry)
                    else:
                        stderr_buffer += data
                        lines = stderr_buffer.split(b"\n")
                        stderr_buffer = lines.pop()
                        for raw_line in lines:
                            self._handle_native_line(
                                raw_line.decode(errors="replace").strip()
                            )

            if stderr_buffer:
                self._handle_native_line(
                    stderr_buffer.decode(errors="replace").strip()
                )
            return_code = process.wait()
            if return_code != 0 and not self._stop:
                self.message.emit(
                    f"[ERROR] Native capture exited with code {return_code}\n"
                )
        finally:
            selector.close()
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            self._process = None
