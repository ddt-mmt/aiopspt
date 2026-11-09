# Device Digital Profile Specification

## 1. Purpose
Each individual equipment asset maintains a distinct **Device Digital Profile** combining static manufacturer baselines with dynamic operational telemetry, data quality metrics, learning mode (`INDIVIDUAL_DEVICE_MODEL` vs `EQUIPMENT_FAMILY_MODEL`), and prediction history.

## 2. Profile Components
- **Identity & Versioning:** Equipment ID, profile version, commissioning reference.
- **Operational Baseline:** Learned mean load, operating regimes recognized (e.g., normal load, high load, startup, abnormal temperature), seasonal variation patterns.
- **Data Quality Tracker:** Completeness ratio, staleness ratio, anomaly status (`NO_ANOMALY`, `INSUFFICIENT_DATA`, `SENSOR_UNAVAILABLE`, etc.).
- **Model Registry Link:** Active model version ID and performance tracking.
