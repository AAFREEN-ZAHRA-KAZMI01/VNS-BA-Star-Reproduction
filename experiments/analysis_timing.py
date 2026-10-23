"""E6 - Why the published planning times cannot be reproduced: compare the published times with
implementation-independent effort counters of our runs.

    python -m experiments.analysis_timing
Output: results/phase4/timing_analysis.csv, timing_correlations.csv
"""
from __future__ import annotations
import pandas as pd
from scipy.stats import spearmanr, pearsonr

from experiments.common import RESULTS


def run():
    d = pd.read_csv(RESULTS / "main_results.csv")
    d["pub_ms_per_expanded"] = 1000 * d.pub_time_s / d.expanded
    d["our_us_per_generated"] = 1e6 * d.time_s / d.generated
    d.to_csv(RESULTS / "timing_analysis.csv", index=False)
    rows = []
    for x in ["expanded", "generated", "time_s"]:
        rows.append(dict(predictor=x, scope="all 20 cells", spearman=spearmanr(d[x], d.pub_time_s).correlation,
                         pearson=pearsonr(d[x], d.pub_time_s)[0]))
        for m, g in d.groupby("map"):
            rows.append(dict(predictor=x, scope=m, spearman=spearmanr(g[x], g.pub_time_s).correlation, pearson=float("nan")))
    c = pd.DataFrame(rows).round(3)
    c.to_csv(RESULTS / "timing_correlations.csv", index=False)
    return d, c


if __name__ == "__main__":
    print(run()[1])
