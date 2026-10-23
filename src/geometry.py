"""Grid geometry shared by all planners.

* line-of-sight between cell centres (used by the Euclid/Manhattan switch of Sec. 2
  and by the polyline pruning of Sec. 3.3),
* obstacle density of the rectangle spanned by two cells (rho of Sec. 3.2), via an
  integral image so every query is O(1).

Cell (c, r) is the unit square centred at (c, r).  A segment "crosses" a cell when it runs
through that cell's interior for a positive length; merely touching a corner does not count
(Sec. 2: grid size includes the safety margin, so touching an obstacle corner is collision-free).
"""
from __future__ import annotations
import math
import numpy as np


class GridGeometry:
    def __init__(self, grid: np.ndarray):
        self.grid = np.asarray(grid, dtype=np.uint8)
        self.n = self.grid.shape[0]
        ii = np.zeros((self.n + 1, self.n + 1), dtype=np.int64)
        ii[1:, 1:] = self.grid.cumsum(0).cumsum(1)
        self._ii = ii
        self._los_cache: dict = {}

    # ------------------------------------------------------------------ cells
    def inside(self, c: int, r: int) -> bool:
        return 0 <= c < self.n and 0 <= r < self.n

    def free(self, c: int, r: int) -> bool:
        return 0 <= c < self.n and 0 <= r < self.n and self.grid[r, c] == 0

    # ------------------------------------------------------------------ segments
    @staticmethod
    def segment_cells(a, b):
        """Cells whose interior the straight segment a->b passes through (ordered from a to b)."""
        x0, y0 = a
        x1, y1 = b
        dx, dy = x1 - x0, y1 - y0
        ts = [0.0, 1.0]
        if dx:
            lo, hi = (x0, x1) if x0 < x1 else (x1, x0)
            ts += [(k + 0.5 - x0) / dx for k in range(int(math.floor(lo)), int(math.ceil(hi)))
                   if lo < k + 0.5 < hi]
        if dy:
            lo, hi = (y0, y1) if y0 < y1 else (y1, y0)
            ts += [(k + 0.5 - y0) / dy for k in range(int(math.floor(lo)), int(math.ceil(hi)))
                   if lo < k + 0.5 < hi]
        ts.sort()
        cells = []
        for t0, t1 in zip(ts, ts[1:]):
            if t1 - t0 < 1e-12:            # zero-length piece = touching a corner
                continue
            tm = 0.5 * (t0 + t1)
            cell = (int(math.floor(x0 + dx * tm + 0.5)), int(math.floor(y0 + dy * tm + 0.5)))
            if not cells or cells[-1] != cell:
                cells.append(cell)
        return cells

    def line_of_sight(self, a, b) -> bool:
        """True if the segment between the centres of cells a and b crosses no obstacle cell."""
        key = (a, b) if a <= b else (b, a)
        hit = self._los_cache.get(key)
        if hit is None:
            hit = all(self.free(c, r) for c, r in self.segment_cells(a, b))
            self._los_cache[key] = hit
        return hit

    def segment_free(self, p, q) -> bool:
        """Same test for arbitrary real-valued points (used to validate smoothed curves)."""
        return all(self.free(c, r) for c, r in self.segment_cells(p, q))

    # ------------------------------------------------------------------ density
    def density(self, a, b) -> float:
        """Obstacle fraction of the axis-aligned rectangle with corner cells a and b (inclusive)."""
        c0, c1 = sorted((a[0], b[0]))
        r0, r1 = sorted((a[1], b[1]))
        ii = self._ii
        s = ii[r1 + 1, c1 + 1] - ii[r0, c1 + 1] - ii[r1 + 1, c0] + ii[r0, c0]
        return s / ((c1 - c0 + 1) * (r1 - r0 + 1))


# ---------------------------------------------------------------------- distances
def euclid(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def manhattan(a, b) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def chebyshev(a, b) -> float:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def switch_distance(geo: GridGeometry, a, b) -> float:
    """Sec. 2 of the paper: Euclidean if the line a-b is obstacle-free, otherwise Manhattan."""
    return euclid(a, b) if geo.line_of_sight(a, b) else manhattan(a, b)
