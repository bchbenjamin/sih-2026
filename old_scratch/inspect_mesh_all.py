import bpy
import mathutils
import sys

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
dg = bpy.context.evaluated_depsgraph_get()

for frame_num in [24, 48, 72]:
    obj = bpy.data.objects.get(f"Flood_{frame_num:04d}")
    if not obj:
        print(f"Flood_{frame_num:04d} object not found!")
        continue

    eval_obj = obj.evaluated_get(dg)
    verts = len(eval_obj.data.vertices)
    polys = len(eval_obj.data.polygons)

    world_corners = [(eval_obj.matrix_world @ mathutils.Vector(corner)) for corner in eval_obj.bound_box]
    xs = [c.x for c in world_corners]
    ys = [c.y for c in world_corners]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    print(f"--- Flood_{frame_num:04d} Stats ---")
    print(f"Vertices: {verts}, Faces: {polys}")
    print(f"Bounding Box X: {min_x:.2f} to {max_x:.2f} (width: {max_x - min_x:.2f})")
    print(f"Bounding Box Y: {min_y:.2f} to {max_y:.2f} (width: {max_y - min_y:.2f})")

