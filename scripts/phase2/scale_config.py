#!/usr/bin/env python3
"""Write the explicit Froude-similarity conversion contract."""
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    config = yaml.safe_load((ROOT / "case_config.yaml").read_text())
    lr = float(config.get("execution", {}).get("model_scale_Lr", 40.0))
    if lr <= 1:
        raise SystemExit("model_scale_Lr must be > 1 (prototype length / model length)")
    ratio = lr ** 0.5
    result = {
        "case_name": config["case_name"], "scale_factor_Lr": lr,
        "velocity_ratio_Vr": ratio, "time_ratio_Tr": ratio,
        "discharge_ratio_Qr": lr ** 2.5,
        "definitions": {"prototype_time_s": "model_time_s * time_ratio_Tr",
                        "prototype_discharge_m3s": "model_discharge_m3s * discharge_ratio_Qr"},
        "froude_similarity": True,
    }
    output = ROOT / "output" / config["case_name"] / "scale_config.yaml"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(result, sort_keys=False))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
