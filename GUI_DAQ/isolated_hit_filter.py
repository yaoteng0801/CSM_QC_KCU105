"""Python port of native_capture/isolated_hits.h (IsolatedHitFilter).

Used by the Windows capture path (win_capture.py), where the C++ helper is not
built.  The logic follows the header line by line so both produce byte-identical
.dat files; test_win_capture.py runs the native test cases against this port.

Triggerless event filter: buffer one complete event before classifying hits, so
later hits can rescue earlier ones.  Damaged/incomplete events pass through
verbatim; filtering must not conceal acquisition errors or invent neighbors.
"""

from __future__ import annotations

from typing import List

_MASK40 = (1 << 40) - 1


class _FilterSettings:
    __slots__ = ("enabled", "total", "per_ml", "per_layer", "hit_layers")

    def __init__(self):
        self.enabled = self.total = self.per_ml = self.per_layer = self.hit_layers = 0


def _is_hit(word: int) -> bool:
    # Physical CSMs 0/1, local TDC 0..19, channel 0..23.
    return (word >> 36) < 4 and ((word >> 27) & 31) < 24 and (word & 0xFFFFFFFF) != 0


def _channel_index(word: int) -> int:
    csm, tdc = (word >> 37) & 7, (word >> 32) & 31
    if csm > 1 or tdc >= 20:
        return -1
    return (csm * 20 + tdc) * 32 + ((word >> 27) & 31)


def _append(output: bytearray, word: int) -> None:
    output += (word & _MASK40).to_bytes(5, "big")


