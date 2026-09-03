#!/usr/bin/env python3
"""Bootstrap a persistent project checkout in a Google Colab session.

Run this from a Colab cell after copying it into the runtime, for example:
``!python scripts/cloud/colab_bootstrap.py --repo-url https://github.com/<org>/<repo>.git``.
It mounts Drive before cloning so solver outputs and compiled binaries survive
the ephemeral runtime.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def command(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(list(args), cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--drive-dir", default="MyDrive/sih-2026")
    parser.add_argument("--skip-pull", action="store_true")
    args = parser.parse_args()
    try:
        from google.colab import drive
    except ImportError as error:
        raise SystemExit("This bootstrap is for Google Colab. Use the Kaggle instructions in docs/free_tier_notebooks.md.") from error
    drive.mount("/content/drive")
    if shutil.which("nvidia-smi"):
        command("nvidia-smi")
    else:
        print("WARNING: no GPU runtime assigned. Switch Colab runtime or use Kaggle before Phase 2.")
    checkout = Path("/content/drive") / args.drive_dir
    if (checkout / ".git").is_dir():
        if not args.skip_pull:
            command("git", "pull", "--ff-only", cwd=checkout)
    elif checkout.exists() and any(checkout.iterdir()):
        raise SystemExit(f"{checkout} exists but is not a Git checkout; choose another --drive-dir.")
    else:
        checkout.parent.mkdir(parents=True, exist_ok=True)
        command("git", "clone", args.repo_url, str(checkout))
    command("python", "-m", "pip", "install", "-r", "requirements.txt", cwd=checkout)
    print(f"Ready: {checkout}")
    print("Set DUALSPHYSICS_ROOT to the Drive-cached binary directory before Phase 2.")


if __name__ == "__main__":
    main()
