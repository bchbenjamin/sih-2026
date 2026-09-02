#!/usr/bin/env python3
"""Compare only outputs produced by declared, supported far-field solvers."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED = {"delft3d_fm", "anuga"}


def hydrograph_peak(path: Path) -> dict[str, float]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Empty hydrograph: {path}")
    peak = max(rows, key=lambda row: float(row["discharge_m3s"]))
    return {"peak_discharge_m3s": float(peak["discharge_m3s"]), "peak_time_s": float(peak["time_s"])}


def raster_value(path: Path, lat: float, lon: float) -> float | None:
    with rasterio.open(path) as dataset:
        if dataset.crs is None or dataset.crs.to_epsg() != 4326:
            raise ValueError(f"Expected EPSG:4326: {path}")
        value = next(dataset.sample([(lon, lat)]))[0]
        if dataset.nodata is not None and value == dataset.nodata:
            return None
        value = float(value)
        return None if value < 0 and "arrival" in path.name else value


def main() -> None:
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    output = ROOT / "output" / config["case_name"]
    standalone = output / "standalone"
    for directory in (output, standalone):
        marker = directory / "solver_used.txt"
        if not marker.exists() or marker.read_text().strip() not in SUPPORTED:
            raise SystemExit(f"Refusing comparison: {marker} must name delft3d_fm or anuga")
    hybrid_peak, standalone_peak = hydrograph_peak(output / "hydrograph.csv"), hydrograph_peak(standalone / "hydrograph.csv")
    report = {"scenario_definition": {"hybrid": "DualSPHysics hydrograph routed far-field",
                                      "standalone": "formula hydrograph routed far-field"},
              "breach": {"hybrid": hybrid_peak, "standalone": standalone_peak,
                         "delta_peak_discharge_m3s": hybrid_peak["peak_discharge_m3s"] - standalone_peak["peak_discharge_m3s"],
                         "delta_peak_time_s": hybrid_peak["peak_time_s"] - standalone_peak["peak_time_s"]},
              "downstream_points": {}}
    for point in config.get("downstream_points", []):
        lat, lon = point["coordinates"]
        rows = {}
        for name, directory in (("hybrid", output), ("standalone", standalone)):
            rows[name] = {"max_depth_m": raster_value(directory / "farfield_depth.tif", lat, lon),
                          "max_velocity_mps": raster_value(directory / "farfield_velocity.tif", lat, lon),
                          "arrival_time_s": raster_value(directory / "farfield_arrival.tif", lat, lon)}
        report["downstream_points"][point["name"]] = rows
    (output / "comparison_report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "comparison_report.md").write_text("# Scenario comparison\n\nMachine-readable results: `comparison_report.json`.\n")
    print(f"Wrote {output / 'comparison_report.json'}")


if __name__ == "__main__":
    main()
