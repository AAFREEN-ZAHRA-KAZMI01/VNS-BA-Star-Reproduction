"""Unit tests for the VNS-BA* re-implementation (run: python -m pytest -q tests)."""
import math
import numpy as np
import pytest

from src.geometry import GridGeometry, euclid
from src.neighborhood import extension_offsets, neighbors_81113, neighbors_8, neighbors_5dir
from src.search import best_first
from src.postprocess import natural_cubic_spline, eval_spline, prune_path, prune_huang, smooth_turns, compress_collinear
from src.metrics import turn_metrics, path_length
from src.planners import plan, ALGORITHMS, validate_path
from src.reference_planner import dijkstra_8
from src.random_maps import random_map
from src.grid_map import GridMap


def empty(n=9):
    return GridGeometry(np.zeros((n, n), dtype=np.uint8))


# ----------------------------------------------------------------------------- Sec. 3.1, Fig. 1
def test_extension_axis_gives_11_neighbourhood():
    assert sorted(extension_offsets(0, 5)) == [(-1, 2), (0, 2), (1, 2)]      # Fig. 1c (up)
    assert sorted(extension_offsets(-3, 0)) == [(-2, -1), (-2, 0), (-2, 1)]  # left


def test_extension_quadrant_gives_13_neighbourhood():
    assert sorted(extension_offsets(4, 7)) == sorted([(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)])  # Fig. 1b
    assert len(extension_offsets(-1, -9)) == 5


def test_81113_falls_back_to_8_when_neighbour_blocked():
    geo = empty()
    geo.grid[4, 3] = 1                                    # left neighbour of (4,4) is an obstacle (Fig. 1a)
    nbs, mode = neighbors_81113(geo, (4, 4), (8, 8))
    assert mode == 8 and len(nbs) == 7


def test_81113_expands_13_in_free_space():
    nbs, mode = neighbors_81113(empty(), (4, 4), (8, 8))
    assert mode == 13 and len(nbs) == 13
    costs = {nb: c for nb, c in nbs}
    assert math.isclose(costs[(6, 5)], math.sqrt(5)) and math.isclose(costs[(6, 6)], 2 * math.sqrt(2))


def test_5dir_keeps_directions_towards_target():
    nbs = {nb for nb, _ in neighbors_5dir(empty(), (4, 4), (8, 4))}       # target to the right
    assert nbs == {(5, 4), (5, 5), (5, 3), (4, 5), (4, 3)}


# ----------------------------------------------------------------------------- geometry
def test_segment_cells_corner_touch_is_not_crossing():
    assert GridGeometry.segment_cells((0, 0), (2, 2)) == [(0, 0), (1, 1), (2, 2)]
    geo = empty(5)
    geo.grid[0, 1] = 1                                    # cell (1,0) touches the diagonal only at a corner
    assert geo.line_of_sight((0, 0), (2, 2))


def test_line_of_sight_blocked():
    geo = empty(7)
    geo.grid[3, 3] = 1
    assert not geo.line_of_sight((0, 3), (6, 3))
    assert geo.line_of_sight((0, 0), (6, 1))


def test_density_matches_brute_force():
    rng = np.random.default_rng(0)
    grid = (rng.random((15, 15)) < 0.3).astype(np.uint8)
    geo = GridGeometry(grid)
    for _ in range(200):
        a = tuple(rng.integers(0, 15, 2)); b = tuple(rng.integers(0, 15, 2))
        c0, c1 = sorted((a[0], b[0])); r0, r1 = sorted((a[1], b[1]))
        assert math.isclose(geo.density(a, b), grid[r0:r1 + 1, c0:c1 + 1].mean())


# ----------------------------------------------------------------------------- search
@pytest.mark.parametrize("seed", range(10))
def test_astar_with_admissible_heuristic_is_optimal(seed):
    m = random_map(30, seed)
    geo = GridGeometry(m.grid)
    res = best_first(geo, m.start, m.goal, neighbors_8, lambda n: euclid(n, m.goal))
    opt, _ = dijkstra_8(m.grid, m.start, m.goal, "free")
    assert math.isclose(path_length(res.path), opt, rel_tol=1e-9)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("alg", list(ALGORITHMS))
