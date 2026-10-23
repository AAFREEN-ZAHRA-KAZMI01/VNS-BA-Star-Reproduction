"""Shared helpers for all experiment scripts: paths, config, published values, timing."""
from __future__ import annotations
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.grid_map import GridMap                     # noqa: E402
from src.planners import plan, ALGORITHMS, validate_path   # noqa: E402

RESULTS = ROOT / "results" / "phase4"
FIGURES = ROOT / "results" / "figures"
RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

MAP_NAMES = ["map_A_20", "map_B_40", "map_C_60", "map_D_80"]
MAP_LABEL = {"map_A_20": "A (20x20)", "map_B_40": "B (40x40)", "map_C_60": "C (60x60)", "map_D_80": "D (80x80)"}
METRICS = ["nodes", "turns", "turn_angle_deg", "time_s", "length"]
METRIC_LABEL = {"nodes": "Number of nodes", "turns": "Number of turns", "turn_angle_deg": "Turn angle (deg)",
                "time_s": "Planning time (s)", "length": "Path length"}

# --- published values, Tables 1-6 and Fig. 12 of Li, Li & Dai (2024) --------------------------
PUBLISHED = {  # (nodes, turns, turn_angle_deg, time_s, length)
    "map_A_20": {"astar": (84, 7, 315, 4.350, 28.627), "improved_astar_28": (81, 7, 315, 3.597, 28.627),
                 "bastar": (88, 10, 450, 2.155, 28.627), "improved_bastar_29": (91, 14, 630, 3.247, 29.213),
                 "vns_bastar": (100, 4, 208.967, 2.553, 27.476)},
    "map_B_40": {"astar": (345, 9, 405, 154.602, 61.598), "improved_astar_28": (277, 11, 495, 104.956, 64.083),
                 "bastar": (286, 12, 540, 28.129, 61.598), "improved_bastar_29": (263, 18, 810, 33.863, 61.598),
                 "vns_bastar": (252, 4, 289.823, 20.419, 61.263)},
    "map_C_60": {"astar": (423, 7, 315, 296.377, 59.385), "improved_astar_28": (258, 7, 945, 72.996, 69.0833),
                 "bastar": (564, 8, 360, 212.650, 59.3848), "improved_bastar_29": (239, 21, 990, 22.531, 61.598),
                 "vns_bastar": (257, 4, 163.072, 12.330, 57.517)},
    "map_D_80": {"astar": (352, 25, 1125, 108.308, 103.297), "improved_astar_28": (344, 27, 1215, 105.124, 104.125),
                 "bastar": (611, 24, 1080, 80.221, 102.125), "improved_bastar_29": (392, 30, 1350, 66.982, 106.225),
                 "vns_bastar": (355, 14, 672.95, 35.345, 103.700)},
}
PUBLISHED_TABLE6 = {  # VNS-BA* improvement ratio (%) vs algorithm, per map: nodes, turns, angle, time, length
    "astar": {"map_A_20": (-19.05, 42.86, 33.67, 41.31, 4.02), "map_B_40": (26.96, 55.56, 28.44, 86.80, 0.54),
              "map_C_60": (39.24, 42.86, 48.23, 95.84, 3.14), "map_D_80": (-0.85, 44.00, 39.91, 67.37, -0.39)},
    "improved_astar_28": {"map_A_20": (-23.46, 42.86, 33.67, 29.02, 4.02), "map_B_40": (9.02, 63.63, 41.45, 80.55, 4.40),
                          "map_C_60": (0.39, 42.86, 82.74, 83.11, 10.83), "map_D_80": (3.20, 48.15, 44.61, 66.38, 4.08)},
    "bastar": {"map_A_20": (-13.64, 60.0, 53.56, -18.47, 4.02), "map_B_40": (11.89, 66.67, 46.33, 27.40, 0.54),
               "map_C_60": (54.43, 50.0, 54.70, 94.20, 1.869), "map_D_80": (41.90, 41.67, 50.15, 55.94, -1.54)},
    "improved_bastar_29": {"map_A_20": (-9.89, 71.43, 66.83, 21.37, 5.98), "map_B_40": (4.18, 77.78, 64.22, 39.70, 0.54),
                           "map_C_60": (-7.53, 80.96, 83.53, 45.28, 6.63), "map_D_80": (9.44, 53.33, 50.15, 47.23, 2.38)},
}
PUBLISHED_FIG12 = {"map_A_20": (20.56, 17.22, 17.09, 31.14), "map_B_40": (39.66, 39.81, 30.57, 37.28),
                   "map_C_60": (45.86, 43.99, 51.04, 41.77), "map_D_80": (37.72, 33.28, 37.62, 32.51)}
PUBLISHED_TABLE1 = {  # (omega, eta): (avg nodes, avg time s, avg length)
    (0.0, 1.0): (97.5, 1.6526, 24.4121), (0.1, 0.9): (92.5, 1.8305, 25.1159), (0.2, 0.8): (91.75, 1.8056, 24.0503),
    (0.3, 0.7): (89, 1.7324, 24.1349), (0.4, 0.6): (79.75, 1.2657, 24.1159), (0.5, 0.5): (78, 0.9382, 24.2818),
    (0.6, 0.4): (83, 1.2025, 25.3870), (0.7, 0.3): (81.75, 1.2419, 24.3708), (0.8, 0.2): (83.75, 1.2762, 25.4154),
    (0.9, 0.1): (85.25, 1.2658, 25.3154), (1.0, 0.0): (85.5, 1.3067, 25.7689),
}


def load_config():
    p = ROOT / "configs" / "params.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def load_map(name):
    folder = ROOT / "maps" / ("random" if name.startswith("rand_") else "")
    return GridMap.load(folder, name)


def timed_plan(grid_map, algorithm, repeats=1, **kw):
    """Run plan() `repeats` times; metrics from the first run (planners are deterministic),
    timing statistics over all runs.  Each run rebuilds all caches, so runs are independent."""
    times, first = [], None
    for i in range(repeats):
        r = plan(grid_map, algorithm, **kw)
        times.append(r["time_s"])
        if first is None:
            first = r
    first["valid"] = validate_path(grid_map, first)
    first["time_s"] = statistics.median(times)
    first["time_mean_s"] = statistics.fmean(times)
    first["time_std_s"] = statistics.stdev(times) if len(times) > 1 else 0.0
    first["repeats"] = repeats
    return first


def flat(r, **extra):
    """Keep only scalar fields of a planner result (for CSV)."""
    keep = ["algorithm", "name", "map", "success", "valid", "nodes", "expanded", "generated", "turns",
            "turn_angle_deg", "turn_angle_45conv", "time_s", "time_mean_s", "time_std_s", "repeats",
            "length", "length_polyline", "length_raw", "raw_turns", "prune", "smooth"]
    d = {k: r.get(k) for k in keep}
    d.update(extra)
    return d


def improvement(other, ours):
    return (other - ours) / other * 100.0 if other else float("nan")


def environment():
    import numpy, scipy
    return dict(python=sys.version.split()[0], platform=platform.platform(), processor=platform.processor(),
                numpy=numpy.__version__, scipy=scipy.__version__,
                time=time.strftime("%Y-%m-%d %H:%M:%S"))


def save_json(obj, name):
    (RESULTS / name).write_text(json.dumps(obj, indent=2, default=str))
