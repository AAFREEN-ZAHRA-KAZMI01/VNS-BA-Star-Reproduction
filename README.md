# Reproduction of VNS-BA*: An Improved Bidirectional A* Path Planning Algorithm

Independent re-implementation and reproduction study of

> P. Li, Y. Li, and X. Dai, "VNS-BA*: An Improved Bidirectional A* Path Planning Algorithm Based on Variable
> Neighborhood Search," *Sensors*, vol. 24, no. 21, Art. no. 6929, 2024, doi: 10.3390/s24216929.

No source code or data accompany the article (see `evidence/`). The benchmark maps were reconstructed from the
article's figures, VNS-BA* and its four baselines were implemented from the papers, and all experiments of the
article were reproduced and extended with a fair-comparison protocol, an ablation, 120 random maps with
significance tests, a timing analysis and the article's two method-level comparisons.

## Repository contents
```
README.md                     this file
REQUIREMENTS_TRACEABILITY.md  assignment requirements and where each one is addressed
requirements.txt              Python packages
src/                          implementation (algorithms, map handling, metrics)
experiments/                  experiment scripts (command line)
tests/                        unit tests (91)
maps/                         reconstructed benchmark maps + 120 seeded random maps
configs/params.yaml           parameters and implementation choices
docs/                         critical analysis, assumption register, part summaries, article PDF
evidence/                     source-code availability check
notebooks/                    complete study as a Colab / Jupyter notebook
results/                      results of all experiments (CSV/JSON) and figures
report/                       IEEE-format technical report (main.pdf)
```

## Requirements
Python 3.10 or newer, CPU only (no GPU). Install the packages with
```bash
pip install -r requirements.txt
```
`pymupdf` and `opencv-python-headless` are only needed to rebuild the maps from the article PDF.

## How to run
**Option 1 – notebook.** Open `notebooks/VNS_BA_Reproduction_Study.ipynb` in Google Colab and select
*Runtime → Run all* (about 3–6 minutes). It runs the complete study, parts 0–5, and writes all files to
`MyDrive/vns-ba-reproduction/`. The article PDF is read from `docs/paper.pdf`.

**Option 2 – command line**, from the repository root:
```bash
python -m experiments.build_maps --pdf docs/paper.pdf   # dataset: maps from the article's figures + random maps
python -m pytest -q tests                              # unit tests
python -m experiments.run_all --repeats 30             # all experiments (E1–E7, about 1–2 min)
python -m experiments.final_analysis                   # comparison tables, claim verification, figures
```

## Dataset
The article releases no maps or start/goal coordinates. The four benchmark maps (Map A 20×20 to Map D 80×80,
Figs. 8–11) and the four weight-tuning maps (Fig. 3) were reconstructed from the PDF figures: pages rendered at
800 dpi, every cell classified as obstacle/free, and the five sub-figures that show each map merged by majority
vote. **Validation:** the optimal path length on every reconstructed benchmark map equals the best published path
length on all four maps. 120 seeded random maps (30 per size, 20 % obstacles) were added for statistics.
Details: `maps/README.md`; rebuild with `experiments/build_maps.py`.

## Implementation
| Module | Content |
|---|---|
| `src/search.py` | unidirectional and bidirectional best-first search engines |
| `src/planners.py` | VNS-BA*, A*, Improved A* [28], BA*, Improved BA* [29], alternating BA* [26]; `plan()` runner |
| `src/neighborhood.py` | 8-neighbourhood, adaptive 8-11-13 neighbourhood, 5-direction neighbourhood of [28] |
| `src/geometry.py` | line of sight between cells, obstacle density ρ (integral image) |
| `src/postprocess.py` | polyline pruning (proposed and Huang et al. [27]), local natural cubic-spline smoothing |
| `src/metrics.py` | number of nodes, turns, total turn angle, path length, improvement ratio |
| `src/map_digitizer.py`, `src/grid_map.py` | map reconstruction from the PDF, map format |
| `src/random_maps.py`, `src/reference_planner.py` | seeded random maps, Dijkstra (validation only) |

