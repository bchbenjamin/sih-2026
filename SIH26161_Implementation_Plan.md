# SIH26161 — Dam Break Inundation Modelling: Detailed Implementation Plan

**Problem statement:** SIH26161, "Dam Break Inundation Modelling Using Hydrodynamic Modelling of any River" — Sponsor: NTRO — Track: Software / Disaster Management

**PS-mandated requirements this plan satisfies:**
- Simulation via Smooth Particle Hydrodynamics (SPH) *and* Delft3D models, with scenario comparison (Deliverable i)
- Customizable framework accepting different input datasets (Deliverable ii)
- Dashboard/GUI with `.shp`/`.kml` output — **deferred**, this plan covers the compute backend only, built with exportability in mind
- Near-real-time framework via Google Earth Engine (Deliverable iv) — **separately owned track**, noted at the end
- Final demo on real, open-source Indian river/dam data (Deliverable v)

This document is written for agentic AI coding assistants to execute directly. Every phase specifies: inputs, outputs, concrete tools/commands, validation criteria, and the exact file contract handed to the next phase. Do not skip validation steps — treat a failed benchmark check as a blocking failure, not a warning.

---

## Session Handoff / Context for Agents (read this before writing any code)

**This is a continuation of existing work, not a fresh start.** Repo/scene files from a prior agent session already exist. Before producing anything new:
1. Audit every file against the Data Contract Summary table at the end of this document. For each expected file, report: exists / missing / exists-but-looks-like-a-placeholder.
2. Do not trust a prior agent's numeric outputs at face value, even if the file exists and looks populated — a prior run on this project produced a Blender animation with a physically implausible vertical "spike" instead of a graded flood surge, most likely from a raw m³/s discharge value being fed into Mantaflow's flow-rate parameter without unit/scale conversion. Treat every number currently in `case_config.yaml`, `hydrograph.csv`, and any breach-parameter output as unverified until traced back to its source.

**Mandatory sourcing discipline (this was missing before, and it's why the last run couldn't be checked):** every numeric value written into `case_config.yaml` must be traceable to an actual citation, not silently computed or approximated by the agent. For each value, write a companion `/data/{case_name}/sources.md` with the format `field_name: value — source (paper/report title, table/figure reference)`. If a value cannot be sourced, use a formula from Phase 2.2 and label it explicitly as "derived via [formula name], not directly published," rather than presenting it as a sourced figure.

**Concrete sources for the Rishiganga case, so the agent doesn't need to re-search:**
- Shugar et al., 2021, *Science* — "A massive rock and ice avalanche caused the 2021 disaster at Chamoli, Indian Himalaya." Primary source for pre/post-event satellite-derived geometry and DEM differencing; check supplementary materials for elevation-change data.
- NDMA Joint Study Team report — "Detailed Report: Uttarakhand Disaster on 7th February 2021." Official ground-truthed impact and geomorphological assessment.
- ScienceDirect paper documenting the moraine-dammed lake geometry: ~700–800 m length, ~100 m front width, ~46 m depth — use these three figures directly for `lake_length_m`, `lake_front_width_m`, `lake_depth_m` in `case_config.yaml`, with this citation in `sources.md`.

**Blender-specific failure modes already encountered — bake these into Phase 6 explicitly, do not let the agent skip them:**
1. **Unit/scale mismatch causing a spike artifact.** The `hydrograph.csv` discharge values are real-world m³/s. There must be an explicit, documented conversion step between that CSV and whatever units Mantaflow's inflow object actually expects at the scene's working scale — write the conversion factor into code comments, do not feed the raw number in directly.
2. **Terrain not set as a collision/effector object.** The BlenderGIS terrain mesh must be explicitly configured as an effector for the Mantaflow domain, or water has nothing to flow across.
3. **Geometry disappearing when the viewport is zoomed out.** This is a BlenderGIS large-coordinate clipping issue, not a simulation limitation. Fix: (a) confirm BlenderGIS imports using a local/false origin near (0,0,0) rather than raw absolute lat/lon-derived coordinates, and (b) increase both the viewport Clip End (View tab) and the camera object's own Clip End to comfortably exceed the terrain's full extent.
4. **Mandatory smoke test before touching real terrain or real hydrograph data.** Build a small synthetic flat-plane test domain with a hand-picked, obviously-reasonable inflow rate first. Confirm water visibly flows and pools across the plane, does not spike vertically, and does not disappear on zoom-out. Only proceed to the real Rishiganga terrain and hydrograph after this test passes cleanly.

