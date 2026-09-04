import bpy
terrain = bpy.data.objects.get("Terrain")
if terrain:
    print("Terrain dimensions:", terrain.dimensions)
    print("Terrain location:", terrain.location)
