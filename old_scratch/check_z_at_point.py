import bpy

terrain = bpy.data.objects.get("Terrain")
min_dist = 100000
closest_z = 0
for v in terrain.data.vertices:
    world_pos = terrain.matrix_world @ v.co
    dist = (world_pos.x - 8.0)**2 + (world_pos.y - -35.0)**2
    if dist < min_dist:
        min_dist = dist
        closest_z = world_pos.z
print("Terrain Z near (8, -35):", closest_z)
