import bpy
import math
import sys

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.frame_set(48)

camera = bpy.data.objects.get("Camera")
if camera:
    # Dam is at Y ~ -22.7, X ~ 8
    # Let's put the camera just behind and above the dam, looking down at the surge
    camera.location = (8.0, -35.0, 15.0)
    
    # Point camera at the flood surge (which has advanced to Y ~ 0 by now)
    target = (8.0, 0.0, 0.0)
    
    # Calculate rotation
    dx = target[0] - camera.location.x
    dy = target[1] - camera.location.y
    dz = target[2] - camera.location.z
    
    dist_xy = math.sqrt(dx**2 + dy**2)
    rot_x = math.atan2(dist_xy, -dz)
    rot_z = math.atan2(dx, dy)
    
    # In Blender, Y is up/forward, Z is up in world, but camera points -Z in local.
    # Actually, let's just use a track-to constraint or look_at matrix
    
    from mathutils import Vector
    direction = Vector(target) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

bpy.context.scene.render.filepath = 'frame_48_tight.png'
bpy.ops.render.render(write_still=True)
