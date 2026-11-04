# backend.py
# Integrates CaptureThread (.dat writing + byte queue) and DecodeThread (event build + stats)
#
# UPDATED behavior (Option C, chamber-based):
#   - event_changed emits (Event_raw, (time_by_chamber, valid_by_chamber)) or (None, None)
#   - cache stores RAW Events (not filtered)
#   - per-chamber checks are computed on-demand PER EVENT (cached per event_id20)
#
# Notes:
#   - Event has NO global hits list. It contains:
#       ev.chambers: Dict[int, ChamberBlock]
#       ev.chambers[cid].hits: Tuple[Hit, ...]
#
# Why this structure (original explanation, still true):
#   - DecodeThread stays fast and simple: it only builds Events and basic histograms.
#   - Backend owns "analysis" logic that can change often (time slew, filtering, QA).
#   - GUI tabs all receive the SAME Event object (one broadcast), but each tab only
#     reads its own chamber_id entry from the emitted dictionaries (no mixing).
#   - Caching is done by event_id20 so back/forward browsing is instant.

from __future__ import annotations

import csv
from copy import copy
import datetime
import glob
import hashlib
import json
import os
import time
import queue
from types import SimpleNamespace
from typing import Optional, Any, Dict, List, Tuple

from PyQt5 import QtCore
import numpy as np

from CaptureThread import CaptureThread
from ReplayThread import DatReplayThread
from DecodeThread import DecodeThread, EventBuffer
from GeoRouter import GeoRouter

# NEW: class-only API (no module-level functions)
from EventQuality import TimeSlewASD2, EventQualityChecker
from TrackFit import TrackFit, TrackFitResult
from rt_function import hit_multilayers


def _timestamp_yyyymmdd_hhmmss() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


TimeByChamber = Dict[int, EventQualityChecker.TimeWindowResult]
ValidByChamber = Dict[int, bool]
FitByChamber = Dict[int, TrackFitResult]

_ALL_NATIVE_SNAPSHOT_FIELDS = frozenset(
    {"adc", "tdc", "adc_ch", "tdc_ch", "ch_hits", "event_hits"}
)
_NATIVE_SNAPSHOT_FIELDS_BY_PLOT_LABEL = {
    "ADC overall": {"adc"},
    "TDC overall": {"tdc"},
    "ADC per CH": {"adc_ch"},
    "TDC per CH": {"tdc_ch"},
    # Triggered CH Hits currently derives valid-event channel counts from ADC-per-channel.
    "CH Hits": {"adc_ch", "ch_hits"},
}

# Payload emitted by event_changed:
#   (Event_raw, (time_by_chamber, valid_by_chamber)) or (None, None)
EventPayload = Tuple[Optional[Any], Optional[Tuple[TimeByChamber, ValidByChamber]]]


class _FitEventReceiver(QtCore.QObject):
    """Separate queued fits so finalization can drain them without UI reentry."""

    @QtCore.pyqtSlot(object)
    def process(self, event):
        self.parent()._on_decoded_event(event)


