#!/usr/bin/env python3
"""Create a traceable landslide-dam breach parameter report.

The primary peak-flow estimate is Peng & Zhang (2012), simplified equation for
landslide dams. Width and breach duration are deliberately *not* invented:
their full regression needs dam geometry and a justified erodibility class that
are not in the published Rishiganga lake description. Supply them with
``--calibration`` before a production solver run.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ERODIBILITY = {"high": 1.236, "medium": -0.380, "low": -1.615}
PLACEHOLDER_CITATIONS = {"", "your source / report / calibration id", "todo", "tbd", "unknown", "n/a"}


def peng_zhang_peak_discharge(volume_m3: float, dam_height_m: float, erodibility: str) -> float:
    """Peng & Zhang (2012) simplified Qp equation (SI units)."""
    if volume_m3 <= 0 or dam_height_m <= 0:
        raise ValueError("lake volume and dam height must be positive")
    a = ERODIBILITY[erodibility]
    return (math.sqrt(9.81) * dam_height_m ** 2.5 * dam_height_m ** -1.371
            * ((volume_m3 ** (1.0 / 3.0)) / dam_height_m) ** 1.536 * math.exp(a))


def walder_oconnor_volume_check(volume_m3: float) -> float:
    """Walder & O'Connor (1997) volume-only screening relation, SI units."""
    return 1.60 * volume_m3 ** 0.46


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "case_config.yaml")
    parser.add_argument("--calibration", type=Path,
                        help="YAML with breach_width_m, breach_time_s, erodibility and citation")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    volume = float(config["reservoir_volume_m3"])
    height = float(config["lake_depth_m"])
    calibration = yaml.safe_load(args.calibration.read_text()) if args.calibration else {}
    erodibility = calibration.get("erodibility", "medium")
    if erodibility not in ERODIBILITY:
        raise SystemExit(f"Unknown erodibility {erodibility!r}; choose {', '.join(ERODIBILITY)}")

    q_peak = peng_zhang_peak_discharge(volume, height, erodibility)
    selected = {"peak_discharge_m3s": q_peak,
                "breach_width_m": calibration.get("breach_width_m"),
                "breach_time_s": calibration.get("breach_time_s")}
    citation = str(calibration.get("citation", "")).strip()
    ready = (all(value is not None for value in selected.values())
             and citation.casefold() not in PLACEHOLDER_CITATIONS)
    report = {
        "case_name": config["case_name"],
        "status": "READY_FOR_SOLVER" if ready else "NEEDS_CALIBRATION",
        "primary_method": {
            "name": "Peng & Zhang (2012), simplified peak-discharge equation",
            "doi": "10.1007/s10346-011-0271-y",
            "equation": "Qp=sqrt(g)*Hd^2.5*(Hd/1m)^-1.371*(Vl^(1/3)/Hd)^1.536*exp(a)",
            "erodibility": erodibility,
            "erodibility_coefficient_a": ERODIBILITY[erodibility],
            "inputs": {"lake_volume_m3": volume, "dam_height_m": height},
            "peak_discharge_m3s": q_peak,
        },
        "secondary_screening_check": {
            "name": "Walder & O'Connor (1997), volume-only relation",
            "doi": "10.1029/97WR01616",
            "peak_discharge_m3s": walder_oconnor_volume_check(volume),
            "warning": "Screening check only; it does not represent breach-formation rate.",
        },
        "selected_parameters": selected,
        "calibration": calibration or {
            "required": ["breach_width_m", "breach_time_s", "citation"],
            "reason": "Published lake dimensions do not establish final breach geometry or erosion rate.",
        },
    }
    output = ROOT / "output" / config["case_name"] / "breach_params.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {output} ({report['status']})")
    if not ready:
        print("No solver run is permitted until a cited breach calibration is supplied.")


if __name__ == "__main__":
    main()