class IsolatedHitFilter:
    def __init__(self):
        self.enabled = False
        self.dropped_hits = self.filtered_events = self.preserved_events = self.rejected_events = 0
        self._filters = [_FilterSettings(), _FilterSettings()]
        self._reapply_filters = False
        self._tube_chambers = [-1] * 960
        self._tube_ml = [0] * 960
        self._tube_layer = [0] * 960
        self._layer_ml = [[-1] * 256 for _ in range(2)]
        self._selected_mls = [[False] * 16 for _ in range(2)]
        self._channels = [-1] * 1280
        self._chambers = [-1] * 1280
        self._neighbors: List[List[int]] = [[] for _ in range(960)]
        self._pending: List[int] = []
        self._event_id = 0
        self._hit_count = 0
        self._valid = True

    # -- configuration -----------------------------------------------------

    def load(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="ascii", errors="strict") as handle:
                lines = handle.read().split("\n")
        except (OSError, UnicodeDecodeError):
            return False
        # std::getline semantics: a trailing newline does not add an empty line.
        if lines and lines[-1] == "":
            lines.pop()
        if not lines:
            return False
        header = lines[0].rstrip("\r")
        self._reapply_filters = header == "MINIDAQ_NEIGHBORS_V2"
        if not self._reapply_filters and header != "MINIDAQ_NEIGHBORS_V1":
            return False
        row_index = 1
        if self._reapply_filters:
            for chamber in range(2):
                if row_index >= len(lines):
                    return False
                fields = lines[row_index].split()
                row_index += 1
                if len(fields) != 7 or fields[0] != "FILTER":
                    return False
                try:
                    cid, enabled, total, per_ml, per_layer, hit_layers = map(int, fields[1:])
                except ValueError:
                    return False
                if (cid != chamber or not 0 <= enabled <= 15 or not 0 <= total <= 256
                        or not 0 <= per_ml <= 256 or not 0 <= per_layer <= 256
                        or not 0 <= hit_layers <= 256):
                    return False
                cfg = self._filters[chamber]
                cfg.enabled, cfg.total, cfg.per_ml = enabled, total, per_ml
                cfg.per_layer, cfg.hit_layers = per_layer, hit_layers

        entries = 0
        for line in lines[row_index:]:
            fields = line.split()
            try:
                values = [int(v) for v in fields]
            except ValueError:
                return False
            if len(values) < 3:
                return False
            index, chamber, tube = values[:3]
            position = 3
            ml = layer = 0
            if self._reapply_filters:
                if len(values) < 5:
                    return False
                ml, layer = values[3], values[4]
                position = 5
                if not (0 <= ml < 16 and 0 <= layer < 256):
                    return False
            if len(values) <= position:
                return False
            count = values[position]
            if (not 0 <= index < 1280 or index % 32 >= 24 or not 0 <= chamber <= 1
                    or not 0 <= tube < 960 or not 0 <= count <= 959
                    or self._channels[index] != -1):
                return False
            neighbors = values[position + 1:]
            if len(neighbors) != count or any(n < 0 or n >= 960 or n == tube for n in neighbors):
                return False
            if self._reapply_filters:
                if ((self._tube_chambers[tube] >= 0 and (
                        self._tube_chambers[tube] != chamber or self._tube_ml[tube] != ml
                        or self._tube_layer[tube] != layer))
                        or (self._layer_ml[chamber][layer] >= 0
                            and self._layer_ml[chamber][layer] != ml)):
                    return False
                self._tube_chambers[tube] = chamber
                self._tube_ml[tube] = ml
                self._tube_layer[tube] = layer
                self._layer_ml[chamber][layer] = ml
                self._selected_mls[chamber][ml] = True
            self._channels[index] = tube
            self._chambers[index] = chamber
            self._neighbors[tube] = neighbors
            entries += 1
        self.enabled = entries > 0
        return self.enabled

    # -- streaming -----------------------------------------------------------

    def packet_loss(self) -> None:
        if self._pending:
            self._valid = False

    def feed(self, five_bytes: bytes, output: bytearray) -> None:
        if not self.enabled:
            output += five_bytes
            return
        word = int.from_bytes(five_bytes, "big")
        tag = word >> 36
        if tag == 0xA:
            self.finish(output)
            self._valid = True
            self._event_id = (word >> 16) & 0xFFFFF
            self._hit_count = 0
            self._pending.append(word)
            return
        if not self._pending:
            _append(output, word)
            return
        self._pending.append(word)
        if tag == 0xC:
            if ((word >> 16) & 0xFFFFF) != self._event_id or (word & 1023) != self._hit_count:
                self._valid = False
            if self._valid:
                self._filter(output)
            else:
                self.finish(output)
            return
        if _is_hit(word):
            self._hit_count += 1
            index = _channel_index(word)
            if index < 0 or (self._channels[index] >= 0
                             and self._chambers[index] != (self._event_id >> 19)):
                self._valid = False
        elif not (tag == 0xE and ((word >> 30) & 63) == 0):
            # Abort, decoder error, noise data, or unexpected control word.
            self._valid = False
        if len(self._pending) >= 8192:
            self.finish(output)  # bounded on missing trailer

    def finish(self, output: bytearray) -> None:
        if not self._pending:
            return
        for word in self._pending:
            _append(output, word)
        self._pending.clear()
        self.preserved_events += 1

    # -- internals -------------------------------------------------------------

    def _passes_filters(self, kept: List[bool]) -> bool:
        if not self._reapply_filters:
            return True  # legacy V1 isolation-only snapshot
        chamber = self._event_id >> 19
        cfg = self._filters[chamber]
        total = 0
        per_ml = [0] * 16
        hit_layers = [0] * 16
        per_layer = [0] * 256
        for tube in range(960):
            if not kept[tube] or self._tube_chambers[tube] != chamber:
                continue
            total += 1
            per_ml[self._tube_ml[tube]] += 1
            layer = self._tube_layer[tube]
            if per_layer[layer] == 0:
                hit_layers[self._tube_ml[tube]] += 1
            per_layer[layer] += 1
        # Match tube_event_filter.sv: distinct mapped tubes, all enabled cuts
        # ANDed, and even disabled cuts require a nonempty mapped-tube event.
        if total == 0 or ((cfg.enabled & 1) and total < cfg.total):
            return False
        for ml in range(16):
            if not self._selected_mls[chamber][ml]:
                continue
            if (cfg.enabled & 2) and per_ml[ml] < cfg.per_ml:
                return False
            if (cfg.enabled & 8) and hit_layers[ml] < cfg.hit_layers:
                return False
        if cfg.enabled & 4:
            for layer in range(256):
                if self._layer_ml[chamber][layer] >= 0 and per_layer[layer] < cfg.per_layer:
                    return False
        return True

    def _filter(self, output: bytearray) -> None:
        occupied = [False] * 960
        for word in self._pending:
            if not _is_hit(word):
                continue
            tube = self._channels[_channel_index(word)]
            if tube >= 0:
                occupied[tube] = True
        kept = [False] * 960
        for tube in range(960):
            if occupied[tube]:
                kept[tube] = any(occupied[n] for n in self._neighbors[tube])
        removed = 0
        for word in self._pending:
            if not _is_hit(word):
                continue
            tube = self._channels[_channel_index(word)]
            if tube >= 0 and not kept[tube]:
                removed += 1
        self.dropped_hits += removed
        self.filtered_events += 1
        if not self._passes_filters(kept):
            self.rejected_events += 1
            self._pending.clear()
            return
        for word in self._pending[:-1]:
            if _is_hit(word):
                tube = self._channels[_channel_index(word)]
                if tube >= 0 and not kept[tube]:
                    continue
            _append(output, word)
        # Preserve event ID, trigger count and all framing, including empty events.
        _append(output, (self._pending[-1] & ~1023) | ((self._hit_count - removed) & _MASK40))
        self._pending.clear()
