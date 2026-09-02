#!/usr/bin/env python3
"""Prepare or launch a DualSPHysics near-field run; never fabricate SPH output."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", help="site wrapper receiving the generated manifest path")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    case = config["case_name"]
    output = ROOT / "output" / case
    breach = json.loads((output / "breach_params.json").read_text())
    scale = yaml.safe_load((output / "scale_config.yaml").read_text())
    if breach["status"] != "READY_FOR_SOLVER":
        raise SystemExit("Breach parameters need a cited calibration; refusing a misleading solver run.")
    manifest = {
        "backend": "dualsphysics", "case_name": case, "input_crs": "EPSG:4326",
        "prototype_parameters": breach["selected_parameters"], "froude_scaling": scale,
        "required_outputs": {"particle_files": "*.bi4", "hydrograph": "hydrograph.csv",
                             "mesh_sequence": "blender_mesh_sequence/frame_####.obj"},
        "postprocessing": ["FlowTool at breach cross-section", "rescale using Tr and Qr",
                           "IsoSurface marching-cubes mesh export"],
        "validation_gate": "validation/stoker_check_<case>.json must report PASS",
    }
    manifest_path = output / "dualsphysics_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {manifest_path}")
    if not args.run:
        return
    runner = args.runner or os.getenv("DUALSPHYSICS_RUNNER")
    if not runner:
        raise SystemExit("Set DUALSPHYSICS_RUNNER or pass --runner. It receives the manifest path.")
    subprocess.run([shutil.which(runner) or runner, str(manifest_path)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
