"""E7 - The two method-level claims of the article (Sec. 3.2 / Fig. 2 and Sec. 3.3 / Fig. 5).

(a) Pruning (Sec. 3.3): the proposed pruning removes more redundant turns than the method of Huang et al. [27].
    Both are applied to the same raw grid paths (A*, BA*, VNS-BA* search output) on Maps A-D and 120 random maps.
(b) Bidirectional strategy (Sec. 3.2): the alternating search of Li et al. [26] (target = opposite current node)
    produces more turns than the proposed heuristic; compared on raw search paths (no post-processing).

    python -m experiments.run_method_claims
Output: results/phase4/e7_pruning.csv, e7_pruning_summary.csv, e7_bidirectional.csv, e7_summary.json
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from experiments.common import ROOT, RESULTS, MAP_NAMES, load_map
from src.geometry import GridGeometry
from src.planners import plan
from src.postprocess import prune_path, prune_huang, compress_collinear
from src.metrics import turn_metrics, path_length

SOURCES = ["astar", "bastar", "vns_bastar"]


def maps():
    names = list(MAP_NAMES) + list(pd.read_csv(ROOT / "maps" / "random" / "index.csv")["name"])
    return [load_map(n) for n in names]


def run():
    prow, brow = [], []
    for m in maps():
        geo = GridGeometry(m.grid)
        group = "paper maps" if m.name in MAP_NAMES else f"random {m.size}x{m.size}"
        for alg in SOURCES:
            r = plan(m, alg, prune=False, smooth=False)
            raw = r["raw_path"]
            for meth, fn in [("raw (collinear removed)", compress_collinear), ("Huang et al. [27]", lambda p: prune_huang(geo, p)),
                             ("proposed (Sec. 3.3)", lambda p: prune_path(geo, p))]:
                poly = fn(raw)
                tm = turn_metrics(poly)
                prow.append(dict(map=m.name, group=group, source=alg, method=meth, turns=tm["turns"],
                                 turn_angle_deg=tm["turn_angle_deg"], length=path_length(poly)))
        for alg in ["alternating_26", "vns_bastar"]:
            r = plan(m, alg, prune=False, smooth=False)
            brow.append(dict(map=m.name, group=group, algorithm=alg, nodes=r["nodes"], turns=r["turns"],
                             turn_angle_deg=r["turn_angle_deg"], length=r["length"]))
    P, B = pd.DataFrame(prow), pd.DataFrame(brow)
    P.to_csv(RESULTS / "e7_pruning.csv", index=False); B.to_csv(RESULTS / "e7_bidirectional.csv", index=False)

    ps = P.assign(random=P.group != "paper maps").groupby(["random", "method"])[["turns", "turn_angle_deg", "length"]].mean().round(3)
    ps.to_csv(RESULTS / "e7_pruning_summary.csv")
    piv = P.pivot_table(index=["map", "source"], columns="method", values="turns")
    hu, pr = piv["Huang et al. [27]"], piv["proposed (Sec. 3.3)"]
    paper = P[P.group == "paper maps"].pivot_table(index=["map", "source"], columns="method", values="turns")
    bv = B.pivot_table(index="map", columns="algorithm", values=["turns", "nodes", "length"])
    summary = dict(
        pruning_cases=int(len(piv)),
        proposed_fewer_turns_frac=float((pr < hu).mean()), equal_frac=float((pr == hu).mean()),
        proposed_more_turns_frac=float((pr > hu).mean()),
        mean_turns_huang=float(hu.mean()), mean_turns_proposed=float(pr.mean()),
        mean_turns_raw=float(piv["raw (collinear removed)"].mean()),
        reduction_vs_huang_pct=float(100 * (hu.mean() - pr.mean()) / hu.mean()),
        wilcoxon_p=float(wilcoxon(pr, hu).pvalue),
        paper_maps_turns={f"{a}|{b}": [int(x) for x in paper.loc[(a, b)]] for a, b in paper.index},
        alt26_mean_turns=float(bv["turns"]["alternating_26"].mean()), vns_mean_turns=float(bv["turns"]["vns_bastar"].mean()),
        alt26_more_turns_frac=float((bv["turns"]["alternating_26"] > bv["turns"]["vns_bastar"]).mean()),
        alt26_mean_nodes=float(bv["nodes"]["alternating_26"].mean()), vns_mean_nodes=float(bv["nodes"]["vns_bastar"].mean()),
        alt26_turns_wilcoxon_p=float(wilcoxon(bv["turns"]["alternating_26"], bv["turns"]["vns_bastar"]).pvalue),
        paper_maps_alt26_vs_vns_turns={m: [int(bv["turns"]["alternating_26"][m]), int(bv["turns"]["vns_bastar"][m])] for m in MAP_NAMES},
    )
    (RESULTS / "e7_summary.json").write_text(json.dumps(summary, indent=2))
    return P, B, summary


if __name__ == "__main__":
    print(json.dumps(run()[2], indent=2))
