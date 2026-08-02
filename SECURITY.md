# Security and publication boundary

This public case study has no network integration, credentials, model endpoint, or database connector. The default pipeline runs offline from generated synthetic data.

The CI-sensitive-content check scans tracked text for common credential and private-infrastructure patterns. HTML output escapes labels, claim fields, metric names, and evidence identifiers before rendering.

Do not add real business-review exports, customer data, internal queries, private URLs, screenshots, credentials, or production configuration to this repository.
