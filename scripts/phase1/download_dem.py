#!/usr/bin/env python3
"""Download and validate the DEM; never replace failed data with fake terrain."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests
import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if key and key not in os.environ:
            os.environ[key] = value


def bbox_covers_request(bounds, requested_bbox, resolution):
    west, south, east, north = requested_bbox
    x_tol = max(abs(float(resolution[0])), 1e-9) * 0.5
    y_tol = max(abs(float(resolution[1])), 1e-9) * 0.5
    return (
        bounds.left <= west + x_tol
        and bounds.right >= east - x_tol
        and bounds.bottom <= south + y_tol
        and bounds.top >= north - y_tol
    )


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.getenv("OPENTOPOGRAPHY_API_KEY"))
    parser.add_argument("--config", type=Path, default=ROOT / "case_config.yaml")
    args = parser.parse_args()
    if not args.api_key:
        raise SystemExit("OPENTOPOGRAPHY_API_KEY is required; a DEM must not be silently synthesised.")
    config = yaml.safe_load(args.config.read_text())
    west, south, east, north = config["dem_bbox"]
    output = ROOT / "data" / config["case_name"] / "dem.tif"
    output.parent.mkdir(parents=True, exist_ok=True)
    url = "https://portal.opentopography.org/API/globaldem"
    params = {"demtype": "SRTMGL1", "south": south, "north": north, "west": west,
              "east": east, "outputFormat": "GTiff", "API_Key": args.api_key}
    response = requests.get(url, params=params, timeout=(10, 180))
    response.raise_for_status()
    if response.content[:2] != b"II" and response.content[:2] != b"MM":
        raise SystemExit("OpenTopography returned a non-TIFF response; destination was left unchanged.")
    temporary = output.with_suffix(".download.tif")
    temporary.write_bytes(response.content)
    try:
        with rasterio.open(temporary) as dataset:
            if dataset.crs is None or dataset.crs.to_epsg() != 4326:
                raise ValueError(f"expected EPSG:4326, got {dataset.crs}")
            bounds = dataset.bounds
            resolution = dataset.res
            if not bbox_covers_request(bounds, (west, south, east, north), resolution):
                raise ValueError(
                    f"DEM does not cover requested bbox within one half-pixel tolerance: {bounds} "
                    f"requested={west, south, east, north} res={resolution}"
                )
            data = dataset.read(1, masked=True)
            if data.mask.all():
                raise ValueError("DEM contains no valid cells")
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    temporary.replace(output)
    (output.parent / "dem_metadata.json").write_text(json.dumps({
        "source": "OpenTopography SRTMGL1",
        "request": {"endpoint": url, "demtype": "SRTMGL1",
                    "bbox": [west, south, east, north], "output_format": "GTiff"},
        "crs": "EPSG:4326", "credential_redacted": True,
    }, indent=2) + "\n")
    print(f"Downloaded validated EPSG:4326 DEM to {output}")


if __name__ == "__main__":
    main()
