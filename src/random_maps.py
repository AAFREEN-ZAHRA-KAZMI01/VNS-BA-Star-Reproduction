"""Seeded random occupancy maps for multi-run experiments (addition to the paper)."""
import numpy as np
from src.grid_map import GridMap
from src.reference_planner import dijkstra_8


def random_map(n: int, seed: int, density: float = 0.20, max_attempts: int = 50) -> GridMap:
    start, goal = (0, 0), (n - 1, n - 1)
    for attempt in range(max_attempts):
        s = seed + 1000 * attempt
        rng = np.random.default_rng(s)
        grid = (rng.random((n, n)) < density).astype(np.uint8)
        for (c, r) in (start, goal):
            grid[r, c] = 0
        length, _ = dijkstra_8(grid, start, goal, "free")
        if np.isfinite(length):
            return GridMap(f"rand_{n}_s{seed:02d}", grid, start, goal,
                           source="generated: numpy default_rng, i.i.d. obstacles",
                           meta=dict(seed=seed, effective_seed=s, attempt=attempt,
                                     target_density=density, optimal_length=round(length, 4)))
    raise RuntimeError(f"no solvable map for n={n}, seed={seed}")
