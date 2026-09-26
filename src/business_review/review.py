"""Validated human-review state transitions for generated claims."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class ReviewDecisionError(ValueError):
    """Raised when a decision file cannot be applied safely."""


def _reject_formula_prefixed_text(frame: pd.DataFrame, label: str) -> None:
    text = frame.select_dtypes(include=["object", "string"]).astype("string")
    for column in text:
        if text[column].str.strip().str.startswith(("=", "+", "-", "@")).any():
            raise ReviewDecisionError(
                f"{label} column {column} contains a spreadsheet-formula prefix"
            )


def apply_review_decisions(
    claims_path: Path,
    decisions_path: Path,
    output_path: Path,
) -> dict[str, int]:
    """Apply explicit analyst decisions without triggering downstream actions."""
    claims = pd.read_csv(claims_path, dtype={"claim_id": "string"})
    decisions = pd.read_csv(decisions_path, dtype="string")
    _reject_formula_prefixed_text(claims, "Claim")
    _reject_formula_prefixed_text(decisions, "Decision")
    required = {"claim_id", "decision", "reviewer", "reviewed_at", "rationale"}
    claim_required = {"claim_id", "review_status"}
    claim_missing = sorted(claim_required.difference(claims.columns))
    if claim_missing:
        raise ReviewDecisionError(f"Claim file is missing columns: {claim_missing}")
    if claims["claim_id"].isna().any() or claims["claim_id"].duplicated().any():
        raise ReviewDecisionError("Claim file must contain unique populated claim_id values")
    if not claims["review_status"].eq("pending_human_review").all():
        raise ReviewDecisionError("Only a pending claim queue can receive decisions")
    missing = sorted(required.difference(decisions.columns))
    if missing:
        raise ReviewDecisionError(f"Decision file is missing columns: {missing}")
    if decisions.empty:
        raise ReviewDecisionError("Decision file must contain at least one row")
    if decisions["claim_id"].duplicated().any():
        raise ReviewDecisionError("Each claim_id may appear only once in a decision file")
    allowed = {"approved", "rejected"}
    invalid = sorted(set(decisions["decision"].dropna()).difference(allowed))
    if invalid or decisions["decision"].isna().any():
        raise ReviewDecisionError(f"decision must be one of {sorted(allowed)}")
    for column in ("claim_id", "reviewer", "reviewed_at", "rationale"):
        if decisions[column].isna().any() or decisions[column].str.strip().eq("").any():
            raise ReviewDecisionError(f"{column} must be populated for every decision")
    parsed_reviewed_at = pd.to_datetime(decisions["reviewed_at"], errors="coerce", utc=True)
    if parsed_reviewed_at.isna().any():
        raise ReviewDecisionError("reviewed_at must contain valid ISO-8601 timestamps")
    unknown = sorted(set(decisions["claim_id"]).difference(set(claims["claim_id"])))
    if unknown:
        raise ReviewDecisionError(f"Decision file references unknown claims: {unknown}")

    decision_fields = decisions.copy()
    decision_fields["reviewed_at"] = parsed_reviewed_at.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    decision_fields = decision_fields.rename(columns={"decision": "human_decision"})
    result = claims.drop(
        columns=["human_decision", "reviewer", "reviewed_at", "rationale"], errors="ignore"
    ).merge(decision_fields, on="claim_id", how="left")
    result["review_status"] = (
        result["human_decision"]
        .map({"approved": "approved_by_human", "rejected": "rejected_by_human"})
        .fillna(result["review_status"])
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return {
        "claims": len(result),
        "decisions_applied": len(decisions),
        "approved": int(decisions["decision"].eq("approved").sum()),
        "rejected": int(decisions["decision"].eq("rejected").sum()),
        "pending": int(result["review_status"].eq("pending_human_review").sum()),
        "downstream_actions_triggered": 0,
    }
