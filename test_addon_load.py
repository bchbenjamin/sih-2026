import bpy
import sys
import os
import traceback

sys.path.append(os.path.abspath("blender_addon"))
bpy.ops.preferences.addon_enable(module="dam_inundation_panel")

settings = bpy.context.scene.dam_settings

try:
    bpy.ops.dam.load_config()
    print(f"SUCCESS: use_regression={settings.use_regression}, width={settings.breach_width_m}, time={settings.breach_time_s}")
except Exception as e:
    print("FAILED TO LOAD CONFIG:")
    traceback.print_exc()
