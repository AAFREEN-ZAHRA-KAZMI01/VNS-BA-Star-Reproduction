# Phase 1 — Analysis summary (2026-10-23)

## Audit of published results
- Table 6: 6 of 80 improvement ratios inconsistent with Tables 2–5 (tolerance 0.1 pp).
  - vs A*, Map D, turn_angle_deg: printed 39.91%, recomputed 40.18%
  - vs Improved A* [28], Map C, length: printed 10.83%, recomputed 16.74%
  - vs Improved A* [28], Map D, nodes: printed 3.2%, recomputed -3.2%
  - vs Improved A* [28], Map D, length: printed 4.08%, recomputed 0.41%
  - vs BA*, Map C, length: printed 1.869%, recomputed 3.15%
  - vs BA*, Map D, turn_angle_deg: printed 50.15%, recomputed 37.69%
- Baseline turn angles not equal to turns×45°: 2 rows
  - Map C, Improved A* [28]: 7 turns but 945.0° (135.0°/turn)
  - Map C, Improved BA* [29]: 21 turns but 990.0° (47.14°/turn)
- Fig. 12 bars equal to mean of printed Table 6: 15/16
- Published timing spans 24.5–700.7 ms per expanded node → absolute times not reproducible.
- Table 1: (0.5, 0.5) minimises nodes and time, but not path length.

## Feasibility verdict
Feasible on a CPU (Colab). Main risks: map reconstruction accuracy, baseline re-implementation, 15 documented ambiguities
(7 high-impact).
