#!/usr/bin/env python3
"""ANUGA solver wrapper for Phase 3 Far-field scenario."""
import sys
import json
import csv
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import Transformer

def reproject_raster(src_path, dst_path, dst_crs):
    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        with rasterio.open(dst_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear)
        return transform, width, height

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: anuga_wrapper.py /path/to/farfield_manifest.json")
    
    manifest_path = Path(sys.argv[1])
    with open(manifest_path) as f:
        manifest = json.load(f)
        
    out_dir = manifest_path.parent
    dem_4326 = manifest['dem']
    dem_32644 = out_dir / "dem_32644.tif"
    
    # 1. Reproject DEM to EPSG:32644 (UTM 44N)
    print("Reprojecting DEM to EPSG:32644...")
    transform, width, height = reproject_raster(dem_4326, dem_32644, "EPSG:32644")
    
    # 2. Reproject Dam Coordinates
    dam_lat, dam_lon = manifest['dam_coordinates']
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    dam_x, dam_y = transformer.transform(dam_lon, dam_lat)
    
    print(f"Dam Coordinates in EPSG:32644: X={dam_x}, Y={dam_y}")
    
    import anuga
    
    # Read raster data for elevation
    with rasterio.open(dem_32644) as src:
        dem_data = src.read(1)
        nodata = src.nodata
        if nodata is not None:
            dem_data[dem_data == nodata] = np.nan
        # Fill nan with a high elevation or nearest
        dem_data = np.nan_to_num(dem_data, nan=np.nanmax(dem_data))
        
        dx = transform[0]
        dy = -transform[4]
        xllcorner = transform[2]
        yllcorner = transform[5] - (height * dy)
        width_m = width * dx
        height_m = height * dy
    
    print(f"Creating ANUGA domain: {width}x{height} ({width_m}m x {height_m}m)")
    # To avoid memory limits on large DEMs, we can downsample the domain size if it's too huge.
    # Let's cap the resolution to avoid ANUGA memory crash (ANUGA triangular meshes are heavy).
    # If width > 300, let's downsample the mesh.
    mesh_w, mesh_h = width, height
    scale = 1
    if mesh_w > 500:
        scale = mesh_w // 250
        mesh_w //= scale
        mesh_h //= scale
        print(f"Downsampling ANUGA mesh to {mesh_w}x{mesh_h} to save memory.")

    domain = anuga.rectangular_cross_domain(mesh_w, mesh_h, len1=width_m, len2=height_m)
    
    def elevation_fn(x, y):
        # x, y are numpy arrays of coordinates
        col = (x / dx).astype(int)
        row = ((height_m - y) / dy).astype(int)
        col = np.clip(col, 0, width - 1)
        row = np.clip(row, 0, height - 1)
        return dem_data[row, col]
        
    domain.set_quantity('elevation', elevation_fn)
    domain.set_quantity('friction', 0.05)
    
    # Boundary conditions
    Br = anuga.Reflective_boundary(domain)
    domain.set_boundary({'left': Br, 'right': Br, 'top': Br, 'bottom': Br})
    
    # Hydrograph
    times = []
    discharges = []
    with open(manifest['hydrograph']) as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row['time_s']))
            discharges.append(float(row['discharge_m3s']))
            
    def hydrograph_fn(t):
        return float(np.interp(t, times, discharges, right=0.0))
        
    rel_x = dam_x - xllcorner
    rel_y = dam_y - yllcorner
    print(f"Inlet center relative to domain: {rel_x}, {rel_y}")
    
    region = anuga.Region(domain, center=(rel_x, rel_y), radius=100.0)
    anuga.Inlet_operator(domain, region, Q=hydrograph_fn)
    
    print("Running ANUGA simulation...")
    max_depth = np.zeros(len(domain.get_quantity('elevation').centroid_values))
    max_velocity = np.zeros_like(max_depth)
    arrival_time = np.full_like(max_depth, -1.0)
    
    final_time = max(times) * 1.5
    for t in domain.evolve(yieldstep=10, finaltime=final_time):
        stage = domain.get_quantity('stage').centroid_values
        elev = domain.get_quantity('elevation').centroid_values
        depth = np.maximum(stage - elev, 0)
        
        x_mom = domain.get_quantity('xmomentum').centroid_values
        y_mom = domain.get_quantity('ymomentum').centroid_values
        velocity = np.sqrt(x_mom**2 + y_mom**2) / np.maximum(depth, 1e-3)
        
        mask = depth > 0.1
        first_arrival = mask & (arrival_time < 0)
        arrival_time[first_arrival] = t
        
        max_depth = np.maximum(max_depth, depth)
        max_velocity = np.maximum(max_velocity, velocity)
        
        if int(t) % 100 == 0:
            print(f"Time {t:.1f}/{final_time:.1f} s")
            
    # We now have max values on centroids. We need to rasterize them back to the grid.
    print("Rasterizing outputs...")
    # Get centroid coordinates
    centroids = domain.centroid_coordinates
    cx = centroids[:, 0]
    cy = centroids[:, 1]
    
    # Map centroids back to the grid
    # Since we used a rectangular cross domain, we can interpolate or scatter.
    # For simplicity, nearest neighbor rasterization:
    from scipy.interpolate import griddata
    grid_x, grid_y = np.meshgrid(np.arange(width)*dx + dx/2, height_m - (np.arange(height)*dy + dy/2))
    
    depth_grid = griddata((cx, cy), max_depth, (grid_x, grid_y), method='nearest')
    vel_grid = griddata((cx, cy), max_velocity, (grid_x, grid_y), method='nearest')
    arrival_grid = griddata((cx, cy), arrival_time, (grid_x, grid_y), method='nearest')
    
    # Write temporary EPSG:32644 rasters
    def write_raster(path, data):
        with rasterio.open(dem_32644) as src:
            kwargs = src.meta.copy()
            kwargs.update(dtype=rasterio.float32, nodata=-9999.0)
            with rasterio.open(path, 'w', **kwargs) as dst:
                data = data.astype(np.float32)
                data[np.isnan(data)] = -9999.0
                dst.write(data, 1)
                
    write_raster(out_dir / "depth_32644.tif", depth_grid)
    write_raster(out_dir / "vel_32644.tif", vel_grid)
    write_raster(out_dir / "arrival_32644.tif", arrival_grid)
    
    print("Reprojecting outputs back to EPSG:4326...")
    reproject_raster(out_dir / "depth_32644.tif", out_dir / "farfield_depth.tif", "EPSG:4326")
    reproject_raster(out_dir / "vel_32644.tif", out_dir / "farfield_velocity.tif", "EPSG:4326")
    reproject_raster(out_dir / "arrival_32644.tif", out_dir / "farfield_arrival.tif", "EPSG:4326")
    
    print("Writing solver marker...")
    (out_dir / "solver_used.txt").write_text("anuga\n")
    print("ANUGA Phase 3 wrapper complete.")

if __name__ == "__main__":
    main()
