import bpy
import sys
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])

cam = bpy.data.objects.get("Camera")
if cam:
    cam.location = (8.0, -35.0, 75.0)  # Move it way above the terrain!
    
    target = Vector((8.0, 0.0, 38.0))  # Terrain Z is ~38 here
    direction = target - cam.location
    
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
    cam.rotation_mode = 'XYZ'
    
    # Update the fcurves to match the new rotation
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            if fc.data_path == 'rotation_euler':
                # Remove the old point
                if len(fc.keyframe_points) > 0:
                    fc.keyframe_points.remove(fc.keyframe_points[0])
                # Add the new point with the new rotation
                fc.keyframe_points.insert(1, cam.rotation_euler[fc.array_index])

bpy.ops.wm.save_mainfile()
