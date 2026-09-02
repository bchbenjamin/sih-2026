#!/usr/bin/env python3
"""Audit the cross-phase data contract without trusting old artefacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[1]


def raster_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing"}
    try:
        with rasterio.open(path) as src:
            valid = src.crs is not None and src.crs.to_epsg() == 4326
            return {"status": "valid" if valid else "invalid", "crs": str(src.crs),
                    "shape": [src.height, src.width], "bounds": list(src.bounds)}
    except Exception as error:
        return {"status": "invalid", "reason": str(error)}


def file_status(path: Path, minimum_bytes: int = 2) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing"}
    return {"status": "valid" if path.stat().st_size >= minimum_bytes else "placeholder",
            "bytes": path.stat().st_size}


def provenance_status(path: Path, metadata: Path, minimum_bytes: int = 2) -> dict[str, Any]:
    result = file_status(path, minimum_bytes)
    if result["status"] == "valid" and not metadata.exists():
        result["status"] = "unverified"
        result["reason"] = f"missing provenance metadata: {metadata.name}"
    return result


def farfield_status(path: Path, marker: Path) -> dict[str, Any]:
    result = raster_status(path)
    if result["status"] == "valid":
        solver = marker.read_text().strip() if marker.exists() else None
        if solver not in {"delft3d_fm", "anuga"}:
            result["status"] = "unverified"
            result["reason"] = f"solver_used.txt must be delft3d_fm or anuga (was {solver!r})"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    config_path = ROOT / "case_config.yaml"
    config = yaml.safe_load(config_path.read_text())
    case = config["case_name"]
    data, output = ROOT / "data" / case, ROOT / "output" / case
    report = {
        "case_config.yaml": file_status(config_path),
        f"data/{case}/sources.md": file_status(data / "sources.md", 200),
        f"data/{case}/dem.tif": provenance_status(data / "dem.tif", data / "dem_metadata.json"),
        f"data/{case}/buildings.geojson": provenance_status(data / "buildings.geojson", data / "buildings_metadata.json", 100),
        f"data/{case}/landuse.geojson": provenance_status(data / "landuse.geojson", data / "landuse_metadata.json", 100),
        f"output/{case}/hydrograph.csv": provenance_status(output / "hydrograph.csv", output / "dualsphysics_run_metadata.json", 40),
        f"output/{case}/scale_config.yaml": file_status(output / "scale_config.yaml", 40),
        f"output/{case}/farfield_depth.tif": farfield_status(output / "farfield_depth.tif", output / "solver_used.txt"),
        f"output/{case}/farfield_velocity.tif": farfield_status(output / "farfield_velocity.tif", output / "solver_used.txt"),
        f"output/{case}/farfield_arrival.tif": farfield_status(output / "farfield_arrival.tif", output / "solver_used.txt"),
        f"output/{case}/damage.csv": file_status(output / "damage.csv", 40),
        f"output/{case}/comparison_report.json": file_status(output / "comparison_report.json", 40),
    }
    print(json.dumps(report, indent=2))
    if args.strict and any(item["status"] != "valid" for item in report.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
