import numpy as np
import rasterio.features
from shapely.geometry import shape, MultiPolygon
from shapely.ops import triangulate

wet = np.array([[0, 1, 1],
                [0, 1, 0],
                [1, 1, 0]], dtype=np.uint8)
shapes = list(rasterio.features.shapes(wet, mask=wet))
polygons = [shape(geom) for geom, val in shapes]
merged = MultiPolygon(polygons)

triangles = triangulate(merged)
print("Triangles:", len(triangles))
print(triangles[0].exterior.coords[:])
