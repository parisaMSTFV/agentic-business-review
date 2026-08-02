from pathlib import Path

import pandas as pd

from business_review.config import MetricSpec
from business_review.reporting import render_dashboard


def test_html_renderer_escapes_user_controlled_text(tmp_path: Path) -> None:
    catalog = {
        "sessions": MetricSpec(
            name="sessions",
            label="<script>alert(1)</script>",
            direction="higher",
            format="integer",
            target_tolerance=0.02,
        )
    }
    snapshot = pd.DataFrame(
        [
            {
                "metric": "sessions",
                "value": 100.0,
                "wow_change": 0.1,
                "target_gap": 0.0,
                "status": "on_track",
            }
        ]
    )
    claims = pd.DataFrame(
        [
            {
                "claim_id": "<img src=x onerror=alert(1)>",
                "claim_type": "status",
                "metric": "sessions",
                "change": 0.0,
                "status": "review",
                "evidence_ids": "SYN-W001:sessions",
            }
        ]
    )
    alerts = pd.DataFrame(
        columns=[
            "week_start",
            "metric",
            "target_residual",
            "anomaly_score",
            "evidence_id",
            "is_alert",
        ]
    )
    output = tmp_path / "review.html"
    render_dashboard(snapshot, claims, alerts, catalog, output)
    content = output.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in content
    assert "<img src=x onerror=alert(1)>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
