"""Ground-truth optimal 8-connected planner (Dijkstra). Used ONLY to validate reconstructed maps."""
import heapq, math
import numpy as np


def dijkstra_8(grid: np.ndarray, start, goal, diagonal_rule: str = "free"):
    n = grid.shape[0]
    dist, parent = {start: 0.0}, {start: None}
    pq = [(0.0, start)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal:
            path = [cur]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            return d, path[::-1]
        if d > dist[cur]:
            continue
        c, r = cur
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = c + dc, r + dr
                if not (0 <= nc < n and 0 <= nr < n) or grid[nr, nc]:
                    continue
                if dc and dr:
                    side1, side2 = grid[r, nc], grid[nr, c]
                    if diagonal_rule == "strict" and (side1 or side2):
                        continue
                    if diagonal_rule == "no_squeeze" and (side1 and side2):
                        continue
                nd = d + math.hypot(dc, dr)
                if nd < dist.get((nc, nr), float("inf")):
                    dist[(nc, nr)] = nd; parent[(nc, nr)] = cur
                    heapq.heappush(pq, (nd, (nc, nr)))
    return float("inf"), []
