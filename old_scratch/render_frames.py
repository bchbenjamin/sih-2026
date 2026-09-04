import bpy
import sys

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render early frame (24)
bpy.context.scene.frame_set(24)
bpy.context.scene.render.filepath = 'frame_early.png'
bpy.ops.render.render(write_still=True)

# Render peak frame (48)
bpy.context.scene.frame_set(48)
bpy.context.scene.render.filepath = 'frame_peak.png'
bpy.ops.render.render(write_still=True)

# Render late frame (72)
bpy.context.scene.frame_set(72)
bpy.context.scene.render.filepath = 'frame_late.png'
bpy.ops.render.render(write_still=True)
