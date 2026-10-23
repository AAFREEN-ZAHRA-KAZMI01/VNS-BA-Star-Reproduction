"""Phase 5 - final comparison, claim verification, verdict and report material.

Reads the CSVs produced by Phases 3-4 and writes
  results/phase5/*.csv              final tables
  results/phase5/report_tables.tex  IEEE-ready LaTeX tables
  results/figures/report_*.png      compact figures sized for an IEEE two-column paper
    python -m experiments.final_analysis
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from experiments.common import ROOT, MAP_NAMES, MAP_LABEL, ALGORITHMS, FIGURES

P4 = ROOT / "results" / "phase4"
OUT = ROOT / "results" / "phase5"
OUT.mkdir(parents=True, exist_ok=True)
SHORT = {"astar": "A*", "improved_astar_28": "Imp. A* [28]", "bastar": "BA*", "improved_bastar_29": "Imp. BA* [29]",
         "vns_bastar": "VNS-BA*"}
METRIC4 = [("nodes", "Number of nodes"), ("turns", "Number of turns"), ("turn_angle_deg", "Turn angle (deg)"),
           ("length", "Path length")]


def load():
    d = dict(main=pd.read_csv(P4 / "main_results.csv"), t6=pd.read_csv(P4 / "table6_ours.csv"),
             fair=pd.read_csv(P4 / "table6_fair.csv"), ab=pd.read_csv(P4 / "ablation.csv"),
             rtest=pd.read_csv(P4 / "random_wilcoxon.csv"), rsum=pd.read_csv(P4 / "random_summary.csv"),
             sweep=pd.read_csv(P4 / "weight_sweep_summary.csv"), tcorr=pd.read_csv(P4 / "timing_correlations.csv"),
             reg=pd.read_csv(ROOT / "docs" / "ambiguity_register.csv"))
    return d


# ------------------------------------------------------------------------------ assignment table
def assignment_table(main):
    """Assignment Sec. 5 format for the proposed method: per map and averaged over the 4 maps."""
    v = main[main.algorithm == "vns_bastar"].set_index("map")
    rows = []
    for k, lab in METRIC4 + [("time_s", "Planning time (s)")]:
        for name in MAP_NAMES:
            pub, ours = v.loc[name, f"pub_{k}"], v.loc[name, k]
            rows.append(dict(scope=MAP_LABEL[name], metric=lab, published=pub, ours=ours,
                             difference=ours - pub, difference_pct=100 * (ours - pub) / pub))
        pub, ours = v[f"pub_{k}"].mean(), v[k].mean()
        rows.append(dict(scope="Mean of 4 maps", metric=lab, published=pub, ours=ours,
                         difference=ours - pub, difference_pct=100 * (ours - pub) / pub))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "assignment_table_full.csv", index=False)
    headline = t[t.scope == "Mean of 4 maps"].drop(columns="scope").reset_index(drop=True)
    headline.to_csv(OUT / "assignment_table.csv", index=False)
    return t, headline


def improvement_table(t6):
    """Second assignment-style table: the paper's headline improvement ratios (Table 6 means)."""
    rows = []
    for k, lab in METRIC4:
        rows.append(dict(metric=f"Mean improvement in {lab.lower()} (%)", published=t6[f"pub_{k}"].mean(),
                         ours=t6[k].mean(), difference=t6[k].mean() - t6[f"pub_{k}"].mean()))
    rows.append(dict(metric="Mean comprehensive rate, 4 metrics (%)", published=t6.pub_comprehensive_no_time.mean(),
                     ours=t6.comprehensive_no_time.mean(),
                     difference=t6.comprehensive_no_time.mean() - t6.pub_comprehensive_no_time.mean()))
    rows.append(dict(metric="Mean comprehensive rate, Fig. 12 / 5 metrics (%)", published=t6.pub_comprehensive_fig12.mean(),
                     ours=t6.comprehensive.mean(), difference=t6.comprehensive.mean() - t6.pub_comprehensive_fig12.mean()))
    t = pd.DataFrame(rows); t.to_csv(OUT / "improvement_table.csv", index=False)
    return t


def baseline_table(main):
    b = main[main.algorithm != "vns_bastar"].copy()
    b["length_exact"] = (b.length - b.pub_length).abs() < 2e-3
    b["turns_exact"] = b.turns == b.pub_turns
    b["nodes_err_pct"] = 100 * (b.nodes - b.pub_nodes) / b.pub_nodes
    b.to_csv(OUT / "baseline_reproduction.csv", index=False)
    return b


