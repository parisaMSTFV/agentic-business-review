from pathlib import Path

import pandas as pd
import pytest

from business_review.review import ReviewDecisionError, apply_review_decisions


def _write_claims(path: Path) -> None:
    pd.DataFrame(
        [
            {"claim_id": "C-1", "review_status": "pending_human_review", "metric": "sessions"},
            {"claim_id": "C-2", "review_status": "pending_human_review", "metric": "orders"},
        ]
    ).to_csv(path, index=False)


def test_review_decisions_require_explicit_human_fields_and_trigger_no_action(
    tmp_path: Path,
) -> None:
    claims = tmp_path / "claims.csv"
    decisions = tmp_path / "decisions.csv"
    output = tmp_path / "reviewed.csv"
    _write_claims(claims)
    pd.DataFrame(
        [
            {
                "claim_id": "C-1",
                "decision": "approved",
                "reviewer": "Analyst",
                "reviewed_at": "2026-08-14T12:00:00Z",
                "rationale": "Evidence checked",
            }
        ]
    ).to_csv(decisions, index=False)
    summary = apply_review_decisions(claims, decisions, output)
    reviewed = pd.read_csv(output)
    assert reviewed.set_index("claim_id").loc["C-1", "review_status"] == "approved_by_human"
    assert reviewed.set_index("claim_id").loc["C-2", "review_status"] == "pending_human_review"
    assert summary == {
        "claims": 2,
        "decisions_applied": 1,
        "approved": 1,
        "rejected": 0,
        "pending": 1,
        "downstream_actions_triggered": 0,
    }


def test_review_decisions_reject_unknown_claims(tmp_path: Path) -> None:
    claims = tmp_path / "claims.csv"
    decisions = tmp_path / "decisions.csv"
    _write_claims(claims)
    pd.DataFrame(
        [
            {
                "claim_id": "UNKNOWN",
                "decision": "approved",
                "reviewer": "Analyst",
                "reviewed_at": "2026-08-14T12:00:00Z",
                "rationale": "Evidence checked",
            }
        ]
    ).to_csv(decisions, index=False)
    with pytest.raises(ReviewDecisionError, match="unknown claims"):
        apply_review_decisions(claims, decisions, tmp_path / "reviewed.csv")
