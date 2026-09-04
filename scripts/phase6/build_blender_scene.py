"""Run with Blender: build terrain and animated water solely from prepared data."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def material(name, color, metallic=0.0, roughness=0.6, alpha=1.0):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, alpha)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, alpha)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if alpha < 1:
        shader.inputs["Alpha"].default_value = alpha
        try:
            result.surface_render_method = "DITHERED"  # Blender 4.2+
        except AttributeError:
            result.blend_method = "BLEND"  # Blender 3.x/4.0 compatibility
    return result


def mesh_object(name, vertices, faces, material_value):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material_value)
    mesh.update()
    object_value = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(object_value)
    return object_value


def grid_vertices(values, scale, x_cell_m, y_cell_m):
    rows, cols = values.shape
    return [((column - (cols - 1) / 2) * x_cell_m / scale,
             (row - (rows - 1) / 2) * y_cell_m / scale,
             values[row, column] / scale)
            for row in range(rows) for column in range(cols)]


def terrain_faces(rows, cols):
    return [(row * cols + column, row * cols + column + 1, (row + 1) * cols + column + 1, (row + 1) * cols + column)
            for row in range(rows - 1) for column in range(cols - 1)]


def water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m):
    wet = (depth > 0) & np.isfinite(arrival) & (arrival <= elapsed)
    rows, cols = terrain.shape
    vertices = []
    faces = []
    
    vertex_index = np.full((rows + 1, cols + 1), -1, dtype=np.int32)
    
    for r in range(rows):
        for c in range(cols):
            if wet[r, c]:
                corners = [(r, c), (r, c+1), (r+1, c+1), (r+1, c)]
                face = []
                for cr, cc in corners:
                    if vertex_index[cr, cc] == -1:
                        vertex_index[cr, cc] = len(vertices)
                        x = (cc - 0.5 - (cols - 1) / 2) * x_cell_m / scale
                        y = (cr - 0.5 - (rows - 1) / 2) * y_cell_m / scale
                        
                        z_sum = 0
                        z_count = 0
                        for dr, dc in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < rows and 0 <= nc < cols and wet[nr, nc]:
                                z_sum += (terrain[nr, nc] + depth[nr, nc]) / scale
                                z_count += 1
                        z = z_sum / z_count if z_count > 0 else 0
                        
                        vertices.append((x, y, z))
                    face.append(vertex_index[cr, cc])
                faces.append(tuple(face))
                
    return vertices, faces


def key_visibility(obj, frame, visible):
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=frame)


def import_nearfield_sequence(sequence_dir, water_material, frames):
    """Import real IsoSurface OBJ frames, if DualSPHysics produced them."""
    obj_paths = sorted(sequence_dir.glob("frame_*.obj"))
    for frame, path in enumerate(obj_paths[:frames], start=1):
        try:
            bpy.ops.wm.obj_import(filepath=str(path))
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=str(path))
        obj = bpy.context.selected_objects[-1]
        obj.name = f"NearFieldSPH_{frame:04d}"
        obj.data.materials.clear()
        obj.data.materials.append(water_material)
        for other in range(1, frames + 1):
            key_visibility(obj, other, other == frame)


def main():
    # Keep Blender free of PyYAML: pass DAM_CASE_NAME for a non-default case.
    case = os.environ.get("DAM_CASE_NAME", "rishiganga")
    viz = ROOT / "output" / case / "viz_data"
    metadata_path, data_path = viz / "metadata.json", viz / "flood_visualization.npz"
    if not metadata_path.exists() or not data_path.exists():
        raise RuntimeError("Run prepare_viz_data.py before opening Blender.")
    metadata = json.loads(metadata_path.read_text())
    arrays = np.load(data_path)
    terrain, depth, arrival = arrays["terrain_m"], arrays["depth_m"], arrays["arrival_s"]
    scale, frames = metadata["scene_scale_m_per_unit"], metadata["frames"]
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    x_cell_m, y_cell_m = metadata["x_cell_m"], metadata["y_cell_m"]
    terrain_material = material("Terrain", (0.13, 0.22, 0.08), roughness=0.95)
    water_material = material("Flood water", (0.02, 0.16, 0.52), metallic=0.15, roughness=0.18, alpha=0.72)
    terrain_object = mesh_object("Terrain", grid_vertices(terrain, scale, x_cell_m, y_cell_m), terrain_faces(*terrain.shape), terrain_material)
    terrain_object["raster_shape"] = list(terrain.shape)
    terrain_object["scene_size_x"] = (terrain.shape[1] - 1) * x_cell_m / scale
    terrain_object["scene_size_y"] = (terrain.shape[0] - 1) * y_cell_m / scale
    terrain_object["terrain_role"] = "Mantaflow effector when DAM_VISUAL_MODE=mantaflow"
    duration = metadata["simulation_duration_s"]
    for frame in range(1, frames + 1):
        elapsed = duration * (frame - 1) / (frames - 1)
        vertices, faces = water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m)
        if not faces:
            continue
        water = mesh_object(f"Flood_{frame:04d}", vertices, faces, water_material)
        for other in range(1, frames + 1):
            key_visibility(water, other, other == frame)
    import_nearfield_sequence(ROOT / "output" / case / "blender_mesh_sequence", water_material, frames)
    bounds = metadata["bounds"]
    lon_mid, lat_mid = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2
    building_materials = {"none": material("Building intact", (0.55, 0.55, 0.52)),
                          "low": material("Building low", (0.85, 0.7, 0.1)),
                          "moderate": material("Building moderate", (0.9, 0.32, 0.06)),
                          "severe": material("Building severe", (0.55, 0.03, 0.02))}
    for building in json.loads((viz / "buildings.json").read_text()):
        x = (building["lon"] - lon_mid) * 111_320 * math.cos(math.radians(lat_mid)) / scale
        y = (lat_mid - building["lat"]) * 111_320 / scale
        row = min(max(round((y * scale / y_cell_m) + (terrain.shape[0] - 1) / 2), 0), terrain.shape[0] - 1)
        col = min(max(round((x * scale / x_cell_m) + (terrain.shape[1] - 1) / 2), 0), terrain.shape[1] - 1)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, terrain[row, col] / scale + 0.5))
        building_object = bpy.context.object
        building_object.name = f"Building_{building['id']}"
        building_object.dimensions = (0.7, 0.7, 1.0)
        damage_class = building["damage_class"]
        target = building_materials.get(damage_class, building_materials["none"])
        if damage_class != "none" and building.get("arrival_time_s"):
            animated = target.copy()
            animated.name = f"{target.name}_{building['id']}"
            shader = animated.node_tree.nodes.get("Principled BSDF")
            shader.inputs["Base Color"].default_value = (0.55, 0.55, 0.52, 1)
            shader.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=1)
            try:
                arrival_frame = max(1, min(frames, round(float(building["arrival_time_s"]) / duration * frames)))
            except ValueError:
                arrival_frame = frames
            shader.inputs["Base Color"].default_value = target.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
            shader.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=arrival_frame)
            building_object.data.materials.append(animated)
        else:
            building_object.data.materials.append(target)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 100))
    bpy.context.object.rotation_euler = (math.radians(25), math.radians(-20), math.radians(25))
    scene_span = max(terrain_object["scene_size_x"], terrain_object["scene_size_y"])
    bpy.ops.object.camera_add(location=(0, -scene_span * 1.3, scene_span * 0.9))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.data.lens = 40
    camera.data.clip_end = 100_000
    direction = -camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, frames
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 60
    scene["input_verification"] = metadata["input_verification"]
    scene["water_source"] = metadata["water_source"]
    scene["coordinate_origin"] = "Local false origin at raster centre; never raw latitude/longitude Blender coordinates."
    if os.environ.get("DAM_VISUAL_MODE", "raster").casefold() == "mantaflow":
        # Ensure local script directories are on sys.path so Blender's bundled
        # Python can import repository modules when invoked with `--python`.
        import sys
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parents[2]
        sys.path.insert(0, str(script_dir))
        sys.path.insert(0, str(repo_root))
        from mantaflow_scene import setup as setup_mantaflow
        hydrograph_path = ROOT / "output" / case / "hydrograph.csv"
        if not hydrograph_path.exists():
            hydrograph_path = ROOT / "output" / case / "standalone" / "hydrograph.csv"
        if not hydrograph_path.exists():
            raise RuntimeError(f"Mantaflow visual mode requires {hydrograph_path}")
        
        # Get scaling and breach location from environment
        discharge_ratio = float(os.environ.get("DAM_DISCHARGE_RATIO", "1.0"))
        b_lat = float(os.environ.get("DAM_BREACH_LAT", "30.745"))
        b_lon = float(os.environ.get("DAM_BREACH_LON", "79.055"))
        
        # Convert breach lat/lon to Blender coordinates
        bx = (b_lon - lon_mid) * 111_320 * math.cos(math.radians(lat_mid)) / scale
        by = (lat_mid - b_lat) * 111_320 / scale
        b_row = min(max(round((by * scale / y_cell_m) + (terrain.shape[0] - 1) / 2), 0), terrain.shape[0] - 1)
        b_col = min(max(round((bx * scale / x_cell_m) + (terrain.shape[1] - 1) / 2), 0), terrain.shape[1] - 1)
        bz = terrain[b_row, b_col] / scale
        
        setup_mantaflow(terrain_object, hydrograph_path, scale, duration, (bx, by, bz), discharge_ratio, water_material)
        scene["mantaflow_note"] = "Presentation only; raster output remains the hydrodynamic source of truth."
    destination = ROOT / "output" / case / "dam_inundation_visualization.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
