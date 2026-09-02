# SIH26161 — Dam Break Inundation Modelling

This repository is the compute backend for a **counterfactual** catastrophic
breach of the post-event Rishiganga debris-dammed lake. It is not a replay of
the 7 February 2021 Chamoli flood.

It deliberately does not manufacture hydrodynamic results. A valid run needs a
real EPSG:4326 DEM, OSM exposure data, cited breach calibration, DualSPHysics
for SPH, and Delft3D FM (or ANUGA after the agreed time-box) for far-field
routing. Generated artefacts are ignored and must be regenerated from inputs.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export OPENTOPOGRAPHY_API_KEY=...
python3 scripts/phase1/run_phase1.py
cp config/breach_calibration.example.yaml breach_calibration.yaml
# Fill every null field with cited/calibrated values before continuing.
python3 scripts/phase2/breach_parameters.py --calibration breach_calibration.yaml
python3 scripts/phase2/scale_config.py
python3 scripts/audit_contract.py
```

`breach_parameters.py` emits `NEEDS_CALIBRATION` until a cited YAML file
supplies breach width, duration, erodibility, and citation. The tracked
template contains null values on purpose: published lake dimensions alone
cannot establish breach geometry.

## Solver integration

The near-field driver produces a machine-readable DualSPHysics manifest and
only invokes a site wrapper when explicitly requested:

```bash
python3 scripts/phase2/run_case.py
python3 scripts/phase2/run_case.py --run --runner /path/to/dualsphysics-wrapper
```

The wrapper receives the manifest path and must run GenCase, DualSPHysics,
FlowTool, and IsoSurface. `scale_config.yaml` provides the Froude conversion:
`Qprototype = Qmodel × Lr^2.5`. Raw real-world m³/s values must never be
directly assigned to a Blender/Mantaflow flow-rate setting.

Run `python3 scripts/audit_contract.py --strict` before damage/comparison
reporting. Every source-backed and derived case value is in
[sources.md](data/rishiganga/sources.md). Raw data, output, Blender files,
particle data, caches, validation output, and credentials are excluded by
`.gitignore`.

## Blender visualisation

After the far-field outputs exist, prepare the data and build the scene:

```bash
python3 scripts/phase6/prepare_viz_data.py
blender --background --python scripts/phase6/build_blender_scene.py
```

For a local preview of legacy outputs that fail the audit, add
`--allow-unverified` to the first command. This stamps the `.blend` as an
unverified preview; do not use it for analysis or presentation claims.
