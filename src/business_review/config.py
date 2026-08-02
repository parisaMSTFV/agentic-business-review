"""Project configuration and metric catalog loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "configs" / "metric_catalog.json"


@dataclass(frozen=True)
class MetricSpec:
    """Display and decision rules for one KPI."""

    name: str
    label: str
    direction: Literal["higher", "lower"]
    format: Literal["integer", "percent", "currency"]
    target_tolerance: float


def load_metric_catalog(path: Path = DEFAULT_CATALOG_PATH) -> dict[str, MetricSpec]:
    """Load and validate metric display and direction metadata."""
    raw = json.loads(path.read_text(encoding="utf-8"))
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
