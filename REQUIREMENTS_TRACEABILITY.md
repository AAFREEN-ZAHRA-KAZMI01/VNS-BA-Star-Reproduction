# Requirements traceability — Assignment 1 (Research Paper Re-Implementation)

Article: P. Li, Y. Li, X. Dai, "VNS-BA*: An Improved Bidirectional A* Path Planning Algorithm Based on Variable
Neighborhood Search," *Sensors*, 24(21), 6929, 2024.

| Assignment requirement | Where it is fulfilled |
|---|---|
| **§1** one article, read, assess, re-implement, reproduce, explain differences | whole project; summary in `report/main.pdf` |
| **§2** complete source code not public | `evidence/code_availability_check.md` (automated GitHub search, manual searches) |
| **§2** core method implemented independently | `src/` (written from the papers; only NumPy inside algorithms; SciPy only in one test + statistics) |
| **§3 Q1** problem, objectives, contributions | notebook Phase 1; report Sec. II-A/B |
| **§3 Q2** methodology | notebook Phase 1; report Sec. III |
| **§3 Q3** datasets / availability | report Sec. II-C, IV; `maps/README.md` (no data released → reconstructed) |
| **§3 Q4** language, libraries, tools, compute | report Sec. II-C, VI; `results/environment.json`, `requirements.txt` |
| **§3 Q5** feasibility | report Sec. II-C; notebook Phase 1 |
| **§3 Q6** sufficiency of details | report Sec. II-C, Table VII |
| **§3 Q7** missing / unclear details | `docs/ambiguity_register.csv`; report Table VII; audit of the paper's tables (Phase 1) |
| **§4** follow original method / data / parameters | `src/planners.py` (ω = η = 0.5), maps validated against published lengths; all comparisons of the article incl. Figs. 2 and 5 (E7) |
| **§4** document every assumption / deviation | `docs/ambiguity_register.csv`, `configs/params.yaml`, report Table VII + Sec. VIII-E |
| **§4** executable code + instructions | `README.md`; `python -m experiments.run_all`; notebook |
| **§5** Published / Your result / Difference table | `results/phase5/assignment_table.csv`; report Table IV; README "Results" |
| **§5** appropriate metrics, multiple runs | 5 metrics; 30 timing repeats; 120 seeded random maps (`results/phase4/`) |
| **§6** verdict (A)/(B)/(C) | (A) comparable with qualifications — `docs/critical_analysis.md`, report Sec. VIII-A |
| **§6** dataset differences | report Sec. VIII-E; notebook Phase 5 §5.6(a) |
| **§6** settings / parameters | report Sec. VIII-E; sensitivity in `results/phase4/ablation.csv` |
| **§6** randomness / seeds | determinism check + seeds 0-29 (notebook Phase 5 §5.6(c)) |
| **§6** software / resources | report Sec. VIII-D/E (MATLAB vs Python, timing analysis E6) |
| **§6** missing / ambiguous details | report Sec. VIII-E, Table VII |
| **§6** our changes / deviations | report Sec. VIII-E, Table VII; notebook Phase 5 §5.6(f) |
| **§6** fair comparison, valid arguments | E4 fair protocol + ablation, E5 Wilcoxon tests, E7 method-level claims (report Sec. VIII-B/C/D) |
| **§7** IEEE report with all 12 sections | `report/main.pdf` (I Introduction … X Conclusion, Abstract, References) |
| **§7** original vs. ours vs. modifications distinguished | report: [Original] / [Ours] / [Mod.] markers |
| **§7** IEEE reference style | `report/main.pdf`, References section |
| **§8** complete source code | `src/`, `experiments/`, `tests/` |
| **§8** README / execution instructions | `README.md` |
| **§8** required libraries | `requirements.txt` |
| **§8** dataset information / source | `maps/README.md`, `maps/index.csv`, `experiments/build_maps.py` |
| **§8** configuration and parameters | `configs/params.yaml` |
| **§8** experimental results | `results/phase2` … `results/phase5` |
| **§8** graphs / plots | `results/figures/` (all phases) |
| **§8** additional files | `docs/paper.pdf` (needed by the map builder), `notebooks/` |
