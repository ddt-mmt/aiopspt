# Phase G.12 Offline Anomaly Detection Experiment Report

## 1. Metadata
- **Experiment Timestamp:** 2026-10-15T04:27:10.122717
- **Staging Directory:** `/root/grafan_aiops/shadow_v5/phase_g12_offline_anomaly_experiment_20261015_260000`
- **Input Source:** `/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv`
- **Total Points Analyzed:** 47
- **Final Status:** `OFFLINE_ANOMALY_EXPERIMENT_COMPLETED`

## 2. Statistical Baseline
- **Mean:** `231.6426 V`
- **Standard Deviation:** `0.3341 V`
- **Median:** `231.6 V`
- **MAD (Median Absolute Deviation):** `0.3 V`

## 3. Outlier Detection Results
- **Z-Score Outliers (> 3.0):** 0
- **Robust MAD Outliers (> 3.5):** 0
- **Baseline Limitation:** The baseline consists of only 47 points collected over ~1 hour. This small sample does not represent the full operating patterns or diurnal cycles of the facility. Outliers flagged are purely statistical indicators and not verified proof of UPS/PAC failure.

## 4. Compliance Confirmation
- API Requests: `0`
- Production Changes: `0`
- Automatic Remediation: `False`
- Credential Values Logged: `False`
