# Phase 4 - Experiment summary (2026-10-23)
Runtime 39 s on Linux-6.18.44-fc-v153-x86_64-with-glibc2.39; Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1; timing = median of 30 runs.

E1  weight sweep: ours fewest nodes at omega=0.6; omega=0.5 ranks #4/11; paper: 0.5 best. Node-curve Spearman 0.63.
E2  baselines: exact length 14/16, exact turns 13/16;
    VNS-BA* nodes [89, 195, 255, 368] vs paper [100, 252, 257, 355]; turns [5, 7, 4, 15] vs [4, 4, 4, 14].
E3  paper setting: VNS-BA* fewer turns in 16/16 comparisons; mean turn improvement 48.4% (paper 55.3%);
    4-metric comprehensive 34.7% (paper 29.4%).
E4  fair comparison: mean turn improvement drops to 18.6%, 4-metric comprehensive to 13.3%.
E5  random 80x80: vs BA* nodes +41.8% (p=2.35e-06); vs BA*+prune+smooth turns -10.8% (p=0.0136), length -1.6% (p=3.05e-05).
E6  published time vs our iterations Spearman 0.90; vs our time 0.23.
