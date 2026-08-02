"""Input data validation for the weekly KPI pipeline."""

from __future__ import annotations

from dataclasses import dataclass

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
) -> ValidationSummary:
    """Validate schema, ranges, uniqueness, and KPI arithmetic identities."""
    required = {"week_start", "source_row_id"}
    for metric in catalog:
        required.update({metric, f"target_{metric}"})
    required.update(ANOMALY_COLUMNS.values())
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    if frame.empty:
        raise DataValidationError("Input data must not be empty")
    if frame["source_row_id"].duplicated().any():
        raise DataValidationError("source_row_id must be unique")
    if frame["week_start"].duplicated().any():
        raise DataValidationError("week_start must be unique")
    if not frame["week_start"].is_monotonic_increasing:
        raise DataValidationError("week_start must be sorted ascending")

    numeric_columns = [
        column for column in required if column not in {"week_start", "source_row_id"}
    ]
    if frame[numeric_columns].isna().any().any():
        raise DataValidationError("Numeric input columns must not contain nulls")
    if (frame[[*catalog]] < 0).any().any():
        raise DataValidationError("KPI values must be non-negative")
    for metric in ("conversion_rate", "service_failure_rate"):
        if not frame[metric].between(0, 1).all():
            raise DataValidationError(f"{metric} must be between zero and one")
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
