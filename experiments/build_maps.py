"""Phase 2 without the notebook: rebuild the paper's maps from its PDF figures and create the random maps.

    python -m experiments.build_maps --pdf docs/paper.pdf          # paper maps + 120 random maps
    python -m experiments.build_maps --random-only                  # only the random maps
Writes maps/*.txt|json, maps/index.csv, maps/random/. See maps/README.md for the format and the validation.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pandas as pd                                                   # noqa: E402
from src.grid_map import GridMap                                      # noqa: E402
from src.random_maps import random_map                                # noqa: E402
from src.reference_planner import dijkstra_8                          # noqa: E402

SPECS = {  # name: (PDF page, sub-figure frames, grid size, figure)
    "map_A_20": (10, slice(0, 5), 20, "Fig. 8"), "map_B_40": (11, slice(0, 5), 40, "Fig. 9"),
    "map_C_60": (11, slice(5, 10), 60, "Fig. 10"), "map_D_80": (12, slice(0, 5), 80, "Fig. 11"),
}
TUNING = ["tune_a", "tune_b", "tune_c", "tune_d"]                       # Fig. 3, page 6
PUBLISHED_BEST = {"map_A_20": 28.627, "map_B_40": 61.598, "map_C_60": 59.385, "map_D_80": 102.125}


def build_paper_maps(pdf: Path, dpi: int = 800):
    from src.map_digitizer import render_page, find_plot_frames, classify_cells, detect_marker, consensus, mode_point
    pages, out, dig_rows, val_rows = {}, [], [], []
    SUB = ["(a) A*", "(b) Improved A*", "(c) BA*", "(d) Improved BA*", "(e) VNS-BA*"]
    PUB = {"map_A_20": {"A*": 28.627, "Improved A*": 28.627, "BA*": 28.627, "Improved BA*": 29.213},
           "map_B_40": {"A*": 61.598, "Improved A*": 64.083, "BA*": 61.598, "Improved BA*": 61.598},
           "map_C_60": {"A*": 59.385, "Improved A*": 69.0833, "BA*": 59.3848, "Improved BA*": 61.598},
           "map_D_80": {"A*": 103.297, "Improved A*": 104.125, "BA*": 102.125, "Improved BA*": 106.225}}
    for name, (page, frames, n, fig) in SPECS.items():
        if page not in pages:
            img = render_page(str(pdf), page, dpi); pages[page] = (img, find_plot_frames(img))
        img, boxes = pages[page]
        grids = [classify_cells(img, b, n)[0] for b in boxes[frames]]
        grid, agree, disputed, _ = consensus(grids)
        for sub, g, b in zip(SUB, grids, boxes[frames]):
            dig_rows.append(dict(map=name, subfigure=sub, frame_px=f"{b[2]}x{b[3]}", obstacles=int(g.sum()),
                                 **{"agreement_with_consensus_%": round(100 * float((g == grid).mean()), 3)}))
        start = mode_point([detect_marker(img, b, n, "red") for b in boxes[frames]])
        goal = mode_point([detect_marker(img, b, n, "green") for b in boxes[frames]])
        m = GridMap(name, grid, start, goal, f"digitised from {fig} (PDF p.{page}), 5-subfigure majority vote",
                    dict(figure=fig, mean_agreement_pct=round(100 * agree, 3), disputed_cells=int(len(disputed))))
        m.save(ROOT / "maps"); out.append(m)
        opt = dijkstra_8(grid, start, goal, "free")[0]
        res = {rule: dijkstra_8(grid, start, goal, rule)[0] for rule in ["free", "no_squeeze", "strict"]}
        best = min(PUB[name].values())
        val_rows.append(dict(map=name, opt_free=round(res["free"], 3), opt_no_squeeze=round(res["no_squeeze"], 3),
                             opt_strict=round(res["strict"], 3), best_published=best,
                             best_published_by=", ".join(k for k, v in PUB[name].items() if abs(v - best) < 1e-3),
                             published_A_star=PUB[name]["A*"], exact_match=abs(res["free"] - best) < 1e-3,
                             all_published_ge_optimum=all(v >= res["free"] - 1e-3 for v in PUB[name].values())))
        print(f"{name}: agreement {100*agree:.3f} %, optimal length {opt:.3f} (best published {PUBLISHED_BEST[name]}) "
              f"-> {'MATCH' if abs(opt - PUBLISHED_BEST[name]) < 2e-3 else 'CHECK'}")
    (ROOT / "results" / "phase2").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(dig_rows).to_csv(ROOT / "results/phase2/digitisation_per_subfigure.csv", index=False)
    pd.DataFrame(val_rows).to_csv(ROOT / "results/phase2/validation_optimal_length.csv", index=False)
    img6 = render_page(str(pdf), 6, dpi); boxes6 = find_plot_frames(img6)
    for i, name in enumerate(TUNING):
        g = classify_cells(img6, boxes6[i], 20)[0]
        m = GridMap(name, g, detect_marker(img6, boxes6[i], 20, "red"), detect_marker(img6, boxes6[i], 20, "green"),
                    f"digitised from Fig. 3({'abcd'[i]}) (PDF p.6)", dict(figure=f"Fig. 3({'abcd'[i]})"))
        m.save(ROOT / "maps"); out.append(m)
        print(f"{name}: density {100*m.density:.1f} %")
    pd.DataFrame([dict(map=m.name, size=f"{m.size}x{m.size}", obstacles=int(m.grid.sum()), density_pct=round(100 * m.density, 2),
                       start_cr=m.start, goal_cr=m.goal, source=m.source) for m in out]).to_csv(ROOT / "maps" / "index.csv", index=False)


def build_random_maps(seeds=range(30), sizes=(20, 40, 60, 80), density=0.20):
    rows = []
    for n in sizes:
        for s in seeds:
            m = random_map(n, s, density); m.save(ROOT / "maps" / "random")
            rows.append(dict(name=m.name, size=n, seed=s, attempts=m.meta["attempt"] + 1,
                             density=round(m.density, 4), optimal_length=m.meta["optimal_length"]))
    pd.DataFrame(rows).to_csv(ROOT / "maps" / "random" / "index.csv", index=False)
    print(f"random maps: {len(rows)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=str(ROOT / "docs" / "paper.pdf"))
    ap.add_argument("--random-only", action="store_true")
    a = ap.parse_args()
    if not a.random_only:
        build_paper_maps(Path(a.pdf))
    build_random_maps()
