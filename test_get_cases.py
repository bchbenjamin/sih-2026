import bpy
import sys
import os

sys.path.append(os.path.abspath("blender_addon"))
bpy.ops.preferences.addon_enable(module="dam_inundation_panel")

# Let's directly call get_cases to see what it finds
import dam_inundation_panel
cases = dam_inundation_panel.get_cases(None, None)
print(f"FOUND CASES: {cases}")
