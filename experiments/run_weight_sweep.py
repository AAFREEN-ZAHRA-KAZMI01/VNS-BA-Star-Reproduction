"""E1 - Reproduce Table 1: sweep (omega, eta) on the four Fig. 3 tuning maps.

    python -m experiments.run_weight_sweep --repeats 10
Output: results/phase4/weight_sweep.csv (per map) and weight_sweep_summary.csv (averages, as Table 1)
"""
from __future__ import annotations
import argparse
import pandas as pd

from experiments.common import RESULTS, PUBLISHED_TABLE1, load_map, timed_plan, flat

TUNING = ["tune_a", "tune_b", "tune_c", "tune_d"]


def run(repeats=10, step=0.1):
    pairs = [(round(i * step, 2), round(1 - i * step, 2)) for i in range(int(round(1 / step)) + 1)]
    rows = []
    for w, e in pairs:
        for name in TUNING:
            r = timed_plan(load_map(name), "vns_bastar", repeats, omega=w, eta=e)
            rows.append(flat(r, omega=w, eta=e))
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "weight_sweep.csv", index=False)
    s = df.groupby(["omega", "eta"]).agg(avg_nodes=("nodes", "mean"), avg_time_s=("time_s", "mean"),
                                         avg_length=("length", "mean"), avg_turns=("turns", "mean"),
                                         all_valid=("valid", "all")).reset_index()
    s["pub_avg_nodes"] = [PUBLISHED_TABLE1[(w, e)][0] for w, e in zip(s.omega, s.eta)]
    s["pub_avg_time_s"] = [PUBLISHED_TABLE1[(w, e)][1] for w, e in zip(s.omega, s.eta)]
    s["pub_avg_length"] = [PUBLISHED_TABLE1[(w, e)][2] for w, e in zip(s.omega, s.eta)]
    s.to_csv(RESULTS / "weight_sweep_summary.csv", index=False)
    return df, s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=10)
    print(run(ap.parse_args().repeats)[1])
