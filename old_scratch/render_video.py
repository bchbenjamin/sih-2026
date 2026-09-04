import bpy

bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.filepath = '/mnt/WindowsDrive/Fedora/Projects/Dam_Inundation/output/chorabari/dam_inundation_visualization.mp4'

# Optional: Set resolution to 1080p if it isn't already
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.resolution_percentage = 100

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 72
