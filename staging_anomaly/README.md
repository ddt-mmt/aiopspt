# Phase G.37 — AIOps Staging Anomaly Detection & Dashboard

## Overview
This directory (`/root/grafan_aiops/staging_anomaly/`) contains an isolated staging implementation for UPS and PAC telemetry anomaly detection and operational monitoring, adhering strictly to Phase G.37 specifications.

- **Objective:** Telemetry anomaly detection and sensor health monitoring (`ME_UPS1`–`ME_UPS3`, `ME_PAC1`–`ME_PAC4`).
- **Safety Status:** Production-safe. 0 production changes, 0 service restarts, 0 Zabbix write operations.
- **Methodology:** Robust Z-score (MAD threshold 3.5) and Isolation Forest (contamination 0.05) based on G.36 baseline.

---

## Directory Contents
- `staging_detector.py`: Core anomaly detection script reading local CSV exports read-only.
- `test_staging_e2e.py`: End-to-end test script verifying parsing, detection, outputs, and JSON validity.
- `staging_facility_dashboard.json`: Grafana dashboard JSON configuration.
- `rollback_staging.sh`: Rollback script to cleanly remove staging artifacts.
- `output/`: Generated detection summaries, health CSVs, detected anomalies CSV, and SHA-256 checksums.

---

## Instructions

### 1. How to Run the Staging Detector
Execute the detector script directly using Python 3:
```bash
python3 /root/grafan_aiops/staging_anomaly/staging_detector.py
```

### 2. How to Run End-to-End Tests
Execute the E2E test suite to validate execution and output integrity:
```bash
python3 /root/grafan_aiops/staging_anomaly/test_staging_e2e.py
```

### 3. How to Inspect Results
Review generated results in `/root/grafan_aiops/staging_anomaly/output/`:
- `staging_detection_summary.json`: High-level execution summary and metrics.
- `staging_sensor_health.csv`: Sensor-level data quality, sample count, and status.
- `staging_anomalies_detected.csv`: Individual flagged anomalies with timestamps and Robust Z-scores.
- `SHA256SUMS.txt`: Cryptographic checksums of output artifacts.

### 4. How to Stop and Rollback Staging
To remove all staging files and clean up the environment:
```bash
bash /root/grafan_aiops/staging_anomaly/rollback_staging.sh
```

---

## Operational Disclaimer
Detected anomalies represent statistical deviations from baseline telemetry patterns and **do NOT** automatically imply physical equipment failure or Remaining Useful Life (RUL) expiration.
