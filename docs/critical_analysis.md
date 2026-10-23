# Critical Analysis of the Reproduction (2026-10-23)

**Article:** P. Li, Y. Li, X. Dai, "VNS-BA*: An Improved Bidirectional A* Path Planning Algorithm Based on Variable Neighborhood Search," *Sensors*, 24(21), 6929, 2024.

## 1. Results (Assignment Sec. 5)
| Evaluation metric (mean of Maps A-D, VNS-BA*) | Published | Ours | Difference |
|---|---|---|---|
| Number of nodes | 241.000 | 226.750 | -14.250 (-5.9 %) |
| Number of turns | 6.500 | 7.750 | +1.250 (+19.2 %) |
| Turn angle (deg) | 333.703 | 211.860 | -121.843 (-36.5 %) |
| Path length | 62.489 | 61.113 | -1.376 (-2.2 %) |
| Planning time (s) | 17.662 | 0.020 | -17.642 (-99.9 %) |

| Improvement ratio of VNS-BA* (mean of 16 comparisons) | Published | Ours | Difference |
|---|---|---|---|
| Mean improvement in number of nodes (%) | 7.89 | 14.74 | +6.86 |
| Mean improvement in number of turns (%) | 55.29 | 48.37 | -6.92 |
| Mean improvement in turn angle (deg) (%) | 51.39 | 71.31 | +19.92 |
| Mean improvement in path length (%) | 3.19 | 4.52 | +1.33 |
| Mean comprehensive rate, 4 metrics (%) | 29.44 | 34.74 | +5.30 |
| Mean comprehensive rate, Fig. 12 / 5 metrics (%) | 34.82 | -335.73 | -370.55 |

Baselines: exact length in 14/16 and exact turns in 13/16 algorithm-map cells, median node error 0.54 %.

## 2. Verdict
**(A) Comparable** for the path-quality and search-effort metrics in the paper's protocol (nodes -5.9 %, length -2.2 %, turns +0 to +3 per map); the paper's relative claims on turns, turn angle and nodes are reproduced (Table 6: fewer turns in 16/16 comparisons).
Qualifications: (i) the lower turn angle (-36.5 %) is a measurement-point effect, not an improvement; (ii) the planning-time claim is **not reproduced** and is implementation-dependent; (iii) under a **fair protocol** (same pruning + smoothing for all methods) the turn advantage falls from 48.4 % to 18.6 %, and BA* + post-processing is significantly better than VNS-BA* in turns on 80x80 random maps (-10.8 %, p = 0.014) and in length (-1.6 %, p = 3.0e-05). The genuine benefit of the search is fewer nodes than plain BA* (+41.8 % on 80x80, p = 2.3e-06).

## 3. Claim verification
- **C1** Turn-point reduction > 40 % in all scenarios (max 80.96 %): published 41.67-80.96 %; ours 22.22-82.61 %; > 40 % in 11/16 -> **Partially reproduced**. Large reductions everywhere, but 5 of 16 ratios are below 40 % (min 22 %).
- **C2** Turn-angle reduction between 28.44 % and 83.53 %: published 28.44-83.53 %; ours 54.05-90.37 % -> **Reproduced (higher)**. All 16 ratios positive and larger; depends on the turn-angle measurement point (A21).
- **C3** Planning time notably better than unidirectional, some gain over bidirectional: published 29.0-95.8 % vs uni; -18.5-94.2 % vs bi; ours -971 % or worse vs uni; -640 % or worse vs bi -> **Not reproduced (implementation-dependent)**. VNS-BA* is slowest per run in our code; published times follow iterations (Spearman 0.90), and VNS-BA* has the fewest iterations (see E6).
- **C4** Negative node optimisation on the simple map, improving with map size: published Map A: -23.5 to -9.9 %; ours Map A: -8.5 to 3.3 %; Maps C/D within 1-2 pts of paper vs BA* -> **Reproduced**. Map A ratios negative in 3/4 (paper 4/4) and positive on the larger maps vs BA*; node ratios on Maps C, D are within a few points of the paper.
- **C5** Comprehensive optimisation rate > 30 % on Maps B, C, D: published 30.57-51.04 %; ours 4 metrics: 23.57-46.12 % (> 30 % in 10/12); with time: negative -> **Partially reproduced**. Holds without the time metric for Maps B, C and 2 of 4 comparisons on D; time makes it negative.
- **C6** omega = eta = 0.5 minimises nodes and search time: published minimum at 0.5 (78 nodes); ours minimum at omega=0.6 (83.50); 0.5 gives 86.25 -> **Partially reproduced**. Same U-shape; 0.5 is near-optimal (within ~3 %) but not the minimum.
- **C7** Gains are due to the proposed method (implicit in the comparison design): published not tested (post-processing only for VNS-BA*); ours fair: mean turn gain 18.6 % (vs 48.4 %); BA*+prune+smooth better in turns at 80x80 (-10.8 %, p=0.014) -> **Not supported**. Turn/angle gains come mainly from pruning + smoothing; the search mainly saves nodes vs BA*.

## 4. Justification
**Dataset.** No data released; maps reconstructed from Figs. 3, 8-11; validated by 5-copy agreement (>= 99.98 %), stated density, and exact equality of optimal and published grid lengths on all four maps. Tuning maps have no cross-check.
**Settings / parameters.** omega = eta = 0.5 as in the paper; three details calibrated from baseline numbers only (Manhattan heuristic, nodes = generated, Fig. 4 meeting rule); remaining VNS-BA* details chosen by us; sensitivity < 1 % length, 0 turns, <= ~6 % nodes.
**Randomness.** All planners deterministic (identical metrics on repeated runs); timing median of 30 runs; 120 seeded random maps with Wilcoxon tests for statistics the paper lacks.
**Software / resources.** MATLAB R2018b (paper, hardware unreported) vs Python 3 / NumPy on a CPU. Published times are 86-1066 ms per iteration and correlate with iteration counts (Spearman 0.90), not with computational work (0.23).
**Missing / ambiguous details.** 26 register entries (4 high impact): rho, extension cost, f re-evaluation, P1-P4, spline boundary conditions (Eq. 11 under-determined and duplicated), metric measurement points, timing protocol; plus reporting errors in Tables 4, 6 and Fig. 12.
**Deviations.** Python; reconstructed maps; parametric natural spline; baselines re-implemented from refs. [28], [29]; added fair comparison, ablation and random-map statistics.

## 5. Limitations of this reproduction
- VNS-BA* internals not specified by the paper had to be chosen; the reproduction of VNS-BA* is therefore approximate, while the baselines are exact.
- Times are not comparable with the paper; only iteration counts are implementation-independent.
- Random maps use i.i.d. obstacles, which differ from the structured maps of the paper.
- Tuning maps could not be cross-validated.
