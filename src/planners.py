"""The five planners compared in the paper, built on src/search.py.

| key                 | paper name          | core idea                                                   |
|---------------------|---------------------|-------------------------------------------------------------|
| astar               | A*                  | 8-neigh., h = Manhattan to G (calibrated, see A24)          |
| improved_astar_28   | Improved A* [28]    | 5-direction neigh., f = g + e^P * Manhattan (Liu et al.)    |
| bastar              | BA*                 | bidirectional, Manhattan to the other side's start (A24)    |
| improved_bastar_29  | Improved BA* [29]   | bidirectional, h = mu (Euclid + perpendicular dist to SG)   |
| vns_bastar          | VNS-BA* (proposed)  | 8-11-13 neigh., two-target heuristic x e^rho, prune, smooth |

Every planner returns a dict with the raw grid path, the final path and all metrics.
"""
from __future__ import annotations
import math
import time
import numpy as np

from src.geometry import GridGeometry, euclid, manhattan, switch_distance
from src.neighborhood import neighbors_8, neighbors_81113, neighbors_5dir
from src.search import best_first, bidirectional
from src.postprocess import prune_path, smooth_turns, compress_collinear
from src.metrics import path_length, turn_metrics

DEFAULTS = dict(omega=0.5, eta=0.5, spline_offset=1.0)


# ------------------------------------------------------------------------------ A*
def run_astar(geo, S, G, distance="manhattan"):
    d = (lambda a, b: switch_distance(geo, a, b)) if distance == "switch" else \
        {"euclid": euclid, "manhattan": manhattan}[distance]
    return best_first(geo, S, G, neighbors_8, lambda n: d(n, G))


# ------------------------------------------------------------------------------ Improved A* [28]
def run_improved_astar_28(geo, S, G):
    D0 = manhattan(S, G) or 1.0
    def h(n):
        m = manhattan(n, G)
        return math.exp(m / D0) * m                    # f = g + e^P * h,  P = M(n,G)/M(S,G)
    res = best_first(geo, S, G, neighbors_5dir, h)
    if not res.success:                                # A18: fall back to full 8-neighbourhood
        res2 = best_first(geo, S, G, neighbors_8, h)
        res2.stats["fallback_8"] = True
        res2.expanded += res.expanded
        return res2
    return res


# ------------------------------------------------------------------------------ BA*
def run_bastar(geo, S, G, distance="manhattan"):
    d = (lambda a, b: switch_distance(geo, a, b)) if distance == "switch" else \
        {"euclid": euclid, "manhattan": manhattan}[distance]
    roots = {"S": G, "G": S}                           # each side targets the other's start
    return bidirectional(geo, S, G, lambda gg, n, t: neighbors_8(gg, n),
                         lambda side, n, opp_cur: d(n, roots[side]), meet_rule="pop_closed")


# ------------------------------------------------------------------------------ Improved BA* [29]
def run_improved_bastar_29(geo, S, G):
    A, B, C = G[1] - S[1], S[0] - G[0], G[0] * S[1] - G[1] * S[0]
    norm = math.hypot(A, B) or 1.0
    roots = {"S": G, "G": S}
    def h(side, n, opp_cur):
        tgt = roots[side]
        perp = abs(A * n[0] + B * n[1] + C) / norm
        mu = math.exp(geo.density(n, tgt))             # A13: mu = obstacle-density factor e^rho
        return mu * (euclid(n, tgt) + perp)
    return bidirectional(geo, S, G, lambda gg, n, t: neighbors_8(gg, n), h, meet_rule="pop_in_open")


# ------------------------------------------------------------------------------ VNS-BA*
def run_vns_bastar_search(geo, S, G, omega=0.5, eta=0.5, neighborhood="81113", use_rho=True,
                          meet_rule="pop_closed"):
    roots = {"S": G, "G": S}                           # "opposite start" = own global goal (A15)
    def h(side, n, opp_cur):
        p = omega * switch_distance(geo, n, opp_cur) + eta * switch_distance(geo, n, roots[side])
        rho = geo.density(n, opp_cur) if use_rho else 0.0
        return math.exp(rho) * p                       # Eqs. (5)-(6)
    nfn = neighbors_81113 if neighborhood == "81113" else (lambda gg, n, t: neighbors_8(gg, n))
    return bidirectional(geo, S, G, nfn, h, meet_rule=meet_rule)


