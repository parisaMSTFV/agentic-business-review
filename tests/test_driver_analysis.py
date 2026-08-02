from business_review.driver_analysis import decompose_latest_nmv_change
from business_review.synthetic import generate_weekly_kpis


def test_driver_decomposition_reconciles_to_nmv_change() -> None:
    result = decompose_latest_nmv_change(generate_weekly_kpis())
    assert set(result["driver"]) == {"sessions", "conversion_rate", "aov"}
    assert result["reconciliation_error"].abs().max() < 1e-12
