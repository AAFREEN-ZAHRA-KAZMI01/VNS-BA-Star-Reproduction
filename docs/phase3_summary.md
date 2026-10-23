# Phase 3 - Implementation summary (2026-10-23)
- Modules: geometry, neighborhood, search, postprocess, metrics, planners (src/)
- Unit tests: 81 passed in 1.31s
- Calibrated from baseline numbers only: A24 Manhattan heuristic for A*/BA*, A25 nodes = generated, A26 meeting rule
- Baselines on Maps A-D: exact length 14/16, exact turns 13/16,
  median node error 0.6%
- VNS-BA* turns [5, 7, 4, 15] (paper [4, 4, 4, 14]),
  nodes [89, 195, 255, 368] (paper [100, 252, 257, 355])
- Paper typo confirmed: Improved A* Map C = 945 deg with 18 turns (paper prints 7 turns)
