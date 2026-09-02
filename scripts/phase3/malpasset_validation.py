#!/usr/bin/env python3
"""Gate a far-field solver run against a supplied Malpasset gauge series."""
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
    parser.add_argument("--observed", type=Path, required=True, help="CSV: time_s,water_level_m")
    parser.add_argument("--model", type=Path, required=True, help="CSV: time_s,water_level_m")
    parser.add_argument("--tolerance-pct", type=float, default=15.0)
    args = parser.parse_args()
    obs_t, obs_v = read_series(args.observed, "water_level_m")
    model_t, model_v = read_series(args.model, "water_level_m")
    error = max_relative_error(obs_t, obs_v, model_t, model_v)
    result = {"benchmark": "Malpasset observed gauge time series", "observed": str(args.observed),
              "model": str(args.model), "metric": "maximum relative water-level error",
              "error_percentage": error, "tolerance_percentage": args.tolerance_pct,
              "status": "PASS" if error <= args.tolerance_pct else "FAIL"}
    output = ROOT / "validation" / "malpasset_check.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
