"""Snapshot physical tube neighbors for the native DAT writer."""
import math

from triggerless_filters import build_geometry_image


def neighbor_map_text(geometries, filters=None):
    """All six immediate neighbors, within one chamber/ML; aliases share a tube.

    Use measured centers, including imported GEO staggering, not column parity.
    The file is saved beside the DAT so its filtering geometry is reproducible.
    """
    geos = list(geometries)
    image = build_geometry_image(geos)
    by_chamber = {int(g.chamber_id): g for g in geos}
    centers = []
    for chamber, ml, layer, column in image.positions:
        geo = by_chamber[chamber]
        x, y = geo.get_hit_xy(layer, column)
        pitch, spacing = float(geo.column_distance), float(geo.layer_distance)
        if not all(math.isfinite(v) for v in (x, y, pitch, spacing)) or min(pitch, spacing) <= 0:
            raise ValueError("Isolated-hit filtering requires finite tube centers and positive spacing")
        centers.append((x, y, pitch, spacing))
    neighbors = [[] for _ in centers]
    for i, a in enumerate(image.positions):
        x, y, pitch, spacing = centers[i]
        for j in range(i):
            b = image.positions[j]
            if a[:2] != b[:2]:
                continue
            dl = abs(a[2] - b[2])
            dx, dy = abs(x - centers[j][0]), abs(y - centers[j][1])
            adjacent = (
                dl == 0 and abs(dx - pitch) < .05 * pitch and dy < .05 * spacing
            ) or (
                dl == 1 and abs(dx - pitch / 2) < .05 * pitch
                and abs(dy - spacing) < .05 * spacing
            )
            if adjacent:
                neighbors[i].append(j)
                neighbors[j].append(i)
    lines = ["MINIDAQ_NEIGHBORS_V2" if filters is not None else "MINIDAQ_NEIGHBORS_V1"]
    if filters is not None:
        if len(filters) != 2:
            raise ValueError("Expected tube-filter settings for both chambers")
        for chamber, cfg in enumerate(filters):
            lines.append(" ".join(map(str, ("FILTER", chamber, cfg.enabled, cfg.min_tubes,
                cfg.min_tubes_per_ml, cfg.min_tubes_per_layer, cfg.min_layers_per_ml))))
    for index, entry in image.entries:
        if entry & 1:
            tube = (entry >> 23) & 1023
            ns = neighbors[tube]
            fields = (index, (entry >> 1) & 1, tube)
            if filters is not None:
                fields += ((entry >> 2) & 15, (entry >> 6) & 255)
            lines.append(" ".join(map(str, (*fields, len(ns), *ns))))
    return "\n".join(lines) + "\n"
