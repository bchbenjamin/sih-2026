import os
from pathlib import Path
import subprocess
import urllib.request
import tarfile
import sys
import shutil

def mount_drive_if_colab():
    try:
        from google.colab import drive
        print("Google Colab detected. Mounting Google Drive for persistent storage...")
        drive.mount('/content/drive')
        drive_path = "/content/drive/MyDrive/sih-2026_workspace"
        os.makedirs(drive_path, exist_ok=True)
        os.chdir(drive_path)
        print(f"Working directory set to persistent storage: {os.getcwd()}")
    except ImportError:
        # Not in Colab, continue as normal
        pass

def setup_dualsphysics():
    if os.path.exists("DesignSPHysics"):
        print("DualSPHysics binaries already exist in persistent storage, skipping download.")
        return
        
    print("Downloading precompiled DualSPHysics Linux binaries from DesignSPHysics...")
    url = "https://github.com/DualSPHysics/DesignSPHysics/releases/download/0.5.1/release-linux.tar.gz"
    urllib.request.urlretrieve(url, "release-linux.tar.gz")
    
    print("Extracting...")
    with tarfile.open("release-linux.tar.gz", "r:gz") as tar:
        tar.extractall("DesignSPHysics")
        
    print("Setting permissions...")
    subprocess.run("find DesignSPHysics -type f -exec chmod +x {} \\;", shell=True)
    print("DualSPHysics binaries downloaded and cached.")

def clone_repo():
    # If the case file exists locally, we are running from the repo root
    if os.path.exists("cases/stoker/CaseDambreakVal2D_Def.xml"):
        print("Running from local repository root.")
        return os.getcwd()
    
    # Otherwise (e.g. in Colab), clone the repo to the current directory
    repo_url = "https://github.com/bchbenjamin/sih-2026.git"
    repo_path = os.path.join(os.getcwd(), "Dam_Inundation")
    if not os.path.exists(repo_path):
        print(f"Cloning repo from {repo_url}...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    else:
        print("Repo already exists, pulling latest...")
        subprocess.run(["git", "pull"], cwd=repo_path, check=True)
        
    return repo_path

def run_stoker_validation(repo_path):
    print("Running Stoker validation...")
    
    stoker_case_dir = os.path.join(repo_path, "cases", "stoker")
    xml_path_full = os.path.join(stoker_case_dir, "CaseDambreakVal2D_Def.xml")
    xml_path_noext = os.path.join(stoker_case_dir, "CaseDambreakVal2D_Def")
    
    if not os.path.exists(xml_path_full):
        print(f"ERROR: {xml_path_full} not found!")
        sys.exit(1)
        
    out_dir = os.path.join(stoker_case_dir, "stoker_out")
    os.makedirs(out_dir, exist_ok=True)
    data_dir = os.path.join(out_dir, "data")
    
    print("Locating binaries...")
    # Find GenCase and DualSPHysics
    gencase = subprocess.check_output("find DesignSPHysics -name 'GenCase*linux64' | head -n 1", shell=True, text=True).strip()
    ds_cpu = subprocess.check_output("find DesignSPHysics -name 'DualSPHysics*CPU*linux64' | head -n 1", shell=True, text=True).strip()
    measuretool = subprocess.check_output("find DesignSPHysics -name 'MeasureTool*linux64' | head -n 1", shell=True, text=True).strip()
    
    print(f"GenCase: {gencase}")
    print(f"DualSPHysics CPU: {ds_cpu}")
    print(f"MeasureTool: {measuretool}")
    
    print("Running GenCase...")
    subprocess.run([gencase, xml_path_noext, os.path.join(out_dir, "CaseDambreakVal2D"), "-save:all"], check=True)
    
    print("Running DualSPHysics on CPU...")
    ds_env = os.environ.copy()
    ds_env["LD_LIBRARY_PATH"] = os.path.dirname(ds_cpu) + ":" + ds_env.get("LD_LIBRARY_PATH", "")
    # Removed invalid -cpu flag, v4 DualSPHysics expects standard arguments
    subprocess.run([ds_cpu, os.path.join(out_dir, "CaseDambreakVal2D"), out_dir], check=True, env=ds_env)
    
    print("Running MeasureTool...")
    measuretool_out = os.path.join(out_dir, "measuretool")
    os.makedirs(measuretool_out, exist_ok=True)
    
    # Run measuretool to extract Swl_x02. CSV will be dumped. 
    # From the bash script we saw earlier:
    subprocess.run([measuretool, "-dirin", out_dir, 
                    "-points", os.path.join(repo_path, "probe_points.txt"), 
                    "-onlytype:-all,+fluid", "-height", 
                    "-savevtk", os.path.join(measuretool_out, "EtaPoints"), 
                    "-savecsv", os.path.join(out_dir, "MeasuredA")], check=True, env=ds_env)
                    
    # The output CSV is likely MeasuredA.csv. Wait, the stoker_validation.py wants --model stoker_model_output.csv
    shutil.copy(os.path.join(out_dir, "MeasuredA.csv"), os.path.join(out_dir, "stoker_model_output.csv"))
    
    print("Evaluating analytical error...")
    subprocess.run(["python3", os.path.join(repo_path, "scripts", "phase2", "stoker_validation.py"),
                    "--reference", os.path.join(stoker_case_dir, "stoker_analytical_reference.csv"),
                    "--model", os.path.join(out_dir, "stoker_model_output.csv"),
                    "--case", "chorabari",
                    "--t-min", "0.1", "--t-max", "0.2"], check=True)

if __name__ == "__main__":
    mount_drive_if_colab()
    setup_dualsphysics()
    repo_path = clone_repo()
    run_stoker_validation(repo_path)
