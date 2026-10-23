# Maps (dataset)

The original paper (Li, Li & Dai, Sensors 2024, 24, 6929) does **not** release its maps.
All maps here were reconstructed from the paper's figures by `src/map_digitizer.py`
(notebook `Phase2_Maps_VNS_BA.ipynb`, run 2026-10-23).

## Files
| File | Content |
|---|---|
| `map_A_20.*` ... `map_D_80.*` | Evaluation maps of Tables 2-5 (Figs. 8-11) |
| `tune_a.*` ... `tune_d.*` | Weight-tuning maps of Table 1 (Fig. 3) |
| `random/` | 30 seeded random maps per size (20/40/60/80), 20 % density - our addition |
| `index.csv` | Summary of all paper maps |

`*.txt`: 0 = free, 1 = obstacle, **top row first** (as in the figure).
`*.json`: start, goal, density, source, validation info.
Internal convention: `grid[r, c]`, r = 0 bottom row (paper y = 1); points `(c, r)` = (paper x - 1, paper y - 1).

## Validation
- Main maps: each figure contains the same map in 5 sub-plots; all 5 digitised grids agree (majority vote, see `results/phase2/`).
- `tune_d` density = 20.0 % (paper: 20 %).
- Optimal 8-connected path length (corner cutting allowed) on the reconstructed maps vs the best published grid-path length:

| Map | Optimal (ours) | Best published | Match |
|---|---|---|---|
| map_A_20 | 28.627 | 28.627 (A*, Improved A*, BA*) | yes |
| map_B_40 | 61.598 | 61.598 (A*, BA*, Improved BA*) | yes |
| map_C_60 | 59.385 | 59.3848 (A*, BA*) | yes |
| map_D_80 | 102.125 | 102.125 (BA*) | yes |

## Known limitations
- Tuning maps (Fig. 3) appear once in the paper, so no majority vote is possible.
- Start/goal cells are taken from the red/green markers; the dot centre is mapped to the cell containing it.
- Random maps are not part of the paper; they are used only for additional multi-run statistics.
