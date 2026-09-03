"""Top-level Mantaflow shim for Blender import compatibility.

This mirrors `scripts/phase6/mantaflow_scene.py` but lives at the repository
top level so Blender's bundled Python can import it when executing the
`build_blender_scene.py` script.
"""
from __future__ import annotations

from pathlib import Path
import csv


def setup(terrain_object, hydrograph_path: Path, scale: float, duration: float) -> None:
    import bpy

    hydro = Path(hydrograph_path)
    if not hydro.exists():
        raise RuntimeError(f"Missing hydrograph for Mantaflow demo: {hydro}")

    times = []
    flows = []
    try:
        with hydro.open() as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                try:
                    times.append(float(row[0]))
                    flows.append(float(row[1]) if len(row) > 1 else 0.0)
                except Exception:
                    continue
    except Exception:
        raise RuntimeError(f"Failed to read hydrograph: {hydro}")

    scene = bpy.context.scene
    scene["mantaflow_shim"] = True
    scene["mantaflow_hydro_points"] = len(times)
    scene["mantaflow_peak_flow_m3s"] = float(max(flows) if flows else 0.0)

    emitter_name = "MantaflowEmitter"
    if emitter_name in bpy.data.objects:
        emitter = bpy.data.objects[emitter_name]
    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        emitter = bpy.context.object
        emitter.name = emitter_name

    try:
        emitter.parent = terrain_object
    except Exception:
        pass

    scene["mantaflow_note"] = (
        "Mantaflow shim: placeholder emitter created; replace with real Mantaflow "
        "integration for production visualisations."
    )
