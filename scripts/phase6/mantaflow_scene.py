"""Blender-side Mantaflow setup used by ``build_blender_scene.py``.

Mantaflow is presentation-only.  The hydrodynamic source of truth remains the
far-field depth/arrival rasters.  The conversion below prevents the common
error of assigning prototype m³/s directly to a Blender property:

    visual_volume_per_frame_BU3 = Qprototype[m3/s] * seconds_per_frame / scale_m_per_BU**3

The flow object is scaled from this visual volume.  It is deliberately capped
for scene stability; it is not a calibrated discharge boundary condition.
"""
from __future__ import annotations

import csv
from pathlib import Path

import bpy
import numpy as np


def hydrograph(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or {"time_s", "discharge_m3s"} - set(rows[0]):
        raise RuntimeError(f"{path} must have time_s,discharge_m3s columns")
    return (np.asarray([float(row["time_s"]) for row in rows]),
            np.asarray([float(row["discharge_m3s"]) for row in rows]))


def configure_effector(terrain):
    bpy.context.view_layer.objects.active = terrain
    terrain.select_set(True)
    bpy.ops.object.modifier_add(type="FLUID")
    modifier = terrain.modifiers[-1]
    modifier.fluid_type = "EFFECTOR"
    terrain.select_set(False)


def configure_domain(location, dimensions, resolution=48):
    bpy.ops.mesh.primitive_cube_add(location=location)
    domain = bpy.context.object
    domain.name = "MantaflowDomain_VISUAL_ONLY"
    domain.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type="FLUID")
    modifier = domain.modifiers[-1]
    modifier.fluid_type = "DOMAIN"
    bpy.context.view_layer.update()
    settings = modifier.domain_settings
    settings.domain_type = "LIQUID"
    settings.resolution_max = resolution
    settings.cache_type = "MODULAR"
    settings.cache_frame_start = 1
    settings.cache_frame_end = bpy.context.scene.frame_end
    settings.cache_data_format = "OPENVDB"
    domain.display_type = "WIRE"
    return domain


def configure_inflow(location, hydrograph_path: Path, scale_m_per_unit: float, duration_s: float):
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    inflow = bpy.context.object
    inflow.name = "MantaflowInflow_VISUAL_ONLY"
    inflow.dimensions = (1.0, 1.0, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type="FLUID")
    modifier = inflow.modifiers[-1]
    modifier.fluid_type = "FLOW"
    bpy.context.view_layer.update()
    settings = modifier.flow_settings
    settings.flow_type = "LIQUID"
    settings.flow_behavior = "INFLOW"
    settings.surface_distance = 1.5
    times, discharges = hydrograph(hydrograph_path)
    seconds_per_frame = duration_s / max(scene.frame_end - scene.frame_start, 1)
    for frame in range(scene.frame_start, scene.frame_end + 1):
        time_s = duration_s * (frame - scene.frame_start) / max(scene.frame_end - scene.frame_start, 1)
        discharge = max(0.0, float(np.interp(time_s, times, discharges)))
        volume_per_frame = discharge * seconds_per_frame / scale_m_per_unit ** 3
        # A cube side is the cube root of volume. This changes only visual
        # emitter occupancy; it is not a physical unit conversion for the solver.
        side = float(np.clip(volume_per_frame, 0.002, 0.30) ** (1.0 / 3.0))
        inflow.scale = (side, side, side)
        inflow.keyframe_insert(data_path="scale", frame=frame)
    return inflow


def setup(terrain, hydrograph_path: Path, scale_m_per_unit: float, duration_s: float):
    scene_size_x, scene_size_y = terrain["scene_size_x"], terrain["scene_size_y"]
    configure_effector(terrain)
    domain = configure_domain((0, 0, 1.5), (scene_size_x * 1.05, scene_size_y * 1.05, 4.0))
    inflow = configure_inflow((-scene_size_x * 0.42, 0, 1.0), hydrograph_path,
                              scale_m_per_unit, duration_s)
    return domain, inflow