# ------------------------------------------------------------------------------ claims
def claims(d):
    t6, fair, sweep, rtest, tcorr, main = d["t6"], d["fair"], d["sweep"], d["rtest"], d["tcorr"], d["main"]
    uni = t6[t6.compared_to.isin(["astar", "improved_astar_28"])]
    bi = t6[t6.compared_to.isin(["bastar", "improved_bastar_29"])]
    comp_bcd = t6[t6["map"] != "map_A_20"]
    node_a = t6[t6["map"] == "map_A_20"].nodes
    r80 = rtest[rtest["size"] == 80].set_index(["compared_to", "metric"])
    rows = [
        dict(id="C1", claim="Turn-point reduction > 40 % in all scenarios (max 80.96 %)", source="Sec. 4 / Table 6",
             published=f"{t6.pub_turns.min():.2f}-{t6.pub_turns.max():.2f} %",
             ours=f"{t6.turns.min():.2f}-{t6.turns.max():.2f} %; > 40 % in {(t6.turns > 40).sum()}/16",
             verdict="Partially reproduced", why="Large reductions everywhere, but 5 of 16 ratios are below 40 % (min 22 %)."),
        dict(id="C2", claim="Turn-angle reduction between 28.44 % and 83.53 %", source="Sec. 4 / Table 6",
             published=f"{t6.pub_turn_angle_deg.min():.2f}-{t6.pub_turn_angle_deg.max():.2f} %",
             ours=f"{t6.turn_angle_deg.min():.2f}-{t6.turn_angle_deg.max():.2f} %",
             verdict="Reproduced (higher)", why="All 16 ratios positive and larger; depends on the turn-angle measurement point (A21)."),
        dict(id="C3", claim="Planning time notably better than unidirectional, some gain over bidirectional", source="Sec. 4",
             published=f"{uni.pub_time_s.min():.1f}-{uni.pub_time_s.max():.1f} % vs uni; {bi.pub_time_s.min():.1f}-{bi.pub_time_s.max():.1f} % vs bi",
             ours=f"{uni.time_s.max():.0f} % or worse vs uni; {bi.time_s.max():.0f} % or worse vs bi",
             verdict="Not reproduced (implementation-dependent)",
             why=f"VNS-BA* is slowest per run in our code; published times follow iterations (Spearman "
                 f"{tcorr[(tcorr.predictor=='expanded')&(tcorr.scope=='all 20 cells')].spearman.iloc[0]:.2f}), "
                 "and VNS-BA* has the fewest iterations (see E6)."),
        dict(id="C4", claim="Negative node optimisation on the simple map, improving with map size", source="Sec. 4",
             published=f"Map A: {t6[t6['map']=='map_A_20'].pub_nodes.min():.1f} to {t6[t6['map']=='map_A_20'].pub_nodes.max():.1f} %",
             ours=f"Map A: {node_a.min():.1f} to {node_a.max():.1f} %; Maps C/D within 1-2 pts of paper vs BA*",
             verdict="Reproduced", why=f"Map A ratios negative in {(node_a < 0).sum()}/4 (paper 4/4) and positive on the larger maps vs BA*; "
                 "node ratios on Maps C, D are within a few points of the paper."),
        dict(id="C5", claim="Comprehensive optimisation rate > 30 % on Maps B, C, D", source="Fig. 12",
             published=f"{t6[t6['map']!='map_A_20'].pub_comprehensive_fig12.min():.2f}-{t6[t6['map']!='map_A_20'].pub_comprehensive_fig12.max():.2f} %",
             ours=f"4 metrics: {comp_bcd.comprehensive_no_time.min():.2f}-{comp_bcd.comprehensive_no_time.max():.2f} % "
                  f"(> 30 % in {(comp_bcd.comprehensive_no_time > 30).sum()}/12); with time: negative",
             verdict="Partially reproduced", why="Holds without the time metric for Maps B, C and 2 of 4 comparisons on D; time makes it negative."),
        dict(id="C6", claim="omega = eta = 0.5 minimises nodes and search time", source="Table 1",
             published="minimum at 0.5 (78 nodes)",
             ours=f"minimum at omega={sweep.loc[sweep.avg_nodes.idxmin(), 'omega']} ({sweep.avg_nodes.min():.2f}); "
                  f"0.5 gives {sweep[sweep.omega == 0.5].avg_nodes.iloc[0]:.2f}",
             verdict="Partially reproduced", why="Same U-shape; 0.5 is near-optimal (within ~3 %) but not the minimum."),
        dict(id="C7", claim="Gains are due to the proposed method (implicit in the comparison design)", source="Sec. 4 (our test)",
             published="not tested (post-processing only for VNS-BA*)",
             ours=f"fair: mean turn gain {fair.turns.mean():.1f} % (vs {t6.turns.mean():.1f} %); BA*+prune+smooth better in turns at 80x80 "
                  f"({r80.loc[('BA* + prune + smooth','turns'),'mean_improvement_pct']:.1f} %, p={r80.loc[('BA* + prune + smooth','turns'),'wilcoxon_p']:.3f})",
             verdict="Not supported", why="Turn/angle gains come mainly from pruning + smoothing; the search mainly saves nodes vs BA*."),
    ]
    e7p = P4 / "e7_summary.json"
    if e7p.exists():
        import json
        e7 = json.loads(e7p.read_text())
        rows += [
            dict(id="C8", claim="Proposed pruning removes more redundant turns than Huang et al. [27]", source="Sec. 3.3 / Fig. 5",
                 published="6 -> 4 turns vs 6 -> 5 (one illustrative path)",
                 ours=f"{e7['pruning_cases']} paths: equal turns in {100*e7['equal_frac']:.1f} %, fewer in {100*e7['proposed_fewer_turns_frac']:.1f} %, "
                      f"more in {100*e7['proposed_more_turns_frac']:.1f} %; mean {e7['mean_turns_proposed']:.2f} vs {e7['mean_turns_huang']:.2f}",
                 verdict="Not confirmed (marginal)", why="Both pruning methods remove almost the same turns; the mean advantage is 0.2 %."),
            dict(id="C9", claim="Alternating bidirectional search of [26] produces more turns (zig-zag) than the proposed heuristic",
                 source="Sec. 3.2 / Fig. 2",
                 published="qualitative (Fig. 2b vs 2c)",
                 ours=f"raw search paths, 124 maps: {e7['alt26_mean_turns']:.2f} vs {e7['vns_mean_turns']:.2f} turns "
                      f"(Wilcoxon p={e7['alt26_turns_wilcoxon_p']:.2f}); paper maps mixed",
                 verdict="Not confirmed", why="No significant difference in turns; VNS-BA* better on Maps A, B, worse on C, D."),
        ]
    c = pd.DataFrame(rows); c.to_csv(OUT / "claim_verification.csv", index=False)
    return c


