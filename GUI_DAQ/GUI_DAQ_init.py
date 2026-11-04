# GUI_DAQ_init.py
import win_runtime  # noqa: F401 - Windows: newest C++ runtime before PyQt5 (no-op elsewhere)
from MainWindow import Ui_MainWindow

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QObject, pyqtSignal

import sys
import datetime
import os
import traceback

from backend import Backend
from geometry import Geometry
from rt_function import RTFunction   # NEW
from TrackFit import TrackFit


# =============================================================================
# Main Window
# =============================================================================

class StartQT5(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        here = os.path.dirname(os.path.abspath(__file__))

        # Example: all chambers use same default file (can be different per chamber)
        geo_path = os.path.join(here, "mini_sMDT.txt")
        rt_path  = os.path.join(here, "sMDT_rt_ArCO2_93_7_3bar.txt")

        defaults = dict(
            chamberType="A",
            flipTDCs=1,
            tdcColByTubeNo=1,
            MAX_TDC=40,
            MAX_TDC_CHANNEL=24,
            MAX_TUBE_LAYER=8,
            MAX_TUBE_COLUMN=60,
            MAX_TDC_LAYER=4,
            ML_distance=114.95,
            tube_length=0.3,
            layer_distance=13.0769836,
            column_distance=15.1,
            radius=7.5,
            min_drift_dist=0.0,
            max_drift_dist=7.1,
        )

        # ---- USER-DEFINED number of chambers ----
        chamber_ids = [0,1]   # <- edit this list (any length)
        self.geos = [
            Geometry(chamber_id=cid, geo_file=geo_path, **defaults)
            for cid in chamber_ids
        ]
        Geometry.enforce_exclusive_active_tdcs(self.geos, keep_ncol=True, verbose=True)

        # ---------------------------------------------------------------------
        self.backend = Backend()

        # Register geometries for GUI usage (DecodeThread does NOT use them)
        if hasattr(self.backend, "set_geometries_from_list"):
            self.backend.set_geometries_from_list(self.geos)
        elif hasattr(self.backend, "set_geometries"):
            self.backend.set_geometries({int(g.chamber_id): g for g in self.geos})
        else:
            raise AttributeError("Backend is missing set_geometries_from_list() (or set_geometries()).")

        # ---------------------------------------------------------------------
        # NEW: build ONE shared RTFunction here and pass to MainWindow -> tab_geometry
        # ---------------------------------------------------------------------
        self.rt = None
        try:
            if os.path.isfile(rt_path):
                self.rt = self._load_rt_from_file(rt_path)
            else:
                print(f"[GUI] RT file not found: {rt_path} (drift circles will be disabled)")
        except Exception as e:
            print(f"[GUI] Failed to load RT: {e} (drift circles will be disabled)")
            self.rt = None

        # Share RT with the backend's triggerless event-T0 fitter.
        if hasattr(self.backend, "set_trackfit_rt"):
            self.backend.set_trackfit_rt(self.rt)

        # ---------------------------------------------------------------------
        self.ui = Ui_MainWindow()

        # IMPORTANT: pass geo LIST + rt into MainWindow
        # You must update Ui_MainWindow.setupUi signature to accept rt=None
        self.ui.setupUi(self, backend=self.backend, geo=self.geos, rt=self.rt)

        preferred_width = 1350
        preferred_height = 850
        screen = self.screen() or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            self.resize(preferred_width, preferred_height)
        else:
            available = screen.availableGeometry()
            # Leave room for the desktop panel and window frame.  The central
            # scroll area handles content that no longer fits in this space.
            self.resize(
                min(preferred_width, max(320, available.width() - 40)),
                min(preferred_height, max(240, available.height() - 80)),
            )

        self.logfilename = os.path.join(os.getcwd(), "log.txt")
        self.run_logfilename = None
        self.run_warningfilename = None

        # forward backend messages into GUI log
        self.backend.message.connect(self.normalOutputWritten)
        if hasattr(self.backend, "run_log_path_changed"):
            self.backend.run_log_path_changed.connect(self.startRunLog)
        if hasattr(self.backend, "run_finished"):
            self.backend.run_finished.connect(self.finishRunLog)

    def closeEvent(self, event):
        combined = getattr(getattr(self, "ui", None), "tab_monitor_inst", None)
        if combined is not None and combined.worker is not None:
            combined.stop()
            if not getattr(self, '_combined_monitor_close_pending', False):
                self._combined_monitor_close_pending = True
                combined.thread.finished.connect(self.close)
            event.ignore()
            return
        capture = getattr(getattr(self, "ui", None), "tab_capture_inst", None)
        if capture is not None:
            if capture._hardware_run_active or capture._diagnostic_active:
                capture.stop()
            capture._pause_diagnostic_polling()
        # The shared control client owns a persistent raw-Ethernet helper.
        # Close it explicitly so no capture subprocess remains after the GUI.
        eth = getattr(getattr(self, "ui", None), "eth", None)
        if eth is not None:
            try:
                eth.close()
            except Exception:
                pass
        super().closeEvent(event)

    def normalOutputWritten(self, text: str):
        """Append text to GUI log, global log, and active run log."""
        if hasattr(self, "ui") and hasattr(self.ui, "textBrowser") and self.ui.textBrowser is not None:
            self.ui.textBrowser.moveCursor(QtGui.QTextCursor.End)
            self.ui.textBrowser.insertPlainText(text)

        self._write_log_file(self.logfilename, text)

        run_log = getattr(self, "run_logfilename", None)
        if run_log:
            try:
                same_file = os.path.abspath(run_log) == os.path.abspath(self.logfilename)
            except Exception:
                same_file = False
            if not same_file:
                self._write_log_file(run_log, text)

        run_warnings = getattr(self, "run_warningfilename", None)
        if run_warnings and ("[WARN]" in text or "[ERROR]" in text):
            self._write_log_file(run_warnings, text)

    def _write_log_file(self, filename: str, text: str):
        try:
            if not filename:
                return
            out_dir = os.path.dirname(os.path.abspath(filename))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(filename, "a", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    @QtCore.pyqtSlot(str)
    def startRunLog(self, filename: str):
        path = str(filename or "").strip()
        if not path:
            self.run_logfilename = None
            return

        try:
            out_dir = os.path.dirname(os.path.abspath(path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8"):
                pass
            stem, _ = os.path.splitext(path)
            warning_path = f"{stem}_warnings_errors.txt"
            with open(warning_path, "w", encoding="utf-8") as f:
                f.write("MiniDAQ warnings and errors\n")
        except Exception as e:
            self.run_logfilename = None
            self.run_warningfilename = None
            self.normalOutputWritten(f"[ERROR] Failed to create run log: path={path} error={repr(e)}\n")
            return

        self.run_logfilename = path
        self.run_warningfilename = warning_path
        self.normalOutputWritten(f"Run log: {path}\n")
        self.normalOutputWritten(f"Warnings/errors: {warning_path}\n")

    @QtCore.pyqtSlot()
    def finishRunLog(self):
        path = getattr(self, "run_logfilename", None)
        if not path:
            return
        warning_path = getattr(self, "run_warningfilename", None)
        if warning_path:
            try:
                if os.path.isfile(warning_path) and os.path.getsize(warning_path) <= len("MiniDAQ warnings and errors\n"):
                    with open(warning_path, "a", encoding="utf-8") as f:
                        f.write("No warnings or errors recorded.\n")
            except Exception:
                pass
        self.normalOutputWritten(f"Run log closed: {path}\n")
        self.run_logfilename = None
        self.run_warningfilename = None

    def _load_rt_from_file(self, rt_path: str, *, nrt=None, time_ranges=None) -> RTFunction:
        path = str(rt_path).strip()
        if not path:
            raise RuntimeError("RT path is empty.")
        if not os.path.isfile(path):
            raise RuntimeError(f"RT file not found: {path}")
        return RTFunction(
            txt_file=path,
            n_coeff=10,
            nrt=nrt,
            time_ranges=time_ranges,
        )

    def apply_rt_file(self, rt_path: str, *, nrt=None, time_ranges=None) -> bool:
        if self.backend.is_running():
            print("[GUI] Stop capture or replay before changing the RT calibration.")
            return False
        path = str(rt_path).strip()

        try:
            rt = None if not path else self._load_rt_from_file(path, nrt=nrt, time_ranges=time_ranges)
            if rt is not None and rt.nrt == 2 and TrackFit.available():
                # Reject an outdated native fitter before replacing the active RT.
                TrackFit.from_rt(rt)
        except Exception as e:
            print(f"[GUI] Failed to load RT '{path}': {e}")
            return False

        self.rt = rt
        if hasattr(self.backend, "set_trackfit_rt"):
            self.backend.set_trackfit_rt(self.rt)

        if hasattr(self, "ui"):
            self.ui.rt = self.rt
            self.ui.tab_capture_inst.set_rt_summary(self.rt)
            for tab in getattr(self.ui, "tab_geometries", []):
                if hasattr(tab, "set_rt"):
                    tab.set_rt(self.rt)

        if path:
            print(f"[GUI] Using RT file: {path}, NRT={rt.nrt}")
        else:
            print("[GUI] RT disabled.")
        return True


# =============================================================================
# Stdout / stderr capture helpers
# =============================================================================

class BufferingStream(QObject):
    """
    Capture stdout/stderr BEFORE the UI exists.
    After UI creation, flush buffer into textBrowser.
    """
    textWritten = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buf = []

    def write(self, text):
        if not text:
            return
        self._buf.append(text)
        self.textWritten.emit(text)

    def flush(self):
        pass

    def dump(self) -> str:
        s = "".join(self._buf)
        self._buf.clear()
        return s


class TeeStream(QObject):
    """
    Line-buffered 'tee' stream:
      - writes to the real console stream (stdout OR stderr)
      - also emits complete lines to the GUI
    """
    textWritten = pyqtSignal(str)

    def __init__(self, real_stream, parent=None, add_timestamp=True):
        super().__init__(parent)
        self._real = real_stream
        self._buf = ""
        self._add_ts = add_timestamp

    def write(self, text):
        if not text:
            return

        # 1) ALWAYS write to the real stream (no loss)
        try:
            self._real.write(text)
            self._real.flush()
        except Exception:
            pass

        # 2) Copy to GUI, line-buffered
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)

            if self._add_ts and line != "":
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                out = f"{ts}>> {line}\n"
            else:
                out = line + "\n"

            self.textWritten.emit(out)

    def flush(self):
        # flush any partial line (optional)
        if self._buf:
            line = self._buf
            self._buf = ""
            if self._add_ts and line != "":
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                out = f"{ts}>> {line}\n"
            else:
                out = line + "\n"
            self.textWritten.emit(out)

        try:
            self._real.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self._real.isatty()
        except Exception:
            return False

    @property
    def encoding(self):
        return getattr(self._real, "encoding", "utf-8")


# =============================================================================
# Application entry
# =============================================================================

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # -------------------------------------------------------------------------
    # 1) Capture stdout/stderr during EARLY startup (before UI exists)
    # -------------------------------------------------------------------------
    early_buffer = BufferingStream()
    sys.stdout = early_buffer
    sys.stderr = early_buffer

    # Build the GUI (prints here are captured)
    try:
        myapp = StartQT5()
        myapp.show()
    except Exception:
        sys.__stderr__.write("---- early buffer ----\n")
        sys.__stderr__.write(early_buffer.dump())
        sys.__stderr__.write("\n---- traceback ----\n")
        traceback.print_exc(file=sys.__stderr__)
        sys.__stderr__.flush()
        raise

    # -------------------------------------------------------------------------
    # 2) Tee stdout/stderr to BOTH console and GUI AFTER UI exists
    # -------------------------------------------------------------------------
    tee_out = TeeStream(sys.__stdout__)
    tee_err = TeeStream(sys.__stderr__)

    tee_out.textWritten.connect(myapp.normalOutputWritten)
    tee_err.textWritten.connect(myapp.normalOutputWritten)

    sys.stdout = tee_out
    sys.stderr = tee_err

    # -------------------------------------------------------------------------
    # 3) Flush early startup logs into GUI log
    # -------------------------------------------------------------------------
    early_text = early_buffer.dump()
    if early_text.strip():
        myapp.normalOutputWritten("---- early startup log ----\n")
        myapp.normalOutputWritten(early_text + ("" if early_text.endswith("\n") else "\n"))
        myapp.normalOutputWritten("---- end early startup log ----\n")


    print("MiniDAQ GUI started.\n")

    sys.exit(app.exec_())
