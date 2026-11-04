from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from rt_function import hit_multilayers

try:
    import trackfit_cpp  # type: ignore
except Exception as exc:  # pragma: no cover
    trackfit_cpp = None
    _IMPORT_ERROR: Optional[Exception] = exc
else:
    _IMPORT_ERROR = None


@dataclass(frozen=True)
class FitParams:
    theta_min: float = -1.2
    theta_max: float = 1.2
    theta_steps: int = 241
    # Optional hard limits on top of adaptive event-by-event t0 bounds.
    # Defaults are wide enough to effectively disable extra hard bounds.
    t0_min: float = -1.0e9
    t0_max: float = 1.0e9
    # Optional margin for strict feasible interval:
    #   t0 in [max(t_corr)-Tmax+margin, min(t_corr)-T0-margin]
    t0_bound_margin_ns: float = 0.0
    # Legacy scan knobs retained for the C++ fallback path.
    lr_iters: int = 5
    t0_golden_iters: int = 32
    # Triggerless-style iterative fit controls.
    max_residual_sigma: float = 5.0
    optimizer_tolerance: float = 1.0e-3
    optimizer_max_iters: int = 64


@dataclass(frozen=True)
class TrackFitResult:
    chamber_id: int
    ok: bool
    reason: str
    n_input: int
    n_used: int
    values: Mapping[str, Any] = field(default_factory=dict)


