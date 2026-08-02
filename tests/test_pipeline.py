import json
from pathlib import Path

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
