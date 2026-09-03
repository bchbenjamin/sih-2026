import os
import subprocess
import urllib.request
import tarfile
import sys
import shutil

def setup_dualsphysics():
    print("Downloading precompiled DualSPHysics Linux binaries from DesignSPHysics...")
    url = "https://github.com/DualSPHysics/DesignSPHysics/releases/download/0.5.1/release-linux.tar.gz"
    urllib.request.urlretrieve(url, "release-linux.tar.gz")
    
    print("Extracting...")
    with tarfile.open("release-linux.tar.gz", "r:gz") as tar:
        tar.extractall("DesignSPHysics")
        
    print("Setting permissions...")
    subprocess.run("find DesignSPHysics -type f -exec chmod +x {} \\;", shell=True)
    print("DualSPHysics binaries downloaded.")

def clone_repo():
    repo_url = "https://github.com/bchbenjamin/sih-2026.git"
    repo_path = "/content/Dam_Inundation"
    if os.path.exists(repo_path):
        print("Repo already exists, pulling latest...")
        subprocess.run(["git", "pull"], cwd=repo_path, check=True)
    else:
        print(f"Cloning repo from {repo_url}...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
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
    subprocess.run([ds_cpu, "-cpu", os.path.join(out_dir, "CaseDambreakVal2D"), out_dir], check=True)
    
    print("Running MeasureTool...")
    measuretool_out = os.path.join(out_dir, "measuretool")
    os.makedirs(measuretool_out, exist_ok=True)
    
    # Run measuretool to extract Swl_x02. CSV will be dumped. 
    # From the bash script we saw earlier:
    subprocess.run([measuretool, "-dirdata", data_dir, 
                    "-pointsdef:ptels[x=0.2:0:0.2,y=0:0:0,z=0:0.02:2.1]", 
                    "-onlytype:-all,+fluid", "-elevation", 
                    "-savevtk", os.path.join(measuretool_out, "EtaPoints"), 
                    "-savecsv", os.path.join(out_dir, "MeasuredA")], check=True)
                    
    # The output CSV is likely MeasuredA.csv. Wait, the stoker_validation.py wants --model stoker_model_output.csv
    shutil.copy(os.path.join(out_dir, "MeasuredA.csv"), os.path.join(out_dir, "stoker_model_output.csv"))
    
    print("Evaluating analytical error...")
    subprocess.run(["python3", os.path.join(repo_path, "scripts", "phase2", "stoker_validation.py"),
                    "--reference", os.path.join(stoker_case_dir, "stoker_analytical_reference.csv"),
                    "--model", os.path.join(out_dir, "stoker_model_output.csv"),
                    "--case", "chorabari"], check=True)

if __name__ == "__main__":
    setup_dualsphysics()
    repo_path = clone_repo()
    run_stoker_validation(repo_path)
