# geometry.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import math
from statistics import median
from typing import List, Tuple, Dict, Any, Optional


@dataclass
class Geometry:
    # =========================
    # settings
    # =========================
    chamberType: str = "A"   # "A" or "C"
    flipTDCs: int = 1
    tdcColByTubeNo: int = 1

    # =========================
    # dimensions
    # =========================
    MAX_TDC: int = 40
    MAX_TDC_CHANNEL: int = 24
    MAX_TUBE_LAYER: int = 8
    MAX_TUBE_COLUMN: int = 60
    MAX_TDC_LAYER: int = 4

    ML_distance: float = 114.5695
    tube_length: float = 1.6715
    layer_distance: float = 13.0769836
    column_distance: float = 15.1
    radius: float = 7.5

    min_drift_dist: float = 0.0
    max_drift_dist: float = 7.1

    # =========================
    # assignment (persisted)
    # =========================
    n_mls: int = 2
    slots_per_ml: int = 10
    ml0: List[Tuple[int, int]] = field(default_factory=list)  # (tdc_id, ncol)
    ml1: List[Tuple[int, int]] = field(default_factory=list)
    ml_slots: List[List[Tuple[int, int]]] = field(default_factory=list, metadata={"persist": False})

    # =========================
    # auto-load
    # =========================
    geo_file: Optional[str] = None

    # =========================
    # runtime identity (NOT persisted)
    # =========================
    chamber_id: int = field(default=-1, repr=False, compare=False, metadata={"persist": False})

    # =========================
    # internal flags (NOT persisted)
    # =========================
    _skip_autoload: bool = field(default=False, repr=False, compare=False, metadata={"persist": False})

    # =========================
    # runtime arrays
    # =========================
    isActiveTDC: List[int] = field(default_factory=list)      # size MAX_TDC
    TDC_ML: List[int] = field(default_factory=list)           # size MAX_TDC
    TDC_COL: List[int] = field(default_factory=list)          # size MAX_TDC
    hit_layer_map: List[int] = field(default_factory=list)    # size MAX_TDC_CHANNEL
    hit_column_map: List[int] = field(default_factory=list)   # size MAX_TDC_CHANNEL
    tdc_map: List[Tuple[int, int, int]] = field(default_factory=list)  # (tdc, ml, colstart)
    # Explicit physical layout, independent of hardware TDC assignments.
    # (ML, slot, channel) -> (global layer, column, x_mm, y_mm), all indices zero based.
    tube_map: Dict[Tuple[int, int, int], Tuple[int, int, float, float]] = field(
        default_factory=dict, metadata={"persist": False})
    _channel_tubes: Dict = field(default_factory=dict, repr=False, metadata={"persist": False})
    _tube_channels: Dict = field(default_factory=dict, repr=False, metadata={"persist": False})
    _tube_centers: Dict = field(default_factory=dict, repr=False, metadata={"persist": False})
    _tube_slots: Dict = field(default_factory=dict, repr=False, metadata={"persist": False})

    # =============================================================================
    # init hook
    # =============================================================================

    def __post_init__(self) -> None:
        """
        Autoload policy:
          - If geo_file exists and _skip_autoload is False:
              load file into a temporary Geometry, then copy into self.
              Keep chamber_id from caller (not persisted).
          - If file missing / load fails:
              use init values.
        """
        # autoload first (so we don't build maps from wrong defaults)
        if (not self._skip_autoload) and self.geo_file:
            path = Path(self.geo_file)
            if path.is_file():
                try:
                    loaded = type(self).load(str(path), apply_map=True)  # loaded has its own post_init
                    keep_chamber_id = int(self.chamber_id)
                    self._copy_from(loaded)
                    self.chamber_id = keep_chamber_id
                    self.geo_file = str(path)
                    print(f"[Geometry] Loaded geometry from '{path}' (chamber_id={self.chamber_id})")
                    return
                except Exception as e:
                    print(f"[Geometry] Failed to load geometry from '{path}': {e} (using init values)")
            else:
                print(f"[Geometry] Geometry file not found: '{path}' (using init values)")

        # normal init path (no file)
        self._alloc()
        self.reset_tube_layout()
        self.set_assignment(
            self.slots_per_ml,
            self.ml0,
            self.ml1,
            ml_slots=self.ml_slots or None,
            n_mls=self.n_mls,
            apply_map=True,
        )

    def _copy_from(self, other: "Geometry") -> None:
        """
        Copy ALL geometry config + runtime arrays from 'other' into self.
        Does NOT copy chamber_id (caller-owned identity).
        """
        # persisted config / settings
        self.chamberType = other.chamberType
        self.flipTDCs = int(other.flipTDCs)
        self.tdcColByTubeNo = int(other.tdcColByTubeNo)

        self.MAX_TDC = int(other.MAX_TDC)
        self.MAX_TDC_CHANNEL = int(other.MAX_TDC_CHANNEL)
        self.MAX_TUBE_LAYER = int(other.MAX_TUBE_LAYER)
        self.MAX_TUBE_COLUMN = int(other.MAX_TUBE_COLUMN)
        self.MAX_TDC_LAYER = int(other.MAX_TDC_LAYER)

        self.ML_distance = float(other.ML_distance)
        self.tube_length = float(other.tube_length)
        self.layer_distance = float(other.layer_distance)
        self.column_distance = float(other.column_distance)
        self.radius = float(other.radius)

        self.min_drift_dist = float(other.min_drift_dist)
        self.max_drift_dist = float(other.max_drift_dist)

        # assignment
        self.n_mls = int(getattr(other, "n_mls", 2))
        self.slots_per_ml = int(other.slots_per_ml)
        self.ml0 = list(other.ml0)
        self.ml1 = list(other.ml1)
        self.ml_slots = [list(slots) for slots in getattr(other, "ml_slots", [])]

        # runtime arrays / maps
        self.isActiveTDC = list(other.isActiveTDC)
        self.TDC_ML = list(other.TDC_ML)
        self.TDC_COL = list(other.TDC_COL)
        self.hit_layer_map = list(other.hit_layer_map)
        self.hit_column_map = list(other.hit_column_map)
        self.tdc_map = list(other.tdc_map)
        self.geo_file = other.geo_file
        self.tube_map = dict(other.tube_map)
        self._rebuild_explicit_maps()

    def _alloc(self) -> None:
        self.isActiveTDC = [0] * int(self.MAX_TDC)
        self.TDC_ML = [0] * int(self.MAX_TDC)
        self.TDC_COL = [0] * int(self.MAX_TDC)
        self.hit_layer_map = [0] * int(self.MAX_TDC_CHANNEL)
        self.hit_column_map = [0] * int(self.MAX_TDC_CHANNEL)

    # =============================================================================
    # Geometry mapping
    # =============================================================================

    def reset_tube_layout(self) -> None:
        for i in range(int(self.MAX_TDC_CHANNEL)):
            if int(self.MAX_TDC_LAYER) == 3:
                # Standard three-layer MDT mezzanine. Imported GEO wiring
                # overrides this for each individual channel, including ML2.
                self.hit_layer_map[i] = 2 - i // 8
                self.hit_column_map[i] = (7, 0, 6, 1, 5, 2, 4, 3)[i % 8]
            else:
                self.hit_layer_map[i] = (i + 2) % int(self.MAX_TDC_LAYER)
                self.hit_column_map[i] = i // int(self.MAX_TDC_LAYER)

    def configure_tdc_map(
        self,
        active_tdcs: List[int],
        tdc_multilayer: List[int],
        tdc_colstart: List[int],
        strict_duplicates: bool = False,
    ) -> None:
        if not (len(active_tdcs) == len(tdc_multilayer) == len(tdc_colstart)):
            raise ValueError("ActiveTDCs/TDCMultilayer/TDCColumn length mismatch")

        self.tdc_map = []
        self.isActiveTDC = [0] * int(self.MAX_TDC)
        self.TDC_ML = [0] * int(self.MAX_TDC)
        self.TDC_COL = [0] * int(self.MAX_TDC)

        seen = set()
        for tdc, ml, colstart in zip(active_tdcs, tdc_multilayer, tdc_colstart):
            tdc = int(tdc)
            ml = int(ml)
            colstart = int(colstart)

            if not (0 <= tdc < int(self.MAX_TDC)):
                continue
            n_mls = max(1, int(getattr(self, "n_mls", 2) or 2))
            if not (0 <= ml < n_mls):
                continue
            if strict_duplicates and tdc in seen:
                raise ValueError(f"Duplicate tdc {tdc}")
            seen.add(tdc)

            self.tdc_map.append((tdc, ml, colstart))
            self.isActiveTDC[tdc] = 1
            self.TDC_ML[tdc] = ml
            self.TDC_COL[tdc] = colstart
        self._rebuild_explicit_maps()

    def _rebuild_explicit_maps(self) -> None:
        self._channel_tubes = {}
        self._tube_channels = {}
        self._tube_centers = {}
        self._tube_slots = {}
        slots = self.ml_slots
        for (ml, slot, channel), (layer, col, x, y) in self.tube_map.items():
            if not (0 <= ml < self.n_mls and 0 <= slot < self.slots_per_ml
                    and 0 <= channel < self.MAX_TDC_CHANNEL
                    and 0 <= layer < self.MAX_TUBE_LAYER and 0 <= col < self.MAX_TUBE_COLUMN
                    and self.multilayer_from_layer(layer) == ml
                    and math.isfinite(x) and math.isfinite(y) and x >= 0 and y >= 0):
                raise ValueError(f"Invalid explicit tube: ML/slot/channel {ml}/{slot}/{channel}")
            if (layer, col) in self._tube_centers:
                raise ValueError(f"Duplicate tube at layer {layer}, column {col}")
            self._tube_centers[layer, col] = (x, y)
            self._tube_slots[layer, col] = slot
            if ml >= len(slots) or slot >= len(slots[ml]):
                continue
            tdc, ncol = slots[ml][slot]
            if tdc < 0 or ncol <= 0 or not self.isActiveTDC[tdc]:
                continue
            if (tdc, channel) in self._channel_tubes:
                raise ValueError(f"Duplicate TDC/channel assignment: {tdc}/{channel}")
            self._channel_tubes[tdc, channel] = (layer, col)
            self._tube_channels[layer, col] = (tdc, channel)

    def tdc_channel_for_tube(self, layer: int, col: int) -> Optional[Tuple[int, int]]:
        if self.tube_map:
            return self._tube_channels.get((int(layer), int(col)))
        for tdc, active in enumerate(self.isActiveTDC):
            if active:
                for channel in range(self.MAX_TDC_CHANNEL):
                    if self.get_hit_layer_column(tdc, channel) == (layer, col):
                        return tdc, channel
        return None

    def multilayer_from_layer(self, layer: int) -> int:
        return int(layer) // int(self.MAX_TDC_LAYER)

    def get_hit_layer_column(self, tdc_id: int, channel_id: int) -> Tuple[int, int]:
        if not (0 <= int(tdc_id) < int(self.MAX_TDC)):
            raise ValueError(f"tdc_id out of range: {tdc_id}")
        if not (0 <= int(channel_id) < int(self.MAX_TDC_CHANNEL)):
            raise ValueError(f"channel_id out of range: {channel_id}")
        if int(self.isActiveTDC[int(tdc_id)]) == 0:
            raise ValueError(f"tdc_id not active: {tdc_id}")
        if self.tube_map:
            try:
                return self._channel_tubes[int(tdc_id), int(channel_id)]
            except KeyError as exc:
                raise ValueError(f"No GEO mapping for TDC {tdc_id}, channel {channel_id}") from exc

        hit_column = int(self.TDC_COL[int(tdc_id)]) + int(self.hit_column_map[int(channel_id)])
        hit_layer = int(self.MAX_TDC_LAYER) * int(self.TDC_ML[int(tdc_id)]) + int(self.hit_layer_map[int(channel_id)])
        return hit_layer, hit_column

    def get_hit_xy(self, hitL: int, hitC: int) -> Tuple[float, float]:
        if self.tube_map:
            return self._tube_centers.get((int(hitL), int(hitC)), (-1.0, -1.0))
        if hitL < 0 or hitC < 0 or hitL >= int(self.MAX_TUBE_LAYER) or hitC >= int(self.MAX_TUBE_COLUMN):
            return -1.0, -1.0

        x = float(self.radius + hitC * self.column_distance + (hitL % 2) * (self.column_distance / 2.0))
        y = float(
            self.radius
            + hitL * self.layer_distance
            + (self.ML_distance - int(self.MAX_TDC_LAYER) * self.layer_distance) * self.multilayer_from_layer(hitL)
        )
        return x, y

    def wire_center_from_hit(self, tdc_id: int, channel_id: int) -> Tuple[float, float, int, int]:
        layer, col = self.get_hit_layer_column(tdc_id, channel_id)
        x, y = self.get_hit_xy(layer, col)
        return x, y, layer, col

    def channel_id_from_local(self, local_layer: int, local_col: int) -> int:
        for channel, (layer, col) in enumerate(zip(self.hit_layer_map, self.hit_column_map)):
            if (layer, col) == (int(local_layer), int(local_col)):
                return channel
        return -1

    # =============================================================================
    # Assignment helpers
    # =============================================================================

    def _pad_and_clamp_slots(self, slots_per_ml: int, vals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        slots_per_ml = int(slots_per_ml)
        out = list(vals[:slots_per_ml])
        while len(out) < slots_per_ml:
            out.append((-1, 6))

        max_cols = int(self.MAX_TUBE_COLUMN)
        acc = 0
        out2: List[Tuple[int, int]] = []
        for tdc_id, ncol in out:
            tdc_id = int(tdc_id)
            ncol = max(0, int(ncol))
            if acc >= max_cols:
                ncol = 0
            else:
                ncol = min(ncol, max_cols - acc)
            out2.append((tdc_id, ncol))
            acc += ncol
        return out2

    def assignment_by_ml(self) -> List[List[Tuple[int, int]]]:
        n_mls = max(1, int(getattr(self, "n_mls", 2) or 2))
        src = [list(slots) for slots in getattr(self, "ml_slots", [])]
        if not src:
            src = [list(getattr(self, "ml0", [])), list(getattr(self, "ml1", []))]
        while len(src) < n_mls:
            src.append([])
        return [self._pad_and_clamp_slots(int(self.slots_per_ml), src[i]) for i in range(n_mls)]

    def set_assignment(
        self,
        slots_per_ml: int,
        ml0: Optional[List[Tuple[int, int]]] = None,
        ml1: Optional[List[Tuple[int, int]]] = None,
        *,
        ml_slots: Optional[List[List[Tuple[int, int]]]] = None,
        n_mls: Optional[int] = None,
        apply_map: bool = False,
        strict_duplicates: bool = False,
    ) -> None:
        self.slots_per_ml = int(slots_per_ml)

        if ml_slots is None:
            src: List[List[Tuple[int, int]]] = [
                list(ml0 or []),
                list(ml1 or []),
            ]
            if getattr(self, "ml_slots", None):
                src.extend([list(slots) for slots in self.ml_slots[2:]])
        else:
            src = [list(slots or []) for slots in ml_slots]

        if n_mls is None:
            n_mls = max(1, len(src), int(getattr(self, "n_mls", 2) or 2))
        self.n_mls = max(1, int(n_mls))
        self.MAX_TUBE_LAYER = max(int(self.MAX_TUBE_LAYER), self.n_mls * int(self.MAX_TDC_LAYER))
        if any(src):
            max_src_cols = max(
                (
                    sum(max(0, int(ncol)) for _tdc_id, ncol in slots[: self.slots_per_ml])
                    for slots in src
                ),
                default=0,
            )
        else:
            max_src_cols = int(self.slots_per_ml) * 6
        self.MAX_TUBE_COLUMN = max(int(self.MAX_TUBE_COLUMN), int(max_src_cols))

        while len(src) < self.n_mls:
            src.append([])

        self.ml_slots = [
            self._pad_and_clamp_slots(self.slots_per_ml, src[ml_id])
            for ml_id in range(self.n_mls)
        ]
        self.ml0 = list(self.ml_slots[0]) if self.n_mls >= 1 else []
        self.ml1 = list(self.ml_slots[1]) if self.n_mls >= 2 else []

        max_tdc_id = max(
            (
                int(tdc_id)
                for slots in self.ml_slots
                for tdc_id, ncol in slots
                if int(tdc_id) >= 0 and int(ncol) > 0
            ),
            default=-1,
        )
        if max_tdc_id >= int(self.MAX_TDC):
            self.MAX_TDC = int(max_tdc_id) + 1

        if apply_map:
            active: List[int] = []
            mls: List[int] = []
            cols: List[int] = []

            for ml_id, slots in enumerate(self.ml_slots):
                acc = 0
                for tdc_id, ncol in slots[: self.slots_per_ml]:
                    if int(tdc_id) >= 0 and int(ncol) > 0:
                        active.append(int(tdc_id))
                        mls.append(int(ml_id))
                        cols.append(int(acc))
                    acc += max(0, int(ncol))

            self.configure_tdc_map(active, mls, cols, strict_duplicates=strict_duplicates)

    # =============================================================================
    # Serialization / loading
    # =============================================================================

    def to_text(self) -> str:
        g = self
        slots_per_ml = int(self.slots_per_ml)
        n_mls = max(1, int(getattr(self, "n_mls", 2) or 2))
        ml_slots = self.assignment_by_ml()

        lines: List[str] = []
        lines.append("# geometry assignment")
        lines.append("")
        lines.append("chamberType " + str(g.chamberType))
        lines.append(f"flipTDCs {int(g.flipTDCs)}")
        lines.append(f"tdcColByTubeNo {int(g.tdcColByTubeNo)}")
        lines.append("")
        lines.append(f"MAX_TDC {int(g.MAX_TDC)}")
        lines.append(f"MAX_TDC_CHANNEL {int(g.MAX_TDC_CHANNEL)}")
        lines.append(f"MAX_TUBE_LAYER {int(g.MAX_TUBE_LAYER)}")
        lines.append(f"MAX_TUBE_COLUMN {int(g.MAX_TUBE_COLUMN)}")
        lines.append(f"MAX_TDC_LAYER {int(g.MAX_TDC_LAYER)}")
        lines.append("")
        lines.append(f"ML_distance {float(g.ML_distance)}")
        lines.append(f"tube_length {float(g.tube_length)}")
        lines.append(f"layer_distance {float(g.layer_distance)}")
        lines.append(f"column_distance {float(g.column_distance)}")
        lines.append(f"radius {float(g.radius)}")
        lines.append(f"min_drift_dist {float(g.min_drift_dist)}")
        lines.append(f"max_drift_dist {float(g.max_drift_dist)}")
        lines.append("")
        lines.append(f"n_mls {n_mls}")
        lines.append(f"slots_per_ml {slots_per_ml}")
        lines.append("")
        for ml_id, slots in enumerate(ml_slots[:n_mls]):
            lines.append(f"ML{ml_id}")
            for i, (tdc_id, ncol) in enumerate(slots[:slots_per_ml]):
                lines.append(f"{i} {int(tdc_id)} {int(ncol)}")
            lines.append("")
        if self.tube_map:
            lines.append("TUBES")
            lines.append("# ml slot channel layer column x_mm y_mm (zero based)")
            for (ml, slot, channel), (layer, col, x, y) in sorted(self.tube_map.items()):
                lines.append(f"{ml} {slot} {channel} {layer} {col} {x!r} {y!r}")
        return "\n".join(lines)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_text())

    @classmethod
    def load(cls, path: str, *, apply_map: bool = False) -> "Geometry":
        with open(path, "r", encoding="utf-8") as f:
            geo = cls.from_text(f.read(), apply_map=apply_map)
        geo.geo_file = str(path)
        return geo

    @classmethod
    def from_text(cls, text: str, *, apply_map: bool = False) -> "Geometry":
        content = [line.split("#", 1)[0].strip() for line in text.splitlines()]
        content = [line for line in content if line]
        if content and ("MZ" in content[0].split() or "MezzCh" in content[0].split()):
            return cls.from_geo_table(text)
        gdict: Dict[str, Any] = {}
        n_mls: Optional[int] = None
        slots_per_ml = 10
        ml_by_id: Dict[int, List[Tuple[int, int]]] = {}
        cur_ml: Optional[int] = None
        tube_map = {}
        in_tubes = False

        allowed_geo_keys = {
            k for k, f in cls.__dataclass_fields__.items()
            if (not k.startswith("_")) and f.metadata.get("persist", True)
        }

        lines: List[str] = []
        for raw in text.splitlines():
            s = raw.strip()
            s = s.split("#", 1)[0].strip()
            if not s or s.startswith("#"):
                continue
            lines.append(s)

        for s in lines:
            up = s.upper()
            if up == "TUBES":
                in_tubes = True
                continue
            if in_tubes:
                parts = s.split()
                if len(parts) != 7:
                    raise ValueError("TUBES rows require ml slot channel layer column x_mm y_mm")
                ml, slot, ch, layer, col = map(int, parts[:5])
                key = (ml, slot, ch)
                if key in tube_map:
                    raise ValueError(f"Duplicate explicit channel {key}")
                tube_map[key] = (layer, col, float(parts[5]), float(parts[6]))
                continue
            if up.startswith("ML") and up[2:].isdigit():
                cur_ml = int(up[2:])
                ml_by_id.setdefault(cur_ml, [])
                continue

            parts = s.split()

            if cur_ml is not None and len(parts) >= 3:
                try:
                    _slot = int(parts[0])
                    tdc_id = int(parts[1])
                    ncol = max(0, int(parts[2]))
                except ValueError:
                    continue
                ml_by_id.setdefault(cur_ml, []).append((tdc_id, ncol))
                continue

            if len(parts) == 2:
                k, v = parts[0], parts[1]

                if k == "slots_per_ml":
                    try:
                        slots_per_ml = int(v)
                    except ValueError:
                        pass
                    continue

                if k == "n_mls":
                    try:
                        n_mls = int(v)
                    except ValueError:
                        pass
                    continue

                if k not in allowed_geo_keys:
                    continue

                if k == "chamberType":
                    gdict[k] = str(v)
                    continue

                if k.startswith("MAX_") or k in ("flipTDCs", "tdcColByTubeNo"):
                    try:
                        gdict[k] = int(v)
                    except ValueError:
                        pass
                    continue

                try:
                    gdict[k] = float(v)
                except ValueError:
                    pass

        if n_mls is None:
            n_mls = max(2, max(ml_by_id.keys(), default=1) + 1)
        if not gdict and not ml_by_id:
            raise ValueError("Unrecognized geometry file: expected geometry settings or a MZ/MezzCh GEO table")
        n_mls = max(1, int(n_mls))
        ml_slots = [ml_by_id.get(ml_id, []) for ml_id in range(n_mls)]

        geo = cls(_skip_autoload=True, slots_per_ml=slots_per_ml, n_mls=n_mls, **gdict)
        geo.tube_map = tube_map
        geo.set_assignment(slots_per_ml, ml_slots=ml_slots, n_mls=n_mls, apply_map=apply_map)
        geo._rebuild_explicit_maps()
        return geo

    @classmethod
    def from_geo_table(cls, text: str) -> "Geometry":
        """Import MZ/MezzCh/locY/locZ/Layer/Tube_y/ML chamber survey tables.

        MZ is the initial zero-based global TDC ID. MezzCh is either the local
        channel or 100*(MZ+1)+channel. Layer/Tube_y/ML are one based. locZ is
        horizontal (GUI x), locY vertical (GUI y), both in mm.
        """
        lines = [(number, line.split("#", 1)[0].strip())
                 for number, line in enumerate(text.splitlines(), 1)]
        lines = [(number, line) for number, line in lines if line]
        required = ("MZ", "MezzCh", "locY", "locZ", "Layer", "Tube_y", "ML")
        if not lines or len(lines[0][1].split()) != len(required) or set(lines[0][1].split()) != set(required):
            raise ValueError("GEO header must contain: " + " ".join(required))
        header = lines[0][1].split()
        rows = []
        channels, tubes, mz_ml = set(), set(), {}
        for number, line in lines[1:]:
            values = line.split()
            if len(values) != len(header):
                raise ValueError(f"GEO line {number}: expected seven columns")
            row = dict(zip(header, values))
            try:
                mz, encoded = int(row["MZ"]), int(row["MezzCh"])
                layer, col, ml = int(row["Layer"])-1, int(row["Tube_y"])-1, int(row["ML"])-1
                x, y = float(row["locZ"]), float(row["locY"])
            except ValueError as exc:
                raise ValueError(f"GEO line {number}: invalid number") from exc
            ch = encoded if 0 <= encoded < 24 else encoded - 100*(mz+1)
            if not (0 <= mz < 40 and 0 <= ch < 24 and 0 <= ml < 16
                    and 0 <= layer < 16 and 0 <= col < 512
                    and math.isfinite(x) and math.isfinite(y) and x >= 0 and y >= 0):
                raise ValueError(f"GEO line {number}: invalid MZ/channel, tube index, or position")
            if (mz, ch) in channels:
                raise ValueError(f"GEO line {number}: duplicate MZ/channel {mz}/{ch}")
            if (ml, layer, col) in tubes:
                raise ValueError(f"GEO line {number}: duplicate tube {ml+1}/{layer+1}/{col+1}")
            if mz_ml.setdefault(mz, ml) != ml:
                raise ValueError(f"GEO line {number}: MZ {mz} belongs to multiple multilayers")
            channels.add((mz, ch))
            tubes.add((ml, layer, col))
            rows.append((mz, ch, ml, layer, col, x, y))
        if not rows:
            raise ValueError("GEO file contains no tubes")
        n_mls = max(row[2] for row in rows)+1
        n_layers = max(row[3] for row in rows)+1
        for ml in range(n_mls):
            if {row[3] for row in rows if row[2] == ml} != set(range(n_layers)):
                raise ValueError("GEO multilayers must have the same consecutive layer numbers starting at 1")

        ml_slots, slot_for_mz = [], {}
        for ml in range(n_mls):
            mezzanines = sorted((mz for mz in mz_ml if mz_ml[mz] == ml),
                               key=lambda mz: min(r[4] for r in rows if r[0] == mz))
            slots = []
            for slot, mz in enumerate(mezzanines):
                slot_for_mz[mz] = slot
                slots.append((mz, len({r[4] for r in rows if r[0] == mz})))
            ml_slots.append(slots)
        slots_per_ml = max(map(len, ml_slots))
        # Empty slots occupy no physical columns in a file-defined layout.
        for slots in ml_slots:
            slots.extend([(-1, 0)] * (slots_per_ml-len(slots)))

        by_layer = {}
        for _, _, ml, layer, col, x, y in rows:
            by_layer.setdefault((ml, layer), []).append((col, x, y))
        pitches = []
        for points in by_layer.values():
            points.sort()
            pitches.extend((b[1]-a[1])/(b[0]-a[0]) for a, b in zip(points, points[1:])
                           if b[0] > a[0] and b[1] > a[1])
        heights = {key: median(p[2] for p in points) for key, points in by_layer.items()}
        layer_gaps = [heights[ml, layer+1]-heights[ml, layer]
                      for ml in range(n_mls) for layer in range(n_layers-1)]
        ml_gaps = [heights[ml+1, 0]-heights[ml, 0] for ml in range(n_mls-1)]
        geo = cls(_skip_autoload=True, MAX_TUBE_LAYER=n_mls*n_layers,
                  MAX_TDC_LAYER=n_layers, MAX_TUBE_COLUMN=max(r[4] for r in rows)+1,
                  n_mls=n_mls, slots_per_ml=slots_per_ml, ml_slots=ml_slots,
                  column_distance=median(pitches) if pitches else 30.035,
                  layer_distance=median(layer_gaps) if layer_gaps else 26.0111,
                  ML_distance=median(ml_gaps) if ml_gaps else 0.0,
                  radius=14.985, max_drift_dist=14.6)
        geo.tube_map = {(ml, slot_for_mz[mz], ch): (ml*n_layers+layer, col, x, y)
                        for mz, ch, ml, layer, col, x, y in rows}
        geo._rebuild_explicit_maps()
        return geo

    @classmethod
    def enforce_exclusive_active_tdcs(
        cls,
        geos: List["Geometry"],
        *,
        keep_ncol: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Make active TDC IDs exclusive across a list of Geometry objects.

        Rule:
          - Sort by chamber_id ascending
          - Lowest chamber_id "owns" a TDC
          - If a later (higher chamber_id) geo has the same active TDC (tdc_id>=0 and ncol>0),
            remove it from the later geo by setting tdc_id=-1.

        keep_ncol:
          - True: (-1, ncol)  keeps packing unchanged (recommended)
          - False: (-1, 0)    frees columns (packing changes)

        This mutates the Geometry objects in-place and re-applies set_assignment(apply_map=True).
        """
        if not geos:
            return

        # deterministic: lowest chamber_id wins
        geos_sorted = sorted(geos, key=lambda g: int(getattr(g, "chamber_id", 0)))

        seen: set[int] = set()

        for g in geos_sorted:
            # Ensure internal maps match current assignment before checking
            g.set_assignment(
                g.slots_per_ml,
                ml_slots=g.assignment_by_ml(),
                n_mls=getattr(g, "n_mls", 2),
                apply_map=True,
            )

            removed: List[Tuple[str, int]] = []

            def _scrub(slot_list: List[Tuple[int, int]], ml_name: str) -> List[Tuple[int, int]]:
                out: List[Tuple[int, int]] = []
                for (tdc_id, ncol) in slot_list:
                    t = int(tdc_id)
                    n = max(0, int(ncol))

                    if t >= 0 and n > 0 and t in seen:
                        out.append((-1, n if keep_ncol else 0))
                        removed.append((ml_name, t))
                    else:
                        out.append((t, n))
                        if t >= 0 and n > 0:
                            seen.add(t)
                return out

            old_ml_slots = g.assignment_by_ml()
            new_ml_slots = [
                _scrub(slots, f"ML{ml_id}")
                for ml_id, slots in enumerate(old_ml_slots)
            ]

            if new_ml_slots != old_ml_slots:
                g.set_assignment(
                    g.slots_per_ml,
                    ml_slots=new_ml_slots,
                    n_mls=getattr(g, "n_mls", 2),
                    apply_map=True,
                )

            if verbose and removed:
                print(f"[Geometry] chamber_id={g.chamber_id}: removed duplicated TDCs {removed}")
