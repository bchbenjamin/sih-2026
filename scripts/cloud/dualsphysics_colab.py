# Run this in a Google Colab GPU instance
import os
import subprocess
import urllib.request
import tarfile

def setup_dualsphysics():
    # 1. Download DesignSPHysics binaries (which includes DualSPHysics binaries)
    print("Downloading precompiled DualSPHysics Linux binaries from DesignSPHysics...")
    url = "https://github.com/DualSPHysics/DesignSPHysics/releases/download/0.5.1/release-linux.tar.gz"
    urllib.request.urlretrieve(url, "release-linux.tar.gz")
    
    # 2. Extract
    print("Extracting...")
    with tarfile.open("release-linux.tar.gz", "r:gz") as tar:
        tar.extractall("DualSPHysics")
        
    # 3. Make binaries executable (path depends on where tar extracts to)
    # The binaries should be inside DualSPHysics directory or its subdirectories
    print("Setting permissions...")
    # Using bash to blindly chmod all binaries in the extraction folder
    subprocess.run("find DualSPHysics -type f -exec chmod +x {} \\;", shell=True)
        
    print("DualSPHysics is ready.")

def run_stoker_validation():
    print("Running Stoker validation...")
    # NOTE: You will need to clone your Dam_Inundation repo to the Colab environment
    # and provide the path to the repo here.
    repo_path = "/content/Dam_Inundation"
    
    stoker_case_dir = os.path.join(repo_path, "cases", "stoker")
    
    # Note: Adjust these binary paths based on where they actually unpack
    # from the DesignSPHysics tarball. Often they are inside a folder like:
    # DualSPHysics/linux64/GenCase ... 
    
    print("Running GenCase...")
    subprocess.run(["find DualSPHysics -name 'GenCase' -exec {} " + 
                    f"{os.path.join(stoker_case_dir, 'stoker_Def.xml')} " + 
                    "stoker_out/stoker \\;"], shell=True, check=True)
                    
    print("Running DualSPHysics on GPU...")
    subprocess.run(["find DualSPHysics -name 'DualSPHysics5.2' -exec {} " + 
                    "stoker_out/stoker stoker_out -dirout stoker_out \\;"], shell=True, check=True)
                    
    # (Assuming tools extract wave height to a CSV file)
    
    print("Evaluating analytical error...")
    subprocess.run(["python3", os.path.join(repo_path, "scripts", "phase2", "stoker_validation.py"),
                    "--reference", os.path.join(stoker_case_dir, "stoker_analytical_reference.csv"),
                    "--model", "stoker_out/stoker_model_output.csv",
                    "--case", "chorabari"], check=True)

if __name__ == "__main__":
    setup_dualsphysics()
    # Uncomment and run once the repo is cloned
    # run_stoker_validation()
