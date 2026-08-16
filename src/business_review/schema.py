"""Input data validation for the weekly KPI pipeline."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from business_review.config import MetricSpec
from business_review.synthetic import ANOMALY_COLUMNS


class DataValidationError(ValueError):
    """Raised when the input dataset violates a required invariant."""


@dataclass(frozen=True)
class ValidationSummary:
    """Compact validation result stored in the run report."""

    rows: int
    columns: int
    start_week: str
    end_week: str
    checks_passed: int


def validate_weekly_kpis(
    frame: pd.DataFrame,
    catalog: dict[str, MetricSpec],
    require_evaluation_labels: bool = True,
) -> ValidationSummary:
    """Validate schema, ranges, uniqueness, and KPI arithmetic identities."""
    required = {"week_start", "source_row_id"}
    for metric in catalog:
        required.update({metric, f"target_{metric}"})
    if require_evaluation_labels:
        required.update(ANOMALY_COLUMNS.values())
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    if frame.empty:
        raise DataValidationError("Input data must not be empty")
    if (
        frame["source_row_id"].isna().any()
        or frame["source_row_id"].astype(str).str.strip().eq("").any()
    ):
        raise DataValidationError("source_row_id must be populated")
    if frame["week_start"].isna().any():
        raise DataValidationError("week_start must contain valid dates")
    if frame["source_row_id"].duplicated().any():
        raise DataValidationError("source_row_id must be unique")
    if frame["week_start"].duplicated().any():
        raise DataValidationError("week_start must be unique")
    if not frame["week_start"].is_monotonic_increasing:
        raise DataValidationError("week_start must be sorted ascending")
    if len(frame) < 14:
        raise DataValidationError("At least 14 weekly rows are required for rolling detection")
    gaps = frame["week_start"].diff().dropna()
    if not gaps.eq(pd.Timedelta(days=7)).all():
        raise DataValidationError("week_start must use a complete seven-day cadence")

    numeric_columns = [
        column for column in required if column not in {"week_start", "source_row_id"}
    ]
    if frame[numeric_columns].isna().any().any():
        raise DataValidationError("Numeric input columns must not contain nulls")
    if not np.isfinite(frame[numeric_columns].to_numpy(dtype=float)).all():
        raise DataValidationError("Numeric input columns must contain only finite values")
    if (frame[[*catalog]] < 0).any().any():
        raise DataValidationError("KPI values must be non-negative")
    target_columns = [f"target_{metric}" for metric in catalog]
    if (frame[target_columns] <= 0).any().any():
        raise DataValidationError("KPI targets must be positive")
    for metric in ("conversion_rate", "service_failure_rate"):
        if not frame[metric].between(0, 1).all():
            raise DataValidationError(f"{metric} must be between zero and one")
    if require_evaluation_labels:
        for column in ANOMALY_COLUMNS.values():
            if not frame[column].isin([0, 1]).all():
                raise DataValidationError(f"{column} must contain only zero or one")

    expected_orders = np.rint(frame["sessions"] * frame["conversion_rate"])
    if not np.allclose(frame["orders"], expected_orders, atol=1):
        raise DataValidationError("orders must match sessions multiplied by conversion_rate")
    expected_nmv = frame["orders"] * frame["aov"]
    if not np.allclose(frame["nmv"], expected_nmv, rtol=1e-12, atol=1e-6):
        raise DataValidationError("nmv must match orders multiplied by aov")

    return ValidationSummary(
        rows=len(frame),
        columns=len(frame.columns),
        start_week=pd.Timestamp(frame["week_start"].iloc[0]).date().isoformat(),
        end_week=pd.Timestamp(frame["week_start"].iloc[-1]).date().isoformat(),
        checks_passed=10,
    )


def load_weekly_kpis(
    path: Path,
    catalog: dict[str, MetricSpec],
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load a supplied CSV and return normalized data plus content provenance."""
    if path.suffix.lower() != ".csv":
        raise DataValidationError("Supplied KPI input must be a CSV file")
    try:
        content = path.read_bytes()
        frame = pd.read_csv(io.BytesIO(content), dtype={"source_row_id": "string"})
    except (OSError, pd.errors.ParserError) as exc:
        raise DataValidationError(f"Could not read supplied KPI input: {exc}") from exc
    if "week_start" in frame:
        frame["week_start"] = pd.to_datetime(frame["week_start"], errors="coerce")
    numeric_columns = [metric for metric in catalog]
    numeric_columns.extend(f"target_{metric}" for metric in catalog)
    for column in numeric_columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "source_row_id" in frame:
        frame["source_row_id"] = frame["source_row_id"].str.strip()
    validation = validate_weekly_kpis(frame, catalog, require_evaluation_labels=False)
    provenance = {
        "input_file": path.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "rows": validation.rows,
        "contract_version": "weekly-kpi-v1.0",
    }
    return frame, provenance
