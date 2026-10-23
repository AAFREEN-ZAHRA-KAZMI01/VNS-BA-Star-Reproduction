"""E2/E3 - Reproduce Tables 2-6 and Fig. 12 on the reconstructed Maps A-D.

    python -m experiments.run_main --repeats 30
Outputs: results/phase4/main_results.csv, table6_ours.csv, fig12_ours.csv
"""
from __future__ import annotations
import argparse
import pandas as pd

from experiments.common import (MAP_NAMES, METRICS, PUBLISHED, PUBLISHED_TABLE6, PUBLISHED_FIG12, ALGORITHMS,
                                RESULTS, load_map, timed_plan, flat, improvement, environment, save_json)


def run(repeats=30, verbose=True):
    rows = []
    for name in MAP_NAMES:
        m = load_map(name)
        for alg in ALGORITHMS:
            r = timed_plan(m, alg, repeats)
            pub = dict(zip(METRICS, PUBLISHED[name][alg]))
            row = flat(r)
            row.update({f"pub_{k}": v for k, v in pub.items()})
            rows.append(row)
            if verbose:
                print(f"{name} {ALGORITHMS[alg]:18s} nodes {r['nodes']:4d} turns {r['turns']:3d} "
                      f"angle {r['turn_angle_deg']:8.2f} len {r['length']:8.3f} "
                      f"time {1000*r['time_s']:7.2f} ms (+-{1000*r['time_std_s']:.2f}) valid={r['valid']}")
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "main_results.csv", index=False)

    # Table 6 (ours) and comparison with the published Table 6
    t6 = []
    for name in MAP_NAMES:
        vns = df[(df["map"] == name) & (df.algorithm == "vns_bastar")].iloc[0]
        for alg in [a for a in ALGORITHMS if a != "vns_bastar"]:
            o = df[(df["map"] == name) & (df.algorithm == alg)].iloc[0]
            row = dict(map=name, compared_to=alg)
            for i, k in enumerate(METRICS):
                row[k] = round(improvement(o[k], vns[k]), 2)
                row[f"pub_{k}"] = PUBLISHED_TABLE6[alg][name][i]
            row["comprehensive"] = round(sum(row[k] for k in METRICS) / len(METRICS), 2)
            row["comprehensive_no_time"] = round(sum(row[k] for k in METRICS if k != "time_s") / 4, 2)
            row["pub_comprehensive_no_time"] = round(sum(row[f"pub_{k}"] for k in METRICS if k != "time_s") / 4, 2)
            row["pub_comprehensive_fig12"] = PUBLISHED_FIG12[name][list(ALGORITHMS).index(alg)]
            t6.append(row)
    t6 = pd.DataFrame(t6)
    t6.to_csv(RESULTS / "table6_ours.csv", index=False)
    save_json(dict(environment=environment(), repeats=repeats), "main_meta.json")
    return df, t6


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=30)
    args = ap.parse_args()
    df, t6 = run(args.repeats)
    print(t6[["map", "compared_to", "comprehensive", "pub_comprehensive_fig12"]])
