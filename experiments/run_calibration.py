"""Calibration of unspecified baseline details against the published BASELINE numbers only (Phase 3, Sec. 3.6).
Tests the heuristic of the traditional A*/BA*, the meaning of "Number of Nodes" and the BA* meeting rule.

    python -m experiments.run_calibration
Output: results/phase3/calibration.csv
"""
from __future__ import annotations
import pandas as pd

from experiments.common import ROOT, MAP_NAMES, PUBLISHED, load_map
from src.geometry import GridGeometry, euclid, manhattan, switch_distance
from src.neighborhood import neighbors_8
from src.search import best_first, bidirectional
from src.metrics import path_length, turn_metrics


def run():
    rows = []
    for name in MAP_NAMES:
        m = load_map(name); geo = GridGeometry(m.grid); S, G = tuple(m.start), tuple(m.goal); roots = {"S": G, "G": S}
        for hname in ["manhattan", "euclid", "switch"]:
            d = {"manhattan": manhattan, "euclid": euclid, "switch": lambda a, b: switch_distance(geo, a, b)}[hname]
            ra = best_first(geo, S, G, neighbors_8, lambda n: d(n, G)); p = PUBLISHED[name]["astar"]
            rows.append(dict(map=name, algorithm="A*", variant=f"h={hname}", expanded=ra.expanded, generated=ra.generated,
                             pub_nodes=p[0], length=round(path_length(ra.path), 3), pub_length=p[4],
                             turns=turn_metrics(ra.path)["turns"], pub_turns=p[1]))
        for meet in ["pop_closed", "open_closed", "pop_in_open"]:
            rb = bidirectional(geo, S, G, lambda gg, n, t: neighbors_8(gg, n), lambda s, n, o: manhattan(n, roots[s]), meet_rule=meet)
            p = PUBLISHED[name]["bastar"]
            rows.append(dict(map=name, algorithm="BA*", variant=f"h=manhattan, meet={meet}", expanded=rb.expanded,
                             generated=rb.generated, pub_nodes=p[0], length=round(path_length(rb.path), 3), pub_length=p[4],
                             turns=turn_metrics(rb.path)["turns"], pub_turns=p[1]))
    cal = pd.DataFrame(rows)
    cal["length_match"] = (cal.length - cal.pub_length).abs() < 2e-3
    cal["turns_match"] = cal.turns == cal.pub_turns
    cal["gen_err_%"] = (100 * (cal.generated - cal.pub_nodes) / cal.pub_nodes).round(1)
    cal["exp_err_%"] = (100 * (cal.expanded - cal.pub_nodes) / cal.pub_nodes).round(1)
    out = ROOT / "results" / "phase3"; out.mkdir(parents=True, exist_ok=True)
    cal.to_csv(out / "calibration.csv", index=False)
    return cal


if __name__ == "__main__":
    c = run()
    print(c.groupby(["algorithm", "variant"]).agg(length_matches=("length_match", "sum"), turn_matches=("turns_match", "sum")))
