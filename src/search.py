"""Generic unidirectional and bidirectional best-first (A*-family) search engines.

The algorithm-specific parts (heuristic, neighbourhood, meeting rule) are injected, so the
traditional A*, Improved A* [28], BA*, Improved BA* [29] and VNS-BA* share one tested core.
Counters returned:
    expanded  = nodes moved to a closed list  (reported as "Number of Nodes")
    generated = distinct nodes ever inserted in an open list
"""
from __future__ import annotations
import heapq
import itertools
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    path: list                      # list of cells (c, r) from start to goal, [] if failed
    expanded: int
    generated: int
    closed: dict = field(default_factory=dict)       # side -> set of closed cells (for plots)
    meet: tuple | None = None
    stats: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return bool(self.path)


def _chain(parent, node):
    out = []
    while node is not None:
        out.append(node)
        node = parent[node]
    return out


# ---------------------------------------------------------------------------- unidirectional
def _key(f, g, h, tie, mode):
    if mode == "fifo":
        return (f, tie)
    if mode == "lifo":
        return (f, -tie)
    if mode == "low_h":
        return (f, h, tie)
    if mode == "high_g":
        return (f, -g, tie)
    raise ValueError(mode)


def best_first(geo, start, goal, neighbors_fn, h_fn, max_expansions=10**7, tie_break="fifo"):
    """A* skeleton of Sec. 2 (steps 1-7): pop min f, stop when the goal is closed."""
    tie = itertools.count()
    g = {start: 0.0}
    parent = {start: None}
    h0 = h_fn(start)
    open_heap = [(_key(h0, 0.0, h0, next(tie), tie_break), start)]
    closed = set()
    while open_heap and len(closed) < max_expansions:
        _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue                                   # stale heap entry
        closed.add(cur)
        if cur == goal:
            return SearchResult(_chain(parent, goal)[::-1], len(closed), len(g), {"S": closed})
        for nb, cost in neighbors_fn(geo, cur, goal):
            if nb in closed:
                continue
            ng = g[cur] + cost
            if ng < g.get(nb, float("inf")):           # step 6: keep the better parent
                g[nb] = ng
                parent[nb] = cur
                hv = h_fn(nb)
                heapq.heappush(open_heap, (_key(ng + hv, ng, hv, next(tie), tie_break), nb))
    return SearchResult([], len(closed), len(g), {"S": closed})


# ---------------------------------------------------------------------------- bidirectional
def bidirectional(geo, start, goal, neighbors_fn, h_fn, meet_rule="pop_closed",
                  max_expansions=10**7, tie_break="fifo"):
    """Bidirectional best-first search with alternating expansion (assumption A3).

    neighbors_fn(geo, node, target) -> list[(nb, cost)] or (list, mode)
    h_fn(side, node, opp_current)   -> heuristic value; side is "S" (forward) or "G" (backward)
    meet_rule:
      "pop_closed"  - Fig. 4 of the paper (default): the node just moved from one side's open list to
                      its closed list is already in the other side's closed list.  Calibrated in
                      Phase 3: reproduces the published BA* nodes/length/turns on Maps A-D.
      "open_closed" - stricter variant: also stop as soon as a generated node is in the other
                      side's closed list (kept for sensitivity analysis)
      "pop_in_open" - baseline [29] (Appendix A): the popped node is in the other side's open set
    """
    tie = itertools.count()
    roots = {"S": start, "G": goal}
    other = {"S": "G", "G": "S"}
    g = {"S": {start: 0.0}, "G": {goal: 0.0}}
    parent = {"S": {start: None}, "G": {goal: None}}
    closed = {"S": set(), "G": set()}
    current = {"S": start, "G": goal}             # each front's most recently expanded node
    heaps = {}
    for s in "SG":
        h0 = h_fn(s, roots[s], roots[other[s]])
        heaps[s] = [(_key(h0, 0.0, h0, next(tie), tie_break), roots[s])]
    modes = {8: 0, 11: 0, 13: 0}

    def finish(meet):
        fwd = _chain(parent["S"], meet)[::-1]
        bwd = _chain(parent["G"], meet)[1:]
        path = fwd + bwd
        return SearchResult(path, len(closed["S"]) + len(closed["G"]),
                            len(g["S"]) + len(g["G"]), closed, meet, {"modes": modes})

    if start == goal:
        return finish(start)
    while heaps["S"] and heaps["G"]:
        if len(closed["S"]) + len(closed["G"]) >= max_expansions:
            break
        for side in ("S", "G"):
            opp = other[side]
            heap = heaps[side]
            cur = None
            while heap:
                _, cand = heapq.heappop(heap)
                if cand not in closed[side]:
                    cur = cand
                    break
            if cur is None:
                return SearchResult([], len(closed["S"]) + len(closed["G"]),
                                    len(g["S"]) + len(g["G"]), closed, None, {"modes": modes})
            closed[side].add(cur)
            current[side] = cur
            if meet_rule == "pop_in_open" and cur in g[opp]:
                return finish(cur)
            if meet_rule in ("pop_closed", "open_closed") and cur in closed[opp]:
                return finish(cur)
            res = neighbors_fn(geo, cur, current[opp])
            if isinstance(res, tuple):
                res, mode = res
                modes[mode] = modes.get(mode, 0) + 1
            for nb, cost in res:
                if nb in closed[side]:
                    continue
                ng = g[side][cur] + cost
                if ng < g[side].get(nb, float("inf")):
                    g[side][nb] = ng
                    parent[side][nb] = cur
                    if meet_rule == "open_closed" and nb in closed[opp]:
                        return finish(nb)
                    hv = h_fn(side, nb, current[opp])
                    heapq.heappush(heap, (_key(ng + hv, ng, hv, next(tie), tie_break), nb))
    return SearchResult([], len(closed["S"]) + len(closed["G"]),
                        len(g["S"]) + len(g["G"]), closed, None, {"modes": modes})
