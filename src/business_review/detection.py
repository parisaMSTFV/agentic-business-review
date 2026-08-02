"""Leakage-safe anomaly detection and labeled evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from business_review.synthetic import ANOMALY_COLUMNS


def detect_anomalies(
    frame: pd.DataFrame,
    metrics: tuple[str, ...] = tuple(ANOMALY_COLUMNS),
    window: int = 12,
    threshold: float = 3.5,
    minimum_scale: float = 0.004,
) -> pd.DataFrame:
    """Score target residuals using only the prior rolling window."""
    if window < 4:
        raise ValueError("window must be at least four")
    if threshold <= 0 or minimum_scale <= 0:
        raise ValueError("threshold and minimum_scale must be positive")

    results: list[pd.DataFrame] = []
    for metric in metrics:
        target_column = f"target_{metric}"
        label_column = ANOMALY_COLUMNS[metric]
        residual = frame[metric] / frame[target_column] - 1
        historical = residual.shift(1)
        center = historical.rolling(window, min_periods=window).mean()
        scale = historical.rolling(window, min_periods=window).std(ddof=0)
        safe_scale = scale.clip(lower=minimum_scale)
        score = (residual - center) / safe_scale
        valid = score.notna()
        metric_result = pd.DataFrame(
            {
                "week_start": frame.loc[valid, "week_start"].to_numpy(),
                "source_row_id": frame.loc[valid, "source_row_id"].to_numpy(),
                "metric": metric,
                "value": frame.loc[valid, metric].to_numpy(),
                "target": frame.loc[valid, target_column].to_numpy(),
                "target_residual": residual.loc[valid].to_numpy(),
                "anomaly_score": score.loc[valid].to_numpy(),
                "is_alert": score.loc[valid].abs().ge(threshold).astype(int).to_numpy(),
                "injected_anomaly": frame.loc[valid, label_column].astype(int).to_numpy(),
            }
        )
        metric_result["evidence_id"] = (
            metric_result["source_row_id"] + ":" + metric_result["metric"]
        )
        results.append(metric_result)
    return pd.concat(results, ignore_index=True)


def baseline_alerts(alert_frame: pd.DataFrame, threshold: float = 0.12) -> pd.DataFrame:
    """Apply a simple fixed percentage-to-target rule as a baseline."""
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    result = alert_frame.copy()
    result["is_alert"] = result["target_residual"].abs().ge(threshold).astype(int)
    result["anomaly_score"] = np.nan
    return result


def evaluate_alerts(alert_frame: pd.DataFrame) -> dict[str, float | int]:
    """Calculate classification metrics from injected synthetic labels."""
    actual = alert_frame["injected_anomaly"].astype(int)
    predicted = alert_frame["is_alert"].astype(int)
    tp = int(((actual == 1) & (predicted == 1)).sum())
    fp = int(((actual == 0) & (predicted == 1)).sum())
    fn = int(((actual == 1) & (predicted == 0)).sum())
    tn = int(((actual == 0) & (predicted == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    false_alert_rate = fp / (fp + tn) if fp + tn else 0.0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alert_rate": false_alert_rate,
    }
