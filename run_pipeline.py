#!/usr/bin/env python3
"""Explicit orchestration. Default mode prepares manifests, not fake outputs."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if key and key not in os.environ:
            os.environ[key] = value


def call(relative: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(ROOT / relative), *arguments], cwd=ROOT, check=True)


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=range(0, 7))
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--skip-acquisition", action="store_true")
    args = parser.parse_args()
    phases = {0: [], 1: ["scripts/phase1/run_phase1.py"],
              2: ["scripts/phase2/breach_parameters.py", "scripts/phase2/scale_config.py", "scripts/phase2/run_case.py"],
              3: ["scripts/phase3/run_farfield.py", "scripts/phase3/run_standalone.py"],
              4: ["scripts/phase4/comparison.py"], 5: ["scripts/phase5/run_damage_both_scenarios.py"], 6: []}
    for phase in ([args.phase] if args.phase is not None else list(phases)):
        if phase == 1 and args.skip_acquisition:
            continue
        for script in phases[phase]:
            invoke = args.run and script.endswith(("run_case.py", "run_farfield.py", "run_standalone.py"))
            call(script, *( ["--run"] if invoke else []))
    call("scripts/audit_contract.py")


if __name__ == "__main__":
    main()