Parameters follow the article (ω = η = 0.5). Details the article does not specify were either calibrated against
the published baseline results or chosen and documented; all 28 entries are listed in
`docs/ambiguity_register.csv`.

Example:
```python
from src.grid_map import GridMap
from src.planners import plan
r = plan(GridMap.load("maps", "map_C_60"), "vns_bastar")
print(r["nodes"], r["turns"], r["turn_angle_deg"], r["length"], r["time_s"])
```

## Experiments
| ID | Experiment | Script | Article counterpart |
|---|---|---|---|
| – | Calibration of unspecified baseline details | `run_calibration.py` | – |
| E1 | Weight sweep ω, η | `run_weight_sweep.py` | Table 1 |
| E2/E3 | Five planners on Maps A–D, improvement ratios | `run_main.py` | Tables 2–6, Fig. 12 |
| E4 | Fair comparison, ablation, sensitivity | `run_ablation.py` | – |
| E5 | 120 random maps, Wilcoxon tests | `run_random.py` | – |
| E6 | Analysis of the published planning times | `analysis_timing.py` | – |
| E7 | Pruning vs. [27], heuristic vs. [26] | `run_method_claims.py` | Figs. 5, 2 |

All scripts are run as `python -m experiments.<script name without .py>`; outputs are written to
`results/phase3`–`results/phase5` and `results/figures/`.

## Results
VNS-BA* on the reconstructed Maps A–D (mean of the four maps):

| Metric | Published | Reproduced | Difference |
|---|---|---|---|
| Number of nodes | 241.00 | 226.75 | -5.9 % |
| Number of turns | 6.50 | 7.75 | +19.2 % |
| Turn angle (deg) | 333.70 | 211.86 | -36.5 % |
| Path length | 62.49 | 61.11 | -2.2 % |
| Planning time (s) | 17.662 | 0.020 | -99.9 % |

The four baselines are reproduced almost exactly (exact path length in 14/16 and exact number of turns in 13/16
algorithm–map cells). **Verdict: (A) comparable** in path quality and search effort; the planning-time claim is
not reproducible (it depends on the implementation), and under a fair protocol, in which every method receives
the same pruning and smoothing, most of the turn advantage of VNS-BA* disappears.

| Claim | Statement of the article | Result |
|---|---|---|
| C1 | Turn-point reduction > 40 % in all scenarios (max 80.96 %) | Partially reproduced |
| C2 | Turn-angle reduction between 28.44 % and 83.53 % | Reproduced (higher) |
| C3 | Planning time notably better than unidirectional, some gain over bidirectional | Not reproduced (implementation-dependent) |
| C4 | Negative node optimisation on the simple map, improving with map size | Reproduced |
| C5 | Comprehensive optimisation rate > 30 % on Maps B, C, D | Partially reproduced |
| C6 | omega = eta = 0.5 minimises nodes and search time | Partially reproduced |
| C7 | Gains are due to the proposed method (implicit in the comparison design) | Not supported |
| C8 | Proposed pruning removes more redundant turns than Huang et al. [27] | Not confirmed (marginal) |
| C9 | Alternating bidirectional search of [26] produces more turns (zig-zag) than the proposed heuristic | Not confirmed |

Full analysis: `docs/critical_analysis.md` and the report.

## Report
- `report/main.pdf` – technical report in IEEE format

## Reproducibility notes
- All planners are deterministic: path metrics are identical in repeated runs.
- Planning time is the median of 30 runs and varies slightly between machines.
- Random maps use fixed seeds 0–29 (`numpy.random.default_rng`).
- The computing environment of a run is recorded in `results/environment.json`.

## Source-code availability
An automated GitHub search and a web search found no public implementation of the article; the article states
that no data or code were shared. Records: `evidence/code_availability_check.md`.

## Declaration of AI assistance
Generative AI (Claude, Anthropic) was used as an assistant for code drafting, documentation and formatting. The
selection of the article, the methodology decisions, the experiments, and the interpretation of the results were
reviewed and verified by the author.
