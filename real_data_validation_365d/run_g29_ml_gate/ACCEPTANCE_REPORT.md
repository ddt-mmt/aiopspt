# Acceptance Report — Phase G.29 Isolated ML Dataset Quality Gate (`ACCEPTANCE_REPORT.md`)

- **Timestamp:** 2026-10-16T13:26:02.443756+00:00
- **Status Final:** **`READY_FOR_ISOLATED_ML_TRAINING`**
- **Valid Events Count:** 180
- **Unique Incident IDs:** 180 (Unique Check: True)
- **Recovered Events:** 89
- **Active Events:** 91
- **Sensor Coverage:** 26368 total sensor records sampled across 7 hosts.
- **Data Leakage Check:** PASSED (Strict pre-event feature windowing enforced; no future sensor values utilized).
- **Temporal Split:** Train (125), Validation (28), Test (27).
- **Baseline Metrics:** Precision (0.78), Recall (0.72), F1-score (0.75).
- **Safety Compliance:** Production changes = 0, Zabbix writes = 0, Restarts = 0.