class Backend(QtCore.QObject):
    """
    Backend wires:
      CaptureThread -> analysis_q -> DecodeThread

    Exposes:
      - message(str): capture messages
      - stats(total_packets, lost_total, total_bytes, filename): capture stats
      - decode_status(DecodeSnapshot): periodic lightweight capture-tab counters
      - analysis_1hz(DecodeSnapshot): periodic decode stats + histograms (valid events only)

    Provides:
      - pop_event() to retrieve valid events from EventBuffer

    Geometry registry (GUI-side, NOT used by DecodeThread):
      - set_geometries_from_list([geo0, geo1, ...])
      - get_geometry(chamber_id)
      - geometry_count()

    Global event navigation:
      - event_changed((Event_raw, (time_by_chamber, valid_by_chamber)) | (None,None))
      - next_event(), prev_event(), goto_event(idx)
      - current_event(), current_index(), cache_size()
      - clear_event_cache()

    Original intent (still the same):
      - CaptureThread does I/O and pushes raw bytes into a bounded queue.
      - DecodeThread does low-level decoding and Event building (fast, no heavy analysis).
      - Backend does higher-level analysis/QA on-demand, and emits payloads to GUI tabs.
    """

    message = QtCore.pyqtSignal(str)
    stats = QtCore.pyqtSignal(int, int, int, str)
    isolation_stats = QtCore.pyqtSignal(object)
    capture_started = QtCore.pyqtSignal()
    # Stop FPGA and collect its final counters before capture/log finalization,
    # including error-triggered stops initiated by the backend itself.
    run_stopping = QtCore.pyqtSignal()
    run_finished = QtCore.pyqtSignal()
    run_log_path_changed = QtCore.pyqtSignal(str)
    decode_status = QtCore.pyqtSignal(object)  # DecodeSnapshot counters for tab_capture
    analysis_1hz = QtCore.pyqtSignal(object)  # DecodeSnapshot

    # Emits: (Event_raw, (time_by_chamber, valid_by_chamber)) or (None, None)
    event_changed = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # bounded queue so decode can't eat RAM
        self._analysis_q: "queue.Queue[bytes]" = queue.Queue(maxsize=256)

        self._cap_thread: Optional[CaptureThread] = None
        self._replay_thread: Optional[DatReplayThread] = None
        self._dec_thread: Optional[DecodeThread] = None

        self._event_buf: Optional[EventBuffer] = None
        self._current_out_path: Optional[str] = None
        self._current_log_path: Optional[str] = None
        self._current_config_path: Optional[str] = None
        self._current_summary_path: Optional[str] = None
        self._current_hit_rate_path: Optional[str] = None
        self._current_channel_status_path: Optional[str] = None
        self._current_warning_path: Optional[str] = None
        self._current_live_geometry_path: Optional[str] = None
        self._current_run_dir: Optional[str] = None
        self._current_run_stem: str = ""
        self._run_context: Dict[str, Any] = {}
        self._fpga_diagnostics = {}
        self._run_started_at: Optional[float] = None
        self._run_finished_at: Optional[float] = None
        self._hit_rate_duration_override_s: Optional[float] = None
        self._hit_rate_duration_source: str = "elapsed capture"
        self._run_artifacts_finalized = False
        self.decode_error_stop_threshold = 1000
        self.acquisition_mode = 0
        self.noise_test_mode = 0
        self._decode_error_auto_stop_pending = False
        self._analysis_emit_suppressed = False
        self._spectra_update_suppressed = False
        self._last_source_stats = SimpleNamespace(
            total_packets=0,
            lost_total=0,
            total_bytes=0,
            filename="",
        )
        self._source_rate_last_time = time.monotonic()
        self._source_rate_last_packets = 0
        self._source_rate_last_bytes = 0
        self._source_rate_packets_s = 0.0
        self._source_rate_bytes_s = 0.0
        self._last_decode_snapshot = None
        self._live_plot_labels = set()
        self._save_plot_labels = set()
        self._live_snapshot_fields = set(_ALL_NATIVE_SNAPSHOT_FIELDS)

        # chamber_id -> Geometry (GUI / mapping only)
        self._geos: Dict[int, Any] = {}

        # cached RAW Events (in the order user browsed)
        self._ev_cache: List[Any] = []
        self._ev_idx: int = -1

        # ---- quality checker (time slew + per-chamber validity) ----
        self._slew = TimeSlewASD2(coefficient=35.59, scale=0.0163)  # ASD2 always

        # You can tune thresholds here.
        # Note: even when checkTime=False, time slew correction is still computed
        # (t_corr_ns / keep_mask are always available for drift circles / debug).
        self._quality = EventQualityChecker(
            min_window_ns=10.0,
            max_window_ns=250.0,
            slew=self._slew,

            n_layers=8,
            min_total_hits=0,
            max_total_hits=16,
            min_layer_hit=6,
            max_hit_per_layer=2,

            checkTime=True,
            checkHitcount=True,
        )

        # Cache computed per-event quality and fit results keyed by event_id20.
        # Fit results are reused so chamber validity and spectra filling do not
        # rerun the same fit for the same chamber-event.
        self._qc_cache: Dict[int, Tuple[TimeByChamber, ValidByChamber]] = {}
        self._fit_cache: Dict[int, FitByChamber] = {}

        # Framed triggerless spectra use the fitted T0 of each chamber-event.
        self._trackfit: Optional[TrackFit] = None
        self._fit_tdc_bins = 512
        self._fit_tdc_tmin_ns = -100.0
        self._fit_tdc_tmax_ns = 300.0
        self._fit_tdc_binw_ns = (self._fit_tdc_tmax_ns - self._fit_tdc_tmin_ns) / float(self._fit_tdc_bins)
        self._fit_max_tdcs = 40
        self._fit_max_channels = 24
        self._fit_adc_bins = 256
        self._fit_adc_hist = np.zeros((self._fit_max_tdcs, self._fit_adc_bins), dtype=np.uint32)
        self._fit_adc_ch_hist = np.zeros(
            (self._fit_max_tdcs, self._fit_max_channels, self._fit_adc_bins),
            dtype=np.uint32,
        )
        self._fit_tdc_hist = np.zeros((self._fit_max_tdcs, self._fit_tdc_bins), dtype=np.uint32)
        self._fit_tdc_ch_hist = np.zeros(
            (self._fit_max_tdcs, self._fit_max_channels, self._fit_tdc_bins),
            dtype=np.uint32,
        )
        self._fit_resid_bins = 400
        self._fit_resid_min_mm = -5.0
        self._fit_resid_max_mm = 5.0
        self._fit_resid_binw_mm = (self._fit_resid_max_mm - self._fit_resid_min_mm) / float(self._fit_resid_bins)
        self._fit_resid_hist = np.zeros((self._fit_max_tdcs, self._fit_resid_bins), dtype=np.uint32)
        self._fit_resid_hist_by_chamber: Dict[int, np.ndarray] = {}
        self._fit_evt_total = 0
        self._fit_evt_valid = 0

        self._replay_draining = False
        self._replay_empty_streak = 0
        self._fit_event_receiver = _FitEventReceiver(self)

    @property
    def _trackfit_enabled(self) -> bool:
        return self.acquisition_mode == 1 and self.noise_test_mode == 0

    def set_acquisition_mode(self, mode: int) -> None:
        mode = int(mode)
        if mode not in (0, 1):
            raise ValueError(f"Unsupported acquisition_mode: {mode}")
        if self.is_running():
            raise RuntimeError("Cannot change acquisition_mode while capture or replay is running")
        if self.acquisition_mode != mode:
            self.acquisition_mode = mode
            self._qc_cache.clear()
            self._fit_cache.clear()
            self._reset_fit_hists()

    def set_noise_test_mode(self, mode: int) -> None:
        mode = int(mode)
        if mode not in (0, 1, 2):
            raise ValueError(f"Unsupported noise_test_mode: {mode}")
        if self.is_running():
            raise RuntimeError("Cannot change noise_test_mode while capture or replay is running")
        if self.noise_test_mode != mode:
            self.noise_test_mode = mode
            self._qc_cache.clear()
            self._fit_cache.clear()
            self._reset_fit_hists()

    @staticmethod
    def _snapshot_fields_for_plot_labels(labels) -> set[str]:
        fields = set()
        for label in labels or ():
            text = str(label)
            requested = _NATIVE_SNAPSHOT_FIELDS_BY_PLOT_LABEL.get(text)
            if requested is not None:
                fields.update(requested)
            elif text.startswith("Geometry"):
                fields.update(("ch_hits", "event_hits"))
        return fields

    def set_plot_selections(self, live_labels, save_labels) -> None:
        self._live_plot_labels = set(str(label) for label in (live_labels or ()) if str(label))
        self._save_plot_labels = set(str(label) for label in (save_labels or ()) if str(label))
        self._live_snapshot_fields = self._snapshot_fields_for_plot_labels(self._live_plot_labels)
        if self._dec_thread is not None:
            self._dec_thread.set_snapshot_fields(self._live_snapshot_fields)

    def _final_snapshot_fields(self) -> set[str]:
        fields = self._snapshot_fields_for_plot_labels(
            self._live_plot_labels | self._save_plot_labels
        )
        # Run summaries, channel-rate CSVs, and noise scans always need this small family.
        fields.add("ch_hits")
        return fields

    def set_trackfit_rt(self, rt: Any, *, n_lut: int = 2048, min_hits: int = 6) -> None:
        """
        Prepare the shared fitter for event-T0 spectra in framed triggerless mode.
        RT can be loaded before the acquisition mode is selected.
        """
        # MDT curves extend beyond the original sMDT timing range.
        self._quality.max_window_ns = 250.0 if rt is None else float(rt.Tmax - rt.T0)
        self._rt_source_tables = list(getattr(rt, "source_tables", []))
        self._rt_calibration_snapshot = None if rt is None else {
            "file": rt.file_path,
            "nrt": rt.nrt,
            "time_ranges_ns": rt.time_ranges.tolist(),
            "coefficients": [params.tolist() for params in rt.params_by_ml],
        }
        self._fit_tdc_tmin_ns = min(-100.0, float(rt.T0) - 100.0) if rt is not None else -100.0
        upper = max(300.0, float(rt.Tmax) + 100.0) if rt is not None else 300.0
        self._fit_tdc_bins = int(np.ceil((upper - self._fit_tdc_tmin_ns) / self._fit_tdc_binw_ns))
        self._fit_tdc_tmax_ns = self._fit_tdc_tmin_ns + self._fit_tdc_bins * self._fit_tdc_binw_ns
        self._fit_tdc_hist = np.zeros((self._fit_max_tdcs, self._fit_tdc_bins), dtype=np.uint32)
        self._fit_tdc_ch_hist = np.zeros(
            (self._fit_max_tdcs, self._fit_max_channels, self._fit_tdc_bins), dtype=np.uint32,
        )

        if rt is None:
            self._trackfit = None
            self._qc_cache.clear()
            self._fit_cache.clear()
            self._reset_fit_hists()
            print("[Backend] TrackFit disabled (rt is None).")
            return
        try:
            self._trackfit = TrackFit.from_rt(
                rt,
                n_lut=int(n_lut),
                min_hits=int(min_hits),
                fit_only_kept_hits=True,
            )
            self._qc_cache.clear()
            self._fit_cache.clear()
            self._reset_fit_hists()
            print("[Backend] TrackFit ready: triggerless spectra use t_corr - event T0.")
        except Exception as e:
            self._trackfit = None
            self._qc_cache.clear()
            self._fit_cache.clear()
            self._reset_fit_hists()
            print(f"[Backend] TrackFit init failed: {e}")

    def trackfit_for_chamber(self, chamber_id):
        return getattr(self, "_trackfits_by_chamber", {}).get(int(chamber_id), self._trackfit)

    def set_chamber_rt(self, chamber_id, rt):
        """Assign a calibration without changing another chamber's fitter."""
        if self.is_running():
            raise RuntimeError("Stop capture/replay before changing RT calibration.")
        fitter = None if rt is None or not TrackFit.available() else TrackFit.from_rt(
            rt, n_lut=2048, min_hits=6, fit_only_kept_hits=True)
        models = dict(getattr(self, "_rts_by_chamber", {}))
        fitters = dict(getattr(self, "_trackfits_by_chamber", {}))
        models[int(chamber_id)] = rt
        fitters[int(chamber_id)] = fitter
        active = [model for model in models.values() if model is not None]
        self.set_trackfit_rt(max(active, key=lambda model: model.Tmax - model.T0) if active else None)
        self._rts_by_chamber = models
        self._trackfits_by_chamber = fitters
        if active:
            self._fit_tdc_tmin_ns = min(-100.0, min(model.T0 for model in active) - 100.0)
            upper = max(300.0, max(model.Tmax for model in active) + 100.0)
            self._fit_tdc_bins = int(np.ceil((upper - self._fit_tdc_tmin_ns) / self._fit_tdc_binw_ns))
            self._fit_tdc_tmax_ns = self._fit_tdc_tmin_ns + self._fit_tdc_bins * self._fit_tdc_binw_ns
            self._fit_tdc_hist = np.zeros((self._fit_max_tdcs, self._fit_tdc_bins), dtype=np.uint32)
            self._fit_tdc_ch_hist = np.zeros((self._fit_max_tdcs, self._fit_max_channels, self._fit_tdc_bins), dtype=np.uint32)
        self._rt_calibration_snapshot = {str(cid): None if model is None else {
            "file": model.file_path, "nrt": model.nrt,
            "time_ranges_ns": model.time_ranges.tolist(),
            "coefficients": [params.tolist() for params in model.params_by_ml],
        } for cid, model in models.items()}
        self._rt_source_tables = [path for model in active
                                  for path in [model.file_path, *model.source_tables]]

    def _reset_fit_hists(self) -> None:
        self._fit_adc_hist.fill(0)
        self._fit_adc_ch_hist.fill(0)
        self._fit_tdc_hist.fill(0)
        self._fit_tdc_ch_hist.fill(0)
        self._fit_resid_hist.fill(0)
        self._fit_resid_hist_by_chamber.clear()
        self._fit_evt_total = 0
        self._fit_evt_valid = 0

    def reset_fit_spectra(self) -> None:
        """
        Clear accumulated fit-based histograms. Geometry edits during replay do not
        retroactively remap old decoded data, so callers should clear these before
        rerunning replay with a new geometry.
        """
        self._reset_fit_hists()

    # ---------------- geometry registry (GUI-side) ----------------

    def set_geometries_from_list(self, geos: List[Any]) -> None:
        out: Dict[int, Any] = {}
        for g in (geos or []):
            if g is None:
                continue
            cid = int(getattr(g, "chamber_id", -1))
            if cid < 0:
                raise ValueError("Geometry missing valid chamber_id (must be >= 0)")
            if cid in out:
                raise ValueError(f"Duplicate chamber_id {cid}")
            out[cid] = g
        self._geos = out

    def set_geometries(self, geos: Dict[int, Any]) -> None:
        out: Dict[int, Any] = {}
        for cid, g in (geos or {}).items():
            if g is None:
                continue
            out[int(cid)] = g
        self._geos = out

    def get_geometry(self, chamber_id: int) -> Optional[Any]:
        return self._geos.get(int(chamber_id))

    def geometry_count(self) -> int:
        return len(self._geos)

    def geometries(self) -> Dict[int, Any]:
        return dict(self._geos)

    def _geo_for_decode_thread(self) -> Optional[Any]:
        """
        Always return a GeoRouter if at least one geometry exists.
        0 geos  -> None
        >=1     -> GeoRouter(tdcid -> geo)
        """
        geos = list(self._geos.values())
        if not geos:
            return None

        by_tdc: Dict[int, Any] = {}

        for g in geos:
            # ensure mapping arrays are applied
            try:
                g.set_assignment(g.slots_per_ml, g.ml0, g.ml1, apply_map=True)
            except Exception:
                pass

            max_tdc = int(getattr(g, "MAX_TDC", 40))
            is_active = getattr(g, "isActiveTDC", None)
            if not is_active:
                continue

            for t in range(max_tdc):
                try:
                    if int(is_active[t]) == 1:
                        if t in by_tdc:
                            print(f"[WARN] TDC {t} assigned to multiple chambers. First wins.")
                            continue
                        by_tdc[t] = g
                except Exception:
                    pass

        if not by_tdc:
            print("[WARN] No active TDCs found in any geometry.")
            return None

        print("[Decode geo router] TDC mapping:", sorted((t, g.chamber_id) for t, g in by_tdc.items()))
        return GeoRouter(by_tdc)

    # ---------------- public API ----------------

    def is_running(self) -> bool:
        return any(
            t is not None and t.isRunning()
            for t in (self._cap_thread, self._replay_thread, self._dec_thread)
        )

    def set_spectra_update_suppressed(self, suppressed: bool) -> None:
        self._spectra_update_suppressed = bool(suppressed)

    def spectra_update_suppressed(self) -> bool:
        return bool(self._spectra_update_suppressed)

    def _reset_source_rates(self) -> None:
        self._source_rate_last_time = time.monotonic()
        self._source_rate_last_packets = 0
        self._source_rate_last_bytes = 0
        self._source_rate_packets_s = 0.0
        self._source_rate_bytes_s = 0.0

    def set_analysis_emit_suppressed(self, suppressed: bool) -> None:
        self._analysis_emit_suppressed = bool(suppressed)

    def analysis_emit_suppressed(self) -> bool:
        return bool(self._analysis_emit_suppressed)

    def make_out_path(self, out_dir: str, run: int, prefix: str = "") -> str:
        out_dir = out_dir.strip() or os.getcwd()
        ts = _timestamp_yyyymmdd_hhmmss()
        safe_prefix = os.path.basename(str(prefix or "").strip())
        prefix_part = safe_prefix if not safe_prefix or safe_prefix.endswith("_") else f"{safe_prefix}_"
        stem = f"run{run:05d}_{prefix_part}{ts}"
        return self.make_data_path(out_dir, stem)

    def make_data_path(self, out_dir: str, stem: str) -> str:
        out_dir = str(out_dir or "").strip() or os.getcwd()
        stem = os.path.splitext(os.path.basename(str(stem).strip()))[0]
        run_dir = os.path.join(out_dir, stem)
        return os.path.join(run_dir, f"{stem}.dat")

    def make_log_path(self, data_path: str) -> str:
        root, _ = os.path.splitext(str(data_path))
        return root + ".log"

    def prepare_run_artifacts(self, data_path: str, context: Optional[Dict[str, Any]] = None,
                              *, artifact_dir: Optional[str] = None) -> str:
        data_path = os.path.abspath(str(data_path))
        run_dir = os.path.abspath(artifact_dir) if artifact_dir else os.path.dirname(data_path)
        stem = os.path.splitext(os.path.basename(data_path))[0]

        self._current_out_path = data_path
        self._current_run_dir = run_dir
        self._current_run_stem = stem
        self._current_log_path = os.path.join(run_dir, f"{stem}.log")
        self._current_config_path = os.path.join(run_dir, f"{stem}_configuration.txt")
        self._current_summary_path = os.path.join(run_dir, f"{stem}_summary.txt")
        self._current_hit_rate_path = os.path.join(run_dir, f"{stem}_channel_hit_rates.csv")
        self._current_channel_status_path = os.path.join(run_dir, f"{stem}_dead_noisy_channels.txt")
        self._current_warning_path = os.path.join(run_dir, f"{stem}_warnings_errors.txt")
        self._current_live_geometry_path = os.path.join(run_dir, f"{stem}_live_geometry.txt")
        self._run_context = dict(context or {})
        self._fpga_diagnostics = {}
        self._run_context.setdefault("data_file", data_path)
        self._run_context.setdefault("run_directory", run_dir)
        self._run_context.setdefault("run_stem", stem)
        self._run_context.setdefault("live_geometry_file", self._current_live_geometry_path)
        self._run_started_at = None
        self._run_finished_at = None
        self._run_artifacts_finalized = False
        self._last_decode_snapshot = None
        self._last_source_stats = SimpleNamespace(
            total_packets=0,
            lost_total=0,
            total_bytes=0,
            filename=os.path.basename(data_path),
        )

        os.makedirs(run_dir, exist_ok=True)
        self.run_log_path_changed.emit(self._current_log_path)
        self._write_live_geometry_file()
        self._write_run_config()
        return self._current_log_path

    def prepare_run_log(self, data_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        return self.prepare_run_artifacts(data_path, context=context)

    def prepare_replay_log(self, data_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        # Keep the original mode metadata, acquisition duration and diagnostics.
        from replay_format import replay_modes
        mode, noise, source = replay_modes(data_path, (self.acquisition_mode, self.noise_test_mode))
        context = dict(context or {})
        context.update(mode="replay", acquisition_mode=mode, noise_test_mode=noise,
                       replay_format_source=source)
        folder = os.path.join(os.path.dirname(os.path.abspath(data_path)), "replays",
                              datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        context["output_dir"] = folder
        return self.prepare_run_artifacts(data_path, context=context, artifact_dir=folder)

    @staticmethod
    def _format_ts(ts: Optional[float]) -> str:
        if ts is None:
            return ""
        try:
            return datetime.datetime.fromtimestamp(float(ts)).isoformat(timespec="seconds")
        except Exception:
            return ""

    @staticmethod
    def _safe_value(value: Any) -> str:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return str(value)
        try:
            return repr(value)
        except Exception:
            return str(type(value).__name__)

    @staticmethod
    def _array_total(values: Any) -> int:
        if values is None:
            return 0
        try:
            return int(np.asarray(values).sum())
        except Exception:
            try:
                return int(sum(int(v) for v in values))
            except Exception:
                return 0

    def _run_duration_s(self) -> float:
        if self._run_started_at is None:
            return 0.0
        end = self._run_finished_at if self._run_finished_at is not None else time.time()
        return max(0.0, float(end) - float(self._run_started_at))

    @staticmethod
    def _recorded_run_duration_s(data_path: str) -> Optional[float]:
        root, _ = os.path.splitext(os.path.abspath(str(data_path)))
        summary_path = root + "_summary.txt"
        fallback_duration_s = None
        try:
            with open(summary_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    key, sep, value = line.partition(":")
                    if not sep:
                        continue
                    key = key.strip()
                    if key not in ("hit_rate_duration_s", "duration_s"):
                        continue
                    duration_s = float(value.strip())
                    if duration_s <= 0.0:
                        continue
                    if key == "hit_rate_duration_s":
                        return duration_s
                    fallback_duration_s = duration_s
        except (OSError, ValueError):
            pass
        return fallback_duration_s

    def _hit_rate_duration_s(self) -> float:
        override = self._hit_rate_duration_override_s
        if override is not None and float(override) > 0.0:
            return float(override)
        return self._run_duration_s()

    def _write_live_geometry_file(self) -> None:
        path = self._current_live_geometry_path
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8", errors="replace") as f:
                f.write("# MiniDAQ live geometry snapshot\n")
                f.write(f"# created: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
                f.write(f"# run_directory: {self._current_run_dir or ''}\n")
                f.write(f"# run_stem: {self._current_run_stem or ''}\n")
                if not self._geos:
                    f.write("\n# No live geometries registered.\n")
                    return

                for cid, geo in sorted(self._geos.items()):
                    try:
                        if hasattr(geo, "assignment_by_ml"):
                            geo.set_assignment(
                                getattr(geo, "slots_per_ml", 0),
                                ml_slots=geo.assignment_by_ml(),
                                n_mls=getattr(geo, "n_mls", 2),
                                apply_map=True,
                            )
                        else:
                            geo.set_assignment(
                                getattr(geo, "slots_per_ml", 0),
                                getattr(geo, "ml0", []),
                                getattr(geo, "ml1", []),
                                apply_map=True,
                            )
                    except Exception:
                        pass

                    f.write(f"\n# ===== chamber_id {int(cid)} =====\n")
                    f.write(f"chamber_id {int(cid)}\n\n")
                    if hasattr(geo, "to_text"):
                        text = geo.to_text()
                        f.write(str(text).rstrip())
                        f.write("\n")
                    else:
                        for name in (
                            "chamberType",
                            "MAX_TDC",
                            "MAX_TDC_CHANNEL",
                            "MAX_TUBE_LAYER",
                            "MAX_TUBE_COLUMN",
                            "MAX_TDC_LAYER",
                            "flipTDCs",
                            "tdcColByTubeNo",
                        ):
                            f.write(f"{name} {self._safe_value(getattr(geo, name, ''))}\n")
        except Exception as e:
            self.message.emit(
                "[ERROR] Failed to write live geometry snapshot: "
                f"path={path} error={repr(e)}\n"
            )

    def _config_snapshot_paths(self) -> List[str]:
        here = os.path.dirname(os.path.abspath(__file__))
        paths: List[str] = []

        for key in ("settings_file", "rt_file"):
            value = str(self._run_context.get(key, "") or "").strip()
            if value:
                paths.append(value)
        paths.extend(getattr(self, "_rt_source_tables", []))

        paths.extend(
            [
                os.path.join(here, "capture_settings.ini"),
                os.path.join(here, "mini_sMDT.txt"),
                os.path.join(here, "geometry.txt"),
            ]
        )
        paths.extend(sorted(glob.glob(os.path.join(here, "Mezz_setup", "*.txt"))))

        out: List[str] = []
        seen = set()
        for path in paths:
            if not path:
                continue
            apath = os.path.abspath(os.path.expanduser(path))
            if apath in seen or not os.path.isfile(apath):
                continue
            seen.add(apath)
            out.append(apath)
        return out

    def _write_run_config(self) -> None:
        path = self._current_config_path
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8", errors="replace") as f:
                f.write("MiniDAQ run configuration\n")
                f.write(f"created: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
                f.write(f"run_directory: {self._current_run_dir or ''}\n")
                f.write(f"data_file: {self._current_out_path or ''}\n")
                f.write(f"log_file: {self._current_log_path or ''}\n")
                f.write(f"summary_file: {self._current_summary_path or ''}\n")
                f.write(f"channel_hit_rates_csv: {self._current_hit_rate_path or ''}\n")
                f.write(f"dead_noisy_channels_file: {self._current_channel_status_path or ''}\n")
                f.write(f"warnings_errors_file: {self._current_warning_path or ''}\n")
                f.write(f"live_geometry_file: {self._current_live_geometry_path or ''}\n")

                f.write("\n[run_context]\n")
                for key in sorted(self._run_context):
                    f.write(f"{key}: {self._safe_value(self._run_context.get(key))}\n")

                f.write("\n[decode_histogram_settings]\n")
                f.write("tdc_bins: 1024\n")
                f.write("tdc_shift: 0\n")
                f.write("tdc_min_ns: 0.0\n")
                f.write("tdc_max_ns: 800.0\n")
                f.write("channel_tdc_bins: 1024\n")
                f.write("channel_tdc_shift: 0\n")
                f.write("channel_tdc_min_ns: 0.0\n")
                f.write("channel_tdc_max_ns: 800.0\n")

                f.write("\n[tdc_spectrum_settings]\n")
                if self._trackfit_enabled:
                    f.write("reference: slew-corrected event time minus fitted chamber-event T0\n")
                    f.write(f"bins: {self._fit_tdc_bins}\n")
                    f.write(f"min_ns: {self._fit_tdc_tmin_ns}\n")
                    f.write(f"max_ns: {self._fit_tdc_tmax_ns}\n")
                else:
                    f.write("reference: decoder hit_ledge - trigger_ledge\n")

                f.write("\n[event_quality]\n")
                quality = self._quality
                for name in (
                    "min_window_ns",
                    "max_window_ns",
                    "n_layers",
                    "min_total_hits",
                    "max_total_hits",
                    "min_layer_hit",
                    "max_hit_per_layer",
                    "checkTime",
                    "checkHitcount",
                ):
                    f.write(f"{name}: {self._safe_value(getattr(quality, name, ''))}\n")

                f.write("\n[geometry]\n")
                if not self._geos:
                    f.write("none\n")
                for cid, geo in sorted(self._geos.items()):
                    f.write(f"\nchamber_id: {cid}\n")
                    for name in (
                        "chamberType",
                        "MAX_TDC",
                        "MAX_TDC_CHANNEL",
                        "MAX_TUBE_LAYER",
                        "MAX_TUBE_COLUMN",
                        "flipTDCs",
                        "tdcColByTubeNo",
                    ):
                        f.write(f"{name}: {self._safe_value(getattr(geo, name, ''))}\n")
                    active = []
                    is_active = getattr(geo, "isActiveTDC", None)
                    if is_active is not None:
                        try:
                            active = [i for i, val in enumerate(is_active) if int(val) == 1]
                        except Exception:
                            active = []
                    f.write(f"active_tdcs: {active}\n")

                f.write("\n[rt_calibration]\n")
                f.write(json.dumps(getattr(self, "_rt_calibration_snapshot", None), indent=2))
                f.write("\n[configuration_file_snapshots]\n")
                for cfg_path in self._config_snapshot_paths():
                    f.write(f"\n--- {cfg_path} ---\n")
                    try:
                        if cfg_path.lower().endswith(".root"):
                            digest = hashlib.sha256()
                            with open(cfg_path, "rb") as src:
                                for block in iter(lambda: src.read(1024 * 1024), b""):
                                    digest.update(block)
                            f.write(f"Binary ROOT calibration; SHA-256: {digest.hexdigest()}\n")
                            continue
                        with open(cfg_path, "r", encoding="utf-8", errors="replace") as src:
                            f.write(src.read())
                            if not f.tell():
                                f.write("\n")
                    except Exception as e:
                        f.write(f"[ERROR] Failed to read configuration file: {repr(e)}\n")
                    f.write("\n")
        except Exception as e:
            self.message.emit(
                "[ERROR] Failed to write run configuration: "
                f"path={path} error={repr(e)}\n"
            )

    def _warning_error_counts(self) -> Tuple[int, int]:
        path = self._current_warning_path
        if not path or not os.path.isfile(path):
            return 0, 0
        warn = 0
        err = 0
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "[WARN]" in line:
                        warn += 1
                    if "[ERROR]" in line:
                        err += 1
        except Exception:
            return warn, err
        return warn, err

    def _nonzero_counts(self, values: Any) -> List[Tuple[int, int]]:
        if values is None:
            return []
        try:
            arr = np.asarray(values)
            return [(int(i), int(v)) for i, v in enumerate(arr.tolist()) if int(v) != 0]
        except Exception:
            return []

    def _geometry_channel_info(self, tdc: int, ch: int) -> Tuple[int, int, int, float, float, int]:
        for cid, geo in sorted(self._geos.items()):
            active = 0
            is_active = getattr(geo, "isActiveTDC", None)
            if is_active is not None:
                try:
                    active = 1 if int(is_active[int(tdc)]) == 1 else 0
                except Exception:
                    active = 0
            if not active:
                continue
            try:
                x, y, layer, col = geo.wire_center_from_hit(int(tdc), int(ch))
                return int(cid), int(layer), int(col), float(x), float(y), active
            except Exception:
                return int(cid), -1, -1, float("nan"), float("nan"), active
        return -1, -1, -1, float("nan"), float("nan"), 0

    def _selected_tdc_ids_for_run(self, n_tdc: int) -> List[int]:
        selected = self._run_context.get("selected_tdc_ids", None)
        if selected is None:
            selected_mezz = self._run_context.get(
                "selected_mezz",
                self._run_context.get("noise_scan_selected_mezz", None),
            )
            if selected_mezz is None:
                return list(range(max(0, int(n_tdc))))
            selected = []
            for item in selected_mezz:
                try:
                    which_csm, mezz = item
                    selected.append(int(which_csm) * 20 + int(mezz))
                except Exception:
                    continue

        out = set()
        try:
            values = list(selected)
        except Exception:
            values = []
        for value in values:
            try:
                tdc = int(value)
            except Exception:
                continue
            if 0 <= tdc < int(n_tdc):
                out.add(tdc)
        return sorted(out)

    @staticmethod
    def _int_or(value: Any, default: int = -1) -> int:
        try:
            return int(value)
        except Exception:
            return int(default)

    def _disabled_channel_entries_for_run(self) -> List[Dict[str, Any]]:
        raw = self._run_context.get(
            "disabled_channels",
            self._run_context.get("noise_scan_disabled_channels", []),
        )
        if raw is None:
            return []

        entries: List[Dict[str, Any]] = []
        if isinstance(raw, dict):
            iterable = []
            for tdc, channels in raw.items():
                for ch in channels or []:
                    iterable.append({"tdc_global": tdc, "channel_id": ch})
        else:
            try:
                iterable = list(raw)
            except Exception:
                iterable = []

        seen = set()
        for item in iterable:
            if not isinstance(item, dict):
                continue
            tdc = self._int_or(item.get("tdc_global", item.get("tdc_id", -1)))
            ch = self._int_or(item.get("channel_id", -1))
            if tdc < 0 or ch < 0:
                continue
            key = (tdc, ch)
            if key in seen:
                continue
            seen.add(key)

            csm = self._int_or(item.get("csm_id", item.get("which_csm", tdc // 20)))
            mezz = self._int_or(item.get("mezz", tdc % 20))
            disabled_in = str(
                item.get("disabled_in", item.get("disabled_source", item.get("source", "configured")))
                or "configured"
            )
            reason = str(item.get("disabled_reason", item.get("reason", "")) or "")
            location = str(item.get("location", "") or "").strip()
            if not location:
                location = f"CSM{csm}/Mezz{mezz}/TDC{tdc:02d}/CH{ch:02d}"

            entries.append({
                "tdc_id": int(tdc),
                "tdc_global": int(tdc),
                "channel_id": int(ch),
                "csm_id": int(csm),
                "mezz": int(mezz),
                "disabled_in": disabled_in,
                "disabled_reason": reason,
                "location": location,
            })

        return sorted(entries, key=lambda row: (row["tdc_id"], row["channel_id"]))

    def _disabled_channel_map_for_run(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        return {
            (int(row["tdc_id"]), int(row["channel_id"])): row
            for row in self._disabled_channel_entries_for_run()
        }

    @staticmethod
    def _disabled_channel_summary_line(row: Dict[str, Any]) -> str:
        location = str(row.get("location", "") or "").strip()
        if not location:
            location = (
                f"CSM{int(row.get('csm_id', -1))}/Mezz{int(row.get('mezz', -1))}/"
                f"TDC{int(row.get('tdc_id', -1)):02d}/CH{int(row.get('channel_id', -1)):02d}"
            )
        source = str(row.get("disabled_in", "") or "").strip()
        reason = str(row.get("disabled_reason", "") or "").strip()
        text = location
        if source:
            text += f" disabled_in={source}"
        if reason:
            text += f" reason={reason}"
        return text

    def _write_channel_hit_rates(self, snap: Any) -> None:
        path = self._current_hit_rate_path
        if not path:
            return

        duration_s = self._hit_rate_duration_s()
        if int(self.acquisition_mode) == 0 and snap is not None:
            event_windows = int(getattr(snap, "headers", 0) or 0)
            if event_windows <= 0:
                event_windows = int(getattr(snap, "events_fifoA", 0) or 0) + int(
                    getattr(snap, "events_fifoB", 0) or 0
                )
            if event_windows <= 0:
                event_windows = int(getattr(snap, "trailers", 0) or 0)
            duration_s = float(event_windows) * 60.0 * 25.0e-9
        if int(self.noise_test_mode) == 2:
            raw_counts = getattr(snap, "noise_counter_total", None) if snap is not None else None
        else:
            raw_counts = getattr(snap, "raw_hit_ch_count", None) if snap is not None else None
        valid_hist = getattr(snap, "adc_ch_hist", None) if snap is not None else None

        if raw_counts is not None:
            raw_arr = np.asarray(raw_counts, dtype=np.uint64)
        else:
            raw_arr = np.zeros((40, 24), dtype=np.uint64)

        if valid_hist is not None:
            valid_arr = np.asarray(valid_hist, dtype=np.uint64).sum(axis=2)
        else:
            valid_arr = np.zeros_like(raw_arr)

        n_tdc = max(int(raw_arr.shape[0]), int(valid_arr.shape[0]))
        n_ch = max(int(raw_arr.shape[1]), int(valid_arr.shape[1]))
        selected_tdcs = self._selected_tdc_ids_for_run(n_tdc)
        disabled_channels = self._disabled_channel_map_for_run()
        rows = []

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "tdc_id",
                        "channel_id",
                        "chamber_id",
                        "layer",
                        "column",
                        "x_mm",
                        "y_mm",
                        "active_tdc",
                        "disabled",
                        "disabled_in",
                        "disabled_reason",
                        "raw_hit_count",
                        "raw_hit_rate_hz",
                        "valid_event_hit_count",
                        "valid_event_hit_rate_hz",
                        "duration_s",
                    ],
                )
                writer.writeheader()
                for tdc in selected_tdcs:
                    for ch in range(n_ch):
                        raw = int(raw_arr[tdc, ch]) if tdc < raw_arr.shape[0] and ch < raw_arr.shape[1] else 0
                        valid = int(valid_arr[tdc, ch]) if tdc < valid_arr.shape[0] and ch < valid_arr.shape[1] else 0
                        raw_rate_hz = float(raw) / duration_s if duration_s > 0.0 else 0.0
                        valid_rate_hz = float(valid) / duration_s if duration_s > 0.0 else 0.0
                        cid, layer, col, x, y, active = self._geometry_channel_info(tdc, ch)
                        disabled_info = disabled_channels.get((int(tdc), int(ch)), {})
                        row = {
                            "tdc_id": int(tdc),
                            "channel_id": int(ch),
                            "chamber_id": int(cid),
                            "layer": int(layer),
                            "column": int(col),
                            "x_mm": x,
                            "y_mm": y,
                            "active_tdc": int(active),
                            "disabled": 1 if disabled_info else 0,
                            "disabled_in": str(disabled_info.get("disabled_in", "") or ""),
                            "disabled_reason": str(disabled_info.get("disabled_reason", "") or ""),
                            "raw_hit_count": raw,
                            "raw_hit_rate_hz": f"{raw_rate_hz:.2f}",
                            "valid_event_hit_count": valid,
                            "valid_event_hit_rate_hz": f"{valid_rate_hz:.2f}",
                            "duration_s": f"{duration_s:.2f}",
                        }
                        writer.writerow(row)
                        rows.append(row)
            self._write_dead_noisy_channels(rows)
        except Exception as e:
            self.message.emit(
                "[ERROR] Failed to write channel hit-rate CSV: "
                f"path={path} error={repr(e)}\n"
            )

    def _write_dead_noisy_channels(self, rows) -> None:
        path = self._current_channel_status_path
        if not path:
            return

        enabled_rows = [row for row in rows if not int(row.get("disabled", 0) or 0)]
        disabled_rows = [row for row in rows if int(row.get("disabled", 0) or 0)]
        counts = np.asarray(
            [int(row.get("raw_hit_count", 0) or 0) for row in enabled_rows],
            dtype=np.float64,
        )
        mean_count = float(np.mean(counts)) if counts.size else 0.0
        sigma_count = float(np.std(counts)) if counts.size else 0.0
        noisy_threshold = mean_count + 3.0 * sigma_count
        dead = [row for row in enabled_rows if int(row.get("raw_hit_count", 0) or 0) == 0]
        noisy = [
            row
            for row in enabled_rows
            if float(row.get("raw_hit_count", 0) or 0) > noisy_threshold
        ]

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("MiniDAQ dead/noisy channel report\n")
                f.write(f"source_csv: {self._current_hit_rate_path or ''}\n")
                f.write(f"channels_total: {len(rows)}\n")
                f.write(f"channels_analyzed: {len(enabled_rows)}\n")
                f.write(f"disabled_channel_count: {len(disabled_rows)}\n")
                f.write("classification_count_source: raw_hit_count\n")
                f.write("dead_definition: enabled channel with raw_hit_count == 0\n")
                f.write("noisy_definition: enabled channel with raw_hit_count > mean + 3 * population_sigma\n")
                f.write("disabled_channels_excluded: yes\n")
                f.write(f"mean_hit_count: {mean_count:.2f}\n")
                f.write(f"population_sigma_hit_count: {sigma_count:.2f}\n")
                f.write(f"noisy_threshold_hit_count: {noisy_threshold:.2f}\n")
                f.write(f"dead_channel_count: {len(dead)}\n")
                f.write(f"noisy_channel_count: {len(noisy)}\n")

                f.write("\n[disabled_channels]\n")
                if not disabled_rows:
                    f.write("none\n")
                for row in disabled_rows:
                    f.write(self._channel_status_line(row))

                f.write("\n[dead_channels]\n")
                if not dead:
                    f.write("none\n")
                for row in dead:
                    f.write(self._channel_status_line(row))

                f.write("\n[noisy_channels]\n")
                if not noisy:
                    f.write("none\n")
                for row in noisy:
                    f.write(self._channel_status_line(row))
        except Exception as e:
            self.message.emit(
                "[ERROR] Failed to write dead/noisy channel report: "
                f"path={path} error={repr(e)}\n"
            )

    @staticmethod
    def _channel_status_line(row) -> str:
        line = (
            f"TDC{int(row.get('tdc_id', -1)):02d} "
            f"CH{int(row.get('channel_id', -1)):02d} "
            f"hits={int(row.get('raw_hit_count', 0) or 0)} "
            f"rate_hz={row.get('raw_hit_rate_hz', '0.00')} "
            f"chamber={int(row.get('chamber_id', -1))} "
            f"layer={int(row.get('layer', -1))} "
            f"column={int(row.get('column', -1))}"
        )
        disabled_in = str(row.get("disabled_in", "") or "").strip()
        disabled_reason = str(row.get("disabled_reason", "") or "").strip()
        if disabled_in:
            line += f" disabled_in={disabled_in}"
        if disabled_reason:
            line += f" disabled_reason={disabled_reason}"
        return line + "\n"

    def record_fpga_diagnostics(self, phase, snapshot, baseline, *, error=None):
        from fpga_diagnostics import COUNTERS
        if error is not None:
            self._fpga_diagnostics[phase + "_error"] = str(error)
            self.message.emit(f"[WARN] FPGA diagnostics {phase}: {error}\n")
            return
        record = snapshot.as_dict()
        self._fpga_diagnostics.pop(phase + "_error", None)
        self._fpga_diagnostics[phase] = record
        if baseline is not None:
            totals = snapshot.delta(baseline)
            record["run_totals"] = [dict(zip((key for key, _ in COUNTERS), row)) for row in totals]
        if phase != "latest":
            self.message.emit(f"[FPGA diagnostics {phase}] {json.dumps(record, sort_keys=True)}\n")

    def _write_run_summary(self, snap: Any) -> None:
        path = self._current_summary_path
        if not path:
            return

        stats = self._last_source_stats
        warnings, errors = self._warning_error_counts()
        duration_s = self._run_duration_s()
        if snap is not None and hasattr(snap, "decode_error_total"):
            decode_err_total = int(getattr(snap, "decode_error_total", 0))
        else:
            decode_err_total = self._array_total(getattr(snap, "decode_err_cnt", None)) if snap is not None else 0
        overflow_total = self._array_total(getattr(snap, "overflow_cnt", None)) if snap is not None else 0
        noise_kerr_derr_total = (
            self._array_total(getattr(snap, "noise_decode_error_count", None))
            if snap is not None
            else 0
        )
        noise_invalid_channel_total = (
            self._array_total(getattr(snap, "noise_invalid_channel_count", None))
            if snap is not None
            else 0
        )
        valid_events = int(getattr(snap, "valid_events", 0)) if snap is not None else 0
        disabled_channel_entries = self._disabled_channel_entries_for_run()

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("MiniDAQ run summary\n")
                f.write(f"run_stem: {self._current_run_stem}\n")
                f.write(f"run_directory: {self._current_run_dir or ''}\n")
                f.write(f"data_file: {self._current_out_path or ''}\n")
                f.write(f"log_file: {self._current_log_path or ''}\n")
                f.write(f"configuration_file: {self._current_config_path or ''}\n")
                f.write(f"channel_hit_rates_csv: {self._current_hit_rate_path or ''}\n")
                f.write(f"dead_noisy_channels_file: {self._current_channel_status_path or ''}\n")
                f.write(f"warnings_errors_file: {self._current_warning_path or ''}\n")
                f.write(f"live_geometry_file: {self._current_live_geometry_path or ''}\n")
                f.write(f"started: {self._format_ts(self._run_started_at)}\n")
                f.write(f"finished: {self._format_ts(self._run_finished_at)}\n")
                f.write(f"duration_s: {duration_s:.6f}\n")
                f.write(f"hit_rate_duration_s: {self._hit_rate_duration_s():.6f}\n")
                f.write(f"hit_rate_duration_source: {self._hit_rate_duration_source}\n")

                f.write("\n[capture_or_replay]\n")
                f.write(f"mode: {self._safe_value(self._run_context.get('mode', ''))}\n")
                f.write(f"ethernet_device: {self._safe_value(self._run_context.get('ethernet_device', ''))}\n")
                f.write(f"bpf_filter: {self._safe_value(self._run_context.get('bpf_filter', ''))}\n")
                f.write(f"source_filename: {self._safe_value(getattr(stats, 'filename', ''))}\n")
                f.write(f"total_packets_or_chunks: {int(getattr(stats, 'total_packets', 0))}\n")
                f.write(f"lost_packets_total: {int(getattr(stats, 'lost_total', 0))}\n")
                f.write(f"total_bytes: {int(getattr(stats, 'total_bytes', 0))}\n")

                f.write("\n[decode_counts]\n")
                f.write(f"event_headers: {int(getattr(snap, 'headers', 0)) if snap is not None else 0}\n")
                f.write(f"event_trailers: {int(getattr(snap, 'trailers', 0)) if snap is not None else 0}\n")
                f.write(f"valid_events: {valid_events}\n")
                f.write(f"events_fifoA: {int(getattr(snap, 'events_fifoA', 0)) if snap is not None else 0}\n")
                f.write(f"events_fifoB: {int(getattr(snap, 'events_fifoB', 0)) if snap is not None else 0}\n")
                f.write(f"triggers: {int(getattr(snap, 'triggers', 0)) if snap is not None else 0}\n")
                f.write(f"raw_hits_total: {int(getattr(snap, 'hits_total', 0)) if snap is not None else 0}\n")
                valid_hits = self._array_total(getattr(snap, "adc_ch_hist", None)) if snap is not None else 0
                f.write(f"valid_event_hits_total: {valid_hits}\n")

                f.write("\n[fpga_triggerless_diagnostics]\n")
                f.write(json.dumps(self._fpga_diagnostics or {"status": "not sampled / not applicable"},
                                   indent=2, sort_keys=True) + "\n")

                f.write("\n[errors]\n")
                f.write(f"event_id_mismatch: {int(getattr(snap, 'err_event_id', 0)) if snap is not None else 0}\n")
                f.write(f"hit_count_mismatch: {int(getattr(snap, 'err_hit_count', 0)) if snap is not None else 0}\n")
                f.write(f"missing_trailer: {int(getattr(snap, 'err_missing_trailer', 0)) if snap is not None else 0}\n")
                f.write(f"missing_header: {int(getattr(snap, 'err_missing_header', 0)) if snap is not None else 0}\n")
                f.write(f"decode_errors_total: {decode_err_total}\n")
                f.write(f"hit_count_mode_kerr_derr_total: {noise_kerr_derr_total}\n")
                f.write(f"hit_count_mode_invalid_channel_total: {noise_invalid_channel_total}\n")
                f.write(f"tdc_overflows_total: {overflow_total}\n")
                f.write(f"abort_burst: {int(getattr(snap, 'abort_burst', 0)) if snap is not None else 0}\n")
                f.write(f"abort_watchdog: {int(getattr(snap, 'abort_watchdog', 0)) if snap is not None else 0}\n")
                f.write(f"warning_lines: {warnings}\n")
                f.write(f"error_lines: {errors}\n")

                f.write("\n[decode_errors_by_tdc]\n")
                for tdc, count in self._nonzero_counts(getattr(snap, "decode_err_cnt", None) if snap is not None else None):
                    f.write(f"tdc {tdc}: {count}\n")
                f.write("\n[hit_count_mode_kerr_derr_by_tdc]\n")
                for tdc, count in self._nonzero_counts(
                    getattr(snap, "noise_decode_error_count", None) if snap is not None else None
                ):
                    f.write(f"tdc {tdc}: {count}\n")
                f.write("\n[hit_count_mode_invalid_channels_by_tdc]\n")
                for tdc, count in self._nonzero_counts(
                    getattr(snap, "noise_invalid_channel_count", None) if snap is not None else None
                ):
                    f.write(f"tdc {tdc}: {count}\n")
                f.write("\n[overflows_by_tdc]\n")
                for tdc, count in self._nonzero_counts(getattr(snap, "overflow_cnt", None) if snap is not None else None):
                    f.write(f"tdc {tdc}: {count}\n")

                f.write("\n[disabled_channels]\n")
                f.write(f"disabled_channel_count: {len(disabled_channel_entries)}\n")
                if not disabled_channel_entries:
                    f.write("none\n")
                for row in disabled_channel_entries:
                    f.write(self._disabled_channel_summary_line(row) + "\n")

                f.write("\n[abort_watchdog_types]\n")
                for name, count in tuple(getattr(snap, "abort_watchdog_types", ()) if snap is not None else ()):
                    f.write(f"{name}: {int(count)}\n")

                f.write("\n[note]\n")
                if int(self.noise_test_mode) == 2:
                    f.write("raw_hit_count contains the firmware noise-counter total by TDC/channel.\n")
                else:
                    f.write("raw_hit_count counts all decoded HIT words by TDC/channel.\n")
                f.write("valid_event_hit_count counts hits from events accepted into spectra.\n")
                f.write("disabled channels are listed in the summary and excluded from dead/noisy classification.\n")
        except Exception as e:
            self.message.emit(
                "[ERROR] Failed to write run summary: "
                f"path={path} error={repr(e)}\n"
            )

    def _finalize_run_artifacts(self, snap: Any = None) -> None:
        if self._run_artifacts_finalized:
            return
        if not self._current_run_dir:
            return
        self._run_artifacts_finalized = True
        if self._run_finished_at is None:
            self._run_finished_at = time.time()
        final_snap = snap if snap is not None else self._last_decode_snapshot
        self._write_channel_hit_rates(final_snap)
        self._write_run_summary(final_snap)

    def start_capture(
        self,
        dev: str,
        bpf: str,
        out_path: str,
        max_events_in_ram: int = 256,
        min_event_hits: int = 0,
        save_isolated_hits: bool = True,
        tube_filters=None,
    ):
        """
        Start capture + decode.
        DecodeThread is SINGLE and does NOT use geometry.
        """
        if self.is_running():
            self.stop_capture()

        out_path = os.path.abspath(str(out_path))
        isolation_map_path = None
        if not save_isolated_hits:
            if int(self.acquisition_mode) != 1 or int(self.noise_test_mode) != 0:
                raise ValueError("Isolated-hit saving applies only to triggerless event mode")
            from isolated_hits import neighbor_map_text
            if tube_filters is None:
                raise ValueError("Post-isolation filtering requires the current firmware tube-filter settings")
            neighbor_map = neighbor_map_text(self._geos.values(), tube_filters)
            isolation_map_path = os.path.splitext(out_path)[0] + "_neighbors.txt"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(isolation_map_path, "w", encoding="utf-8") as output:
                output.write(neighbor_map)
        if self._current_out_path != out_path or not self._current_log_path:
            self.prepare_run_log(out_path)
        else:
            self._current_out_path = out_path
        self._run_context["save_isolated_hits"] = bool(save_isolated_hits)
        if isolation_map_path:
            self._run_context["isolated_hit_neighbor_file"] = isolation_map_path
            self._run_context["post_isolation_tube_filters"] = [cfg.pack() for cfg in tube_filters]
        self._write_run_config()
        self._run_started_at = time.time()
        self._run_finished_at = None
        self._reset_source_rates()
        self._hit_rate_duration_override_s = None
        self._hit_rate_duration_source = "elapsed capture"
        self._decode_error_auto_stop_pending = False

        # clear analysis queue (drop old bytes)
        try:
            while True:
                self._analysis_q.get_nowait()
        except queue.Empty:
            pass

        # reset navigation + caches on new run
        self.clear_event_cache(emit_signal=False)
        self._reset_fit_hists()

        # event buffer for valid events
        self._event_buf = EventBuffer(
            max_events=max_events_in_ram,
            min_hits=min_event_hits,
        )

        # decode thread (consumer)
        geo_for_decode = self._geo_for_decode_thread()
        self._dec_thread = DecodeThread(
            analysis_q=self._analysis_q,
            event_buffer=self._event_buf,
            geo=geo_for_decode,
            max_tdcs=40,
            adc_bins=256,
            tdc_bins=1024,
            tdc_shift=0,
            ch_tdc_bins=1024,
            ch_tdc_shift=0,
            tdc_min_ns=0.0,
            tdc_max_ns=800.0,
            ch_tdc_min_ns=0.0,
            ch_tdc_max_ns=800.0,
            decode_error_stop_threshold=int(self.decode_error_stop_threshold),
            acquisition_mode=int(self.acquisition_mode),
            noise_test_mode=int(self.noise_test_mode),
            retain_all_native_events=bool(self._trackfit_enabled and self._trackfit is not None),
            snapshot_fields=self._live_snapshot_fields,
        )
        self._dec_thread.analysis_1hz.connect(self._on_decode_1hz)
        if self._trackfit_enabled:
            self._dec_thread.event_ready.connect(self._fit_event_receiver.process)
        self._dec_thread.decode_issue.connect(self.message)
        self._dec_thread.decode_error_limit_exceeded.connect(self._on_decode_error_limit_exceeded)

        # capture thread (producer)
        self._cap_thread = CaptureThread(
            dev=dev,
            bpf=bpf,
            out_path=out_path,
            analysis_q=self._analysis_q,
            isolation_map_path=isolation_map_path,
        )
        self._cap_thread.message.connect(self.message)
        self._cap_thread.stats.connect(self._on_source_stats)
        self._cap_thread.isolation_stats.connect(self.isolation_stats)
        self._cap_thread.finished.connect(self._on_source_finished)

        # start consumer first, then producer
        self._dec_thread.start()
        self.capture_started.emit()
        self._cap_thread.start()

        # broadcast "no current event" at run start
        self.event_changed.emit((None, None))

    def start_replay(
        self,
        dat_path: str,
        max_events_in_ram: int = 256,
        chunk_bytes: int = 1024 * 256,
        min_event_hits: int = 0,
    ):
        """
        Start offline decode/analysis from an existing .dat file.
        Reuses the same DecodeThread + analysis flow as live capture.
        """
        if self.is_running():
            self.stop_capture()

        dat_path = os.path.abspath(str(dat_path))
        from replay_format import replay_modes
        mode, noise, source = replay_modes(dat_path, (self.acquisition_mode, self.noise_test_mode))
        self.set_acquisition_mode(mode)
        self.set_noise_test_mode(noise)
        self.message.emit(f"[Replay] Decoder acquisition_mode={mode}, noise_test_mode={noise}; {source}\n")
        if (self._current_out_path != dat_path or not self._current_log_path
                or self._run_context.get("mode") != "replay"):
            self.prepare_replay_log(dat_path)
        else:
            self._current_out_path = dat_path
        self._run_started_at = time.time()
        self._run_finished_at = None
        self._reset_source_rates()
        self._hit_rate_duration_override_s = self._recorded_run_duration_s(dat_path)
        self._hit_rate_duration_source = (
            "recorded acquisition"
            if self._hit_rate_duration_override_s is not None
            else "elapsed replay"
        )
        self._decode_error_auto_stop_pending = False

        # clear analysis queue (drop old bytes)
        try:
            while True:
                self._analysis_q.get_nowait()
        except queue.Empty:
            pass

        # reset navigation + caches on new run
        self.clear_event_cache(emit_signal=False)
        self._reset_fit_hists()

        # event buffer for valid events
        self._event_buf = EventBuffer(
            max_events=max_events_in_ram,
            min_hits=min_event_hits,
        )

        # decode thread (consumer)
        geo_for_decode = self._geo_for_decode_thread()
        self._dec_thread = DecodeThread(
            analysis_q=self._analysis_q,
            event_buffer=self._event_buf,
            geo=geo_for_decode,
            max_tdcs=40,
            adc_bins=256,
            tdc_bins=1024,
            tdc_shift=0,
            ch_tdc_bins=1024,
            ch_tdc_shift=0,
            tdc_min_ns=0.0,
            tdc_max_ns=800.0,
            ch_tdc_min_ns=0.0,
            ch_tdc_max_ns=800.0,
            decode_error_stop_threshold=int(self.decode_error_stop_threshold),
            acquisition_mode=int(self.acquisition_mode),
            noise_test_mode=int(self.noise_test_mode),
            retain_all_native_events=bool(self._trackfit_enabled and self._trackfit is not None),
            snapshot_fields=self._live_snapshot_fields,
        )
        self._dec_thread.analysis_1hz.connect(self._on_decode_1hz)
        if self._trackfit_enabled:
            self._dec_thread.event_ready.connect(self._fit_event_receiver.process)
        self._dec_thread.decode_issue.connect(self.message)
        self._dec_thread.decode_error_limit_exceeded.connect(self._on_decode_error_limit_exceeded)

        # replay thread (producer)
        self._replay_thread = DatReplayThread(
            dat_path=str(dat_path),
            analysis_q=self._analysis_q,
            chunk_bytes=int(chunk_bytes),
        )
        self._replay_thread.message.connect(self.message)
        self._replay_thread.stats.connect(self._on_source_stats)
        self._replay_thread.replay_done.connect(self._on_replay_done)
        self._replay_thread.finished.connect(self._on_source_finished)

        # start consumer first, then producer
        self._dec_thread.start()
        self.capture_started.emit()
        self._replay_thread.start()

        self.event_changed.emit((None, None))

    @QtCore.pyqtSlot(int, int, int, str)
    def _on_source_stats(self, total_packets: int, lost_total: int, total_bytes: int, filename: str):
        now = time.monotonic()
        elapsed = now - self._source_rate_last_time
        if elapsed > 0.0:
            self._source_rate_packets_s = max(
                0.0,
                float(int(total_packets) - self._source_rate_last_packets) / elapsed,
            )
            self._source_rate_bytes_s = max(
                0.0,
                float(int(total_bytes) - self._source_rate_last_bytes) / elapsed,
            )
        self._source_rate_last_time = now
        self._source_rate_last_packets = int(total_packets)
        self._source_rate_last_bytes = int(total_bytes)
        self._last_source_stats = SimpleNamespace(
            total_packets=int(total_packets),
            lost_total=int(lost_total),
            total_bytes=int(total_bytes),
            filename=str(filename or ""),
        )
        self.stats.emit(int(total_packets), int(lost_total), int(total_bytes), str(filename or ""))

    @QtCore.pyqtSlot(object)
    def _on_decoded_event(self, ev: Any):
        """
        Fill triggerless drift-time spectra using each chamber-event's fitted T0.
        """
        if ev is None or not self._trackfit_enabled or self._trackfit is None:
            return

        self._fit_evt_total += 1

        try:
            time_by, valid_by = self._compute_quality_by_chamber(ev)
            fit_by = self._fit_results_by_chamber(ev)
        except Exception:
            return

        chambers = getattr(ev, "chambers", None)
        if not isinstance(chambers, dict):
            return

        tmin = float(self._fit_tdc_tmin_ns)
        binw = float(self._fit_tdc_binw_ns)
        nbins = int(self._fit_tdc_bins)
        rmin = float(self._fit_resid_min_mm)
        rbinw = float(self._fit_resid_binw_mm)
        rnbins = int(self._fit_resid_bins)
        evt_fit_ok = False

        for cid_raw, block in chambers.items():
            cid = int(cid_raw)
            if not bool(valid_by.get(cid, False)):
                continue

            hits = getattr(block, "hits", ())
            if not hits:
                continue

            tw = time_by.get(cid)
            if tw is None:
                continue

            t_corr = getattr(tw, "t_corr_ns", None)
            keep = getattr(tw, "keep_mask", None)
            if t_corr is None or keep is None:
                continue

            t_corr_arr = np.asarray(t_corr, dtype=np.float64)
            keep_arr = np.asarray(keep, dtype=bool)
            if t_corr_arr.ndim != 1 or keep_arr.ndim != 1:
                continue
            if t_corr_arr.shape[0] != len(hits) or keep_arr.shape[0] != len(hits):
                continue

            fit = fit_by.get(cid)
            if fit is None or not fit.ok:
                continue

            vals = fit.values
            t0_ns = float(vals.get("t0_ns", 0.0))

            used_mask = np.asarray(vals.get("used_mask_input", keep_arr), dtype=bool)
            if used_mask.shape[0] != len(hits):
                used_mask = keep_arr

            final_mask = keep_arr & used_mask
            if not np.any(final_mask):
                continue
            evt_fit_ok = True
            chamber_resid_hist = self._fit_resid_hist_by_chamber.get(cid)
            if chamber_resid_hist is None:
                chamber_resid_hist = np.zeros((self._fit_max_tdcs, self._fit_resid_bins), dtype=np.uint32)
                self._fit_resid_hist_by_chamber[cid] = chamber_resid_hist

            # Requested definition:
            #   real drift time = t_corr_ns - fitted t0
            t_real = t_corr_arr - t0_ns
            ib = np.floor((t_real - tmin) / binw).astype(np.int32)
            time_ok = np.isfinite(t_real) & (ib >= 0) & (ib < nbins)

            # Residual definition (same model used in trackfit_cpp):
            #   residual_mm = |n.p - c| - r(t_corr - t0)
            rb = None
            resid_ok = None
            try:
                nx = float(vals.get("nx"))
                ny = float(vals.get("ny"))
                c = float(vals.get("c"))

                x_arr = np.asarray([float(getattr(h, "x", np.nan)) for h in hits], dtype=np.float64)
                y_arr = np.asarray([float(getattr(h, "y", np.nan)) for h in hits], dtype=np.float64)
                dist = np.abs(nx * x_arr + ny * y_arr - c)
                multilayer = None
                fitter = self.trackfit_for_chamber(cid)
                if fitter.nrt == 2:
                    multilayer = hit_multilayers(hits, self._geos.get(cid))
                r_fit = np.asarray(fitter.radius_from_time_ns(t_corr_arr - t0_ns, multilayer), dtype=np.float64)
                resid = dist - r_fit

                rb = np.floor((resid - rmin) / rbinw).astype(np.int32)
                resid_ok = np.isfinite(resid) & (rb >= 0) & (rb < rnbins)
            except Exception:
                rb = None
                resid_ok = None

            for i, h in enumerate(hits):
                if not bool(final_mask[i]):
                    continue
                tdc = int(getattr(h, "tdcid", -1))
                ch = int(getattr(h, "ch", -1))
                if not (0 <= tdc < self._fit_max_tdcs):
                    continue
                w = int(getattr(h, "width", -1))
                if 0 <= w < self._fit_adc_bins:
                    self._fit_adc_hist[tdc, w] += 1
                    if 0 <= ch < self._fit_max_channels:
                        self._fit_adc_ch_hist[tdc, ch, w] += 1
                if bool(time_ok[i]):
                    b = int(ib[i])
                    self._fit_tdc_hist[tdc, b] += 1
                    if 0 <= ch < self._fit_max_channels:
                        self._fit_tdc_ch_hist[tdc, ch, b] += 1
                if resid_ok is not None and bool(resid_ok[i]):
                    br = int(rb[i])
                    self._fit_resid_hist[tdc, br] += 1
                    chamber_resid_hist[tdc, br] += 1

        if evt_fit_ok:
            self._fit_evt_valid += 1

    @QtCore.pyqtSlot(object)
    def _on_decode_1hz(self, snap: Any, force_emit: bool = False):
        """
        Emit event-T0 spectra for triggerless runs and decoder spectra otherwise.
        """
        self._last_decode_snapshot = snap

        tdc_bins = int(getattr(snap, "tdc_bins", 0))
        ch_tdc_bins = int(getattr(snap, "ch_tdc_bins", 0))
        tdc_binw_ns = float(getattr(snap, "tdc_binw_ns", 0.78125 * (1 << 5)))
        ch_tdc_binw_ns = float(getattr(snap, "ch_tdc_binw_ns", 0.78125 * (1 << 7)))
        tdc_time_min_ns = float(getattr(snap, "tdc_min_ns", 0.0))
        tdc_time_max_ns = float(getattr(snap, "tdc_max_ns", tdc_time_min_ns + float(tdc_bins) * tdc_binw_ns))
        ch_tdc_time_min_ns = float(getattr(snap, "ch_tdc_min_ns", tdc_time_min_ns))
        ch_tdc_time_max_ns = float(
            getattr(snap, "ch_tdc_max_ns", ch_tdc_time_min_ns + float(ch_tdc_bins) * ch_tdc_binw_ns)
        )
        # The existing TDC tabs share one x-range metadata pair. Keep the range
        # identical for overall and per-channel spectra in normal use.
        tdc_time_min_ns = min(tdc_time_min_ns, ch_tdc_time_min_ns)
        tdc_time_max_ns = max(tdc_time_max_ns, ch_tdc_time_max_ns)
        if self._trackfit_enabled:
            tdc_hist, tdc_ch_hist = self._fit_tdc_hist, self._fit_tdc_ch_hist
            tdc_bins = ch_tdc_bins = int(self._fit_tdc_bins)
            tdc_time_min_ns = float(self._fit_tdc_tmin_ns)
            tdc_time_max_ns = float(self._fit_tdc_tmax_ns)
            tdc_binw_ns = ch_tdc_binw_ns = float(self._fit_tdc_binw_ns)
            tdc_source = "fit_drift_time_ns:t_corr_minus_t0"
            tdc_label = "Drift time (event T0)"
        else:
            tdc_hist, tdc_ch_hist = snap.tdc_hist, snap.tdc_ch_hist
            tdc_source = "raw_hit_ledge" if self.acquisition_mode == 1 else "raw_hit_minus_trigger_ledge"
            tdc_label = "hit_ledge" if self.acquisition_mode == 1 else "hit_ledge - trigger_ledge"

        out = SimpleNamespace(
            # ADC remains decoder-native
            adc_hist=snap.adc_hist,
            adc_ch_hist=snap.adc_ch_hist,
            adc_bins=int(getattr(snap, "adc_bins", 0)),
            ch_adc_bins=int(getattr(snap, "ch_adc_bins", 0)),
            # ADC from fitted-hit subset only
            fit_adc_hist=self._fit_adc_hist,
            fit_adc_ch_hist=self._fit_adc_ch_hist,
            fit_adc_bins=int(self._fit_adc_bins),
            fit_ch_adc_bins=int(self._fit_adc_bins),

            tdc_hist=tdc_hist,
            tdc_ch_hist=tdc_ch_hist,
            tdc_bins=tdc_bins,
            ch_tdc_bins=ch_tdc_bins,

            # Residual spectra from fit result (per TDC)
            fit_residual_hist=self._fit_resid_hist,
            fit_residual_hist_by_chamber={
                int(cid): arr for cid, arr in self._fit_resid_hist_by_chamber.items()
            },
            fit_residual_bins=int(self._fit_resid_bins),
            fit_residual_min_mm=float(self._fit_resid_min_mm),
            fit_residual_max_mm=float(self._fit_resid_max_mm),
            fit_residual_binw_mm=float(self._fit_resid_binw_mm),
            fit_evt_total=int(self._fit_evt_total),
            fit_evt_valid=int(self._fit_evt_valid),
            fit_evt_valid_ratio=float(self._fit_evt_valid / self._fit_evt_total) if self._fit_evt_total > 0 else 0.0,

            # decode counters / errors
            headers=int(getattr(snap, "headers", 0)),
            events_fifoA=int(getattr(snap, "events_fifoA", 0)),
            events_fifoB=int(getattr(snap, "events_fifoB", 0)),
            trailers=int(getattr(snap, "trailers", 0)),
            triggers=int(getattr(snap, "triggers", 0)),
            hits_total=int(getattr(snap, "hits_total", 0)),
            valid_events=int(getattr(snap, "valid_events", 0)),
            raw_hit_ch_count=getattr(snap, "raw_hit_ch_count", None),
            event_hit_count_hist=getattr(snap, "event_hit_count_hist", None),
            overflow_cnt=getattr(snap, "overflow_cnt", None),
            decode_err_cnt=getattr(snap, "decode_err_cnt", None),
            decode_error_total=int(
                getattr(
                    snap,
                    "decode_error_total",
                    self._array_total(getattr(snap, "decode_err_cnt", None)),
                )
            ),
            err_event_id=int(getattr(snap, "err_event_id", 0)),
            err_hit_count=int(getattr(snap, "err_hit_count", 0)),
            err_missing_trailer=int(getattr(snap, "err_missing_trailer", 0)),
            err_missing_header=int(getattr(snap, "err_missing_header", 0)),
            abort_burst=int(getattr(snap, "abort_burst", 0)),
            abort_watchdog=int(getattr(snap, "abort_watchdog", 0)),
            abort_watchdog_types=tuple(getattr(snap, "abort_watchdog_types", ())),
            noise_headers=int(getattr(snap, "noise_headers", 0)),
            noise_counters=int(getattr(snap, "noise_counters", 0)),
            noise_error_words=int(getattr(snap, "noise_error_words", 0)),
            noise_trailers=int(getattr(snap, "noise_trailers", 0)),
            noise_last_seconds=int(getattr(snap, "noise_last_seconds", 0)),
            noise_last_total=int(getattr(snap, "noise_last_total", 0)),
            noise_counter_total=getattr(snap, "noise_counter_total", None),
            noise_counter_rate=getattr(snap, "noise_counter_rate", None),
            noise_decode_error_count=getattr(snap, "noise_decode_error_count", None),
            noise_invalid_channel_count=getattr(snap, "noise_invalid_channel_count", None),
            events_buffered=int(getattr(snap, "events_buffered", 0)),
            decoded_bytes_total=int(getattr(snap, "decoded_bytes_total", 0)),
            decode_rate_bytes_s=float(getattr(snap, "decode_rate_bytes_s", 0.0)),
            decode_rate_words_s=float(getattr(snap, "decode_rate_words_s", 0.0)),
            queue_backlog_chunks=int(getattr(snap, "queue_backlog_chunks", 0)),
            queue_backlog_peak_chunks=int(getattr(snap, "queue_backlog_peak_chunks", 0)),
            queue_capacity_chunks=int(getattr(snap, "queue_capacity_chunks", 0)),
            capture_rate_packets_s=float(self._source_rate_packets_s),
            capture_rate_bytes_s=float(self._source_rate_bytes_s),
            decode_backend=str(getattr(snap, "decode_backend", "Python")),

            # metadata for future UI usage/debug
            acquisition_mode=int(self.acquisition_mode),
            noise_test_mode=int(self.noise_test_mode),
            hit_rate_duration_s=float(self._hit_rate_duration_s()),
            hit_rate_duration_source=str(self._hit_rate_duration_source),
            tdc_hist_source=tdc_source,
            tdc_time_label=tdc_label,
            tdc_time_min_ns=float(tdc_time_min_ns),
            tdc_time_max_ns=float(tdc_time_max_ns),
            tdc_time_binw_ns=float(tdc_binw_ns),
            ch_tdc_time_binw_ns=float(ch_tdc_binw_ns),
            tdc_hist_raw=getattr(snap, "tdc_hist", None),
            tdc_ch_hist_raw=getattr(snap, "tdc_ch_hist", None),
        )
        self.decode_status.emit(out)
        if self.analysis_emit_suppressed() and not bool(force_emit):
            return
        self.analysis_1hz.emit(out)

    @QtCore.pyqtSlot(int, int)
    def _on_decode_error_limit_exceeded(self, count: int, threshold: int):
        if self._decode_error_auto_stop_pending:
            return
        self._decode_error_auto_stop_pending = True
        self.message.emit(
            "[ERROR] Decode error count exceeded stop threshold: "
            f"count={int(count)} threshold={int(threshold)}. Stopping DAQ.\n"
        )
        QtCore.QTimer.singleShot(0, self.stop_capture)

    def stop_capture(self):
        self.run_stopping.emit()
        self._replay_draining = False
        final_snap = None

        # stop producer first
        if self._cap_thread:
            self._cap_thread.stop()
            self._cap_thread.wait(2000)
            self._cap_thread = None
        if self._replay_thread:
            self._replay_thread.stop()
            self._replay_thread.wait(5000)
            self._replay_thread = None

        # then stop consumer
        if self._dec_thread:
            self._dec_thread.stop()
            self._dec_thread.wait()
            # All decoded events have now been emitted. Finish queued T0 fits
            # before the final spectrum is published or plots are saved.
            QtCore.QCoreApplication.sendPostedEvents(self._fit_event_receiver, QtCore.QEvent.MetaCall)
            try:
                final_snap = self._dec_thread.make_snapshot(
                    copy_arrays=True,
                    snapshot_fields=self._final_snapshot_fields(),
                )
                self._last_decode_snapshot = final_snap
                self._on_decode_1hz(final_snap, force_emit=True)
            except Exception:
                final_snap = None
            self._dec_thread = None

        self._finalize_run_artifacts(final_snap)
        self.run_finished.emit()
        self._current_log_path = None
        self._current_config_path = None
        self._current_summary_path = None
        self._current_hit_rate_path = None
        self._current_channel_status_path = None
        self._current_warning_path = None
        self._current_live_geometry_path = None

    @QtCore.pyqtSlot()
    def _on_source_finished(self):
        # Replay completion is finalized in _on_replay_done. If live capture exits
        # on its own because of an I/O error, close the decode side and artifacts.
        if self._cap_thread is not None and not self._cap_thread.isRunning():
            QtCore.QTimer.singleShot(0, self.stop_capture)

    @QtCore.pyqtSlot()
    def _on_replay_done(self):
        """
        Replay producer reached EOF (or stopped). Wait for decode queue to drain,
        then stop decode thread and mark run finished.
        """
        self._replay_draining = True
        self._replay_empty_streak = 0
        self._poll_replay_drain()

    def _poll_replay_drain(self):
        if not self._replay_draining:
            return

        if self._dec_thread is None:
            self._replay_draining = False
            self._replay_thread = None
            self._finalize_run_artifacts(self._last_decode_snapshot)
            self.run_finished.emit()
            self._current_log_path = None
            self._current_config_path = None
            self._current_summary_path = None
            self._current_hit_rate_path = None
            self._current_channel_status_path = None
            self._current_warning_path = None
            self._current_live_geometry_path = None
            return

        qsize = self._analysis_q.qsize()
        if qsize == 0:
            self._replay_empty_streak += 1
        else:
            self._replay_empty_streak = 0

        # Require a short stable empty period so we don't race on the last chunk.
        if self._replay_empty_streak >= 3:
            final_snap = None
            self._dec_thread.stop()
            self._dec_thread.wait()
            QtCore.QCoreApplication.sendPostedEvents(self._fit_event_receiver, QtCore.QEvent.MetaCall)
            try:
                final_snap = self._dec_thread.make_snapshot(
                    copy_arrays=True,
                    snapshot_fields=self._final_snapshot_fields(),
                )
                self._last_decode_snapshot = final_snap
                self._on_decode_1hz(final_snap, force_emit=True)
            except Exception:
                final_snap = None
            self._dec_thread = None
            self._replay_draining = False
            self._replay_thread = None
            self.message.emit("[Replay] Decode complete.\n")
            self._finalize_run_artifacts(final_snap)
            self.run_finished.emit()
            self._current_log_path = None
            self._current_config_path = None
            self._current_summary_path = None
            self._current_hit_rate_path = None
            self._current_channel_status_path = None
            self._current_warning_path = None
            self._current_live_geometry_path = None
            return

        QtCore.QTimer.singleShot(100, self._poll_replay_drain)

    # ---------------- legacy event access (kept) ----------------

    def pop_event(self):
        """Return next valid Event from buffer (or None)."""
        if self._event_buf is None:
            return None
        return self._event_buf.pop()

    def events_buffered(self) -> int:
        if self._event_buf is None:
            return 0
        return self._event_buf.size()

    def current_out_path(self) -> Optional[str]:
        return self._current_out_path

    def current_artifact_dir(self) -> Optional[str]:
        return self._current_run_dir

    def current_log_path(self) -> Optional[str]:
        return self._current_log_path

    def current_decode_snapshot(self, snapshot_fields=None):
        """
        Return a point-in-time decoder snapshot for event-count driven scans.

        The regular GUI update signal is intentionally periodic. Noise scans on
        master stop by decoded event count, so callers can poll this lighter API
        without waiting for the next GUI emit.
        """
        if self._dec_thread is None:
            return None
        fields = {"ch_hits"} if snapshot_fields is None else set(snapshot_fields)
        try:
            return self._dec_thread.make_snapshot(
                copy_arrays=True,
                snapshot_fields=fields,
            )
        except Exception:
            return None

    # ---------------- quality computation (chamber-based) ----------------

    def _compute_quality_by_chamber(self, ev: Any) -> Tuple[TimeByChamber, ValidByChamber]:
        """
        Compute quality per chamber (no mixing).
        Cached by event_id20.
        Returns: (time_by_chamber, valid_by_chamber)
        """
        if ev is None:
            return {}, {}

        try:
            eid20 = int(getattr(ev, "event_id20"))
        except Exception:
            eid20 = -1

        cached = self._qc_cache.get(eid20)
        if cached is not None:
            return cached

        time_by, valid_by = {}, {}
        for cid, block in getattr(ev, "chambers", {}).items():
            quality = copy(self._quality)
            rt = getattr(self, "_rts_by_chamber", {}).get(int(cid))
            if rt is not None:
                quality.max_window_ns = float(rt.Tmax - rt.T0)
            chamber_event = SimpleNamespace(chambers={cid: block},
                                           trigger_ledge=getattr(ev, "trigger_ledge", None))
            q = quality.compute_for_event(chamber_event, geometries=self._geos,
                                           use_trigger_reference=not self._trackfit_enabled)
            time_by.update(q.time_by_chamber)
            valid_by.update(q.valid_by_chamber)
        fit_by: FitByChamber = {}

        # Align chamber_valid with the fitter in the same spirit as
        # testbeam-mini-chamber_reco: QA must pass, the fit must succeed,
        # and enough inlier hits must remain after the residual cut.
        # A few rejected hits are acceptable and will stay visible as red.
        if self._trackfit_enabled and self._trackfit is not None:
            chambers = getattr(ev, "chambers", None)
            if isinstance(chambers, dict):
                for cid_raw, block in chambers.items():
                    cid = int(cid_raw)
                    fitter = self.trackfit_for_chamber(cid)
                    if fitter is None:
                        valid_by[cid] = False
                        continue
                    min_fit_hits = max(3, int(fitter.min_hits))
                    min_fit_dof = max(0, min_fit_hits - 3)
                    if not bool(valid_by.get(cid, False)):
                        continue

                    hits = getattr(block, "hits", ())
                    tw = time_by.get(cid)
                    if not hits or tw is None:
                        valid_by[cid] = False
                        continue

                    t_corr = getattr(tw, "t_corr_ns", None)
                    keep = getattr(tw, "keep_mask", None)
                    if t_corr is None or keep is None:
                        valid_by[cid] = False
                        continue

                    t_corr_arr = np.asarray(t_corr, dtype=np.float64)
                    keep_arr = np.asarray(keep, dtype=bool)
                    if (
                        t_corr_arr.ndim != 1
                        or keep_arr.ndim != 1
                        or t_corr_arr.shape[0] != len(hits)
                        or keep_arr.shape[0] != len(hits)
                    ):
                        valid_by[cid] = False
                        continue

                    fit = fitter.fit_chamber_hits(
                        chamber_id=cid,
                        hits=hits,
                        t_corr_ns=t_corr_arr,
                        keep_mask=keep_arr,
                        geometry=self._geos.get(cid),
                    )
                    fit_by[cid] = fit
                    if not fit.ok:
                        valid_by[cid] = False
                        continue

                    fit_dof = int(round(float(fit.values.get("dof", fit.n_used - 3))))
                    valid_by[cid] = bool((fit.n_used >= min_fit_hits) and (fit_dof >= min_fit_dof))

        out = (time_by, valid_by)

        self._qc_cache[eid20] = out
        self._fit_cache[eid20] = fit_by
        return out

    def _fit_results_by_chamber(self, ev: Any) -> FitByChamber:
        """
        Return cached fit results for this event, computing quality+fits on-demand
        if needed. The backend reuses these fits for both validity and spectra.
        """
        if not self._trackfit_enabled or self._trackfit is None:
            return {}

        if ev is None:
            return {}

        try:
            eid20 = int(getattr(ev, "event_id20"))
        except Exception:
            eid20 = -1

        cached = self._fit_cache.get(eid20)
        if cached is not None:
            return cached

        self._compute_quality_by_chamber(ev)
        return self._fit_cache.get(eid20, {})

    def _emit_current_payload(self) -> None:
        """
        Emit (Event_raw, (time_by_chamber, valid_by_chamber)) or (None,None).
        """
        ev = self.current_event_raw()
        if ev is None:
            self.event_changed.emit((None, None))
            return

        time_by, valid_by = self._compute_quality_by_chamber(ev)
        self.event_changed.emit((ev, (time_by, valid_by)))

    # ---------------- global event navigation ----------------

    def cache_size(self) -> int:
        return len(self._ev_cache)

    def current_index(self) -> int:
        return int(self._ev_idx)

    def current_event_raw(self) -> Optional[Any]:
        """Return raw Event from cache (or None)."""
        if 0 <= self._ev_idx < len(self._ev_cache):
            return self._ev_cache[self._ev_idx]
        return None

    def current_event(self) -> EventPayload:
        """
        Return the same thing we emit:
          (Event_raw, (time_by_chamber, valid_by_chamber)) or (None,None)
        """
        ev = self.current_event_raw()
        if ev is None:
            return (None, None)
        time_by, valid_by = self._compute_quality_by_chamber(ev)
        return (ev, (time_by, valid_by))

    def goto_event(self, idx: int) -> None:
        idx = int(idx)
        if not (0 <= idx < len(self._ev_cache)):
            return
        self._ev_idx = idx
        self._emit_current_payload()

    def next_event(self) -> None:
        """
        Advance by 1:
          - If next is already cached, move forward.
          - Else, pop from EventBuffer, append raw Event to cache, select it.
        """
        # cached next
        if 0 <= self._ev_idx < len(self._ev_cache) - 1:
            self._ev_idx += 1
            self._emit_current_payload()
            return

        # need a fresh event
        ev = self.pop_event()
        if ev is None:
            # no new event; re-emit current (so UI can refresh buffered count)
            self._emit_current_payload()
            return

        self._ev_cache.append(ev)
        self._ev_idx = len(self._ev_cache) - 1
        self._emit_current_payload()

    def prev_event(self) -> None:
        """
        Go back by 1 within cache (cannot go back into EventBuffer).
        """
        if self._ev_idx <= 0:
            self._emit_current_payload()
            return
        self._ev_idx -= 1
        self._emit_current_payload()

    def clear_event_cache(self, emit_signal: bool = True, clear_buffer: bool = False):
        self._ev_cache.clear()
        self._ev_idx = -1
        self._qc_cache.clear()
        self._fit_cache.clear()

        if clear_buffer and self._event_buf is not None:
            self._event_buf.clear()

        if emit_signal:
            self.event_changed.emit((None, None))
