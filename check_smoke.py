import bpy
import os

bpy.ops.wm.open_mainfile(filepath="mantaflow_smoke_test.blend")

domain = bpy.data.objects.get("SmokeTestDomain")
inflow = bpy.data.objects.get("SmokeTestInflow")

print("\n--- SMOKE TEST DIAGNOSTICS ---")

# 1. Was it actually baked?
cache_dir = domain.modifiers["Fluid"].domain_settings.cache_directory
print(f"1. Cache directory path: {cache_dir}")
abs_cache_dir = bpy.path.abspath(cache_dir)
print(f"   Absolute path: {abs_cache_dir}")
print(f"   Directory exists: {os.path.exists(abs_cache_dir)}")
if os.path.exists(abs_cache_dir):
    print(f"   Files in directory: {os.listdir(abs_cache_dir)}")
print(f"   Has baked data (internal flag): {domain.modifiers['Fluid'].domain_settings.has_cache_baked_data}")

# 2. Is Flow Type Inflow?
print(f"\n2. Inflow Flow Type: {inflow.modifiers['Fluid'].flow_settings.flow_type}")
print(f"   Inflow Flow Behavior: {inflow.modifiers['Fluid'].flow_settings.flow_behavior}")

# 3. Does it overlap?
def get_bounds(obj):
    bbox = [obj.matrix_world @ mathutils.Vector(b) for b in obj.bound_box]
    xs = [v.x for v in bbox]
    ys = [v.y for v in bbox]
    zs = [v.z for v in bbox]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

import mathutils
d_bounds = get_bounds(domain)
i_bounds = get_bounds(inflow)
print(f"\n3. Domain bounds: X {d_bounds[0]}, Y {d_bounds[1]}, Z {d_bounds[2]}")
print(f"   Inflow bounds: X {i_bounds[0]}, Y {i_bounds[1]}, Z {i_bounds[2]}")
overlap = (d_bounds[0][0] <= i_bounds[0][1] and d_bounds[0][1] >= i_bounds[0][0] and
           d_bounds[1][0] <= i_bounds[1][1] and d_bounds[1][1] >= i_bounds[1][0] and
           d_bounds[2][0] <= i_bounds[2][1] and d_bounds[2][1] >= i_bounds[2][0])
print(f"   Overlaps: {overlap}")

# 4. Domain resolution
res = domain.modifiers["Fluid"].domain_settings.resolution_max
print(f"\n4. Domain resolution: {res}")
print("------------------------------\n")
