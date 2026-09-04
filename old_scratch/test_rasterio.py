import numpy as np
import rasterio.features

wet = np.array([[0, 1, 1],
                [0, 1, 0],
                [1, 1, 0]], dtype=np.uint8)
shapes = list(rasterio.features.shapes(wet, mask=wet))
print(shapes)
