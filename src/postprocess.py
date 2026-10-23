"""Path post-processing of VNS-BA*: polyline pruning (Sec. 3.3) and local cubic-spline
smoothing at the turning points (Sec. 3.4).  The cubic spline is solved here directly
(tridiagonal system) instead of calling a library, so the method is fully re-implemented."""
from __future__ import annotations
import math
import numpy as np


# ------------------------------------------------------------------------------ helpers
def compress_collinear(path):
    """Remove intermediate nodes that lie on a straight run (same heading)."""
    pts = [tuple(p) for p in path]
    if len(pts) <= 2:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
        if abs(cross) > 1e-9 or dot < 0:
            out.append(b)
    out.append(pts[-1])
    return out


# ------------------------------------------------------------------------------ Sec. 3.3
def prune_path(geo, path):
    """Greedy line-of-sight pruning exactly as described in Sec. 3.3:
    keep the front endpoint, extend the back endpoint along the path until the segment crosses an
    obstacle, then keep the previous node as the new front endpoint."""
    pts = [tuple(p) for p in path]
    if len(pts) <= 2:
        return pts
    out = [pts[0]]
    anchor = pts[0]
    i = 1
    while i < len(pts):
        if geo.line_of_sight(anchor, pts[i]):
            i += 1
            continue
        prev = pts[i - 1]
        if prev == anchor:                      # cannot happen for a valid path; guard anyway
            prev = pts[i]
            i += 1
        out.append(prev)
        anchor = prev
    out.append(pts[-1])
    return compress_collinear(out)


def prune_huang(geo, path):
    """Comparison method of Sec. 3.3 (Huang et al. [27], as described in the VNS-BA* article):
    (1) remove collinear redundant nodes, then (2) remove unnecessary turning points: a turning point is
    dropped when the segment from the last kept vertex to the next turning point is collision-free.
    Unlike prune_path, only the turning points of the grid path are candidates (assumption A28)."""
    pts = compress_collinear(path)
    if len(pts) <= 2:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        if not geo.line_of_sight(out[-1], pts[i + 1]):
            out.append(pts[i])
    out.append(pts[-1])
    return compress_collinear(out)


# ------------------------------------------------------------------------------ cubic spline
def natural_cubic_spline(t, y):
    """Coefficients (a, b, c, d) per interval for the natural cubic spline through (t_i, y_i):
        S_i(x) = a_i + b_i (x - t_i) + c_i (x - t_i)^2 + d_i (x - t_i)^3
    Conditions: interpolation, C1 and C2 continuity at interior knots (Eq. 11 of the paper),
    natural boundary S''(t_0) = S''(t_n) = 0 (assumption A6).  Solved with the Thomas algorithm."""
    t = np.asarray(t, float); y = np.asarray(y, float)
    n = len(t) - 1
    h = np.diff(t)
    M = np.zeros(n + 1)                          # second derivatives at knots
    if n >= 2:
        lower = h[1:-1].copy(); diag = 2 * (h[:-1] + h[1:]); upper = h[1:-1].copy()
        rhs = 6 * ((y[2:] - y[1:-1]) / h[1:] - (y[1:-1] - y[:-2]) / h[:-1])
        m = n - 1
        cp = np.zeros(m); dp = np.zeros(m)
        cp[0] = upper[0] / diag[0] if m > 1 else 0.0
        dp[0] = rhs[0] / diag[0]
        for i in range(1, m):
            den = diag[i] - lower[i - 1] * cp[i - 1]
            cp[i] = upper[i] / den if i < m - 1 else 0.0
            dp[i] = (rhs[i] - lower[i - 1] * dp[i - 1]) / den
        sol = np.zeros(m)
        sol[-1] = dp[-1]
        for i in range(m - 2, -1, -1):
            sol[i] = dp[i] - cp[i] * sol[i + 1]
        M[1:-1] = sol
    a = y[:-1]
    b = (y[1:] - y[:-1]) / h - h * (2 * M[:-1] + M[1:]) / 6
    c = M[:-1] / 2
    d = (M[1:] - M[:-1]) / (6 * h)
    return a, b, c, d


def eval_spline(t, coeffs, x):
    a, b, c, d = coeffs
    x = np.atleast_1d(np.asarray(x, float))
    idx = np.clip(np.searchsorted(t, x, side="right") - 1, 0, len(a) - 1)
    dx = x - np.asarray(t)[idx]
    return a[idx] + b[idx] * dx + c[idx] * dx ** 2 + d[idx] * dx ** 3


def spline_through(points, samples_per_segment=10):
    """Parametric (x(s), y(s)) natural cubic spline with chord-length parameter s (assumption A5)."""
    P = np.asarray(points, float)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    cx, cy = natural_cubic_spline(s, P[:, 0]), natural_cubic_spline(s, P[:, 1])
    xs = np.linspace(0, s[-1], samples_per_segment * (len(P) - 1) + 1)
    return np.column_stack([eval_spline(s, cx, xs), eval_spline(s, cy, xs)])


# ------------------------------------------------------------------------------ Sec. 3.4
def smooth_turns(geo, polyline, offset=1.0, outer_factor=2.0, samples=10, retries=3):
    """Replace each turning vertex V by a cubic spline through P1, P2 (before V) and P3, P4 (after V).
    V itself is not a control point (paper).  P2/P3 lie `offset` cells from V and P1/P4
    `outer_factor*offset` cells (assumption A7), clipped to 45 % of the adjacent segment so that
    neighbouring turns never overlap.  If the curve would cross an obstacle the offset is halved
    (up to `retries` times); otherwise the corner is kept (assumption A22).
    Returns (smoothed points as (k,2) array, list of per-turn info)."""
    pts = [np.asarray(p, float) for p in polyline]
    if len(pts) < 3:
        return np.asarray(pts), []
    out = [pts[0]]
    info = []
    for i in range(1, len(pts) - 1):
        A, V, B = pts[i - 1], pts[i], pts[i + 1]
        lin, lout = np.linalg.norm(V - A), np.linalg.norm(B - V)
        uin, uout = (V - A) / lin, (B - V) / lout
        off = offset
        done = False
        for _ in range(retries + 1):
            o_in = min(off, 0.45 * lin / outer_factor)
            o_out = min(off, 0.45 * lout / outer_factor)
            P1, P2 = V - uin * outer_factor * o_in, V - uin * o_in
            P3, P4 = V + uout * o_out, V + uout * outer_factor * o_out
            curve = spline_through([P1, P2, P3, P4], samples)
            if all(geo.segment_free(tuple(p), tuple(q)) for p, q in zip(curve[:-1], curve[1:])):
                out.extend(list(curve))
                info.append(dict(vertex=tuple(V), offset=o_in, smoothed=True))
                done = True
                break
            off /= 2
        if not done:
            out.append(V)
            info.append(dict(vertex=tuple(V), offset=0.0, smoothed=False))
    out.append(pts[-1])
    arr = np.asarray(out)
    keep = np.concatenate([[True], np.hypot(*np.diff(arr, axis=0).T) > 1e-9])
    return arr[keep], info
