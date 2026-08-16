"""Reproducible figures, HTML dashboard, and run summary."""

from __future__ import annotations

import html
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from business_review.config import MetricSpec

COLORS = {
    "navy": "#17324D",
    "blue": "#3C78A8",
    "teal": "#4A9D8F",
    "amber": "#D69E3D",
    "red": "#C85C5C",
    "green": "#4D8B65",
    "gray": "#6B7280",
    "ivory": "#F7F3EA",
}


def _format_value(value: float, spec: MetricSpec) -> str:
    if spec.format == "percent":
        return f"{value:.2%}"
    if spec.format == "currency":
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
    return f"{value:,.0f}"


def plot_kpi_trends(
    frame: pd.DataFrame,
    catalog: dict[str, MetricSpec],
    output_path: Path,
) -> None:
    """Plot recent actual-versus-target trends for decision-relevant KPIs."""
    metrics = ("sessions", "conversion_rate", "aov", "service_failure_rate")
    recent = frame.tail(26)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.patch.set_facecolor(COLORS["ivory"])
    for axis, metric in zip(axes.flat, metrics, strict=True):
        spec = catalog[metric]
        axis.set_facecolor("#FCFAF5")
        axis.plot(recent["week_start"], recent[metric], color=COLORS["blue"], label="Actual")
        axis.plot(
            recent["week_start"],
            recent[f"target_{metric}"],
            color=COLORS["gray"],
            linestyle="--",
            label="Target",
        )
        anomaly_column = f"injected_{metric}"
        if anomaly_column in recent:
            injected = recent[recent[anomaly_column] == 1]
            axis.scatter(
                injected["week_start"],
                injected[metric],
                color=COLORS["red"],
                marker="D",
                s=34,
                label="Injected anomaly",
                zorder=3,
            )
        axis.set_title(spec.label, loc="left", color=COLORS["navy"], weight="bold")
        axis.grid(alpha=0.18)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="x", rotation=30)
        if metric in {"conversion_rate", "service_failure_rate"}:
            axis.yaxis.set_major_formatter(lambda value, _: f"{value:.1%}")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncols=3,
        frameon=False,
    )
    fig.suptitle(
        "Synthetic KPI trends and known evaluation events",
        color=COLORS["navy"],
        size=16,
        y=0.985,
    )
    fig.subplots_adjust(top=0.82, bottom=0.10, hspace=0.42, wspace=0.18)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_alert_evaluation(
    comparison: pd.DataFrame,
    output_path: Path,
) -> None:
    """Compare baseline and rolling detector classification metrics."""
    long = comparison.melt(
        id_vars="model",
        value_vars=["precision", "recall", "f1"],
        var_name="metric",
        value_name="score",
    )
    pivot = long.pivot(index="metric", columns="model", values="score").reindex(
        ["precision", "recall", "f1"]
    )
    fig, axis = plt.subplots(figsize=(9, 5), constrained_layout=True)
    fig.patch.set_facecolor(COLORS["ivory"])
    pivot.plot(kind="bar", ax=axis, color=[COLORS["gray"], COLORS["teal"]], width=0.72)
    axis.set_title("Alert evaluation on labeled synthetic anomalies", loc="left", weight="bold")
    axis.set_xlabel("")
    axis.set_ylabel("Score")
    axis.set_ylim(0, 1.08)
    axis.grid(axis="y", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(axis="x", rotation=0)
    axis.legend(title="", frameon=False, loc="upper right")
    for container in axis.containers:
        axis.bar_label(container, fmt="%.2f", padding=3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_driver_contributions(contributions: pd.DataFrame, output_path: Path) -> None:
    """Plot signed log-point contributions to the latest NMV change."""
    plot_frame = contributions.copy()
    plot_frame["contribution_pct"] = 100 * plot_frame["contribution_log_points"]
    colors = [
        COLORS["green"] if value >= 0 else COLORS["red"] for value in plot_frame["contribution_pct"]
    ]
    fig, axis = plt.subplots(figsize=(9, 5), constrained_layout=True)
    fig.patch.set_facecolor(COLORS["ivory"])
    bars = axis.barh(plot_frame["driver"], plot_frame["contribution_pct"], color=colors)
    axis.axvline(0, color=COLORS["navy"], linewidth=0.8)
    axis.set_title("Latest week NMV driver decomposition", loc="left", weight="bold")
    axis.set_xlabel("Contribution to log change (percentage points)")
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.bar_label(
        bars,
        fmt="%.2f pp",
        label_type="center",
        color="white",
        fontweight="bold",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_dashboard(
    snapshot: pd.DataFrame,
    claims: pd.DataFrame,
    alerts: pd.DataFrame,
    catalog: dict[str, MetricSpec],
    output_path: Path,
    data_mode: str = "synthetic_evaluation",
) -> None:
    """Render a deterministic, escaped HTML review artifact."""
    cards: list[str] = []
    for row in snapshot.itertuples(index=False):
        spec = catalog[row.metric]
        status_class = html.escape(str(row.status), quote=True)
        cards.append(
            "<article class='card'>"
            f"<p class='label'>{html.escape(spec.label)}</p>"
            f"<p class='value'>{html.escape(_format_value(row.value, spec))}</p>"
            f"<p class='delta'>{row.wow_change:+.1%} WoW · {row.target_gap:+.1%} vs target</p>"
            f"<span class='status {status_class}'>{status_class.replace('_', ' ')}</span>"
            "</article>"
        )

    claim_rows: list[str] = []
    for row in claims.head(12).itertuples(index=False):
        claim_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.claim_id))}</td>"
            f"<td>{html.escape(str(row.claim_type).replace('_', ' '))}</td>"
            f"<td>{html.escape(str(row.metric))}</td>"
            f"<td>{row.change:+.2%}</td>"
            f"<td>{html.escape(str(row.status).replace('_', ' '))}</td>"
            f"<td><code>{html.escape(str(row.evidence_ids))}</code></td>"
            "</tr>"
        )

    recent_alerts = alerts[alerts["is_alert"] == 1].tail(8)
    alert_rows = "".join(
        "<tr>"
        f"<td>{html.escape(pd.Timestamp(row.week_start).date().isoformat())}</td>"
        f"<td>{html.escape(str(row.metric))}</td>"
        f"<td>{row.target_residual:+.1%}</td>"
        f"<td>{row.anomaly_score:+.2f}</td>"
        f"<td><code>{html.escape(str(row.evidence_id))}</code></td>"
        "</tr>"
        for row in recent_alerts.itertuples(index=False)
    )

    title = (
        "Synthetic Weekly Business Review"
        if data_mode == "synthetic_evaluation"
        else "Weekly Business Review"
    )
    data_notice = (
        "Labeled synthetic evaluation data"
        if data_mode == "synthetic_evaluation"
        else "Supplied KPI input · alert accuracy not evaluated"
    )
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --navy:#17324D; --blue:#3C78A8; --teal:#4A9D8F; --red:#C85C5C;
--green:#4D8B65; --amber:#D69E3D; --ink:#24313F; --muted:#667085; --ivory:#F7F3EA; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--ivory); color:var(--ink);
font-family:Inter,ui-sans-serif,system-ui,sans-serif; }} main {{ max-width:1180px; margin:auto; padding:40px 24px 64px; }}
header {{ border-left:6px solid var(--teal); padding-left:18px; margin-bottom:28px; }}
h1 {{ margin:0 0 8px; color:var(--navy); }} header p {{ margin:0; color:var(--muted); }}
.notice {{ background:#FFF7E5; border:1px solid #E9C46A; padding:12px 16px; border-radius:10px; margin:22px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
.card {{ background:white; border:1px solid #E4E0D7; border-radius:12px; padding:17px; }}
.label {{ color:var(--muted); margin:0; font-size:.86rem; }} .value {{ color:var(--navy); font-size:1.55rem; margin:7px 0; font-weight:700; }}
.delta {{ margin:0 0 9px; font-size:.86rem; }} .status {{ display:inline-block; padding:3px 8px; border-radius:999px; font-size:.75rem; }}
.ahead {{ background:#E5F4EA; color:#2F6D47; }} .on_track {{ background:#E5F0F6; color:#315F7A; }} .behind {{ background:#F9E6E4; color:#933D38; }}
section {{ margin-top:30px; }} h2 {{ color:var(--navy); font-size:1.2rem; }} .table-wrap {{ overflow:auto; background:white; border-radius:12px; border:1px solid #E4E0D7; }}
table {{ width:100%; border-collapse:collapse; font-size:.84rem; }} th,td {{ padding:11px 12px; border-bottom:1px solid #ECE8DF; text-align:left; white-space:nowrap; }}
th {{ background:#F1EEE6; color:var(--navy); }} code {{ color:#315F7A; }} footer {{ margin-top:34px; color:var(--muted); font-size:.82rem; }}
@media (max-width:800px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main>
<header><h1>{title}</h1><p>Deterministic KPI checks, statistical alerts, driver decomposition, and evidence-linked review claims.</p></header>
<div class="notice"><strong>Human review required.</strong> Driver contributions are descriptive and anomaly alerts are signals, not causal diagnoses.</div>
<div class="grid">{"".join(cards)}</div>
<section><h2>Structured review claims</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>Type</th><th>Metric</th><th>Change</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{"".join(claim_rows)}</tbody></table></div></section>
<section><h2>Recent statistical alerts</h2><div class="table-wrap"><table><thead><tr><th>Week</th><th>Metric</th><th>Vs target</th><th>Score</th><th>Evidence</th></tr></thead><tbody>{alert_rows}</tbody></table></div></section>
<footer>{data_notice} · no autonomous action · analyst decisions are applied through the governed review command.</footer>
</main></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_run_summary(
    detector: dict[str, float | int],
    baseline: dict[str, float | int],
    traceability: dict[str, object],
    rows: int,
    fingerprint: str,
    output_path: Path,
) -> None:
    """Write a short Markdown summary using only executed results."""
    text = f"""# Reproduction summary

- Synthetic weeks: {rows}
- Rolling detector precision: {detector["precision"]:.3f}
- Rolling detector recall: {detector["recall"]:.3f}
- Rolling detector F1: {detector["f1"]:.3f}
- Fixed-rule baseline F1: {baseline["f1"]:.3f}
- Claim-to-source traceability: {traceability["coverage"]:.1%}
- Deterministic core artifact fingerprint: `{fingerprint}`

These values describe the checked-in synthetic evaluation only. They do not estimate production accuracy, causal root-cause quality, time savings, or business impact.
"""
    output_path.write_text(text, encoding="utf-8")
