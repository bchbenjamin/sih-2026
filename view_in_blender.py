import bpy
import os

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import the OBJ
filepath = "/mnt/WindowsDrive/Fedora/Projects/Dam_Inundation/cases/stoker/stoker_out/surface/Surface_0100.obj"
if hasattr(bpy.ops.wm, "obj_import"):
    bpy.ops.wm.obj_import(filepath=filepath)
else:
    bpy.ops.import_scene.obj(filepath=filepath)

# Focus the view
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for region in area.regions:
            if region.type == 'WINDOW':
                override = {'area': area, 'region': region}
                bpy.ops.view3d.view_all(override)
