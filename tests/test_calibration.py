"""Regression test: baselines on the reconstructed maps reproduce published Tables 2-5."""
import pytest
from pathlib import Path
from src.grid_map import GridMap
from src.planners import plan

MAPS = Path(__file__).resolve().parents[1] / "maps"
PUBLISHED = {  # (algorithm, map): (length, turns)
    ("astar", "map_A_20"): (28.627, 7), ("astar", "map_B_40"): (61.598, 9),
    ("astar", "map_C_60"): (59.385, 7), ("astar", "map_D_80"): (103.297, 25),
    ("bastar", "map_A_20"): (28.627, 10), ("bastar", "map_B_40"): (61.598, 12),
    ("bastar", "map_C_60"): (59.3848, 8), ("bastar", "map_D_80"): (102.125, 24),
    ("improved_astar_28", "map_B_40"): (64.083, 11), ("improved_astar_28", "map_D_80"): (104.125, 27),
    ("improved_bastar_29", "map_A_20"): (29.213, 14), ("improved_bastar_29", "map_B_40"): (61.598, 18),
    ("improved_bastar_29", "map_D_80"): (106.225, 30),
}


@pytest.mark.skipif(not (MAPS / "map_A_20.txt").exists(), reason="maps not generated (run Phase 2)")
@pytest.mark.parametrize("key", list(PUBLISHED))
def test_published_baseline_reproduced(key):
    alg, name = key
    r = plan(GridMap.load(MAPS, name), alg)
    length, turns = PUBLISHED[key]
    assert r["length"] == pytest.approx(length, abs=2e-3)
    assert r["turns"] == turns
