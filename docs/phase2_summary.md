# Phase 2 - Dataset reconstruction summary (2026-10-23)

- Paper maps reconstructed: 4 evaluation maps + 4 tuning maps
- Source: PDF figures (800 dpi)
- Sub-figure agreement with consensus: min 99.984 %, mean 99.999 %
- tune_d density: 20.0 % (paper 20 %)
- Optimal length = best published grid length on 4/4 maps
- Diagonal rule confirmed: corner cutting allowed (A16)
- Paper's A* on Map D is sub-optimal (103.297 vs optimum 102.125) -> non-admissible heuristic
- Random maps: 120 (30 seeds x 4 sizes)

Files:
  - maps/.gitkeep
  - maps/README.md
  - maps/index.csv
  - maps/map_A_20.json
  - maps/map_A_20.txt
  - maps/map_B_40.json
  - maps/map_B_40.txt
  - maps/map_C_60.json
  - maps/map_C_60.txt
  - maps/map_D_80.json
  - maps/map_D_80.txt
  - maps/tune_a.json
  - maps/tune_a.txt
  - maps/tune_b.json
  - maps/tune_b.txt
  - maps/tune_c.json
  - maps/tune_c.txt
  - maps/tune_d.json
  - maps/tune_d.txt
  - maps/random/ (120 maps)
  - src/map_digitizer.py, src/grid_map.py, src/reference_planner.py, src/random_maps.py
  - results/phase2/*.csv, results/figures/phase2_*.png