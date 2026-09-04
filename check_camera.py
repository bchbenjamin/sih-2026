import bpy

cam = bpy.data.objects.get("Camera")
print(f"Cam loc: {cam.location}")
print(f"Cam rot: {cam.rotation_euler}")
bpy.context.scene.frame_set(48)
print(f"Cam loc (fr 48): {cam.location}")
print(f"Cam rot (fr 48): {cam.rotation_euler}")
