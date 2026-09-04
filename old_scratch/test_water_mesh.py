import numpy as np

def water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m):
    wet = (depth > 0) & np.isfinite(arrival) & (arrival <= elapsed)
    rows, cols = terrain.shape
    vertices = []
    faces = []
    
    # Pre-calculate vertex positions for cell corners
    # A cell at (row, col) has corners at:
    # top-left: (row, col), top-right: (row, col+1)
    # bottom-right: (row+1, col+1), bottom-left: (row+1, col)
    # But wait, vertices can be shared if we just use a grid of (rows+1, cols+1) vertices!
    
    # Yes! A grid of (rows+1, cols+1) vertices!
    vertex_index = np.full((rows + 1, cols + 1), -1, dtype=np.int32)
    
    # Find all corners that belong to a wet cell
    # A corner at (r, c) belongs to a wet cell if any of the 4 adjacent cells are wet
    wet_padded = np.pad(wet, 1, mode='constant', constant_values=False)
    # Corner (r, c) borders cells (r-1, c-1), (r-1, c), (r, c-1), (r, c)
    # In wet_padded, these are shifted by +1: (r, c), (r, c+1), (r+1, c), (r+1, c+1)
    
    for r in range(rows):
        for c in range(cols):
            if wet[r, c]:
                # Add the 4 corners of this cell if not already added
                corners = [(r, c), (r, c+1), (r+1, c+1), (r+1, c)]
                face = []
                for cr, cc in corners:
                    if vertex_index[cr, cc] == -1:
                        vertex_index[cr, cc] = len(vertices)
                        
                        # Calculate X, Y
                        # Cell center is at (c - (cols-1)/2), (r - (rows-1)/2)
                        # Corner is at (cc - 0.5 - (cols-1)/2), (cr - 0.5 - (rows-1)/2)
                        x = (cc - 0.5 - (cols - 1) / 2) * x_cell_m / scale
                        y = (cr - 0.5 - (rows - 1) / 2) * y_cell_m / scale
                        
                        # Calculate Z by averaging wet adjacent cells
                        z_sum = 0
                        z_count = 0
                        for dr, dc in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < rows and 0 <= nc < cols and wet[nr, nc]:
                                z_sum += (terrain[nr, nc] + depth[nr, nc]) / scale
                                z_count += 1
                        z = z_sum / z_count if z_count > 0 else 0
                        
                        vertices.append((x, y, z))
                    face.append(vertex_index[cr, cc])
                faces.append(tuple(face))
                
    return vertices, faces

# Test it
terrain = np.zeros((3, 3))
depth = np.ones((3, 3))
arrival = np.zeros((3, 3))
vertices, faces = water_mesh(terrain, depth, arrival, 1, 100, 10, 10)
print(f"Vertices: {len(vertices)}, Faces: {len(faces)}")
