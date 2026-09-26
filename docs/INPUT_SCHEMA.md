# Weekly KPI input contract

`business-review run` accepts a UTF-8 CSV under contract `weekly-kpi-v1.0`. The checked-in `examples/weekly_kpis.csv` is synthetic and exists only as an executable contract fixture.

## Required columns

| Field | Type | Rule |
|---|---|---|
| `week_start` | date | Unique, ascending, no time component, complete seven-day cadence |
| `source_row_id` | string | Populated, unique, and not prefixed by `=`, `+`, `-`, or `@`; becomes part of each evidence ID |
| `sessions`, `orders`, `conversion_rate`, `aov`, `nmv`, `service_failure_rate` | numeric | Finite and non-negative; rates are between zero and one |
| `target_<metric>` | numeric | Finite and strictly positive for all six metrics |

At least 14 rows are required so a 12-week shifted rolling history can score later observations. `orders` must reconcile to rounded `sessions × conversion_rate` within one order, and `nmv` must reconcile to `orders × aov` within numeric tolerance.

## Execution boundary

The supplied-input path records the input filename, SHA-256 checksum, row count, and contract version. It does not require or infer anomaly labels, so precision, recall, F1, and business impact are not reported. The validated input is copied only into the caller-selected output directory; identifiers remain present in evidence and claim artifacts, so use appropriately governed IDs.

Claims always start as `pending_human_review`. A separate `apply-decisions` command accepts explicit analyst decisions and writes a new reviewed artifact. It triggers no downstream action.

## Decision file

The decision CSV requires `claim_id`, `decision`, `reviewer`, `reviewed_at`, and `rationale`. `decision` is either `approved` or `rejected`; timestamps must be ISO-8601. Partial review is allowed, unknown or duplicate claim IDs fail validation, and undecided claims remain pending. Text beginning with spreadsheet-formula characters (`=`, `+`, `-`, or `@`) is rejected before a reviewed CSV is written.
