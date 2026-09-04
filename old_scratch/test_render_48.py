import bpy
bpy.context.scene.frame_set(48)
bpy.context.scene.render.filepath = 'test_plain_48.png'
bpy.ops.render.render(write_still=True)
