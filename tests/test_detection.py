import pandas as pd

from business_review.detection import baseline_alerts, detect_anomalies, evaluate_alerts
from business_review.synthetic import generate_weekly_kpis


def test_rolling_detector_uses_no_future_values() -> None:
    original = generate_weekly_kpis()
    changed = original.copy()
    cutoff = original["week_start"].iloc[49]
    changed.loc[changed["week_start"] > cutoff, "sessions"] *= 20
    before = detect_anomalies(original)
    after = detect_anomalies(changed)
    keys = ["week_start", "metric", "anomaly_score"]
    pd.testing.assert_frame_equal(
        before.loc[before["week_start"] <= cutoff, keys].reset_index(drop=True),
        after.loc[after["week_start"] <= cutoff, keys].reset_index(drop=True),
    )


def test_detector_recovers_most_injected_events() -> None:
    metrics = evaluate_alerts(detect_anomalies(generate_weekly_kpis()))
    assert metrics["recall"] >= 0.80
    assert metrics["precision"] >= 0.75


def test_fixed_rule_is_a_valid_baseline() -> None:
    alerts = detect_anomalies(generate_weekly_kpis())
    baseline = baseline_alerts(alerts)
    metrics = evaluate_alerts(baseline)
    assert set(baseline["is_alert"].unique()).issubset({0, 1})
    assert 0 <= metrics["f1"] <= 1
