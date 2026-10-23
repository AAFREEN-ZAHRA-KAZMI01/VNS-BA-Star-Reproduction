"""Node-expansion neighbourhoods.

Numbering of the 8-neighbourhood follows Fig. 1 of the paper (1 = top-left, clockwise):
    1 2 3
    8 . 4
    7 6 5
"""
from __future__ import annotations
import math

N8 = [(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)]
SQRT2 = math.sqrt(2.0)


def _sign(v):
    return (v > 0) - (v < 0)


def extension_offsets(dx: int, dy: int):
    """Extra cells of the 11/13-neighbourhood for the vector (dx, dy) = target - current.

    * vector on an axis      -> 3 cells of the second ring on that side   (11-neighbourhood, Fig. 1c)
    * vector inside quadrant -> 5 cells forming the L of that corner      (13-neighbourhood, Fig. 1b)
    """
    sx, sy = _sign(dx), _sign(dy)
    if sx == 0 and sy == 0:
        return []
    if sx == 0:
        return [(-1, 2 * sy), (0, 2 * sy), (1, 2 * sy)]
    if sy == 0:
        return [(2 * sx, -1), (2 * sx, 0), (2 * sx, 1)]
    return [(0, 2 * sy), (sx, 2 * sy), (2 * sx, 2 * sy), (2 * sx, sy), (2 * sx, 0)]


def neighbors_8(geo, node, target=None):
    """Classic 8-neighbourhood; diagonal moves allowed past obstacle corners (assumption A16)."""
    c, r = node
    out = []
    for dc, dr in N8:
        if geo.free(c + dc, r + dr):
            out.append(((c + dc, r + dr), SQRT2 if dc and dr else 1.0))
    return out


def neighbors_81113(geo, node, target):
    """Adaptive 8-11-13 variable neighbourhood (Sec. 3.1).

    Returns (neighbours, mode) where mode is 8, 11 or 13 (for statistics).
    """
    c, r = node
    out, blocked = [], False
    for dc, dr in N8:
        if geo.free(c + dc, r + dr):
            out.append(((c + dc, r + dr), SQRT2 if dc and dr else 1.0))
        else:
            blocked = True                      # obstacle or map border in the 8-neighbourhood
    if blocked or target is None:
        return out, 8
    ext = extension_offsets(target[0] - c, target[1] - r)
    for dc, dr in ext:                          # A8: skip extension cells that are obstacles
        if geo.free(c + dc, r + dr):
            out.append(((c + dc, r + dr), math.hypot(dc, dr)))   # A2: Euclidean move cost
    return out, 8 + len(ext)


def neighbors_5dir(geo, node, target):
    """Baseline [28] (Liu et al. 2023): keep the 5 of 8 directions closest to the target direction,
    discarding the 3 directions pointing away from it."""
    c, r = node
    if target is None or tuple(target) == tuple(node):
        return neighbors_8(geo, node)
    theta = math.atan2(target[1] - r, target[0] - c)
    def ang(d):
        a = math.atan2(d[1], d[0]) - theta
        return abs((a + math.pi) % (2 * math.pi) - math.pi)
    dirs = sorted(N8, key=ang)[:5]
    out = []
    for dc, dr in dirs:
        if geo.free(c + dc, r + dr):
            out.append(((c + dc, r + dr), SQRT2 if dc and dr else 1.0))
    return out
