"""Logarithmic Y axes labeled only at 1 and 5 times each power of ten."""

import math
import pyqtgraph as pg


class SparseLogAxisItem(pg.AxisItem):
    def logTickValues(self, minVal, maxVal, size, stdTicks):
        if not (math.isfinite(minVal) and math.isfinite(maxVal)):
            return []
        low, high = sorted((minVal, maxVal))
        decades, halves = [], []
        for exponent in range(math.floor(low), math.ceil(high) + 1):
            if low <= exponent <= high:
                decades.append(float(exponent))
            halfway = exponent + math.log10(5)
            if low <= halfway <= high:
                halves.append(halfway)
        # Give decades priority; pyqtgraph can suppress the 5x labels when the
        # plot is too short to fit both levels legibly. Linear ticks are unchanged.
        return [(1.0, decades), (None, halves)]
