"""Firmware TFB v1 wire formats and geometry-image construction (no GUI/I/O)."""
from dataclasses import dataclass

SIGNATURE = 0x54464201
MAX_THRESHOLD = 256
FILTER_FIELDS = (
    ("min_tubes", "Minimum tubes / event"),
    ("min_tubes_per_ml", "Minimum tubes / every ML"),
    ("min_tubes_per_layer", "Minimum tubes / every layer"),
    ("min_layers_per_ml", "Minimum hit layers / every ML"),
)
ERRORS = {
    1: "table index out of range", 2: "invalid geometry entry",
    3: "unknown command", 4: "invalid filter settings",
    5: "missing channel entry", 6: "chamber disagrees with TDC routing",
    7: "global layer assigned to multiple MLs", 8: "tube ID reused for another position",
    9: "one tube position has multiple IDs", 10: "no mapped tubes",
}


@dataclass(frozen=True)
class TubeFilterSettings:
    enabled: int = 1
    min_tubes: int = 4
    min_tubes_per_ml: int = 0
    min_tubes_per_layer: int = 0
    min_layers_per_ml: int = 0

    def __post_init__(self):
        if not 0 <= self.enabled <= 15:
            raise ValueError("Tube-filter enable mask must be 0..15")
        for name, _label in FILTER_FIELDS:
            if not 0 <= getattr(self, name) <= MAX_THRESHOLD:
                raise ValueError(f"{name} must be 0..{MAX_THRESHOLD}")

    def pack(self):
        return (self.enabled | self.min_tubes << 4 | self.min_tubes_per_ml << 14 |
                self.min_tubes_per_layer << 24 | self.min_layers_per_ml << 34)

    @classmethod
    def unpack(cls, value):
        value = int(value)
        if not 0 <= value < 1 << 43:
            raise ValueError("Reserved tube-filter bits are set")
        return cls(value & 15, (value >> 4) & 1023, (value >> 14) & 1023,
                   (value >> 24) & 1023, (value >> 34) & 511)


@dataclass(frozen=True)
class GeometryImage:
    enabled_mask: int
    chamber1_mask: int
    entries: tuple  # (table index, packed entry), including explicit invalids
    positions: tuple  # unique (chamber, ML, global layer, column)
    ml_masks: tuple
    layer_masks: tuple

    def validate_filters(self, settings, raw_limit=0):
        """Reject impossible cuts before starting; repeats can still fill PREBUF."""
        capacity = min(256, int(raw_limit) or 1023)
        for chamber, cfg in enumerate(settings):
            tubes = [p for p in self.positions if p[0] == chamber]
            if not tubes:  # an unused chamber must not block the active chamber
                continue
            needed = 0
            for ml in sorted({p[1] for p in tubes}):
                ml_tubes = [p for p in tubes if p[1] == ml]
                layers = {p[2] for p in ml_tubes}
                ml_needed = 0
                if cfg.enabled & 2:
                    if len(ml_tubes) < cfg.min_tubes_per_ml:
                        raise ValueError(f"Chamber {chamber}, ML {ml}: too few mapped tubes for the ML cut")
                    ml_needed = cfg.min_tubes_per_ml
                if cfg.enabled & 4:
                    for layer in layers:
                        if sum(p[2] == layer for p in ml_tubes) < cfg.min_tubes_per_layer:
                            raise ValueError(f"Chamber {chamber}, layer {layer}: too few mapped tubes")
                    ml_needed = max(ml_needed, len(layers) * cfg.min_tubes_per_layer)
                if cfg.enabled & 8:
                    if len(layers) < cfg.min_layers_per_ml:
                        raise ValueError(f"Chamber {chamber}, ML {ml}: too few mapped layers")
                    ml_needed = max(ml_needed, cfg.min_layers_per_ml)
                needed += ml_needed
            if cfg.enabled & 1:
                if len(tubes) < cfg.min_tubes:
                    raise ValueError(f"Chamber {chamber}: too few mapped tubes for the event cut")
                needed = max(needed, cfg.min_tubes)
            if max(1, needed) > capacity:
                raise ValueError(f"Chamber {chamber}: cuts need at least {needed} tubes, "
                                 f"but the prebuffer/raw-word limit is {capacity}")


def build_geometry_image(geometries):
    """Use the exact Geometry channel maps, never reconstruct mezz-slot wiring."""
    owners, entries, tube_ids, layer_owners = {}, [], {}, {}
    ml_masks, layer_masks = [0, 0], [0, 0]
    enabled = chamber1 = 0
    for geo in geometries:
        chamber = int(geo.chamber_id)
        if chamber not in (0, 1):
            raise ValueError(f"Unsupported chamber ID {chamber}; expected 0 or 1")
        for tdc, active in enumerate(geo.isActiveTDC):
            if not active:
                continue
            if not 0 <= tdc < 40 or tdc in owners:
                raise ValueError(f"Invalid or multiply assigned TDC {tdc}")
            owners[tdc] = chamber
            enabled |= 1 << tdc
            chamber1 |= chamber << tdc
            for channel in range(24):
                index = (tdc << 5) | channel
                if channel >= int(geo.MAX_TDC_CHANNEL):
                    entries.append((index, 0))
                    continue
                if geo.tube_map and (tdc, channel) not in geo._channel_tubes:
                    entries.append((index, 0))
                    continue
                layer, column = map(int, geo.get_hit_layer_column(tdc, channel))
                ml = int(geo.TDC_ML[tdc])
                if not (0 <= ml < 16 and 0 <= layer < min(256, int(geo.MAX_TUBE_LAYER))
                        and 0 <= column < min(512, int(geo.MAX_TUBE_COLUMN))):
                    raise ValueError(f"Chamber {chamber}, TDC {tdc}, channel {channel}: "
                                     f"geometry ML/layer/column {ml}/{layer}/{column} is out of range")
                owner = layer_owners.setdefault((chamber, layer), ml)
                if owner != ml:
                    raise ValueError(f"Chamber {chamber}: layer {layer} belongs to multiple MLs")
                position = (chamber, ml, layer, column)
                tube = tube_ids.setdefault(position, len(tube_ids))
                if tube >= 960:
                    raise ValueError("Firmware supports at most 960 canonical tubes")
                entry = 1 | chamber << 1 | ml << 2 | layer << 6 | column << 14 | tube << 23
                entries.append((index, entry))
                ml_masks[chamber] |= 1 << ml
                layer_masks[chamber] |= 1 << layer
    if not tube_ids:
        raise ValueError("Assign mezzanine slots in Geometry before starting triggerless acquisition")
    return GeometryImage(enabled, chamber1, tuple(sorted(entries)), tuple(tube_ids),
                         tuple(ml_masks), tuple(layer_masks))
