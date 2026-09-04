import bpy

terrain = bpy.data.objects.get("Terrain")
max_z = -1000
for v in terrain.data.vertices:
    world_pos = terrain.matrix_world @ v.co
    if world_pos.z > max_z:
        max_z = world_pos.z
print("Max Terrain Z:", max_z)
