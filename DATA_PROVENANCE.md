# Data provenance

All checked-in row-level data and executable examples in this repository are synthetic. The labeled benchmark is generated locally by `src/business_review/synthetic.py`; `examples/weekly_kpis.csv` is a label-free slice with renamed example identifiers used to exercise the supplied-input contract.

The generator creates 64 fictional weekly observations for sessions, orders, conversion rate, average order value, net merchandise value, and service failure rate. Smooth target series represent an illustrative planning baseline. Random noise uses NumPy's deterministic generator with seed 42. Seven events are deliberately injected across four monitored metrics to provide labeled ground truth for alert evaluation.

No source data was sampled, transformed, aggregated, or copied from an employer, customer, production database, private dashboard, or third-party dataset. Identifiers beginning with `SYN-` are generated row keys and do not refer to real entities.

The `business-review run` command can process a caller-supplied CSV without changing the checked-in dataset. It records the input filename, SHA-256 checksum, row count, and contract version in the selected output directory. Supplied inputs have no assumed anomaly ground truth, so the pipeline does not report alert accuracy for them.
