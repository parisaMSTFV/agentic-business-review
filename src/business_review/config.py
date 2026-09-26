"""Project configuration and metric catalog loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal

DEFAULT_OUTPUT_ROOT = Path("local-runs/latest")


@dataclass(frozen=True)
class MetricSpec:
    """Display and decision rules for one KPI."""

    name: str
    label: str
    direction: Literal["higher", "lower"]
    format: Literal["integer", "percent", "currency"]
    target_tolerance: float


def load_metric_catalog(path: Path | None = None) -> dict[str, MetricSpec]:
    """Load and validate metric display and direction metadata."""
    catalog_path = path or files("business_review").joinpath("resources", "metric_catalog.json")
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog: dict[str, MetricSpec] = {}
    for name, values in raw.items():
        direction = values.get("direction")
        if direction not in {"higher", "lower"}:
            raise ValueError(f"Unsupported direction for {name}: {direction}")
        tolerance = float(values.get("target_tolerance", 0.0))
        if tolerance < 0:
            raise ValueError(f"Target tolerance must be non-negative for {name}")
        catalog[name] = MetricSpec(name=name, **values)
    return catalog