def metric_verdicts(headline, base):
    v = []
    for _, r in headline.iterrows():
        pct = r.difference_pct
        if r.metric.startswith("Planning time"):
            verdict, why = "Not comparable", "MATLAB vs Python and unreported timing protocol; ms vs s (E6)"
        elif r.metric.startswith("Turn angle"):
            verdict, why = "Improved (definition-dependent)", "Lower angle; measured on pruned polyline (A21)"
        elif abs(pct) <= 15:
            verdict, why = "Comparable", f"mean difference {pct:+.1f} %"
        else:
            verdict, why = ("Lower" if (r.metric != "Number of nodes" and pct > 0) else "Improved"), f"mean difference {pct:+.1f} %"
        if r.metric == "Number of turns":
            verdict, why = "Comparable (slightly higher)", f"+1 to +3 turns per map (mean {pct:+.1f} %)"
        v.append(dict(metric=r.metric, published=r.published, ours=r.ours, difference_pct=pct, verdict=verdict, reason=why))
    v = pd.DataFrame(v); v.to_csv(OUT / "metric_verdicts.csv", index=False)
    return v


# ------------------------------------------------------------------------------ LaTeX
def _tex(s):
    s = str(s)
    for a, b in [("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"),
                 ("omega", "$\\omega$"), ("eta", "$\\eta$"), ("rho", "$\\rho$"), (">", "$>$"), ("<", "$<$")]:
        s = s.replace(a, b)
    return s.replace("*", "$^*$").replace("$^*$$^*$", "$^{**}$")


