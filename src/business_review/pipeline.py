"""End-to-end reproducible business-review pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from business_review.claims import build_claims, traceability_metrics
from business_review.config import PROJECT_ROOT, load_metric_catalog
from business_review.detection import baseline_alerts, detect_anomalies, evaluate_alerts
from business_review.driver_analysis import decompose_latest_nmv_change
from business_review.metrics import build_evidence_index, build_latest_snapshot
from business_review.reporting import (
    plot_alert_evaluation,
    plot_driver_contributions,
    plot_kpi_trends,
    render_dashboard,
    write_run_summary,
)
from business_review.schema import validate_weekly_kpis
from business_review.synthetic import generate_weekly_kpis


def _fingerprint(frames: list[pd.DataFrame]) -> str:
    digest = hashlib.sha256()
    for frame in frames:
        digest.update(frame.to_csv(index=False, float_format="%.12g").encode("utf-8"))
    return digest.hexdigest()[:16]


def run_pipeline(
    output_root: Path = PROJECT_ROOT,
    seed: int = 42,
    periods: int = 64,
) -> dict[str, Any]:
    """Run data generation, validation, analysis, evaluation, and reporting."""
    data_dir = output_root / "data"
    reports_dir = output_root / "reports"
    figures_dir = reports_dir / "figures"
    for path in (data_dir, reports_dir, figures_dir):
        path.mkdir(parents=True, exist_ok=True)

    catalog = load_metric_catalog()
    weekly = generate_weekly_kpis(seed=seed, periods=periods)
    validation = validate_weekly_kpis(weekly, catalog)
    snapshot = build_latest_snapshot(weekly, catalog)
    detector_alerts = detect_anomalies(weekly)
    baseline = baseline_alerts(detector_alerts)
    detector_metrics = evaluate_alerts(detector_alerts)
    baseline_metrics = evaluate_alerts(baseline)
    driver_contributions = decompose_latest_nmv_change(weekly)
    evidence_index = build_evidence_index(weekly, catalog)
    claims = build_claims(snapshot, detector_alerts, driver_contributions)
    traceability = traceability_metrics(claims, evidence_index)
    fingerprint = _fingerprint([weekly, snapshot, detector_alerts, claims, driver_contributions])

    comparison = pd.DataFrame.from_records(
        [
            {"model": "Fixed 12% rule", **baseline_metrics},
            {"model": "Rolling residual score", **detector_metrics},
        ]
    )

    export_weekly = weekly.copy()
    export_weekly["week_start"] = export_weekly["week_start"].dt.date.astype(str)
    export_alerts = detector_alerts.copy()
    export_alerts["week_start"] = pd.to_datetime(export_alerts["week_start"]).dt.date.astype(str)
    export_weekly.to_csv(data_dir / "synthetic_weekly_kpis.csv", index=False)
    snapshot.to_csv(reports_dir / "latest_kpi_snapshot.csv", index=False)
    export_alerts.to_csv(reports_dir / "alerts.csv", index=False)
    comparison.to_csv(reports_dir / "alert_model_comparison.csv", index=False)
    claims.to_csv(reports_dir / "claims.csv", index=False)
    driver_contributions.to_csv(reports_dir / "driver_contributions.csv", index=False)

    metrics: dict[str, Any] = {
        "data": {
            **asdict(validation),
            "synthetic_anomalies": int(
                weekly[[column for column in weekly if column.startswith("injected_")]].sum().sum()
            ),
        },
        "rolling_detector": detector_metrics,
        "fixed_rule_baseline": baseline_metrics,
        "traceability": traceability,
        "driver_reconciliation_max_abs_error": float(
            driver_contributions["reconciliation_error"].abs().max()
        ),
        "artifact_fingerprint": fingerprint,
        "evaluation_boundary": "Labeled synthetic data only",
    }
    (reports_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8"
    )

    plot_kpi_trends(weekly, catalog, figures_dir / "kpi_trends.png")
    plot_alert_evaluation(comparison, figures_dir / "alert_evaluation.png")
    plot_driver_contributions(driver_contributions, figures_dir / "driver_contributions.png")
    render_dashboard(
        snapshot,
        claims,
        detector_alerts,
        catalog,
        reports_dir / "business_review.html",
    )
    write_run_summary(
        detector_metrics,
        baseline_metrics,
        traceability,
        rows=len(weekly),
        fingerprint=fingerprint,
        output_path=reports_dir / "run_summary.md",
    )
    return metrics
