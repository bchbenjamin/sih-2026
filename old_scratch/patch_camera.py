import re

with open('scripts/phase6/build_blender_scene.py', 'r') as f:
    content = f.read()

# The current camera shake block looks like this:
old_block = """    # Camera shake at frame 24 (when flood first arrives at dam)
    cam = bpy.data.objects.get("Camera")
    if cam:
        cam.rotation_mode = 'XYZ'
        for fc in cam.animation_data.action.fcurves:
            if fc.data_path == 'rotation_euler':
                mod = fc.modifiers.new(type='NOISE')
                mod.scale = 2.0
                mod.strength = 0.05
                mod.use_restricted_range = True
                mod.frame_start = 20
                mod.frame_end = 35
                mod.blend_in = 2
                mod.blend_out = 5"""

new_block = """    # Tight shot camera framing (looking down at dam)
    cam = bpy.data.objects.get("Camera")
    if cam:
        cam.location = (8.0, -35.0, 15.0)
        from mathutils import Vector
        direction = Vector((8.0, 0.0, 0.0)) - cam.location
        cam.rotation_mode = 'QUATERNION'
        cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
        cam.rotation_mode = 'XYZ'
        
        # Ensure it has animation data for fcurves
        if not cam.animation_data:
            cam.animation_data_create()
        if not cam.animation_data.action:
            cam.animation_data.action = bpy.data.actions.new("CameraAction")
        
        # Camera shake at frame 24
        for i in range(3):  # X, Y, Z euler
            fc = cam.animation_data.action.fcurves.new(data_path="rotation_euler", index=i)
            fc.keyframe_points.insert(1, cam.rotation_euler[i])
            mod = fc.modifiers.new(type='NOISE')
            mod.scale = 2.0
            mod.strength = 0.05
            mod.use_restricted_range = True
            mod.frame_start = 20
            mod.frame_end = 35
            mod.blend_in = 2
            mod.blend_out = 5"""

content = content.replace(old_block, new_block)

with open('scripts/phase6/build_blender_scene.py', 'w') as f:
    f.write(content)
