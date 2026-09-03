# Stoker Dam Break Validation

This directory contains the validation case `CaseDambreakVal2D` which simulates a classical 2D dam break over a dry bed. The analytical reference is calculated using the exact closed-form solution derived by Ritter (1892).

## DualSPHysics Version Constraints

**IMPORTANT:** We explicitly use **DualSPHysics v4.4** (instead of the modern v5.x branch) due to execution constraints in our automated Google Colab workflow. 

Specifically:
- Precompiled standalone Linux binaries (that do not require a developer registration wall) are sourced from the `DesignSPHysics` v0.5.1 open-source distribution.
- The `DesignSPHysics` distribution bundles **v4.4** CPU binaries, and does not provide an out-of-the-box Linux GPU binary in its tarball.
- Because `GenCase` v4 cannot parse modern v5 XML configurations, we have checked out `CaseDambreakVal2D_Def.xml` directly from the official `v4.4.007` tag in the DualSPHysics GitHub repository.

If you are running this manually on a workstation with modern DualSPHysics v5+ installed, you will need to replace this XML with the v5 equivalent from the `examples/main/01_DamBreak/` directory.

## Replication Instructions

To replicate the validation run on any Linux environment (local or VM), follow these steps exactly:

### 1. Prerequisites
Ensure you have Python 3 and Git installed on your system.

### 2. Prepare the Repository
Clone the repository to your workspace:
```bash
git clone https://github.com/bchbenjamin/sih-2026.git
cd sih-2026
```

### 3. Generate Analytical Reference
Generate the analytical reference CSV for the Ritter (1892) solution. This script is path-independent and will automatically write to `cases/stoker/stoker_analytical_reference.csv`:
```bash
python3 scripts/phase2/generate_stoker_analytical.py
```

### 4. Run the Validation (Colab / VM)
If you are running in an ephemeral environment (like a fresh Colab VM), you can use the unified provisioning script. This script automatically:
- Downloads and extracts the `DesignSPHysics` v4.4 CPU binaries.
- Adjusts execution permissions and configures `LD_LIBRARY_PATH` to link `libChronoEngine.so`.
- Runs `GenCase4`, `DualSPHysics4.4CPU_linux64`, and `MeasureTool4`.
- Compares the `MeasureTool` output against the generated reference.

To run the unified script:
```bash
python3 scripts/cloud/dualsphysics_colab.py
```

### 5. Review Output
The validation script will dump a JSON result to `validation/stoker_check_chorabari.json`. The run is considered a `PASS` if the maximum relative wave-height error is within the configured tolerance threshold (default: 10%).

All simulation data is stored in `cases/stoker/stoker_out/`.
