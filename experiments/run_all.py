"""Run every Phase 4 experiment from the command line:

    python -m experiments.run_all --repeats 30
"""
from __future__ import annotations
import argparse
import time

from experiments import run_weight_sweep, run_main, run_ablation, run_random, run_method_claims, analysis_timing, run_calibration


def main(repeats=30):
    t = time.time()
    run_calibration.run(); print(f"calibration (Phase 3) done ({time.time()-t:.1f}s)")
    run_weight_sweep.run(repeats=max(3, repeats // 3)); print(f"E1 weight sweep done ({time.time()-t:.1f}s)")
    run_main.run(repeats=repeats, verbose=False); print(f"E2/E3 main done ({time.time()-t:.1f}s)")
    analysis_timing.run(); print(f"E6 timing analysis done ({time.time()-t:.1f}s)")
    run_ablation.run(repeats=max(3, repeats // 3)); print(f"E4 ablation done ({time.time()-t:.1f}s)")
    run_random.run(repeats=3); print(f"E5 random maps done ({time.time()-t:.1f}s)")
    run_method_claims.run(); print(f"E7 method-level claims done ({time.time()-t:.1f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=30)
    main(ap.parse_args().repeats)
