#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from damage_analysis import run

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    case = yaml.safe_load((ROOT / "case_config.yaml").read_text())["case_name"]
    hybrid, standalone = ROOT / "output" / case, ROOT / "output" / case / "standalone"
    if (hybrid / "farfield_depth.tif").exists():
        run(hybrid, hybrid / "damage.csv")
    else:
        print(f"Skipping hybrid damage analysis: {hybrid / 'farfield_depth.tif'} not found.")
    
    if (standalone / "farfield_depth.tif").exists():
        run(standalone, standalone / "damage.csv")
    else:
        print(f"Skipping standalone damage analysis: {standalone / 'farfield_depth.tif'} not found.")


if __name__ == "__main__":
    main()
