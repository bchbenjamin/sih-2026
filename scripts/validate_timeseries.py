#!/usr/bin/env python3
"""Compare model and benchmark time series on shared timestamps."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def read_series(path: Path, value_column: str) -> tuple[np.ndarray, np.ndarray]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or "time_s" not in rows[0] or value_column not in rows[0]:
        raise ValueError(f"{path} needs time_s and {value_column} columns")
    return (np.asarray([float(row["time_s"]) for row in rows]),
            np.asarray([float(row[value_column]) for row in rows]))


def max_relative_error(reference_time: np.ndarray, reference: np.ndarray,
                       model_time: np.ndarray, model: np.ndarray) -> float:
    interpolated = np.interp(reference_time, model_time, model)
    scale = max(float(np.max(np.abs(reference))), 1e-9)
    return float(np.max(np.abs(interpolated - reference)) / scale * 100.0)
