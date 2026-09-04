import bpy
import sys
import os
import time

sys.path.append(os.path.abspath("blender_addon"))
bpy.ops.preferences.addon_enable(module="dam_inundation_panel")

bpy.ops.dam.load_config()
print("Loaded Config!")

# Click Run Pipeline
bpy.ops.dam.run_pipeline()

settings = bpy.context.scene.dam_settings
print("Waiting for pipeline to finish...")
while "Done!" not in settings.status and "Error" not in settings.status:
    time.sleep(1)
    print(f"Status: {settings.status}")

print(f"Final Status: {settings.status}")
