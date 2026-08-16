from pathlib import Path

import pandas as pd
import pytest

from business_review.config import load_metric_catalog
from business_review.schema import DataValidationError, load_weekly_kpis, validate_weekly_kpis
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


def test_supplied_input_loads_without_synthetic_evaluation_labels() -> None:
    path = Path(__file__).parents[1] / "examples" / "weekly_kpis.csv"
    frame, provenance = load_weekly_kpis(path, load_metric_catalog())
    assert len(frame) == 16
    assert not any(column.startswith("injected_") for column in frame)
    assert provenance["contract_version"] == "weekly-kpi-v1.0"
    assert len(str(provenance["sha256"])) == 64


def test_supplied_input_rejects_nonweekly_cadence(tmp_path: Path) -> None:
    frame = generate_weekly_kpis().drop(
        columns=[column for column in generate_weekly_kpis() if column.startswith("injected_")]
    )
    frame.loc[3, "week_start"] = frame.loc[3, "week_start"] + pd.Timedelta(days=1)
    path = tmp_path / "invalid.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(DataValidationError, match="seven-day cadence"):
        load_weekly_kpis(path, load_metric_catalog())
