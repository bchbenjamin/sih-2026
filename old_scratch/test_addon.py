import bpy
import sys

# Add the addon directory to sys.path so it can be found
import sys
import os
sys.path.append(os.path.abspath("blender_addon"))

bpy.ops.preferences.addon_enable(module="dam_inundation_panel")
print("Addon enabled successfully!")

# Ensure it loads config without errors
bpy.ops.dam.load_config()
print("Config loaded!")
