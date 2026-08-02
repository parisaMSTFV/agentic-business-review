# Interview discussion guide

## What the project proves

The project demonstrates how to separate deterministic KPI calculations from review-oriented narrative artifacts. Each generated claim has structured values and evidence identifiers. Statistical alerts are evaluated against known synthetic events, while driver contributions are explicitly described as decomposition rather than causal root-cause analysis.

## Decisions to explain

- Why the alert score uses prior residual history and shifts the rolling window to prevent future leakage.
- Why a fixed percentage-to-target rule is retained as a baseline.
- Why KPI direction belongs in a metric catalog instead of being inferred from the sign of change.
- Why multiplicative NMV drivers are decomposed in log space.
- Why every claim remains pending human review even when its values are traceable.
- Why synthetic evaluation supports reproducibility but cannot estimate production performance or business impact.
