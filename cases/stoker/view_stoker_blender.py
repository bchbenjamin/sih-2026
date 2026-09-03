import bpy
from pathlib import Path

def key_visibility(obj, frame, visible):
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=frame)

def import_nearfield_sequence(sequence_dir, frames):
    obj_paths = sorted(Path(sequence_dir).glob("frame_*.obj"))
    if not obj_paths:
        print("No OBJ files found!")
        return
        
    material = bpy.data.materials.new("Water")
    material.diffuse_color = (0.02, 0.16, 0.52, 0.72)
    
    for frame, path in enumerate(obj_paths[:frames], start=1):
        try:
            bpy.ops.wm.obj_import(filepath=str(path))
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=str(path))
        obj = bpy.context.selected_objects[-1]
        obj.name = f"NearFieldSPH_{frame:04d}"
        obj.data.materials.append(material)
        
        for other in range(1, frames + 1):
            key_visibility(obj, other, other == frame)

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import the sequence and keyframe it natively
sequence_dir = "/mnt/WindowsDrive/Fedora/Projects/Dam_Inundation/cases/stoker/stoker_out/blender_mesh_sequence"
import_nearfield_sequence(sequence_dir, 201)

# Save to .blend file (this allows it to run headless and avoids UI context errors)
output_path = "/mnt/WindowsDrive/Fedora/Projects/Dam_Inundation/cases/stoker/stoker_out/stoker_visualization.blend"
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"\nSaved {output_path} successfully!\n")