class TrackFit:
    """
    Thin Python wrapper around trackfit_cpp.TrackFitter.

    Inputs:
      - hit x/y from event chamber hits
      - corrected times from EventQuality TimeWindowResult (t_corr_ns)
      - optional keep_mask from TimeWindowResult
    """

    def __init__(
        self,
        *,
        r_lut: Sequence[float],
        T0: float,
        Tmax: float,
        time_ranges=None,
        min_hits: int = 6,
        fit_only_kept_hits: bool = True,
        fit_params: Optional[FitParams] = None,
    ):
        if trackfit_cpp is None:  # pragma: no cover
            raise RuntimeError(
                "trackfit_cpp import failed. "
                f"Original error: {repr(_IMPORT_ERROR)}"
            )

        lut = np.asarray(r_lut, dtype=np.float64)
        if lut.ndim == 1:
            lut = lut[None, :]
        if lut.ndim != 2 or lut.shape[0] not in (1, 2) or lut.shape[1] < 2 or not np.all(np.isfinite(lut)):
            raise ValueError("r_lut must contain one or two finite lookup tables with at least 2 entries.")
        self.nrt = int(lut.shape[0])
        self._r_luts = np.ascontiguousarray(lut, dtype=np.float64)
        self._r_lut = self._r_luts[0]
        self._lut_n = int(lut.shape[1])
        ranges = np.tile([T0, Tmax], (self.nrt, 1)) if time_ranges is None else time_ranges
        self.time_ranges = np.ascontiguousarray(ranges, dtype=np.float64)
        if (self.time_ranges.shape != (self.nrt, 2) or not np.all(np.isfinite(self.time_ranges))
                or np.any(self.time_ranges[:, 1] <= self.time_ranges[:, 0])):
            raise ValueError("Invalid RT time ranges.")
        self.T0 = float(self.time_ranges[:, 0].min())
        self.Tmax = float(self.time_ranges[:, 1].max())
        self.min_hits = int(min_hits)
        self.fit_only_kept_hits = bool(fit_only_kept_hits)
        self.fit_params = fit_params or FitParams()
        if self.nrt == 1:
            self._fitter = trackfit_cpp.TrackFitter(self._r_lut, self.T0, self.Tmax)
        else:
            try:
                self._fitter = trackfit_cpp.TrackFitter(self._r_luts, self.time_ranges)
            except TypeError as exc:
                raise RuntimeError("Rebuild cppfit with install_native.sh to enable NRT=2.") from exc

    @staticmethod
    def available() -> bool:
        return trackfit_cpp is not None

    @classmethod
    def from_rt(
        cls,
        rt: Any,
        *,
        n_lut: int = 2048,
        min_hits: int = 6,
        fit_only_kept_hits: bool = True,
        fit_params: Optional[FitParams] = None,
    ) -> "TrackFit":
        if rt is None:
            raise ValueError("rt cannot be None.")

        n = max(64, int(n_lut))
        nrt = int(getattr(rt, "nrt", 1))
        ranges = np.asarray(getattr(rt, "time_ranges", [[rt.T0, rt.Tmax]]), dtype=np.float64)
        tables = []
        for ml, (lo, hi) in enumerate(ranges):
            t = np.linspace(lo, hi, n, dtype=np.float64)
            r = np.asarray(rt.r_of_t(t, ml) if nrt == 2 else rt.r_of_t(t), dtype=np.float64)
            if r.shape != t.shape:
                raise ValueError("rt.r_of_t(t) returned invalid shape.")
            tables.append(np.clip(r, 0.0, None))
        return cls(
            r_lut=tables,
            T0=rt.T0,
            Tmax=rt.Tmax,
            time_ranges=ranges,
            min_hits=min_hits,
            fit_only_kept_hits=fit_only_kept_hits,
            fit_params=fit_params,
        )

    @staticmethod
    def _normalize_fit_out(raw: Mapping[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in dict(raw).items():
            key = str(k)

            if isinstance(v, (bool, list, tuple, dict, str)):
                out[key] = v
                continue

            if isinstance(v, np.generic):
                if np.issubdtype(v.dtype, np.bool_):
                    out[key] = bool(v)
                else:
                    out[key] = float(v)
                continue

            if isinstance(v, (int, float)):
                out[key] = float(v)
                continue

            try:
                out[key] = float(v)
            except Exception:
                out[key] = v

        return out

    def _indices(self, multilayer, shape):
        if multilayer is None:
            if self.nrt == 2:
                raise ValueError("NRT=2 requires multilayer indices.")
            return np.zeros(shape, dtype=np.int32)
        ml = np.broadcast_to(np.asarray(multilayer), shape)
        if np.any((ml != 0) & (ml != 1)):
            raise ValueError("Multilayer indices must be 0 or 1.")
        return ml.astype(np.int32) if self.nrt == 2 else np.zeros(shape, dtype=np.int32)

    def radius_from_time_ns(self, t_ns: Any, multilayer=None):
        """Evaluate each hit's curve with the same interpolation as TrackFitter."""
        t = np.asarray(t_ns, dtype=np.float64)
        indices = self._indices(multilayer, t.shape)
        out = np.empty(t.shape, dtype=np.float64)
        for ml, (lo, hi) in enumerate(self.time_ranges):
            mask = indices == ml
            out[mask] = np.interp(t[mask], np.linspace(lo, hi, self._lut_n), self._r_luts[ml])
        return float(out) if out.ndim == 0 else out

    def _fit_arrays(self, x: np.ndarray, y: np.ndarray, t_corr_ns: np.ndarray,
                    multilayer=None) -> Dict[str, Any]:
        p = self.fit_params
        t = np.asarray(t_corr_ns, dtype=np.float64)
        if t.ndim != 1 or t.size == 0 or not np.all(np.isfinite(t)):
            raise ValueError("t_corr_ns must be a non-empty finite 1D array.")
        indices = self._indices(multilayer, t.shape)
        ranges = self.time_ranges[indices]
        margin = max(0.0, float(p.t0_bound_margin_ns))
        # Intersect the valid t0 interval of every hit using its own ML domain.
        t0_lo = float(np.max(t - ranges[:, 1])) + margin
        t0_hi = float(np.min(t - ranges[:, 0])) - margin

        # Optional extra hard bounds if user provides tighter limits.
        hard_lo = float(p.t0_min)
        hard_hi = float(p.t0_max)
        if hard_lo < hard_hi:
            t0_lo = max(t0_lo, hard_lo)
            t0_hi = min(t0_hi, hard_hi)

        if not (np.isfinite(t0_lo) and np.isfinite(t0_hi) and (t0_lo < t0_hi)):
            raise ValueError("no_feasible_t0_range")

        rt_args = {"rt_indices": indices} if self.nrt == 2 else {}
        out = self._fitter.fit(
            x=x,
            y=y,
            t_corr_ns=t_corr_ns,
            theta_min=float(p.theta_min),
            theta_max=float(p.theta_max),
            theta_steps=int(p.theta_steps),
            t0_min=float(t0_lo),
            t0_max=float(t0_hi),
            lr_iters=int(p.lr_iters),
            t0_golden_iters=int(p.t0_golden_iters),
            max_residual_sigma=float(p.max_residual_sigma),
            optimizer_tolerance=float(p.optimizer_tolerance),
            optimizer_max_iters=int(p.optimizer_max_iters),
            **rt_args,
        )
        out["t0_min_used"] = float(t0_lo)
        out["t0_max_used"] = float(t0_hi)
        return self._normalize_fit_out(out)

    def fit_chamber_hits(
        self,
        *,
        chamber_id: int,
        hits: Sequence[Any],
        t_corr_ns: Sequence[float],
        keep_mask: Optional[Sequence[bool]] = None,
        geometry=None,
        multilayer=None,
    ) -> TrackFitResult:
        n_input = len(hits)
        if n_input == 0:
            return TrackFitResult(chamber_id, False, "no_hits", 0, 0, {})

        t_arr = np.asarray(t_corr_ns, dtype=np.float64)
        if t_arr.ndim != 1 or t_arr.shape[0] != n_input:
            return TrackFitResult(chamber_id, False, "time_size_mismatch", n_input, 0, {})

        x_arr = np.asarray([float(getattr(h, "x", np.nan)) for h in hits], dtype=np.float64)
        y_arr = np.asarray([float(getattr(h, "y", np.nan)) for h in hits], dtype=np.float64)

        good = np.isfinite(x_arr) & np.isfinite(y_arr) & np.isfinite(t_arr)
        good &= (x_arr >= 0.0) & (y_arr >= 0.0)

        if keep_mask is not None and self.fit_only_kept_hits:
            keep = np.asarray(keep_mask, dtype=bool)
            if keep.ndim != 1 or keep.shape[0] != n_input:
                return TrackFitResult(chamber_id, False, "keep_mask_size_mismatch", n_input, 0, {})
            good &= keep

        n_used = int(np.count_nonzero(good))
        if n_used < max(3, self.min_hits):
            return TrackFitResult(chamber_id, False, "not_enough_hits", n_input, n_used, {})

        src_idx = np.flatnonzero(good).astype(np.int64)

        try:
            if self.nrt == 2 and multilayer is None:
                multilayer = hit_multilayers(hits, geometry)
            indices = self._indices(multilayer, t_arr.shape)
            vals = self._fit_arrays(x_arr[good], y_arr[good], t_arr[good], indices[good])
        except ValueError as exc:
            if str(exc) == "no_feasible_t0_range":
                return TrackFitResult(chamber_id, False, "no_feasible_t0_range", n_input, n_used, {})
            return TrackFitResult(chamber_id, False, f"fit_exception:{type(exc).__name__}", n_input, n_used, {})
        except Exception as exc:
            return TrackFitResult(chamber_id, False, f"fit_exception:{type(exc).__name__}", n_input, n_used, {})

        used_mask_input = np.zeros(n_input, dtype=bool)
        used_local = vals.get("used_idx", None)
        if isinstance(used_local, (list, tuple)):
            for j in used_local:
                try:
                    jl = int(j)
                except Exception:
                    continue
                if 0 <= jl < src_idx.size:
                    used_mask_input[int(src_idx[jl])] = True
        else:
            used_mask_input[good] = True

        vals["used_mask_input"] = used_mask_input.astype(np.uint8).tolist()
        vals["used_indices_input"] = np.flatnonzero(used_mask_input).astype(np.int64).tolist()

        n_used_final = int(round(vals.get("n_used", float(n_used))))
        return TrackFitResult(chamber_id, True, "ok", n_input, n_used_final, vals)

    def fit_event(
        self,
        *,
        ev: Any,
        time_by_chamber: Mapping[int, Any],
        valid_by_chamber: Optional[Mapping[int, bool]] = None,
        fit_invalid_chambers: bool = False,
        geometries=None,
    ) -> Dict[int, TrackFitResult]:
        out: Dict[int, TrackFitResult] = {}
        chambers = getattr(ev, "chambers", None)
        if not isinstance(chambers, dict):
            return out

        for cid_raw, block in chambers.items():
            cid = int(cid_raw)
            hits = getattr(block, "hits", ())
            tw = time_by_chamber.get(cid) if time_by_chamber is not None else None

            if tw is None:
                out[cid] = TrackFitResult(cid, False, "missing_timewindow", len(hits), 0, {})
                continue

            if valid_by_chamber is not None and not fit_invalid_chambers:
                if not bool(valid_by_chamber.get(cid, True)):
                    out[cid] = TrackFitResult(cid, False, "chamber_invalid", len(hits), 0, {})
                    continue

            t_corr = getattr(tw, "t_corr_ns", None)
            keep = getattr(tw, "keep_mask", None)
            if t_corr is None:
                out[cid] = TrackFitResult(cid, False, "missing_t_corr_ns", len(hits), 0, {})
                continue

            out[cid] = self.fit_chamber_hits(
                chamber_id=cid,
                hits=hits,
                t_corr_ns=t_corr,
                keep_mask=keep,
                geometry=None if geometries is None else geometries.get(cid),
            )

        return out
