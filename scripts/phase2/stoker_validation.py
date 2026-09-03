#!/usr/bin/env python3
"""Gate a DualSPHysics Stoker run against its analytical reference series."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_timeseries import max_relative_error, read_series

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True, help="analytical CSV: time_s,wave_height_m")
    parser.add_argument("--model", type=Path, required=True, help="DualSPHysics CSV: time_s,wave_height_m")
    parser.add_argument("--tolerance-pct", type=float, default=10.0)
    parser.add_argument("--case", default="rishiganga")
    parser.add_argument("--t-min", type=float, default=0.0)
    parser.add_argument("--t-max", type=float, default=2.0)
    args = parser.parse_args()
    
    ref_t, ref_v = read_series(args.reference, "wave_height_m")
    model_t, model_v = read_series(args.model, "wave_height_m")
    
    # Restrict validation comparison to intended early-time window
    mask = (ref_t >= args.t_min) & (ref_t <= args.t_max)
    error = max_relative_error(ref_t[mask], ref_v[mask], model_t, model_v)
    result = {"benchmark": "Stoker dam-break analytical solution", "reference": str(args.reference),
              "model": str(args.model), "metric": "maximum relative wave-height error",
              "error_percentage": error, "tolerance_percentage": args.tolerance_pct,
              "status": "PASS" if error <= args.tolerance_pct else "FAIL"}
    output = ROOT / "validation" / f"stoker_check_{args.case}.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
