#!/usr/bin/env python3
"""Prepare Blender-neutral arrays from DEM, flood rasters, and exposure data.

This is a visualisation hand-off only. It never synthesises water, terrain, or
buildings; a failed/empty input is an error. Use --allow-unverified only to
inspect legacy artefacts, never for a decision-support render.
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
from rasterio.warp import reproject
from shapely.geometry import shape
import yaml

ROOT = Path(__file__).resolve().parents[2]


def require_verified(allow_unverified: bool) -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_contract.py"), "--strict"],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode and not allow_unverified:
        raise SystemExit("Inputs do not pass strict audit. Run with --allow-unverified only for a clearly labelled preview.")


def read_damage(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as stream:
        return {row["building_id"]: row for row in csv.DictReader(stream)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=180, help="longest terrain dimension in vertices")
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args()
    if args.resolution < 32 or args.frames < 2:
        raise SystemExit("resolution must be >= 32 and frames must be >= 2")
    require_verified(args.allow_unverified)
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    case = config["case_name"]
    data, output = ROOT / "data" / case, ROOT / "output" / case
    dem_path, depth_path, arrival_path = data / "dem.tif", output / "farfield_depth.tif", output / "farfield_arrival.tif"
    for path in (dem_path, depth_path, arrival_path):
        if not path.exists():
            raise SystemExit(f"Missing visualisation input: {path}")
    with rasterio.open(dem_path) as dem:
        if dem.crs is None or dem.crs.to_epsg() != 4326:
            raise SystemExit("DEM must be EPSG:4326")
        aspect = dem.height / dem.width
        width = args.resolution
        height = max(32, round(width * aspect))
        terrain = dem.read(1, out_shape=(height, width), resampling=Resampling.bilinear).astype(np.float32)
        transform = dem.transform * dem.transform.scale(dem.width / width, dem.height / height)
        bounds = dem.bounds
        nodata = dem.nodata
    if nodata is not None:
        terrain[terrain == nodata] = np.nan
    if not np.isfinite(terrain).all():
        raise SystemExit("DEM has no-data cells after resampling; supply a filled DEM for Blender.")
    depth = np.zeros_like(terrain)
    arrival = np.full_like(terrain, np.nan)
    with rasterio.open(depth_path) as source:
        reproject(source.read(1), depth, src_transform=source.transform, src_crs=source.crs,
                  dst_transform=transform, dst_crs="EPSG:4326", resampling=Resampling.bilinear,
                  src_nodata=source.nodata, dst_nodata=0)
    with rasterio.open(arrival_path) as source:
        reproject(source.read(1), arrival, src_transform=source.transform, src_crs=source.crs,
                  dst_transform=transform, dst_crs="EPSG:4326", resampling=Resampling.nearest,
                  src_nodata=source.nodata, dst_nodata=np.nan)
    depth = np.maximum(depth, 0)
    arrival[(arrival < 0) | (depth <= 0)] = np.nan
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
            identifier = str(feature.get("properties", {}).get("id", feature.get("id", index)))
            row = damage.get(identifier, {})
            buildings.append({"id": identifier, "lon": centroid.x, "lat": centroid.y,
                              "damage_class": row.get("damage_class", "none"),
                              "arrival_time_s": row.get("arrival_time_s", "")})
    viz = output / "viz_data"
    viz.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(viz / "flood_visualization.npz", terrain_m=terrain, depth_m=depth,
                        arrival_s=arrival)
    metadata = {"case_name": case, "crs": "EPSG:4326", "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "shape": [height, width], "frames": args.frames,
                "simulation_duration_s": float(np.nanmax(finite_arrival) * 1.15),
                "scene_scale_m_per_unit": 100.0, "input_verification": "unverified_preview" if args.allow_unverified else "strict_audit_passed",
                "water_source": "farfield_depth.tif + farfield_arrival.tif; display-only"}
    (viz / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (viz / "buildings.json").write_text(json.dumps(buildings, indent=2) + "\n")
    print(f"Prepared {viz}; terrain {height}x{width}, {len(buildings)} real building features")


if __name__ == "__main__":
    main()
