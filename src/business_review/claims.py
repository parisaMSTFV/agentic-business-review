"""Create structured review claims and validate evidence lineage."""

from __future__ import annotations

import pandas as pd


def build_claims(
    snapshot: pd.DataFrame,
    alerts: pd.DataFrame,
    driver_contributions: pd.DataFrame,
) -> pd.DataFrame:
    """Create deterministic claim records that remain pending human review."""
    records: list[dict[str, object]] = []
    for row in snapshot.itertuples(index=False):
        records.append(
            {
                "claim_id": f"CLAIM-KPI-{row.metric.upper()}",
                "claim_type": "latest_kpi_status",
                "metric": row.metric,
                "value": row.value,
                "reference_value": row.target,
                "change": row.target_gap,
                "status": row.status,
                "evidence_ids": f"{row.current_evidence_id}|{row.target_evidence_id}",
                "review_status": "pending_human_review",
            }
        )

    recent_cutoff = pd.Timestamp(alerts["week_start"].max()) - pd.Timedelta(weeks=7)
    recent_alerts = alerts[(alerts["week_start"] >= recent_cutoff) & (alerts["is_alert"] == 1)]
    for position, row in enumerate(recent_alerts.itertuples(index=False), start=1):
        records.append(
            {
                "claim_id": f"CLAIM-ALERT-{position:02d}",
                "claim_type": "statistical_alert",
                "metric": row.metric,
                "value": row.value,
                "reference_value": row.target,
                "change": row.target_residual,
                "status": "requires_review",
                "evidence_ids": row.evidence_id,
                "review_status": "pending_human_review",
            }
        )

    for position, row in enumerate(driver_contributions.itertuples(index=False), start=1):
        records.append(
            {
                "claim_id": f"CLAIM-DRIVER-{position:02d}",
                "claim_type": "nmv_driver_contribution",
                "metric": row.driver,
                "value": row.current_value,
                "reference_value": row.previous_value,
                "change": row.contribution_log_points,
                "status": "descriptive_not_causal",
                "evidence_ids": row.evidence_ids,
                "review_status": "pending_human_review",
            }
        )
    return pd.DataFrame.from_records(records)


def traceability_metrics(claims: pd.DataFrame, evidence_index: set[str]) -> dict[str, object]:
    """Measure whether every claim resolves to one or more valid evidence IDs."""
    if claims.empty:
        return {"claim_count": 0, "traceable_claims": 0, "coverage": 0.0, "missing": []}
    traceable = 0
    missing: list[str] = []
    for row in claims.itertuples(index=False):
        evidence_ids = [item for item in str(row.evidence_ids).split("|") if item]
        unresolved = sorted(set(evidence_ids).difference(evidence_index))
        if evidence_ids and not unresolved:
            traceable += 1
        else:
            missing.extend(f"{row.claim_id}:{item}" for item in unresolved or ["EMPTY"])
    return {
        "claim_count": len(claims),
        "traceable_claims": traceable,
        "coverage": traceable / len(claims),
        "missing": missing,
    }
