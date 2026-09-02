#!/usr/bin/env python3
"""Sample validated flood rasters at actual building-footprint centroids."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import rasterio
from shapely.geometry import shape
import yaml

ROOT = Path(__file__).resolve().parents[2]


def damage_class(depth: float | None) -> str:
    if depth is None or depth <= 0:
        return "none"
    if depth < 0.5:
        return "low"
    if depth <= 2.0:
        return "moderate"
    return "severe"


def sample(dataset: rasterio.io.DatasetReader, lon: float, lat: float) -> float | None:
    value = next(dataset.sample([(lon, lat)]))[0]
    if dataset.nodata is not None and value == dataset.nodata:
        return None
    return float(value)


def run(scenario_dir: Path, output: Path) -> None:
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    buildings = ROOT / "data" / config["case_name"] / "buildings.geojson"
    if not buildings.exists():
        raise FileNotFoundError(buildings)
    depth_path, arrival_path = scenario_dir / "farfield_depth.tif", scenario_dir / "farfield_arrival.tif"
    with rasterio.open(depth_path) as depth, rasterio.open(arrival_path) as arrival:
        for dataset in (depth, arrival):
            if dataset.crs is None or dataset.crs.to_epsg() != 4326:
                raise ValueError(f"{dataset.name} is not EPSG:4326")
        features = json.loads(buildings.read_text()).get("features", [])
        rows = []
        for index, feature in enumerate(features):
            geometry = shape(feature["geometry"])
            if geometry.is_empty:
                continue
            centroid = geometry.centroid
            max_depth = sample(depth, centroid.x, centroid.y)
            arrival_s = sample(arrival, centroid.x, centroid.y)
            if arrival_s is not None and arrival_s < 0:
                arrival_s = None
            rows.append({"building_id": str(feature.get("properties", {}).get("id", feature.get("id", index))),
                         "lon": centroid.x, "lat": centroid.y, "max_depth_m": max_depth,
                         "arrival_time_s": arrival_s, "damage_class": damage_class(max_depth)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["building_id", "lon", "lat", "max_depth_m", "arrival_time_s", "damage_class"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} building impacts to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.scenario_dir, args.output)


if __name__ == "__main__":
    main()
