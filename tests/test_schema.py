import pandas as pd
import pytest

from business_review.config import load_metric_catalog
from business_review.schema import DataValidationError, validate_weekly_kpis
from business_review.synthetic import generate_weekly_kpis


def test_synthetic_dataset_passes_schema_and_identity_checks() -> None:
    frame = generate_weekly_kpis()
    summary = validate_weekly_kpis(frame, load_metric_catalog())
    assert summary.rows == 64
    assert summary.checks_passed == 10


def test_schema_rejects_missing_columns() -> None:
    frame = generate_weekly_kpis().drop(columns="sessions")
    with pytest.raises(DataValidationError, match="Missing required columns"):
        validate_weekly_kpis(frame, load_metric_catalog())


def test_schema_rejects_broken_nmv_identity() -> None:
    frame = generate_weekly_kpis()
    frame.loc[3, "nmv"] += 100_000
    with pytest.raises(DataValidationError, match="nmv must match"):
        validate_weekly_kpis(frame, load_metric_catalog())


def test_schema_rejects_duplicate_source_ids() -> None:
    frame = generate_weekly_kpis()
    frame.loc[1, "source_row_id"] = frame.loc[0, "source_row_id"]
    with pytest.raises(DataValidationError, match="source_row_id must be unique"):
        validate_weekly_kpis(frame, load_metric_catalog())


def test_week_start_is_datetime_in_generated_data() -> None:
    assert pd.api.types.is_datetime64_any_dtype(generate_weekly_kpis()["week_start"])
