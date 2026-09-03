#!/usr/bin/env python3
"""Prepare a far-field solver contract for Delft3D FM or ANUGA.

The solver itself is intentionally external. This prevents the former toy SWE
solver and its synthetic hydrograph from being reported as Delft3D/ANUGA.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("hybrid", "standalone"), required=True)
    parser.add_argument("--backend", choices=("delft3d_fm", "anuga"))
    parser.add_argument("--runner", help="wrapper receiving the generated manifest path")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    case = config["case_name"]
    backend = args.backend or config.get("execution", {}).get("farfield_backend", "delft3d_fm")
    root_output = ROOT / "output" / case
    output = root_output if args.scenario == "hybrid" else root_output / "standalone"
    hydrograph = root_output / "hydrograph.csv" if args.scenario == "hybrid" else output / "hydrograph.csv"
    dem = ROOT / "data" / case / "dem.tif"
    for required in (dem, hydrograph):
        if not required.exists() and args.run:
            if required == hydrograph and args.scenario == "hybrid":
                print(f"WARNING: Hybrid hydrograph missing ({required}). Skipping hybrid farfield execution.")
                return
            elif required == hydrograph and args.scenario == "standalone":
                # Synthesize the standalone formula hydrograph (triangular) from breach_params.json
                print(f"Synthesizing missing standalone hydrograph at {hydrograph}...")
                params_path = root_output / "breach_params.json"
                if not params_path.exists():
                    raise SystemExit(f"Cannot synthesize hydrograph: missing {params_path}")
                params = json.loads(params_path.read_text())
                q_peak = params["primary_method"]["peak_discharge_m3s"]
                volume = params["primary_method"]["inputs"]["lake_volume_m3"]
                t_peak = params["selected_parameters"]["breach_time_s"]
                # Triangular hydrograph: Area = 1/2 * base * Qp = Volume => base = 2 * Volume / Qp
                base_time = 2.0 * volume / q_peak
                hydrograph.parent.mkdir(parents=True, exist_ok=True)
                with open(hydrograph, 'w') as f:
                    f.write("time_s,discharge_m3s\n")
                    f.write(f"0.0,0.0\n")
                    f.write(f"{t_peak},{q_peak}\n")
                    f.write(f"{base_time},0.0\n")
            else:
                raise SystemExit(f"Missing required input: {required}")
    if dem.exists():
        with rasterio.open(dem) as dataset:
            if dataset.crs is None or dataset.crs.to_epsg() != 4326:
                raise SystemExit("DEM must be EPSG:4326")
    manifest = {
        "backend": backend, "scenario": args.scenario, "case_name": case,
        "dem": str(dem), "dem_crs": "EPSG:4326", "hydrograph": str(hydrograph),
        "boundary": "time-varying inflow at dam location", "dam_coordinates": config["dam_coordinates"],
        "required_outputs": ["farfield_depth.tif", "farfield_velocity.tif", "farfield_arrival.tif", "solver_used.txt"],
        "solver_used_must_equal": backend,
        "validation_gate": "Malpasset observed-data benchmark must PASS before scenario reporting",
    }
    output.mkdir(parents=True, exist_ok=True)
    path = output / "farfield_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {path}")
    if not args.run:
        return
    runner = args.runner or os.getenv("FARFIELD_SOLVER_RUNNER")
    if not runner:
        raise SystemExit("Set FARFIELD_SOLVER_RUNNER or pass --runner. It receives the manifest path.")
    subprocess.run([shutil.which(runner) or runner, str(path)], cwd=ROOT, check=True)
    marker = output / "solver_used.txt"
    if marker.read_text().strip() != backend:
        raise SystemExit(f"{marker} must contain exactly {backend!r}")


if __name__ == "__main__":
    main()
