# V12 STAGING GRAFANA DASHBOARD ARCHITECTURE (DESIGN-ONLY)

## 1. Overview
This architecture defines the staging visualization panels for V12 live-shadow inferences. All panels are explicitly tagged with `STAGING LIVE SHADOW — NOT PRODUCTION OUTPUT`.

## 2. Panels
1. **V12 Health Score Index**: Time series per host (`ME_UPS1` - `ME_UPS3`, `ME_PAC1` - `ME_PAC4`), range 0-100.
2. **Anomaly Status & Score**: Binary anomaly state and Isolation Forest raw scores.
3. **Data Quality & Freshness**: Status indicator (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`) and data age.
4. **Inference Availability & Execution Rate**: Success vs. skipped inference counts.
5. **Model Version & Provenance**: Stat panel displaying model version `12.0-candidate` and SHA-256 hash.
