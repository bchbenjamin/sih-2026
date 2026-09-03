import os
import subprocess
import sys
from pathlib import Path

def run(*args, **kwargs):
    print(f"Running: {' '.join(args[0])}")
    subprocess.run(args[0], check=True, **kwargs)

def main():
    # Install anuga and rasterio
    run([sys.executable, "-m", "pip", "install", "anuga", "rasterio", "pyproj", "pyyaml", "shapely"])
    
    # Clone repo if not exists
    if not os.path.exists("sih-2026"):
        run(["git", "clone", "https://github.com/bchbenjamin/sih-2026.git"])
    
    os.chdir("sih-2026")
    run(["git", "pull"]) # Ensure latest
    
    # Write .env
    env_content = "FARFIELD_SOLVER_RUNNER=scripts/phase3/anuga_wrapper.py\n"
    env_content += "OPENTOPOGRAPHY_API_KEY=9a8e71191b57efed11ec8f8832dd62fb\n"
    Path(".env").write_text(env_content)
    
    # Extract data
    if os.path.exists("data.tar.gz"):
        print("Extracting data.tar.gz...")
        run(["tar", "-xzf", "data.tar.gz"])
        
    print("Executing pipeline...")
    result = subprocess.run([sys.executable, "run_pipeline.py", "--run", "--skip-acquisition", "--calibration", "breach_calibration.yaml"], 
                            capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    
    if result.returncode != 0:
        print("Pipeline failed!")
        sys.exit(result.returncode)
    
    print("Pipeline run on Colab completed successfully!")

if __name__ == "__main__":
    main()
