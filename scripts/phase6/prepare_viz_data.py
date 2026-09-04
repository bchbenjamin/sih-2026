#!/usr/bin/env python3
"""Prepare Blender-neutral arrays from DEM, flood rasters, and exposure data.

This is a visualisation hand-off only. It never synthesises water, terrain, or
buildings; a failed/empty or unverified input is an error.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from rasterio.warp import reproject
from shapely.geometry import shape
import yaml

ROOT = Path(__file__).resolve().parents[2]


def require_verified() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_contract.py"), "--strict"],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("Inputs do not pass strict audit. Produce verified solver outputs before creating a Blender scene.")


def read_damage(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as stream:
        return {row["building_id"]: row for row in csv.DictReader(stream)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=180, help="longest terrain dimension in vertices")
    parser.add_argument("--frames", type=int, default=72)
    args = parser.parse_args()
    if args.resolution < 32 or args.frames < 2:
        raise SystemExit("resolution must be >= 32 and frames must be >= 2")
    require_verified()
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    case = config["case_name"]
    data, output = ROOT / "data" / case, ROOT / "output" / case
    depth_path = output / "farfield_depth.tif"
    arrival_path = output / "farfield_arrival.tif"
    if not depth_path.exists() and (output / "standalone" / "farfield_depth.tif").exists():
        depth_path = output / "standalone" / "farfield_depth.tif"
        arrival_path = output / "standalone" / "farfield_arrival.tif"
    dem_path = data / "dem.tif"
    for path in (dem_path, depth_path, arrival_path):
        if not path.exists():
            raise SystemExit(f"Missing visualisation input: {path}")
    with rasterio.open(depth_path) as depth_source:
        if depth_source.crs is None or depth_source.crs.to_epsg() != 4326:
            raise SystemExit("Flood depth raster must be EPSG:4326")
        flood_bounds = depth_source.bounds
    with rasterio.open(arrival_path) as arrival_source:
        if arrival_source.crs is None or arrival_source.crs.to_epsg() != 4326:
            raise SystemExit("Flood arrival raster must be EPSG:4326")
    with rasterio.open(dem_path) as dem:
        if dem.crs is None or dem.crs.to_epsg() != 4326:
            raise SystemExit("DEM must be EPSG:4326")
        # The solver domain, rather than the entire source DEM, is the visual
        # extent. It preserves narrow valley flood cells during downsampling.
        west = max(dem.bounds.left, flood_bounds.left)
        south = max(dem.bounds.bottom, flood_bounds.bottom)
        east = min(dem.bounds.right, flood_bounds.right)
        north = min(dem.bounds.top, flood_bounds.top)
        if west >= east or south >= north:
            raise SystemExit("Flood raster does not overlap the DEM extent.")
        crop_bounds = rasterio.coords.BoundingBox(west, south, east, north)
        window = from_bounds(*crop_bounds, transform=dem.transform).round_offsets().round_lengths()
        if window.width < 2 or window.height < 2:
            raise SystemExit("Flood/DEM overlap is smaller than two DEM cells.")
        aspect = window.height / window.width
        width = args.resolution
        height = max(32, round(width * aspect))
        terrain = dem.read(1, window=window, out_shape=(height, width), resampling=Resampling.bilinear).astype(np.float32)
        window_transform = dem.window_transform(window)
        transform = window_transform * window_transform.scale(window.width / width, window.height / height)
        bounds = rasterio.windows.bounds(window, dem.transform)
        nodata = dem.nodata
    if nodata is not None:
        terrain[terrain == nodata] = np.nan
    if not np.isfinite(terrain).all():
        raise SystemExit("DEM has no-data cells after resampling; supply a filled DEM for Blender.")
    # Two-pass depth reprojection: max-pooling determines which output cells
    # are wet (any wet source pixel in a coarser cell keeps it wet), bilinear
    # provides smooth continuous depth values for mesh height/coloring.
    depth_max = np.zeros((height, width), dtype=np.float32)
    depth_bilinear = np.zeros((height, width), dtype=np.float32)
    arrival = np.full((height, width), np.nan, dtype=np.float32)
    with rasterio.open(depth_path) as source:
        src_data = source.read(1)
        reproject(src_data, depth_max, src_transform=source.transform, src_crs=source.crs,
                  dst_transform=transform, dst_crs="EPSG:4326", resampling=Resampling.max,
                  src_nodata=source.nodata, dst_nodata=0)
        reproject(src_data, depth_bilinear, src_transform=source.transform, src_crs=source.crs,
                  dst_transform=transform, dst_crs="EPSG:4326", resampling=Resampling.bilinear,
                  src_nodata=source.nodata, dst_nodata=0)
    with rasterio.open(arrival_path) as source:
        reproject(source.read(1), arrival, src_transform=source.transform, src_crs=source.crs,
                  dst_transform=transform, dst_crs="EPSG:4326", resampling=Resampling.max,
                  src_nodata=source.nodata, dst_nodata=np.nan)
    # Wet/dry from max-pooled raster; depth values from bilinear where wet,
    # falling back to max where bilinear underflows to zero in narrow corridors.
    wet = depth_max > 0
    depth = np.where(wet, np.maximum(depth_bilinear, depth_max * 0.5), 0).astype(np.float32)
    depth = np.maximum(depth, 0)
    arrival[(arrival < 0) | (~wet)] = np.nan
    if not np.any(depth > 0):
        raise SystemExit("Flood-depth raster contains no positive depths in the DEM extent.")
    finite_arrival = arrival[np.isfinite(arrival)]
    if not len(finite_arrival):
        raise SystemExit("Flood arrival raster contains no valid arrival times for flooded cells.")
    damage = read_damage(output / "damage.csv")
    buildings = []
    buildings_path = data / "buildings.geojson"
    if buildings_path.exists():
        for index, feature in enumerate(json.loads(buildings_path.read_text()).get("features", [])):
            centroid = shape(feature["geometry"]).centroid
            if not (west <= centroid.x <= east and south <= centroid.y <= north):
                continue
            identifier = str(feature.get("properties", {}).get("id", feature.get("id", index)))
            row = damage.get(identifier, {})
            buildings.append({"id": identifier, "lon": centroid.x, "lat": centroid.y,
                              "damage_class": row.get("damage_class", "none"),
                              "arrival_time_s": row.get("arrival_time_s", "")})
    viz = output / "viz_data"
    viz.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(viz / "flood_visualization.npz", terrain_m=terrain, depth_m=depth,
                        arrival_s=arrival)
    west, south, east, north = bounds
    latitude_mid = (south + north) / 2
    x_extent_m = (east - west) * 111_320 * np.cos(np.deg2rad(latitude_mid))
    y_extent_m = (north - south) * 111_320
    metadata = {"case_name": case, "crs": "EPSG:4326", "bounds": list(bounds),
                "shape": [height, width], "frames": args.frames,
                "simulation_duration_s": float(np.nanmax(finite_arrival) * 1.15),
                "scene_scale_m_per_unit": 100.0, "input_verification": "strict_audit_passed",
                "x_cell_m": float(x_extent_m / max(width - 1, 1)),
                "y_cell_m": float(y_extent_m / max(height - 1, 1)),
                "water_source": "farfield_depth.tif + farfield_arrival.tif; display-only"}
    (viz / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (viz / "buildings.json").write_text(json.dumps(buildings, indent=2) + "\n")
    print(f"Prepared {viz}; terrain {height}x{width}, {len(buildings)} real building features")


if __name__ == "__main__":
    main()
