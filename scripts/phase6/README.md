# Phase 6 visualisation hand-off

This repository does not create a second hydrodynamic model in Blender. It
creates a display-only scene from the DEM and the validated far-field depth and
arrival rasters. Flood timing is represented by frame-specific mesh surfaces,
so Blender/Mantaflow never receives raw prototype m³/s values.

```bash
python3 scripts/phase6/prepare_viz_data.py
blender --background --python scripts/phase6/build_blender_scene.py
```

Or use `bash scripts/phase6/run_blender_visualization.sh`. Set `BLENDER_BIN`
when Blender is not on `PATH`.

Use `--allow-unverified` only to preview legacy files; the saved Blender scene
records this status. The script uses a local false origin and a large camera
clip distance. SHP/KML exports must still be produced from `farfield_depth.tif`
and `damage.csv`, not from display geometry.
