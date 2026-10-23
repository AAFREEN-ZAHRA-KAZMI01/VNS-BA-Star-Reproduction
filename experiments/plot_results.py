"""Figures for Phase 4 (all read the CSVs written by the run_* scripts)."""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from experiments.common import FIGURES, MAP_NAMES, MAP_LABEL, METRICS, METRIC_LABEL, ALGORITHMS

COLORS = {"astar": "#1f77b4", "improved_astar_28": "#ff7f0e", "bastar": "#2ca02c",
          "improved_bastar_29": "#9467bd", "vns_bastar": "#d62728"}
MARKERS = {"map_A_20": "o", "map_B_40": "s", "map_C_60": "^", "map_D_80": "D"}


def _save(fig, name):
    fig.savefig(FIGURES / name, dpi=140, bbox_inches="tight")
    return fig


def weight_sweep(summary: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    for ax, (ours, pub, lab) in zip(axes, [("avg_nodes", "pub_avg_nodes", "Average number of nodes"),
                                           ("avg_time_s", "pub_avg_time_s", "Average time (s)"),
                                           ("avg_length", "pub_avg_length", "Average path length")]):
        ax.plot(summary.omega, summary[ours], "o-", c="#d62728", label="ours")
        ax.set_xlabel("omega (eta = 1 - omega)"); ax.set_ylabel(f"{lab} - ours", color="#d62728")
        ax2 = ax.twinx(); ax2.plot(summary.omega, summary[pub], "s--", c="#555", label="paper Table 1")
        ax2.set_ylabel(f"{lab} - paper", color="#555")
        ax.axvline(0.5, ls=":", c="gray"); ax.grid(alpha=.3)
        ax.set_title(lab)
    axes[0].legend(loc="upper left"); fig.suptitle("E1 - weight sweep on the Fig. 3 tuning maps (Table 1)")
    fig.tight_layout(); return _save(fig, "phase4_E1_weight_sweep.png")


def published_vs_ours(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 5, figsize=(23, 4.6))
    for ax, k in zip(axes, METRICS):
        for _, r in df.iterrows():
            ax.scatter(r[f"pub_{k}"], r[k], c=COLORS[r.algorithm], marker=MARKERS[r["map"]], s=55,
                       edgecolor="k", lw=.4)
        lo = min(df[k].min(), df[f"pub_{k}"].min()); hi = max(df[k].max(), df[f"pub_{k}"].max())
        if k == "time_s":
            ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_title("Planning time (log-log)\nnot comparable in absolute terms")
        else:
            ax.plot([lo, hi], [lo, hi], "k--", lw=.8); ax.set_title(METRIC_LABEL[k])
        ax.set_xlabel("published"); ax.set_ylabel("ours"); ax.grid(alpha=.3)
    h = [plt.Line2D([], [], ls="", marker="o", c=c, label=ALGORITHMS[a]) for a, c in COLORS.items()]
    h += [plt.Line2D([], [], ls="", marker=mk, c="gray", label=MAP_LABEL[m]) for m, mk in MARKERS.items()]
    axes[-1].legend(handles=h, fontsize=8, loc="center left", bbox_to_anchor=(1.02, .5))
    fig.suptitle("E2 - our results vs published Tables 2-5 (points on the dashed line = exact reproduction)")
    fig.tight_layout(); return _save(fig, "phase4_E2_published_vs_ours.png")


def table6_heatmaps(t6: pd.DataFrame):
    labels = [f"{MAP_LABEL[m][0]} vs {ALGORITHMS[a].split(' [')[0]}" for m, a in zip(t6["map"], t6.compared_to)]
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), sharey=True)
    for ax, pre, title in [(axes[0], "pub_", "Published Table 6"), (axes[1], "", "Ours")]:
        M = t6[[pre + k for k in METRICS]].to_numpy(float)
        im = ax.imshow(np.clip(M, -100, 100), cmap="RdYlGn", vmin=-100, vmax=100, aspect="auto")
        for (i, j), v in np.ndenumerate(M):
            ax.text(j, i, f"{v:.0f}" if abs(v) < 1000 else f"{v:.0e}", ha="center", va="center", fontsize=7)
        ax.set_xticks(range(5)); ax.set_xticklabels(["nodes", "turns", "angle", "time", "length"])
        ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8); ax.set_title(title)
    fig.colorbar(im, ax=axes, shrink=.6, label="VNS-BA* improvement ratio (%)  (clipped to +-100)")
    fig.suptitle("E3 - Table 6: improvement of VNS-BA* over each algorithm")
    return _save(fig, "phase4_E3_table6.png")