def latex_tables(d, headline, impr, base, claim_df):
    main, fair, t6, reg = d["main"], d["fair"], d["t6"], d["reg"]
    L = ["% Auto-generated by experiments/final_analysis.py - requires \\usepackage{booktabs}\n"]
    # T1 VNS-BA* per map
    L += ["\\begin{table*}[t]\\centering\\caption{VNS-BA* on the reconstructed maps: published values vs our re-implementation.}",
          "\\label{tab:vns}\\begin{tabular}{lrrrrrrrrrr}\\toprule",
          " & \\multicolumn{2}{c}{Nodes} & \\multicolumn{2}{c}{Turns} & \\multicolumn{2}{c}{Turn angle ($^\\circ$)} & "
          "\\multicolumn{2}{c}{Length} & \\multicolumn{2}{c}{Time} \\\\",
          "Map & Paper & Ours & Paper & Ours & Paper & Ours & Paper & Ours & Paper (s) & Ours (ms) \\\\\\midrule"]
    v = main[main.algorithm == "vns_bastar"]
    for _, r in v.iterrows():
        L.append(f"{MAP_LABEL[r['map']]} & {r.pub_nodes:.0f} & {r.nodes:.0f} & {r.pub_turns:.0f} & {r.turns:.0f} & "
                 f"{r.pub_turn_angle_deg:.1f} & {r.turn_angle_deg:.1f} & {r.pub_length:.2f} & {r.length:.2f} & "
                 f"{r.pub_time_s:.2f} & {1000*r.time_s:.1f}$\\pm${1000*r.time_std_s:.1f} \\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table*}\n"]
    # T2 assignment headline
    L += ["\\begin{table}[t]\\centering\\caption{Assignment comparison (mean over Maps A--D, VNS-BA*).}\\label{tab:assign}",
          "\\begin{tabular}{lrrr}\\toprule Metric & Published & Ours & Difference \\\\\\midrule"]
    for _, r in headline.iterrows():
        L.append(f"{_tex(r.metric)} & {r.published:.3f} & {r.ours:.3f} & {r.difference:+.3f} ({r.difference_pct:+.1f}\\%) \\\\")
    for _, r in impr.iterrows():
        L.append(f"{_tex(r.metric)} & {r.published:.2f} & {r.ours:.2f} & {r.difference:+.2f} \\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table}\n"]
    # T3 baselines
    L += ["\\begin{table}[t]\\centering\\caption{Reproduction of the four baselines (16 algorithm--map cells).}\\label{tab:base}",
          "\\begin{tabular}{lrrr}\\toprule Algorithm & Exact length & Exact turns & Median $|$node err.$|$ \\\\\\midrule"]
    for alg in [a for a in ALGORITHMS if a != "vns_bastar"]:
        g = base[base.algorithm == alg]
        L.append(f"{_tex(SHORT[alg])} & {int(g.length_exact.sum())}/4 & {int(g.turns_exact.sum())}/4 & {g.nodes_err_pct.abs().median():.1f}\\% \\\\")
    L.append(f"All & {int(base.length_exact.sum())}/16 & {int(base.turns_exact.sum())}/16 & {base.nodes_err_pct.abs().median():.1f}\\% \\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table}\n"]
    # T4 fair comparison
    L += ["\\begin{table}[t]\\centering\\caption{Mean improvement of VNS-BA* (\\%) with raw baselines (paper protocol) and with baselines "
          "given the same pruning and smoothing (fair protocol).}\\label{tab:fair}",
          "\\begin{tabular}{lrrrr}\\toprule Protocol & Turns & Angle & Length & 4-metric \\\\\\midrule",
          f"Paper (raw baselines) & {t6.turns.mean():.1f} & {t6.turn_angle_deg.mean():.1f} & {t6.length.mean():.2f} & {t6.comprehensive_no_time.mean():.1f} \\\\",
          f"Fair (+ prune + smooth) & {fair.turns.mean():.1f} & {fair.turn_angle_deg.mean():.1f} & {fair.length.mean():.2f} & {fair.comprehensive_no_time.mean():.1f} \\\\",
          "\\bottomrule\\end{tabular}\\end{table}\n"]
    # T5 claims
    L += ["\\begin{table*}[t]\\centering\\caption{Verification of the paper's claims.}\\label{tab:claims}",
          "\\begin{tabular}{p{0.5cm}p{5.2cm}p{3.2cm}p{4.6cm}p{2.6cm}}\\toprule ID & Claim & Published & Ours & Verdict \\\\\\midrule"]
    for _, r in claim_df.iterrows():
        L.append(f"{r.id} & {_tex(r.claim)} & {_tex(r.published)} & {_tex(r.ours)} & {_tex(r.verdict)} \\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table*}\n"]
    # T6 deviations (high-impact + calibrated)
    sel = reg[reg.impact_on_reproduction.isin(["High", "Resolved", "Our addition"])]
    L += ["\\begin{table*}[t]\\centering\\caption{Assumptions, calibrated details and deviations (high impact).}\\label{tab:dev}",
          "\\begin{tabular}{p{0.7cm}p{1.2cm}p{4.8cm}p{9.0cm}}\\toprule ID & Paper & Issue & Our decision \\\\\\midrule"]
    for _, r in sel.iterrows():
        L.append(f"{r.id} & {_tex(r.section)} & {_tex(r.issue)} & {_tex(r.our_assumption)} \\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table*}\n"]
    (OUT / "report_tables.tex").write_text("\n".join(L))
    return OUT / "report_tables.tex"


