from business_review.claims import build_claims, traceability_metrics
from business_review.config import load_metric_catalog
from business_review.detection import detect_anomalies
from business_review.driver_analysis import decompose_latest_nmv_change
from business_review.metrics import build_evidence_index, build_latest_snapshot
from business_review.synthetic import generate_weekly_kpis


def test_every_generated_claim_has_valid_evidence() -> None:
    frame = generate_weekly_kpis()
    catalog = load_metric_catalog()
    claims = build_claims(
        build_latest_snapshot(frame, catalog),
        detect_anomalies(frame),
        decompose_latest_nmv_change(frame),
    )
    result = traceability_metrics(claims, build_evidence_index(frame, catalog))
    assert result["coverage"] == 1.0
    assert result["missing"] == []
    assert set(claims["review_status"]) == {"pending_human_review"}


def test_traceability_reports_unknown_evidence() -> None:
    frame = generate_weekly_kpis()
    catalog = load_metric_catalog()
    claims = build_claims(
        build_latest_snapshot(frame, catalog),
        detect_anomalies(frame),
        decompose_latest_nmv_change(frame),
    )
    claims.loc[0, "evidence_ids"] = "UNKNOWN"
    result = traceability_metrics(claims, build_evidence_index(frame, catalog))
    assert result["coverage"] < 1.0
    assert result["missing"] == ["CLAIM-KPI-SESSIONS:UNKNOWN"]