def fig12(t6: pd.DataFrame, t6_fair: pd.DataFrame | None = None):
    algs = [a for a in ALGORITHMS if a != "vns_bastar"]
    series = [("pub_comprehensive_fig12", "Published Fig. 12", t6), ("comprehensive_no_time", "Ours (4 metrics, no time)", t6),
              ("comprehensive", "Ours (5 metrics incl. time)", t6)]
    if t6_fair is not None:
        series.append(("comprehensive_no_time", "Ours vs baselines + prune/smooth (no time)", t6_fair))
    fig, axes = plt.subplots(1, len(series), figsize=(5.2 * len(series), 4.2), sharey=False)
    x = np.arange(4); w = 0.2
    for ax, (col, title, tab) in zip(axes, series):
        for i, a in enumerate(algs):
            vals = [tab[(tab["map"] == m) & (tab.compared_to == a)][col].iloc[0] for m in MAP_NAMES]
            ax.bar(x + (i - 1.5) * w, vals, w, color=COLORS[a], label=f"vs {ALGORITHMS[a]}")
        ax.axhline(0, c="k", lw=.7); ax.set_xticks(x); ax.set_xticklabels([MAP_LABEL[m] for m in MAP_NAMES], fontsize=8)
        ax.set_title(title, fontsize=10); ax.grid(axis="y", alpha=.3)
        if col == "comprehensive":
            ax.set_yscale("symlog", linthresh=50)
    axes[0].set_ylabel("comprehensive improvement (%)"); axes[0].legend(fontsize=7)
    fig.suptitle("E3 - Fig. 12: mean improvement ratio of VNS-BA*"); fig.tight_layout()
    return _save(fig, "phase4_E3_fig12.png")


def ablation(ab: pd.DataFrame):
    order = list(dict.fromkeys(ab.variant))
    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5), sharey=True)
    for ax, k in zip(axes, ["turns", "length", "nodes"]):
        piv = ab.pivot_table(index="variant", columns="map", values=k).loc[order[::-1]]
        y = np.arange(len(piv))
        for j, m in enumerate(MAP_NAMES):
            ax.barh(y + (j - 1.5) * 0.2, piv[m], 0.2, label=MAP_LABEL[m])
        ax.set_yticks(y); ax.set_yticklabels(piv.index, fontsize=8); ax.set_title(METRIC_LABEL[k]); ax.grid(axis="x", alpha=.3)
    axes[0].legend(fontsize=8); fig.suptitle("E4 - fair comparison, ablation and sensitivity (Maps A-D)")
    fig.tight_layout(); return _save(fig, "phase4_E4_ablation.png")


def random_boxplots(rr: pd.DataFrame):
    rr = rr.copy(); rr["length_ratio"] = rr["length"] / rr["optimal_length"]; rr["time_ms"] = 1000 * rr["time_s"]
    variants = list(dict.fromkeys(rr.variant))
    fig, axes = plt.subplots(1, 4, figsize=(24, 5))
    for ax, (k, lab) in zip(axes, [("turns", "Number of turns"), ("length_ratio", "Length / optimal 8-connected length"),
                                   ("nodes", "Number of nodes"), ("time_ms", "Planning time (ms, log)")]):
        sizes = sorted(rr["size"].unique()); w = 0.8 / len(variants)
        for i, v in enumerate(variants):
            data = [rr[(rr["size"] == s) & (rr.variant == v)][k].dropna() for s in sizes]
            pos = np.arange(len(sizes)) + (i - (len(variants) - 1) / 2) * w
            bp = ax.boxplot(data, positions=pos, widths=w * .9, patch_artist=True, showfliers=False)
            col = plt.cm.tab10(i)
            for b in bp["boxes"]:
                b.set_facecolor(col); b.set_alpha(.75)
        ax.set_xticks(range(len(sizes))); ax.set_xticklabels([f"{s}x{s}" for s in sizes]); ax.set_title(lab)
        ax.grid(axis="y", alpha=.3)
        if k == "time_ms":
            ax.set_yscale("log")
    axes[0].legend([plt.Rectangle((0, 0), 1, 1, fc=plt.cm.tab10(i), alpha=.75) for i in range(len(variants))],
                   variants, fontsize=7, loc="upper left")
    fig.suptitle("E5 - 120 random maps (30 seeds per size, 20 % density)")
    fig.tight_layout(); return _save(fig, "phase4_E5_random_maps.png")
