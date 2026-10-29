# Zabbix 365-Day Read-Only Audit

- Zabbix version: 7.0.23
- Requested UTC range: 2026-10-12T07:34:09+00:00 to 2026-10-13T07:34:09+00:00
- Hosts found: 7/7
- Relevant items audited: 0
- Items with returned history: 0
- Unique records exported: 0
- API discovery errors: 0
- Zabbix writes: 0
- Production AIOps script modified: no

## Interpretation limits

Observed span is based on first and last returned raw history samples. It does not prove continuous coverage. Review sampling intervals, gaps, possible truncation, and API errors. This script exports raw history only; it does not silently substitute hourly trends. A missing result may indicate unavailable history, API permissions, unsupported item types, or an item key not covered by discovery. Predictive accuracy, TTF accuracy, precision, recall, and lead time cannot be established without independent ground truth.

## Files

- `DATA_AVAILABILITY_365D.csv`
- `ITEM_COVERAGE_365D.csv`
- `DATA_QUALITY_365D.csv`
- `ZABBIX_EXPORT_MANIFEST.csv`
- `API_ERRORS.csv`
- `AUDIT_METADATA.json`
- `exports/`
