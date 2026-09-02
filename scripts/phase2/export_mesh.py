#!/usr/bin/env python3
"""Invoke a real VisualSPHysics/Splashsurf wrapper; never emit placeholder OBJ."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", default=os.getenv("SPH_MESH_EXPORTER"))
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    case = yaml.safe_load((ROOT / "case_config.yaml").read_text())["case_name"]
    output = ROOT / "output" / case
    particle_dir, mesh_dir = output / "particles", output / "blender_mesh_sequence"
    if not args.run:
        print(f"Prepared mesh target {mesh_dir}; run with --run after DualSPHysics completes.")
        return
    if not list(particle_dir.glob("*.bi4")):
        raise SystemExit(f"No DualSPHysics .bi4 files in {particle_dir}")
    if not args.runner:
        raise SystemExit("Provide SPH_MESH_EXPORTER or --runner; placeholder OBJ files are prohibited.")
    mesh_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([shutil.which(args.runner) or args.runner, str(particle_dir), str(mesh_dir)], check=True)
    if not list(mesh_dir.glob("frame_*.obj")):
        raise SystemExit("Mesh exporter produced no frame_####.obj files")


if __name__ == "__main__":
    main()
