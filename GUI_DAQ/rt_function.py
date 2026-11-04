"""Chebyshev RT calibrations from coefficient text or catalogue ROOT vectors.

Multilayer indices are zero based, matching Geometry.multilayer_from_layer.
ROOT vectors store coefficients on [-1, 1], not physical time limits. By default
those limits come from the matching catalogue tables; callers may supply them.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.polynomial.chebyshev import chebval


class RTFunction:
    def __init__(self, txt_file: str, *, t_min=None, t_max=None,
                 n_coeff: int = 10, nrt: int | None = None, time_ranges=None):
        self.file_path = str(txt_file)
        self.txt_file = self.file_path  # compatibility with existing callers
        path = Path(self.file_path)
        if not path.is_file():
            raise RuntimeError(f"[RT] File not found: {path}")
        if nrt not in (None, 1, 2):
            raise ValueError("NRT must be 1 or 2 (or automatic).")
        self.source_tables = []
        if path.suffix.lower() == ".root":
            params = self._load_root(path, nrt, n_coeff)
        else:
            if nrt == 2:
                raise ValueError("NRT=2 requires a ROOT file containing RTParam0 and RTParam1.")
            params = [self._load_txt(path, n_coeff)]
        self.nrt = len(params)
        self.params_by_ml = tuple(params)
        self.params = params[0]  # legacy single-curve access

        if time_ranges is not None:
            ranges = np.asarray(time_ranges, dtype=np.float64)[:self.nrt]
        elif t_min is not None or t_max is not None:
            if t_min is None or t_max is None:
                raise ValueError("Specify both t_min and t_max.")
            ranges = np.tile([t_min, t_max], (self.nrt, 1))
        elif path.suffix.lower() == ".root":
            ranges = np.asarray([self._catalogue_range(path, ml) for ml in range(self.nrt)])
        else:
            ranges = np.asarray([[0.0, 200.0]])
        if (ranges.shape != (self.nrt, 2) or not np.all(np.isfinite(ranges))
                or np.any(ranges[:, 1] <= ranges[:, 0])):
            raise ValueError("Each RT time range must have finite Tmin < Tmax, in ns.")
        self.time_ranges = ranges
        self.T0 = float(ranges[:, 0].min())
        self.Tmax = float(ranges[:, 1].max())
        self._inverse_luts = None
        self.r_lut_sorted = self.t_lut_sorted = None
        print(f"[RT] Loaded {path}: NRT={self.nrt}, time ranges={ranges.tolist()} ns")

    @staticmethod
    def _validate_coefficients(values, name, n_coeff):
        values = np.asarray(values, dtype=np.float64)
        if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
            raise ValueError(f"[RT] Invalid coefficients in {name}.")
        if n_coeff is not None and values.size != n_coeff:
            raise ValueError(f"[RT] {name}: expected {n_coeff} coefficients, got {values.size}.")
        return values.copy()

    @classmethod
    def _load_txt(cls, path, n_coeff):
        values = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                values.append(float(line))
            except ValueError as exc:
                raise ValueError("Select a coefficient TXT file or the chamber ROOT file; "
                                 "catalogue radius/time/resolution tables are not coefficients.") from exc
        return cls._validate_coefficients(values, path, n_coeff)

    @classmethod
    def _load_root(cls, path, nrt, n_coeff):
        try:
            import uproot
        except ImportError as exc:
            raise RuntimeError("ROOT calibration loading requires uproot. "
                               "Install GUI_DAQ/requirements.txt in the GUI environment.") from exc
        with uproot.open(path) as root:
            count = nrt if nrt is not None else (2 if "RTParam1" in root else 1)
            params = []
            for ml in range(count):
                key = f"RTParam{ml}"
                if key not in root:
                    raise ValueError(f"[RT] {path.name} is missing {key} for NRT={count}.")
                obj = root[key]
                if obj.classname not in ("TVectorT<double>", "TVectorT<float>"):
                    raise ValueError(f"[RT] {key} must be a Chebyshev coefficient vector, got {obj.classname}.")
                if obj.member("fRowLwb") != 0:
                    raise ValueError(f"[RT] {key} must start at coefficient 0.")
                params.append(cls._validate_coefficients(obj.member("fElements"), key, n_coeff))
            return params

    def _catalogue_range(self, path, ml):
        table = path.with_name(f"{path.stem}_ML{ml + 1}.txt")
        if not table.is_file():
            raise ValueError(f"{path.name} contains no time limits. Keep {table.name} beside it "
                             "or turn off catalogue time ranges and enter Tmin/Tmax manually.")
        rows = [line.strip() for line in table.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
        if not rows or rows[0].split() != ["radius_mm", "time_ns", "resolution_mm"]:
            raise ValueError(f"[RT] Invalid catalogue table header: {table}")
        data = np.loadtxt(rows[1:], dtype=np.float64, ndmin=2)
        if (data.shape[0] < 2 or data.shape[1] != 3 or not np.all(np.isfinite(data))
                or np.any(np.diff(data[:, 1]) <= 0)):
            raise ValueError(f"[RT] Invalid catalogue time range: {table}")
        self.source_tables.append(str(table))
        return [data[0, 1], data[-1, 1]]

    def _indices(self, multilayer):
        if multilayer is None:
            if self.nrt == 2:
                raise ValueError("NRT=2 requires a multilayer index for each hit (0=ML1, 1=ML2).")
            return np.asarray(0)
        ml = np.asarray(multilayer)
        if np.any((ml != 0) & (ml != 1)):
            raise ValueError("Multilayer indices must be 0 (ML1) or 1 (ML2).")
        return np.zeros_like(ml, dtype=np.intp) if self.nrt == 1 else ml.astype(np.intp)

    def time_bounds(self, multilayer=None):
        ranges = self.time_ranges[self._indices(multilayer)]
        return ranges[..., 0], ranges[..., 1]

    def r_of_t(self, t, multilayer=None):
        t, indices = np.broadcast_arrays(np.asarray(t, dtype=np.float64), self._indices(multilayer))
        out = np.empty(t.shape, dtype=np.float64)
        for ml, params in enumerate(self.params_by_ml):
            mask = indices == ml
            lo, hi = self.time_ranges[ml]
            out[mask] = chebval(2.0 * (t[mask] - lo) / (hi - lo) - 1.0, params)
        return out

    def build_fast_inverse(self, n: int = 2048):
        if int(n) < 2:
            raise ValueError("Inverse LUT requires at least two points.")
        self._inverse_luts = []
        for ml, (lo, hi) in enumerate(self.time_ranges):
            times = np.linspace(lo, hi, int(n))
            radii = self.r_of_t(times, ml)
            order = np.argsort(radii)
            self._inverse_luts.append((np.maximum(radii[order], 0).astype(np.float32),
                                       times[order].astype(np.float32)))
        self.r_lut_sorted, self.t_lut_sorted = self._inverse_luts[0]

    def t_from_r_fast(self, r_mm, multilayer=None):
        if self._inverse_luts is None:
            raise RuntimeError("Call build_fast_inverse() first.")
        radii, indices = np.broadcast_arrays(np.asarray(r_mm, dtype=np.float32), self._indices(multilayer))
        out = np.full(radii.shape, np.nan, dtype=np.float32)
        for ml, (rr, tt) in enumerate(self._inverse_luts):
            mask = (indices == ml) & (radii >= rr[0]) & (radii <= rr[-1])
            out[mask] = np.interp(radii[mask], rr, tt)
        return out


def hit_multilayers(hits, geometry):
    """Resolve decoded hit layers using the selected chamber's geometry."""
    if geometry is None:
        raise ValueError("NRT=2 requires the chamber geometry to identify multilayers.")
    return np.asarray([geometry.multilayer_from_layer(int(h.layer)) for h in hits], dtype=np.int32)
