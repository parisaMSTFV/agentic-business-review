import json
from pathlib import Path

import pandas as pd

from business_review.pipeline import run_pipeline


def test_pipeline_writes_required_artifacts(tmp_path: Path) -> None:
    metrics = run_pipeline(tmp_path)
    required = [
        "data/synthetic_weekly_kpis.csv",
        "reports/metrics.json",
        "reports/claims.csv",
        "reports/alerts.csv",
        "reports/driver_contributions.csv",
        "reports/business_review.html",
        "reports/figures/kpi_trends.png",
        "reports/figures/alert_evaluation.png",
        "reports/figures/driver_contributions.png",
    ]
    assert all((tmp_path / path).exists() for path in required)
    assert metrics["traceability"]["coverage"] == 1.0


def test_core_artifacts_are_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_metrics = run_pipeline(first)
    second_metrics = run_pipeline(second)
    assert first_metrics["artifact_fingerprint"] == second_metrics["artifact_fingerprint"]
    assert json.loads((first / "reports/metrics.json").read_text()) == json.loads(
        (second / "reports/metrics.json").read_text()
    )


def test_supplied_input_path_omits_unavailable_accuracy_claims(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[1] / "examples" / "weekly_kpis.csv"
    metrics = run_pipeline(tmp_path, input_path=fixture)
    assert metrics["data_mode"] == "supplied_kpi_input"
    assert metrics["alert_summary"]["evaluation_status"] == "not_evaluated_no_ground_truth_labels"
    assert "rolling_detector" not in metrics
    assert "fixed_rule_baseline" not in metrics
    assert (tmp_path / "reports/validated_weekly_kpis.csv").exists()
    assert not (tmp_path / "reports/alert_model_comparison.csv").exists()
    assert not (tmp_path / "reports/figures/alert_evaluation.png").exists()
    assert set(pd.read_csv(tmp_path / "reports/claims.csv")["review_status"]) == {
        "pending_human_review"
    }