# ------------------------------------------------------------------------------ Li et al. [26] (Fig. 2b)
def run_alternating_26(geo, S, G):
    """Bidirectional alternating search of Li et al. [26] as described in Sec. 3.2 of the VNS-BA* article:
    each front uses the current node of the opposite front as its only target (no global guidance, no
    obstacle factor, 8-neighbourhood). Used only for the Fig. 2 comparison (experiment E7)."""
    return bidirectional(geo, S, G, lambda gg, n, t: neighbors_8(gg, n),
                         lambda side, n, opp_cur: switch_distance(geo, n, opp_cur), meet_rule="pop_closed")


# ------------------------------------------------------------------------------ unified runner
EXTRA_ALGORITHMS = {"alternating_26": "Alternating BA* [26]"}

ALGORITHMS = {
    "astar": "A*",
    "improved_astar_28": "Improved A* [28]",
    "bastar": "BA*",
    "improved_bastar_29": "Improved BA* [29]",
    "vns_bastar": "VNS-BA*",
}


def plan(grid_map, algorithm, prune=None, smooth=None, **kw):
    """Run one planner on a GridMap and compute all metrics.

    prune / smooth default to True only for VNS-BA* (as in the paper); pass True explicitly to apply
    the same post-processing to a baseline (ablation / fair comparison)."""
    geo = GridGeometry(grid_map.grid)
    S, G = tuple(grid_map.start), tuple(grid_map.goal)
    is_vns = algorithm == "vns_bastar"
    prune = is_vns if prune is None else prune
    smooth = is_vns if smooth is None else smooth

    t0 = time.perf_counter()
    if algorithm == "astar":
        res = run_astar(geo, S, G, kw.get("distance", "manhattan"))
    elif algorithm == "improved_astar_28":
        res = run_improved_astar_28(geo, S, G)
    elif algorithm == "bastar":
        res = run_bastar(geo, S, G, kw.get("distance", "manhattan"))
    elif algorithm == "improved_bastar_29":
        res = run_improved_bastar_29(geo, S, G)
    elif algorithm == "alternating_26":
        res = run_alternating_26(geo, S, G)
    elif algorithm == "vns_bastar":
        res = run_vns_bastar_search(geo, S, G, kw.get("omega", 0.5), kw.get("eta", 0.5),
                                    kw.get("neighborhood", "81113"), kw.get("use_rho", True),
                                    kw.get("meet_rule", "pop_closed"))
    else:
        raise KeyError(algorithm)
    t_search = time.perf_counter() - t0

    out = dict(algorithm=algorithm, name={**ALGORITHMS, **EXTRA_ALGORITHMS}[algorithm], map=grid_map.name,
               success=res.success, expanded=res.expanded, generated=res.generated,
               prune=prune, smooth=smooth, search_stats=res.stats, closed=res.closed, meet=res.meet)
    if not res.success:
        out.update(time_s=t_search)
        return out

    raw = [tuple(p) for p in res.path]
    t1 = time.perf_counter()
    poly = prune_path(geo, raw) if prune else compress_collinear(raw)
    if smooth:
        final, turn_info = smooth_turns(geo, poly, offset=kw.get("spline_offset", 1.0))
    else:
        final, turn_info = np.asarray(poly, float), []
    t_post = time.perf_counter() - t1
    tm = turn_metrics(poly)
    out.update(
        raw_path=raw, polyline=poly, final_path=final, turn_info=turn_info,
        time_s=t_search + t_post, time_search_s=t_search, time_post_s=t_post,
        nodes=res.generated, turns=tm["turns"], turn_angle_deg=tm["turn_angle_deg"],
        turn_angle_45conv=tm["turn_angle_45conv"],
        length=path_length(final), length_polyline=path_length(poly), length_raw=path_length(raw),
        raw_turns=turn_metrics(raw)["turns"],
    )
    return out


def validate_path(grid_map, result) -> bool:
    """Every segment of the final path must be collision-free (corner touching allowed)."""
    if not result.get("success"):
        return False
    geo = GridGeometry(grid_map.grid)
    P = np.asarray(result["final_path"], float)
    ok_ends = tuple(np.round(P[0]).astype(int)) == tuple(grid_map.start) and \
              tuple(np.round(P[-1]).astype(int)) == tuple(grid_map.goal)
    return ok_ends and all(geo.segment_free(tuple(p), tuple(q)) for p, q in zip(P[:-1], P[1:]))
