import bpy
import math
from mathutils import Vector

bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.frame_set(48)

camera = bpy.data.objects.get("Camera")
if camera:
    camera.location = (8.0, -35.0, 15.0)
    target = (8.0, 0.0, 0.0)
    direction = Vector(target) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

bpy.context.scene.render.filepath = 'test_render_tight2.png'
bpy.ops.render.render(write_still=True)
