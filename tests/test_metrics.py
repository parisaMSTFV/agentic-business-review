from business_review.config import MetricSpec, load_metric_catalog
from business_review.metrics import build_latest_snapshot, target_status
from business_review.synthetic import generate_weekly_kpis


def test_lower_is_better_direction_is_respected() -> None:
    spec = MetricSpec(
        name="failure_rate",
        label="Failure rate",
        direction="lower",
        format="percent",
        target_tolerance=0.02,
    )
    assert target_status(-0.08, spec) == "ahead"
    assert target_status(0.08, spec) == "behind"
    assert target_status(0.01, spec) == "on_track"


def test_snapshot_has_source_and_target_evidence() -> None:
    snapshot = build_latest_snapshot(generate_weekly_kpis(), load_metric_catalog())
    failure = snapshot.loc[snapshot["metric"] == "service_failure_rate"].iloc[0]
    assert failure["current_evidence_id"].endswith(":service_failure_rate")
    assert failure["target_evidence_id"].endswith(":target_service_failure_rate")
    assert failure["business_change"] == -failure["wow_change"]
