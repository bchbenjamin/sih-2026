import bpy
import sys
import os

sys.path.append(os.path.abspath("blender_addon"))
bpy.ops.preferences.addon_enable(module="dam_inundation_panel")

with open("breach_calibration.yaml", "w") as f:
    f.write("breach_time_s: null\nbreach_width_m: null\nerodibility: medium\ncitation: ''\n")

settings = bpy.context.scene.dam_settings

try:
    bpy.ops.dam.load_config()
except Exception as e:
    import traceback
    traceback.print_exc()