# ------------------------------------------------------------------------------ figures (IEEE widths)
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "legend.fontsize": 6,
                     "xtick.labelsize": 6, "ytick.labelsize": 6, "font.family": "serif"})
COL = {"astar": "#1f77b4", "improved_astar_28": "#ff7f0e", "bastar": "#2ca02c", "improved_bastar_29": "#9467bd",
       "vns_bastar": "#d62728"}
MK = {"map_A_20": "o", "map_B_40": "s", "map_C_60": "^", "map_D_80": "D"}


def fig_scatter(main):
    fig, axes = plt.subplots(1, 4, figsize=(7.16, 1.9))
    for ax, (k, lab) in zip(axes, METRIC4):
        for _, r in main.iterrows():
            ax.scatter(r[f"pub_{k}"], r[k], c=COL[r.algorithm], marker=MK[r["map"]], s=14, edgecolor="k", lw=.3)
        lo = min(main[k].min(), main[f"pub_{k}"].min()); hi = max(main[k].max(), main[f"pub_{k}"].max())
        ax.plot([lo, hi], [lo, hi], "k--", lw=.6); ax.set_title(lab); ax.set_xlabel("published"); ax.grid(alpha=.3, lw=.4)
    axes[0].set_ylabel("ours")
    h = [plt.Line2D([], [], ls="", marker="o", ms=4, c=c, label=SHORT[a]) for a, c in COL.items()]
    fig.legend(handles=h, loc="lower center", ncol=5, bbox_to_anchor=(.5, -.1), frameon=False)
    fig.tight_layout(); fig.savefig(FIGURES / "report_fig_published_vs_ours.png", dpi=300, bbox_inches="tight")
    return fig


def fig_fair(t6, fair):
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 1.9))
    x = np.arange(4); w = .38
    for ax, (k, lab) in zip(axes, [("turns", "Turn reduction (%)"), ("comprehensive_no_time", "4-metric comprehensive rate (%)")]):
        a = [t6[t6["map"] == m][k].mean() for m in MAP_NAMES]; b = [fair[fair["map"] == m][k].mean() for m in MAP_NAMES]
        ax.bar(x - w / 2, a, w, color="#d62728", label="paper protocol (raw baselines)")
        ax.bar(x + w / 2, b, w, color="#7f7f7f", label="fair protocol (baselines + prune + smooth)")
        ax.set_xticks(x); ax.set_xticklabels([MAP_LABEL[m] for m in MAP_NAMES]); ax.set_title(lab)
        ax.axhline(0, c="k", lw=.5); ax.grid(axis="y", alpha=.3, lw=.4)
    axes[0].legend(loc="upper left", frameon=False)
    fig.tight_layout(); fig.savefig(FIGURES / "report_fig_fair_comparison.png", dpi=300, bbox_inches="tight")
    return fig


