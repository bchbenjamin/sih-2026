#!/usr/bin/env python3
"""Download OSM building polygons in EPSG:4326 through Overpass."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]


def feature(element: dict) -> dict | None:
    geometry = element.get("geometry", [])
    if len(geometry) < 3:
        return None
    ring = [[node["lon"], node["lat"]] for node in geometry]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    if len(ring) < 4:
        return None
    lon = sum(point[0] for point in ring[:-1]) / (len(ring) - 1)
    lat = sum(point[1] for point in ring[:-1]) / (len(ring) - 1)
    return {"type": "Feature", "id": str(element["id"]),
            "properties": {"id": str(element["id"]), "lon": lon, "lat": lat,
                           **element.get("tags", {})},
            "geometry": {"type": "Polygon", "coordinates": [ring]}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "case_config.yaml")
    parser.add_argument("--endpoint", default="https://overpass-api.de/api/interpreter")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    west, south, east, north = config["dem_bbox"]
    query = f'[out:json][timeout:180];way["building"]({south},{west},{north},{east});out geom;'
    headers = {"Accept": "application/json", "User-Agent": "Dam_Inundation/1.0"}
    response = requests.post(args.endpoint, data={"data": query}, headers=headers, timeout=(10, 240))
    response.raise_for_status()
    features = [item for item in (feature(row) for row in response.json().get("elements", [])) if item]
    payload = {"type": "FeatureCollection", "name": f"{config['case_name']}_buildings",
               "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}, "features": features}
    output = ROOT / "data" / config["case_name"] / "buildings.geojson"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n")
    (output.parent / "buildings_metadata.json").write_text(json.dumps({
        "source": "OpenStreetMap via Overpass", "endpoint": args.endpoint,
        "query": query, "crs": "EPSG:4326", "feature_count": len(features),
    }, indent=2) + "\n")
    print(f"Wrote {len(features)} building footprints to {output}")


if __name__ == "__main__":
    main()