**Animation scope, confirmed for this project:** the Blender render should run from an intact first frame (dam/lake pre-breach) through the breach/surge/destruction sequence, ending on a held aftermath frame (post-event state, flooded or not, whatever the simulation actually produces) — it does not need to animate through full drainage. **This scoping applies to the Blender render only.** The underlying Phase 2–5 compute (DualSPHysics, Delft3D/ANUGA, damage analysis, comparison module) must still run across the full physical hydrograph time range regardless of the shorter render window — do not let the agent truncate the compute to match the visual.

---

## Phase 0 — Case Study Selection (blocking, do first)

**Recommendation: use a natural (landslide/moraine) dam, not an engineered one.** The PS's own Background section opens with natural dam/lake formations by name — Rishi Ganga (Feb 2021), Wapriyang (Nov 2021), Phuktal near Sumdo (Mar 2015) — before it even mentions engineered dams. Using one of the PS's own named examples is a genuine point in your favor with an evaluator who reads closely.

**Chosen case: Chamoli / Rishiganga, Uttarakhand — 7 February 2021.** Of the three PS-named natural-dam examples, this one has by far the strongest public dataset: a peer-reviewed Science paper (Shugar et al., 2021) with satellite-derived pre/post geometry, an official NDMA joint study team report, and published lake dimensions (~700–800 m length, ~100 m front width, ~46 m depth). See Phase 1 for exact sources.

**Important framing nuance, document this in the pitch:** the catastrophic 7 Feb event was primarily a rock-ice avalanche/debris flow, with landslide damming of the Raunthi Gad / Rishiganga as a contributing mechanism, not a single clean dam-break. The moraine-dammed lake that formed afterward is well-characterized geometrically but drained naturally, without a catastrophic breach. Frame this project as **scenario generation** — "what if this real, well-characterized dammed lake had failed catastrophically" — which is explicitly within PS scope ("simulation modelling for flash flood and scenario generation"). Do not present it as a replay of an observed inundation; use Malpasset (Phase 3.3) as the far-field validation case instead, since Rishiganga itself gives you no real breach-flood dataset to validate against.

**Output contract:** a `case_config.yaml` at the repo root containing:
```yaml
case_name: string
dam_name: string                    # e.g. "Rishiganga moraine-dammed lake"
dam_coordinates: [lat, lon]
dam_type: string                    # "natural" / "landslide" / "moraine" — NOT earthfill/gravity/arch
formation_mechanism: string         # e.g. "rock-ice avalanche debris damming, 7 Feb 2021"
formation_date: string
blocking_material: string           # e.g. "rock/ice/debris" — affects breach formula choice, see Phase 2.2
lake_length_m: float
lake_front_width_m: float
lake_depth_m: float
reservoir_volume_m3: float          # derive from lake dimensions if not directly published
river_name: string
downstream_reach_km: float          # how far downstream to model
dem_source: string                  # SRTM / Cartosat-1 / ICESat-2 / Shugar et al. supplementary data
dem_bbox: [min_lon, min_lat, max_lon, max_lat]
```
Every later phase reads this file. Do not hardcode case details elsewhere.

---

## Phase 1 — Data Acquisition

**Natural-dam-specific sources for the Rishiganga case (start here):**
1. **Shugar et al., 2021, Science** — "A massive rock and ice avalanche caused the 2021 disaster at Chamoli, Indian Himalaya" — the primary source for pre/post-event satellite-derived geometry and DEM differencing. Check the supplementary materials for elevation-change data usable as a DEM input.
2. **NDMA (National Disaster Management Authority) Joint Study Team detailed report** — "Uttarakhand Disaster on 7th February 2021" — official Indian government report, ground-truthed impact and geomorphological assessment.
3. **ScienceDirect paper on the moraine-dammed lake** (Shugar et al.-referenced lake geometry study) — gives the ~700–800 m length / ~100 m front width / ~46 m depth figures to seed `lake_length_m`, `lake_front_width_m`, `lake_depth_m` in `case_config.yaml`.
4. **Planet Labs / Sentinel-2 imagery** of the Rishiganga valley, before and after 7 Feb 2021, for visual terrain confirmation and BlenderGIS overlay texture — freely browsable via Sentinel Hub EO Browser even without a Planet account.
5. **ICESat-2** elevation profiles — referenced in multiple published geospatial studies of this event, useful for elevation cross-checks in the near-field zone specifically.