def fig_random(rtest):
    t = rtest[rtest.metric.isin(["turns", "length", "nodes"])]
    comps = ["A*", "Improved A* [28]", "BA*", "Improved BA* [29]", "A* + prune + smooth", "BA* + prune + smooth"]
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.1), sharey=True)
    for ax, k in zip(axes, ["turns", "length", "nodes"]):
        for j, size in enumerate([20, 40, 60, 80]):
            g = t[(t.metric == k) & (t["size"] == size)].set_index("compared_to").loc[comps]
            y = np.arange(len(comps)) + (j - 1.5) * .18
            ax.scatter(g.mean_improvement_pct, y, s=12, marker=["o", "s", "^", "D"][j],
                       facecolors=["k" if p < .05 else "none" for p in g.wilcoxon_p], edgecolors="k", lw=.5,
                       label=f"{size}x{size}")
        ax.axvline(0, c="r", lw=.6); ax.set_title(f"{k}: VNS-BA* improvement (%)"); ax.grid(alpha=.3, lw=.4)
    axes[0].set_yticks(range(len(comps))); axes[0].set_yticklabels(comps)
    h = [plt.Line2D([], [], ls="", marker=mk, mfc="none", mec="k", ms=4, label=f"{s}x{s}")
         for mk, s in zip(["o", "s", "^", "D"], [20, 40, 60, 80])]
    h.append(plt.Line2D([], [], ls="", marker="o", mfc="k", mec="k", ms=4, label="filled = Wilcoxon p < 0.05"))
    fig.legend(handles=h, loc="lower center", ncol=5, bbox_to_anchor=(.55, -.08), frameon=False)
    fig.tight_layout(); fig.savefig(FIGURES / "report_fig_random_maps.png", dpi=300, bbox_inches="tight")
    return fig


def fig_timing(main, tcorr):
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    for alg, c in COL.items():
        g = main[main.algorithm == alg]
        ax.scatter(g.expanded, g.pub_time_s, c=c, s=16, edgecolor="k", lw=.3, label=SHORT[alg])
    rho = tcorr[(tcorr.predictor == "expanded") & (tcorr.scope == "all 20 cells")].spearman.iloc[0]
    rho2 = tcorr[(tcorr.predictor == "time_s") & (tcorr.scope == "all 20 cells")].spearman.iloc[0]
    ax.set_xlabel("expanded nodes (iterations) in our runs"); ax.set_ylabel("published planning time (s)")
    ax.set_title(f"Published time vs iterations: Spearman {rho:.2f} (vs our time: {rho2:.2f})")
    ax.grid(alpha=.3, lw=.4); ax.legend(frameon=False, ncol=2)
    fig.tight_layout(); fig.savefig(FIGURES / "report_fig_timing.png", dpi=300, bbox_inches="tight")
    return fig


def fig_ablation(ab):
    sel = ["VNS-BA* (full)", "VNS-BA* - no pruning/smoothing", "VNS-BA* - 8-neighbourhood only",
           "VNS-BA* - no obstacle factor e^rho", "VNS-BA* - omega=0 (no opposite attraction)", "VNS-BA* - eta=0 (no global guidance)"]
    lab = ["full", "no prune/smooth", "8-neigh. only", "no $e^{\\rho}$", "$\\omega$=0", "$\\eta$=0"]
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 1.9))
    x = np.arange(len(sel)); w = .2
    for ax, k in zip(axes, ["turns", "nodes"]):
        for j, m in enumerate(MAP_NAMES):
            vals = [ab[(ab.variant == s) & (ab["map"] == m)][k].iloc[0] for s in sel]
            ax.bar(x + (j - 1.5) * w, vals, w, label=MAP_LABEL[m])
        ax.set_xticks(x); ax.set_xticklabels(lab, rotation=20); ax.set_title(f"VNS-BA* ablation: {k}"); ax.grid(axis="y", alpha=.3, lw=.4)
    axes[0].legend(frameon=False, ncol=2)
    fig.tight_layout(); fig.savefig(FIGURES / "report_fig_ablation.png", dpi=300, bbox_inches="tight")
    return fig


def run():
    d = load()
    full, headline = assignment_table(d["main"])
    impr = improvement_table(d["t6"])
    base = baseline_table(d["main"])
    cl = claims(d)
    mv = metric_verdicts(headline, base)
    tex = latex_tables(d, headline, impr, base, cl)
    figs = [fig_scatter(d["main"]), fig_fair(d["t6"], d["fair"]), fig_random(d["rtest"]),
            fig_timing(d["main"], d["tcorr"]), fig_ablation(d["ab"])]
    return dict(data=d, full=full, headline=headline, impr=impr, base=base, claims=cl, verdicts=mv, tex=tex, figs=figs)


if __name__ == "__main__":
    r = run()
    print(r["headline"]); print(r["claims"][["id", "verdict"]]); print(r["verdicts"])