def test_every_planner_returns_collision_free_path(seed, alg):
    m = random_map(25 if seed % 2 else 40, seed)
    r = plan(m, alg)
    assert r["success"] and validate_path(m, r)


# ----------------------------------------------------------------------------- Sec. 3.4 spline
def test_natural_spline_conditions():
    t = np.array([0.0, 1.0, 2.5, 3.0]); y = np.array([0.0, 2.0, 1.0, 3.0])
    a, b, c, d = natural_cubic_spline(t, y)
    assert np.allclose(eval_spline(t, (a, b, c, d), t), y)                      # interpolation
    h = np.diff(t)
    left_val = a[:-1] + b[:-1] * h[:-1] + c[:-1] * h[:-1] ** 2 + d[:-1] * h[:-1] ** 3
    left_d1 = b[:-1] + 2 * c[:-1] * h[:-1] + 3 * d[:-1] * h[:-1] ** 2
    left_d2 = 2 * c[:-1] + 6 * d[:-1] * h[:-1]
    assert np.allclose(left_val, a[1:]) and np.allclose(left_d1, b[1:]) and np.allclose(left_d2, 2 * c[1:])
    assert math.isclose(c[0], 0.0, abs_tol=1e-12)                               # natural start
    assert math.isclose(2 * c[-1] + 6 * d[-1] * h[-1], 0.0, abs_tol=1e-9)        # natural end


def test_natural_spline_matches_scipy():
    scipy = pytest.importorskip("scipy.interpolate")
    t = np.array([0.0, 0.7, 1.9, 3.2, 4.0]); y = np.sin(t) * 3
    coeffs = natural_cubic_spline(t, y)
    xs = np.linspace(0, 4, 50)
    assert np.allclose(eval_spline(t, coeffs, xs), scipy.CubicSpline(t, y, bc_type="natural")(xs))


def test_smoothing_keeps_endpoints_and_avoids_obstacles():
    geo = empty(12)
    poly = [(1, 1), (6, 1), (6, 8)]
    curve, info = smooth_turns(geo, poly)
    assert np.allclose(curve[0], (1, 1)) and np.allclose(curve[-1], (6, 8)) and info[0]["smoothed"]
    assert all(geo.segment_free(tuple(p), tuple(q)) for p, q in zip(curve[:-1], curve[1:]))
    assert path_length(curve) < path_length(poly)


# ----------------------------------------------------------------------------- Sec. 3.3 pruning
@pytest.mark.parametrize("seed", range(6))
def test_pruning_never_worse(seed):
    m = random_map(30, seed)
    geo = GridGeometry(m.grid)
    _, raw = dijkstra_8(m.grid, m.start, m.goal)
    pr = prune_path(geo, raw)
    assert pr[0] == tuple(m.start) and pr[-1] == tuple(m.goal)
    assert all(geo.line_of_sight(a, b) for a, b in zip(pr[:-1], pr[1:]))
    assert path_length(pr) <= path_length(raw) + 1e-9
    assert turn_metrics(pr)["turns"] <= turn_metrics(raw)["turns"]


def test_metrics_turns():
    assert turn_metrics([(0, 0), (1, 0), (2, 0), (2, 1), (3, 2)]) == \
        dict(turns=2, turn_angle_deg=pytest.approx(135.0), turn_angle_45conv=90.0)
    assert compress_collinear([(0, 0), (1, 1), (2, 2), (3, 2)]) == [(0, 0), (2, 2), (3, 2)]


@pytest.mark.parametrize("seed", range(6))
def test_huang_pruning_valid_and_not_better_than_proposed_in_turns(seed):
    m = random_map(30, seed)
    geo = GridGeometry(m.grid)
    _, raw = dijkstra_8(m.grid, m.start, m.goal)
    hu = prune_huang(geo, raw)
    assert hu[0] == tuple(m.start) and hu[-1] == tuple(m.goal)
    assert all(geo.line_of_sight(a, b) for a, b in zip(hu[:-1], hu[1:]))
    assert turn_metrics(hu)["turns"] <= turn_metrics(raw)["turns"]


@pytest.mark.parametrize("seed", range(4))
def test_alternating_26_returns_valid_path(seed):
    m = random_map(30, seed)
    r = plan(m, "alternating_26")
    assert r["success"] and validate_path(m, r)
