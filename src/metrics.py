"""Evaluation metrics of Tables 2-6: expanded nodes, number of turns, turn angle, time, length."""
from __future__ import annotations
import math
import numpy as np
from src.postprocess import compress_collinear


def path_length(points) -> float:
    P = np.asarray(points, float)
    if len(P) < 2:
        return 0.0
    return float(np.hypot(*np.diff(P, axis=0).T).sum())


def turn_angles(polyline):
    """Absolute heading change (degrees) at every interior vertex of a polyline."""
    P = compress_collinear(polyline)
    out = []
    for a, b, c in zip(P[:-2], P[1:-1], P[2:]):
        h1 = math.atan2(b[1] - a[1], b[0] - a[0])
        h2 = math.atan2(c[1] - b[1], c[0] - b[0])
        d = abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
        if d > 1e-9:
            out.append(math.degrees(d))
    return out


def turn_metrics(polyline):
    ang = turn_angles(polyline)
    return dict(turns=len(ang), turn_angle_deg=float(sum(ang)),
                turn_angle_45conv=45.0 * len(ang))     # paper's apparent convention for grid paths


def improvement_ratio(other, ours):
    """Table 6: (other - ours) / other * 100."""
    return (other - ours) / other * 100.0 if other else float("nan")
