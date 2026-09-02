#!/usr/bin/env python3
"""Run Phase 1 atomically: a failed acquisition is a failure, not a fallback."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    for filename in ("download_dem.py", "download_buildings.py", "download_landuse.py"):
        subprocess.run([sys.executable, str(HERE / filename)], check=True)


if __name__ == "__main__":
    main()
