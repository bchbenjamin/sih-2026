import bpy
import mathutils
import sys

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])

obj = bpy.data.objects.get("Flood_0048")
if not obj:
    print("Flood_0048 object not found!")
    sys.exit(1)

dg = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(dg)

verts = len(eval_obj.data.vertices)
polys = len(eval_obj.data.polygons)

world_corners = [(eval_obj.matrix_world @ mathutils.Vector(corner)) for corner in eval_obj.bound_box]
xs = [c.x for c in world_corners]
ys = [c.y for c in world_corners]

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

width_x = max_x - min_x
width_y = max_y - min_y

print(f"--- Flood_0048 Stats ---")
print(f"Vertices: {verts}")
print(f"Faces (Polys): {polys}")
print(f"Bounding Box X: {min_x:.2f} to {max_x:.2f} (width: {width_x:.2f} blender units)")
print(f"Bounding Box Y: {min_y:.2f} to {max_y:.2f} (width: {width_y:.2f} blender units)")

scene_scale = 100.0  # From metadata.json
print(f"Estimated Physical Width X: {width_x * scene_scale:.2f} m")
print(f"Estimated Physical Width Y: {width_y * scene_scale:.2f} m")
