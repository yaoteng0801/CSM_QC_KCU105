# Event.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from Signal import Hit


# ---------------- chamber container ----------------

@dataclass(frozen=True)
class ChamberBlock:
    """
    One chamber's payload inside an Event.
    """
    chamber_id: int
    hits: Tuple[Hit, ...]  # immutable hits for this chamber

    @property
    def n_hits(self) -> int:
        return len(self.hits)


# Alias: chamber_id -> ChamberBlock
Chambers = Dict[int, ChamberBlock]


# ---------------- event container ----------------

@dataclass(frozen=True)
class Event:
    event_id20: int
    rd_bank_sel: int
    trigger_count: int
    hit_count_expected: int
    event_id12: int = 0
    chamber_id: int = 0
    chamber_event_id: int = 0
    trigger_ledge: Optional[int] = None
    trigger_overflow: int = 0
    tdc_header_count: int = 0
    tdc_trailer_count: int = 0
    header_count_error: int = 0
    trailer_count_error: int = 0

    # chamber_id -> ChamberBlock
    chambers: Chambers = field(default_factory=dict)
