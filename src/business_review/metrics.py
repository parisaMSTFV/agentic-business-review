"""KPI comparison and decision-status calculations."""

from __future__ import annotations

import pandas as pd

from business_review.config import MetricSpec


def target_status(relative_gap: float, spec: MetricSpec) -> str:
    """Classify a target gap while respecting KPI direction."""
    if abs(relative_gap) <= spec.target_tolerance:
        return "on_track"
    favorable = relative_gap > 0 if spec.direction == "higher" else relative_gap < 0
    return "ahead" if favorable else "behind"


def build_latest_snapshot(
    frame: pd.DataFrame,
    catalog: dict[str, MetricSpec],
) -> pd.DataFrame:
    """Build a one-row-per-KPI comparison for the latest week."""
    if len(frame) < 2:
        raise ValueError("At least two weeks are required for comparison")
    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    records: list[dict[str, object]] = []
    for metric, spec in catalog.items():
        value = float(latest[metric])
        previous_value = float(previous[metric])
        target = float(latest[f"target_{metric}"])
        wow_change = value / previous_value - 1 if previous_value else float("nan")
        target_gap = value / target - 1 if target else float("nan")
        business_change = wow_change if spec.direction == "higher" else -wow_change
        records.append(
            {
                "metric": metric,
                "label": spec.label,
                "direction": spec.direction,
                "value": value,
                "previous_value": previous_value,
                "target": target,
                "wow_change": wow_change,
                "business_change": business_change,
                "target_gap": target_gap,
                "status": target_status(target_gap, spec),
                "current_evidence_id": f"{latest['source_row_id']}:{metric}",
                "previous_evidence_id": f"{previous['source_row_id']}:{metric}",
                "target_evidence_id": f"{latest['source_row_id']}:target_{metric}",
            }
        )
    return pd.DataFrame.from_records(records)


def build_evidence_index(
    frame: pd.DataFrame,
    catalog: dict[str, MetricSpec],
) -> set[str]:
    """Return every valid evidence identifier addressable by generated claims."""
    evidence: set[str] = set()
    for row in frame.itertuples(index=False):
        for metric in catalog:
            evidence.add(f"{row.source_row_id}:{metric}")
            evidence.add(f"{row.source_row_id}:target_{metric}")
    return evidence
