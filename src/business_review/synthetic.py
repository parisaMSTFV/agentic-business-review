"""Generate a deterministic, labeled weekly KPI dataset."""

from __future__ import annotations

import numpy as np
import pandas as pd

ANOMALY_COLUMNS = {
    "sessions": "injected_sessions",
    "conversion_rate": "injected_conversion_rate",
    "aov": "injected_aov",
    "service_failure_rate": "injected_service_failure_rate",
}


def generate_weekly_kpis(seed: int = 42, periods: int = 64) -> pd.DataFrame:
    """Create synthetic weekly actuals, targets, and injected anomaly labels.

    Targets are smooth planning series. Actuals include ordinary noise plus a
    small set of deterministic shocks that act as ground truth for evaluation.
    """
    if periods < 40:
        raise ValueError("At least 40 periods are required for rolling evaluation")

    rng = np.random.default_rng(seed)
    index = np.arange(periods)
    week_start = pd.date_range("2024-01-01", periods=periods, freq="W-MON")

    target_sessions = 980_000 * (1 + 0.0035 * index) * (1 + 0.035 * np.sin(2 * np.pi * index / 13))
    target_conversion = 0.035 + 0.000035 * index
    target_aov = 1_180_000 * (1 + 0.0022 * index)
    target_failure = np.maximum(0.021, 0.032 - 0.00012 * index)

    sessions = target_sessions * (1 + rng.normal(0, 0.018, periods))
    conversion = target_conversion * (1 + rng.normal(0, 0.012, periods))
    aov = target_aov * (1 + rng.normal(0, 0.010, periods))
    failure = target_failure * (1 + rng.normal(0, 0.025, periods))

    labels = {metric: np.zeros(periods, dtype=int) for metric in ANOMALY_COLUMNS}
    shocks = {
        "sessions": {43: -0.13, 56: 0.15},
        "conversion_rate": {47: -0.11, 61: 0.12},
        "aov": {51: -0.10},
        "service_failure_rate": {45: 0.28, 59: 0.31},
    }
    arrays = {
        "sessions": sessions,
        "conversion_rate": conversion,
        "aov": aov,
        "service_failure_rate": failure,
    }
    for metric, metric_shocks in shocks.items():
        for position, shock in metric_shocks.items():
            if position < periods:
                arrays[metric][position] *= 1 + shock
                labels[metric][position] = 1

    sessions = np.maximum(1, np.rint(arrays["sessions"])).astype(int)
    orders = np.maximum(1, np.rint(sessions * arrays["conversion_rate"])).astype(int)
    conversion = orders / sessions
    aov = np.rint(arrays["aov"]).astype(int)
    nmv = orders.astype(float) * aov
    failure = np.clip(arrays["service_failure_rate"], 0.0, 1.0)

    target_orders = np.rint(target_sessions * target_conversion).astype(int)
    target_nmv = target_orders.astype(float) * np.rint(target_aov)

    frame = pd.DataFrame(
        {
            "week_start": week_start,
            "source_row_id": [f"SYN-W{position + 1:03d}" for position in index],
            "sessions": sessions,
            "orders": orders,
            "conversion_rate": conversion,
            "aov": aov,
            "nmv": nmv,
            "service_failure_rate": failure,
            "target_sessions": np.rint(target_sessions).astype(int),
            "target_orders": target_orders,
            "target_conversion_rate": target_conversion,
            "target_aov": np.rint(target_aov).astype(int),
            "target_nmv": target_nmv,
            "target_service_failure_rate": target_failure,
        }
    )
    for metric, column in ANOMALY_COLUMNS.items():
        frame[column] = labels[metric]
    return frame
