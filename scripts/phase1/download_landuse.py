#!/usr/bin/env python3
"""Download OSM land-use features as a provenance-preserving GeoJSON extract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "case_config.yaml")
    parser.add_argument("--endpoint", default="https://overpass-api.de/api/interpreter")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    west, south, east, north = config["dem_bbox"]
    query = (f'[out:json][timeout:180];(way["landuse"]({south},{west},{north},{east});'
             f'way["natural"]({south},{west},{north},{east}););out center;')
    headers = {"Accept": "application/json", "User-Agent": "Dam_Inundation/1.0"}
    response = requests.post(args.endpoint, data={"data": query}, headers=headers, timeout=(10, 240))
    response.raise_for_status()
    features = []
    for element in response.json().get("elements", []):
        center = element.get("center")
        if not center:
            continue
        features.append({"type": "Feature", "id": str(element["id"]),
                         "properties": {"id": str(element["id"]), **element.get("tags", {})},
                         "geometry": {"type": "Point", "coordinates": [center["lon"], center["lat"]]}})
    output = ROOT / "data" / config["case_name"] / "landuse.geojson"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}, "features": features}, indent=2) + "\n")
    (output.parent / "landuse_metadata.json").write_text(json.dumps({
        "source": "OpenStreetMap via Overpass", "endpoint": args.endpoint,
        "query": query, "crs": "EPSG:4326", "feature_count": len(features),
    }, indent=2) + "\n")
    print(f"Wrote {len(features)} land-use features to {output}")


if __name__ == "__main__":
    main()
