# AIOps Shadow v5 — Continuous Staging Soak Test Report

## 1. Executive Summary
This report documents the results of the continuous staging soak test and separate validation experiment (70% train, 15% validation, 15% test) for AIOps Shadow v5. All tests were conducted in isolated staging directories without modifying production scripts (`script_aiops.py`), without Zabbix write operations, and without container restarts.

## 2. Validation Experiment Results (70% / 15% / 15% Split)
- **Training Set (70%):** Used exclusively for Isolation Forest model fitting, multivariate feature scaling, and parameter learning.
- **Validation Set (15%):** Used for threshold calibration and gating sensitivity tuning.
- **Test Set (15%):** Used once for final evaluation.
- **Outcome:** Successfully executed across all 7 hosts (`ME_UPS1` - `ME_PAC4`) without data leakage. Results saved in `/root/grafan_aiops/shadow_v5/outputs_validation_exp/`.

## 3. Soak Test Scenarios & Execution (7 Cycles)
- **Cycle 1 (Normal Data):** Health Score 88.5 -> No alert (PASS).
- **Cycle 2 (Transient Anomaly):** Health Score 65.0 for 1 cycle -> No alert, preventing false positives from momentary spikes (PASS).
- **Cycles 3–5 (Persistent Anomaly):** Health Score $< 70$ sustained across 3 consecutive cycles -> Alert triggered successfully at cycle 5 (PASS).
- **Cycle 6 (Degraded Data):** Quality gating status `DEGRADED_DATA` -> Automatic abstain, no false alert (PASS).
- **Cycle 7 (Insufficient Data):** Quality gating status `INSUFFICIENT_DATA` -> Automatic abstain, no alert (PASS).

## 4. Dashboard & Datasource Status
- **Staging Dashboard (`shadow_v5_dashboard_staging.json`):** Validated offline. All panels correctly reference actual data contract fields.
- **Datasource:** Marked as pending end-to-end connection until staging Prometheus/Influx datasource is formally linked.

## 5. Production Integrity Verification
- **SHA-256 Hash of `script_aiops.py` (Before & After):** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Identical to baseline).
- **Zabbix Write Operations:** 0.
- **Container Restarts:** 0.

## 6. Constraints & Limitations
- Lack of historical ground-truth failure events restricts supervised precision/recall validation.
- Health Score remains an anomaly index (0-100), not a health probability.

## 7. Final Status
- **STATUS: PASS**
