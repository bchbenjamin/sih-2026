#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, **kwargs):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)

def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    
    # 1. Commit and push current configuration changes (if any)
    try:
        subprocess.run(["git", "commit", "-am", "Auto-commit from pipeline"], check=False)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError:
        print("Git operations failed or nothing to commit. Proceeding...")

    # 2. Run on Colab with GPU
    colab_bin = root / ".venv" / "bin" / "colab"
    run_command([str(colab_bin), "run", "--gpu", "T4", "--timeout", "3600", "run_on_colab.py"])
    
    # 3. Download results
    print("Downloading results...")
    run_command([str(colab_bin), "download", "/content/output_results.tar.gz", "output_results.tar.gz"])
    run_command(["tar", "-xzf", "output_results.tar.gz"])
    
    # 4. Trigger prepare_viz_data.py
    print("Preparing viz data...")
    run_command([sys.executable, "scripts/phase6/prepare_viz_data.py"])
    
    # 5. Trigger Blender scene rebuild
    print("Rebuilding Blender scene...")
    run_command([sys.executable, "run_pipeline.py", "--phase", "6"])

    print("Remote pipeline execution and local visualization data processing completed successfully.")

if __name__ == "__main__":
    main()
