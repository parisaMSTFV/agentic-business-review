"""Exact multiplicative driver decomposition for weekly NMV change."""

from __future__ import annotations

import math

import pandas as pd


def decompose_latest_nmv_change(frame: pd.DataFrame) -> pd.DataFrame:
    """Decompose log NMV change into sessions, conversion, and AOV drivers."""
    if len(frame) < 2:
        raise ValueError("At least two weeks are required for driver analysis")
    previous = frame.iloc[-2]
    current = frame.iloc[-1]
    driver_metrics = ("sessions", "conversion_rate", "aov")
    records: list[dict[str, object]] = []
    for metric in driver_metrics:
        before = float(previous[metric])
        after = float(current[metric])
        if before <= 0 or after <= 0:
            raise ValueError(f"{metric} must be positive for log decomposition")
        records.append(
            {
                "driver": metric,
                "previous_value": before,
                "current_value": after,
                "contribution_log_points": math.log(after / before),
                "evidence_ids": (
                    f"{previous['source_row_id']}:{metric}|{current['source_row_id']}:{metric}"
                ),
            }
        )
    result = pd.DataFrame.from_records(records)
    nmv_log_change = math.log(float(current["nmv"]) / float(previous["nmv"]))
    result["nmv_log_change"] = nmv_log_change
    result["reconciliation_error"] = result["contribution_log_points"].sum() - nmv_log_change
    return result
