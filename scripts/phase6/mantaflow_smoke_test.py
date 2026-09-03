"""Minimal flat-plane Mantaflow smoke-test scene.

Run in Blender first. It creates a local-origin plane, a liquid domain, an
effector, and a deliberately small inflow; bake it in the Physics cache UI (or
via your Blender version's bake operator) and inspect the resulting pool.
"""
from __future__ import annotations

def main():
    import bpy
    for item in list(bpy.data.objects):
        bpy.data.objects.remove(item, do_unlink=True)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    plane = bpy.context.object
    plane.name = "SmokeTestTerrainEffector"
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.modifier_add(type="FLUID")
    plane.modifiers[-1].fluid_type = "EFFECTOR"
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.5))
    domain = bpy.context.object
    domain.name = "SmokeTestDomain"
    domain.dimensions = (10, 10, 3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type="FLUID")
    domain.modifiers[-1].fluid_type = "DOMAIN"
    bpy.context.view_layer.update()
    settings = domain.modifiers[-1].domain_settings
    settings.domain_type = "LIQUID"
    settings.resolution_max = 32
    settings.cache_type = "MODULAR"
    settings.cache_frame_start, settings.cache_frame_end = 1, 80
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.5, 0, 0.7))
    inflow = bpy.context.object
    inflow.name = "SmokeTestInflow"
    inflow.scale = (0.35, 0.35, 0.35)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type="FLUID")
    inflow.modifiers[-1].fluid_type = "FLOW"
    bpy.context.view_layer.update()
    flow = inflow.modifiers[-1].flow_settings
    flow.flow_type, flow.flow_behavior = "LIQUID", "INFLOW"
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 80
    bpy.ops.object.camera_add(location=(9, -12, 8))
    camera = bpy.context.object
    camera.data.clip_end = 1000
    scene.camera = camera
    camera.rotation_euler = ((-camera.location).to_track_quat('-Z', 'Y').to_euler())
    scene["smoke_test"] = "Bake this small scene first; inspect for pooling and no vertical spike."
    bpy.ops.wm.save_as_mainfile(filepath="//mantaflow_smoke_test.blend")
    print("Saved mantaflow_smoke_test.blend. Bake and inspect before the real scene.")


if __name__ == "__main__":
    main()
