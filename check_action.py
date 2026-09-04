import bpy

cam = bpy.data.objects.get("Camera")
action = cam.animation_data.action if cam.animation_data else None
if action:
    print(f"Camera uses action: {action.name}")
    print(f"Users of this action: {action.users}")
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action == action:
            print(f"Object {obj.name} uses this action!")

