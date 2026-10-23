"""E5 - Multi-map statistics on 120 seeded random maps (30 seeds x 20/40/60/80), our addition.

    python -m experiments.run_random --repeats 3
Output: results/phase4/random_results.csv, random_summary.csv, random_wilcoxon.csv
"""
from __future__ import annotations
import argparse
import pandas as pd
from scipy.stats import wilcoxon

from experiments.common import ROOT, RESULTS, METRICS, ALGORITHMS, load_map, timed_plan, flat, improvement

EXTRA = {"A* + prune + smooth": ("astar", dict(prune=True, smooth=True)),
         "BA* + prune + smooth": ("bastar", dict(prune=True, smooth=True))}


def run(repeats=3, sizes=(20, 40, 60, 80)):
    index = pd.read_csv(ROOT / "maps" / "random" / "index.csv")
    index = index[index["size"].isin(sizes)]
    rows = []
    for _, row in index.iterrows():
        m = load_map(row["name"])
        for alg, label in ALGORITHMS.items():
            rows.append(flat(timed_plan(m, alg, repeats), variant=label, size=row["size"], seed=row["seed"],
                             optimal_length=row["optimal_length"]))
        for label, (alg, kw) in EXTRA.items():
            rows.append(flat(timed_plan(m, alg, repeats, **kw), variant=label, size=row["size"],
                             seed=row["seed"], optimal_length=row["optimal_length"]))
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "random_results.csv", index=False)

    summ = df.groupby(["size", "variant"]).agg(
        success_rate=("success", "mean"), valid_rate=("valid", "mean"),
        nodes_mean=("nodes", "mean"), nodes_std=("nodes", "std"),
        turns_mean=("turns", "mean"), turns_std=("turns", "std"),
        angle_mean=("turn_angle_deg", "mean"), angle_std=("turn_angle_deg", "std"),
        time_ms_mean=("time_s", lambda s: 1000 * s.mean()), time_ms_std=("time_s", lambda s: 1000 * s.std()),
        length_mean=("length", "mean"), length_std=("length", "std")).reset_index()
    summ.to_csv(RESULTS / "random_summary.csv", index=False)

    tests = []
    vns = df[df.variant == "VNS-BA*"].set_index(["size", "seed"])
    for other in [v for v in df.variant.unique() if v != "VNS-BA*"]:
        o = df[df.variant == other].set_index(["size", "seed"])
        for size in sorted(df["size"].unique()):
            a, b = vns.loc[size], o.loc[size]
            for k in METRICS:
                x, y = a[k].astype(float), b[k].astype(float)
                diff = (y - x)
                try:
                    p = wilcoxon(x, y).pvalue if (diff != 0).any() else 1.0
                except ValueError:
                    p = float("nan")
                tests.append(dict(size=size, compared_to=other, metric=k,
                                  vns_median=x.median(), other_median=y.median(),
                                  mean_improvement_pct=improvement(y.mean(), x.mean()),
                                  vns_better_frac=float((x < y).mean()), ties_frac=float((x == y).mean()),
                                  wilcoxon_p=p))
    tests = pd.DataFrame(tests)
    tests.to_csv(RESULTS / "random_wilcoxon.csv", index=False)
    return df, summ, tests


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    d, s, t = run(ap.parse_args().repeats)
    print(s)
