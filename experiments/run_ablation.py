"""E4 - Fair-comparison and ablation study (our addition; not in the paper).

The paper applies pruning + smoothing only to VNS-BA*.  Here we (a) give every baseline the same
post-processing, and (b) switch off VNS-BA* components one at a time, to see which part of the
method produces the reported gains.  Also includes (c) a sensitivity check of the unspecified details.

    python -m experiments.run_ablation --repeats 10
Output: results/phase4/ablation.csv
"""
from __future__ import annotations
import argparse
import pandas as pd

from experiments.common import MAP_NAMES, RESULTS, load_map, timed_plan, flat

VARIANTS = {
    # (a) fair comparison: same post-processing for everybody
    "A* + prune + smooth":          ("astar", dict(prune=True, smooth=True)),
    "Improved A* [28] + prune + smooth": ("improved_astar_28", dict(prune=True, smooth=True)),
    "BA* + prune + smooth":         ("bastar", dict(prune=True, smooth=True)),
    "Improved BA* [29] + prune + smooth": ("improved_bastar_29", dict(prune=True, smooth=True)),
    # (b) ablation of VNS-BA*
    "VNS-BA* (full)":               ("vns_bastar", dict()),
    "VNS-BA* - no pruning/smoothing": ("vns_bastar", dict(prune=False, smooth=False)),
    "VNS-BA* - no smoothing":       ("vns_bastar", dict(smooth=False)),
    "VNS-BA* - 8-neighbourhood only": ("vns_bastar", dict(neighborhood="8")),
    "VNS-BA* - no obstacle factor e^rho": ("vns_bastar", dict(use_rho=False)),
    "VNS-BA* - omega=0 (no opposite attraction)": ("vns_bastar", dict(omega=0.0, eta=1.0)),
    "VNS-BA* - eta=0 (no global guidance)": ("vns_bastar", dict(omega=1.0, eta=0.0)),
    # (c) sensitivity to unspecified details
    "VNS-BA* - meet rule open_closed (A26)": ("vns_bastar", dict(meet_rule="open_closed")),
    "VNS-BA* - spline offset 0.5 (A7)": ("vns_bastar", dict(spline_offset=0.5)),
    "VNS-BA* - spline offset 1.5 (A7)": ("vns_bastar", dict(spline_offset=1.5)),
}
GROUP = {k: ("fair comparison" if "+ prune" in k else "sensitivity" if "(A" in k else "ablation") for k in VARIANTS}


def run(repeats=10, maps=MAP_NAMES):
    rows = []
    for name in maps:
        m = load_map(name)
        for label, (alg, kw) in VARIANTS.items():
            r = timed_plan(m, alg, repeats, **kw)
            rows.append(flat(r, variant=label, group=GROUP[label]))
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "ablation.csv", index=False)
    fair_table6(df)
    return df


def fair_table6(ab: pd.DataFrame) -> pd.DataFrame:
    """Table 6 recomputed against baselines that received the same pruning + smoothing as VNS-BA*."""
    from experiments.common import METRICS, improvement
    pairs = {"astar": "A* + prune + smooth", "improved_astar_28": "Improved A* [28] + prune + smooth",
             "bastar": "BA* + prune + smooth", "improved_bastar_29": "Improved BA* [29] + prune + smooth"}
    rows = []
    for name in ab["map"].unique():
        v = ab[(ab["map"] == name) & (ab.variant == "VNS-BA* (full)")].iloc[0]
        for alg, label in pairs.items():
            o = ab[(ab["map"] == name) & (ab.variant == label)].iloc[0]
            row = dict(map=name, compared_to=alg)
            for k in METRICS:
                row[k] = round(improvement(o[k], v[k]), 2)
            row["comprehensive"] = round(sum(row[k] for k in METRICS) / 5, 2)
            row["comprehensive_no_time"] = round(sum(row[k] for k in METRICS if k != "time_s") / 4, 2)
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "table6_fair.csv", index=False)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=10)
    d = run(ap.parse_args().repeats)
    print(d.pivot_table(index="variant", columns="map", values="turns"))