**General agent tasks (apply regardless of final case chosen):**
1. Download DEM for `dem_bbox` (SRTM via OpenTopography API or USGS EarthExplorer as baseline; supplement with the Shugar et al. supplementary elevation-change data for the near-field zone specifically, since 30 m SRTM alone won't capture a landslide-scale event well).
2. Download/derive river cross-section or bathymetry data if available (CWC data portals, or approximate from DEM if unavailable — flag as an approximation in output metadata).
3. Acquire land-use/land-cover and building footprint data for the downstream reach (OpenStreetMap via Overpass API is the fastest reliable free source for building footprints in India; note the downstream Rishiganga/Dhauliganga reach also has hydropower infrastructure, e.g. Rishiganga and Tapovan Vishnugad, worth including explicitly as high-value exposure points given they were struck in the real event).
4. Acquire approximate population data if available (WorldPop gridded data, open access).

**Output contract:**
```
/data/{case_name}/dem.tif                  # georeferenced, EPSG:4326
/data/{case_name}/buildings.geojson        # footprints with at least: id, geometry, lat, lon
/data/{case_name}/landuse.geojson
/data/{case_name}/population_grid.tif      # optional, if available
```

**Validation:** confirm DEM covers the full `dem_bbox`, confirm CRS is EPSG:4326 or reproject, confirm no-data gaps aren't present in the breach/near-field zone specifically (data gaps far downstream are more tolerable).

---

## Phase 2 — Near-Field: DualSPHysics (SPH requirement)

### 2.1 Setup
- Install DualSPHysics (GPU build, CUDA required — confirm AWS GPU instance has compatible drivers before this phase).
- Build breach geometry: dam cross-section at `case_config.yaml` dimensions, breach opening per chosen dam-type failure mode.
- **Scale discipline:** this phase runs at **model scale**, not prototype scale. Choose a model scale factor (e.g. 1:20 to 1:50 depending on dam size vs computational cost) and apply **Froude similarity** consistently:
  - Length scale: `Lr`
  - Velocity scale: `Vr = sqrt(Lr)`
  - Time scale: `Tr = sqrt(Lr)`
  - Discharge scale: `Qr = Lr^2.5`
  
  Record the chosen `Lr` in a `scale_config.yaml` — every downstream consumer of near-field output must know this value to rescale back to prototype scale.

### 2.2 Breach parameters
- **Do not use Froehlich's (1995) formula as the primary estimate** — it's calibrated on engineered earthfill dam failures, not landslide/moraine dams, and `case_config.yaml`'s `dam_type` for this case is natural. Use a landslide-dam-specific breach formula instead — **Walder & O'Connor (1997)** or **Peng & Zhang (2012)**, both derived from landslide/moraine dam failure case databases — based on `blocking_material`, `lake_depth_m`, and `reservoir_volume_m3` from `case_config.yaml`.
- Froehlich's formula can still be computed as a secondary cross-check for order-of-magnitude sanity, but the landslide-dam formula's output is the one that feeds the case XML.
- Feed this as the initial/boundary condition for the DualSPHysics case XML.

### 2.3 Run
```
GenCase → {case_name}_Def.xml → DualSPHysics5.x_linux64_GPU → output .bi4 particle files
```

### 2.4 Validation (blocking)
- Before trusting this on the real case geometry, run the standard **Stoker dam-break analytical solution** case (flat bed, instantaneous break, no friction) and compare DualSPHysics output against the closed-form solution. This is one of DualSPHysics's own canonical validation cases — use it as a pass/fail gate, not a one-time sanity check. Store the comparison plot and max error % in `/validation/stoker_check_{case_name}.json`.
- Fail condition: error beyond an agreed tolerance (e.g. >10% on peak wave height/arrival time) — halt and debug the case setup before proceeding, do not proceed to Phase 3 on a failed validation.

### 2.5 Post-processing → hydrograph extraction
- Run `FlowTool` on the .bi4 output at the breach cross-section to extract the outflow discharge time series.
- **Rescale to prototype scale** using the `Tr`/`Qr` factors from `scale_config.yaml`.
- Sanity-check the rescaled peak discharge against the landslide-dam breach formula output from 2.2 — they should be in the same order of magnitude; large divergence means either the breach setup or the rescaling is wrong.

**Output contract:**
```
/output/{case_name}/hydrograph.csv     # columns: time_s (prototype scale), discharge_m3s
/output/{case_name}/scale_config.yaml
/validation/stoker_check_{case_name}.json
```

### 2.6 Post-processing → mesh for Blender
- Run `IsoSurface` on the .bi4 output to generate VTK polydata surface meshes per timestep (marching-cubes mode for quality, not point-splatting).
- Convert to Blender-importable format via one of:
  - **VisualSPHysics** (official DualSPHysics-affiliated Blender toolkit) — preferred, purpose-built for this exact pipeline.
  - **Splashsurf** (Rust-based VTK→OBJ converter) — leaner fallback if VisualSPHysics setup proves time-consuming.

**Output contract:**
```
/output/{case_name}/blender_mesh_sequence/frame_####.obj (or VisualSPHysics native format)
```

---

## Phase 3 — Far-Field: Delft3D FM (primary) / ANUGA (time-boxed fallback)

### 3.1 Decision gate
Attempt Delft3D FM first. **Hard time-box: set an explicit number of days at project kickoff.** If the kernel is not building and running a basic test case cleanly by the deadline, switch to ANUGA and do not revisit Delft3D FM until the rest of the pipeline is working end-to-end.

### 3.2a Primary path: Delft3D FM
- Build D-Flow FM kernel from source on Linux (Deltares/Delft3D GitHub repo, `DIMRset` tagged release — do not use `main` branch, it may be incompatible with the current GUI/tooling versions).
- Use `hydrolib-core` and `dfm_tools` (Deltares' own Python packages) to programmatically generate:
  - The 2D unstructured mesh over the downstream reach, from `dem.tif`
  - Boundary conditions: inflow at the dam location driven by `hydrograph.csv` from Phase 2
  - `dimr_config.xml` for headless execution
- Run headless via `run_dimr.sh` (no GUI required — GUI is Windows-only and has current licensing issues in the open-source release; the compute kernel does not need it).

### 3.2b Fallback path: ANUGA
- `pip install anuga`
- Build the 2D unstructured mesh directly in Python from `dem.tif`
- Set the dam-location boundary as a time-varying inflow from `hydrograph.csv`
- Run via ANUGA's Python API, fully scriptable, no separate kernel build required

### 3.3 Validation (blocking)
- Where feasible, benchmark against the **Malpasset dam-break historical dataset** (well-documented case with real gauge measurements) using either tool, to confirm the far-field solver is behaving sensibly, before trusting real-case output.
- At minimum, sanity-check wave arrival time and peak depth against basic physical expectations (arrival time roughly consistent with flood-wave celerity `sqrt(g*h)`).

**Output contract (same schema regardless of which tool was used, so downstream phases don't care which path was taken):**
```
/output/{case_name}/farfield_depth.tif      # max depth raster, EPSG:4326
/output/{case_name}/farfield_velocity.tif   # max velocity raster
/output/{case_name}/farfield_arrival.tif    # arrival time raster (seconds from breach)
/output/{case_name}/solver_used.txt         # "delft3d_fm" or "anuga", for reporting
```

---

## Phase 4 — Comparison Module ("compare the scenario" requirement)

This is the direct answer to the PS's explicit comparison requirement — do not skip or treat as optional.

**Run two scenarios on the same case:**
1. **Hybrid:** Phase 2 (DualSPHysics near-field) → Phase 3 (Delft3D/ANUGA far-field), as above.
2. **Standalone:** Delft3D/ANUGA run alone across the *entire* domain including the near-field breach zone, using only the landslide-dam-formula-derived hydrograph directly (no SPH detail).

**Compute and report deltas between the two runs:**
- Peak discharge and arrival time at the breach cross-section
- Peak depth and arrival time at 2–3 downstream points (e.g. nearest village, a mid-reach point, the reach boundary)
- Damage/exposure numbers (Phase 5) computed separately for each scenario

**Output contract:**
```
/output/{case_name}/comparison_report.json   # structured deltas as above
/output/{case_name}/comparison_report.md     # human-readable summary for the pitch/demo
```

This produces a genuine, defensible finding for the demo: quantifying what near-field SPH detail changes versus a standalone far-field-only model — not just two disconnected numbers.

---

## Phase 5 — Damage & Exposure Analysis

**Inputs:** `farfield_depth.tif`, `farfield_arrival.tif`, `buildings.geojson`, `population_grid.tif` (if available)

**Per building:**
- Sample max depth and arrival time at each building's centroid from the rasters
- Classify: e.g. low (<0.5m), moderate (0.5–2m), severe (>2m) — thresholds should be documented and justified, not arbitrary

**Output contract:**
```
/output/{case_name}/damage.csv
# columns: building_id, lon, lat, max_depth_m, arrival_time_s, damage_class
```

Run this once per scenario from Phase 4 (hybrid and standalone) for the comparison.

---

## Phase 6 — Blender Visualization Layer

**This phase consumes Phase 2, 3, and 5 outputs. It is purely a visualization consumer — it must never become a second source of truth for the numbers.**

### 6.1 Terrain
- Use the **BlenderGIS** add-on to import real elevation + imagery for `dem_bbox` directly into Blender (same source as `dem.tif` in Phase 1, ideally re-derived through BlenderGIS directly for consistency of coordinate handling).

### 6.2 Near-field
- Import the `blender_mesh_sequence/` from Phase 2.6 (VisualSPHysics or Splashsurf output) at the correct location/orientation matching the real dam coordinates.

### 6.3 Far-field
- Set up a **Mantaflow** domain over the downstream terrain.
- Drive the domain's inflow object emission rate from `hydrograph.csv` (Phase 2.5, prototype-scale), keyframed or scripted via a CSV-driving Python script inside Blender.
- Optionally cross-check the resulting Mantaflow flood extent visually against `farfield_depth.tif`/`farfield_arrival.tif` from Phase 3 — they won't match exactly (Mantaflow is not a validated hydrodynamic solver) but gross mismatches (flood going the wrong direction, wildly wrong timing) indicate a setup error worth catching before the demo.

### 6.4 Destruction
- Load `damage.csv` from Phase 5.
- For each building object placed at its real coordinates, trigger a visual effect (rigid-body collapse, or a depth/class-based color tint) at the frame corresponding to its `arrival_time_s`, scaled to the animation's frame rate.

### 6.5 Demo output
- Bake the Mantaflow simulation and render a flythrough animation (Eevee, real-time capable) for the pitch video.
- For the demo round specifically: exporting `.shp`/`.kml` directly from Blender's baked flood-surface geometry is acceptable as a placeholder, since accuracy isn't required for this round — but flag this clearly in code comments as a throwaway path, since the actual export source of truth is `farfield_depth.tif`/`damage.csv` from Phases 3 and 5, and the dashboard should read from those directly once built, not from Blender.

---

## Phase 7 — Google Earth Engine Near-Real-Time Framework (Deliverable iv)

**Separately owned track — does not block Phases 0–6.**

Rough shape: a GEE script/app that pulls near-real-time satellite imagery (e.g. Sentinel-1 SAR for flood detection, since it works through cloud cover) for the same case-study river reach, to demonstrate the "near-real-time" half of the requirement independent of the physics-based simulation above. This is a distinct deliverable, not an extension of Phases 2–4, and should be scoped and assigned to whoever isn't on the simulation backend.

---

## Phase 8 — Infrastructure (Free-tier GPU notebooks — AWS EC2 dropped)

AWS EC2 was the original plan, but new-account GPU instance quota requests can take 1-2 days to approve, which is an unacceptable blocker on a hackathon timeline. **Use Colab free tier as primary, Kaggle Notebooks as backup.**

### 8.1 Real constraints, plan around these
- Colab free sessions cap at ~12 hours and disconnect after ~90 minutes idle. Nothing survives a session end unless explicitly saved elsewhere.
- GPU is not guaranteed on the free tier — under heavy demand you may get a CPU-only runtime with no GPU at all. Have Kaggle ready as a same-day fallback for this.
- No sudo/install persistence — every session is a fresh container. Cache anything expensive to rebuild (compiled binaries) to Drive.

### 8.2 Persistence: Google Drive as the S3-equivalent
Mount Drive at the start of every session and treat it as durable storage for the repo, DEM data, particle output, and any compiled binaries:
```python
from google.colab import drive
drive.mount('/content/drive')
!nvidia-smi        # confirm GPU actually assigned this session, not just requested
!git clone https://github.com/bchbenjamin/sih-2026.git /content/drive/MyDrive/sih-2026
```

### 8.3 DualSPHysics on Colab
DualSPHysics distributes precompiled Linux binaries (dual.sphysics.org/downloads) — download and try that first:
```python
!wget <precompiled Linux GPU binary URL from dual.sphysics.org/downloads>
!chmod +x DualSPHysics5.x_linux64
```
If it fails to run (glibc/gcc version mismatch between Colab's Ubuntu and the binary's build environment is a real possibility), fall back to building from source using DualSPHysics's own Makefile (clone the repo, set `DIRTOOLKIT` to Colab's CUDA path, `make`) — Colab ships `nvcc` by default. Either way, **cache the resulting binary to Drive** so it doesn't need to be re-downloaded or rebuilt every session.

### 8.4 Delft3D FM vs ANUGA — reconsidered given free-tier constraints
A from-source Delft3D FM build fighting session ephemerality on top of everything else is a lot of friction for a free-tier workflow. **Shorten the original Phase 3.1 time-box, or default to ANUGA outright** rather than treating it as a last-resort fallback — ANUGA is pure Python (`pip install anuga`), trivially survives a session reset with no rebuild step, and fits the free-tier reality far better than a kernel that needs compiling from source each time storage isn't guaranteed to persist cleanly.

### 8.5 Blender on Colab
Install via apt or a precompiled tarball, run headless the same way as originally planned (`blender --background --python scripts/phase6/build_blender_scene.py`). Cycles GPU rendering (CUDA/OptiX) should work headless on Colab's T4. Eevee's OpenGL/EGL headless requirement is uncertain in Colab's container specifically — **test with a trivial scene early**, same principle as the mandatory flat-plane smoke test in the Session Handoff section above, before relying on it for a real bake.

### 8.6 Kaggle Notebooks as backup
Same general workflow as Colab (free GPU, no card required), but with a more predictable weekly GPU quota (~30 hrs/week) rather than Colab's variable allocation. Keep this ready specifically for days Colab won't grant a GPU at all — don't wait until you're blocked to set up a Kaggle account.

---

## Data Contract Summary (for agents working on different phases in parallel)

| File | Produced by | Consumed by |
|---|---|---|
| `case_config.yaml` | Phase 0 | All phases |
| `dem.tif`, `buildings.geojson`, `population_grid.tif` | Phase 1 | Phases 2, 3, 5, 6 |
| `hydrograph.csv`, `scale_config.yaml` | Phase 2 | Phases 3, 6 |
| `blender_mesh_sequence/` | Phase 2 | Phase 6 |
| `farfield_depth.tif`, `farfield_velocity.tif`, `farfield_arrival.tif` | Phase 3 | Phases 5, 6 |
| `damage.csv` | Phase 5 | Phases 6, (future dashboard) |
| `comparison_report.json/.md` | Phase 4 | Pitch/demo materials |

Every file listed above should carry CRS metadata (EPSG:4326) from the point of creation — do not defer CRS handling to a later "export" step, since that's exactly the kind of thing that silently breaks once multiple phases are touching the same geometry.

---

## Open Decisions Still Needed From the Team

1. Confirm Rishiganga/Chamoli 2021 as the final case (recommended in Phase 0), or pick between the other two PS-named natural-dam examples (Wapriyang Nov 2021, Phuktal near Sumdo Mar 2015) if the team prefers — note both have materially less published data than Rishiganga, so budget extra Phase 1 time if chosen
2. GEE track owner (Phase 7)
3. Model-scale factor `Lr` for the DualSPHysics near-field run (Phase 2.1) — note the near-field geometry here is a landslide-blocked valley, not a constructed dam cross-section, so breach geometry setup in GenCase will look different from a typical DualSPHysics dam-break tutorial case
4. Explicit day-count for the Delft3D FM time-box (Phase 3.1)
