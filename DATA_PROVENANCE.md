# Data provenance

All data in this repository is synthetic and generated locally by `src/business_review/synthetic.py`.

The generator creates 64 fictional weekly observations for sessions, orders, conversion rate, average order value, net merchandise value, and service failure rate. Smooth target series represent an illustrative planning baseline. Random noise uses NumPy's deterministic generator with seed 42. Seven events are deliberately injected across four monitored metrics to provide labeled ground truth for alert evaluation.

No source data was sampled, transformed, aggregated, or copied from an employer, customer, production database, private dashboard, or third-party dataset. Identifiers beginning with `SYN-` are generated row keys and do not refer to real entities.
