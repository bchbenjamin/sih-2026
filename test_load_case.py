import bpy
import sys
import os

sys.path.append(os.path.abspath("blender_addon"))
bpy.ops.preferences.addon_enable(module="dam_inundation_panel")

settings = bpy.context.scene.dam_settings

# Check if the fake case is found in the dropdown
import dam_inundation_panel
cases = dam_inundation_panel.get_cases(None, None)
print(f"FOUND CASES: {cases}")

# Select the fake case
settings.selected_case = "rishiganga_landslide_dam_2021_FAKE"

try:
    bpy.ops.dam.load_case()
    print("SUCCESS: Loaded case successfully.")
except Exception as e:
    print("FAILED TO LOAD CASE:")
    import traceback
    traceback.print_exc()
