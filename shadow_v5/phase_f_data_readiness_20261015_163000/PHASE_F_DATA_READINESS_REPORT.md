# Phase F Data Readiness Report — AIOps Shadow v5

## Executive Summary
This report establishes the data readiness and facility telemetry evaluation design for **AIOps Shadow v5**, covering UPS (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`) and PAC (`ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`) assets. All analysis, designs, and offline tests are strictly isolated within `/root/grafan_aiops/shadow_v5/phase_f_data_readiness_20261015_163000/`. Zero Zabbix API calls or production alterations were performed.

## 1. Pipeline Audit (Phase E.1 & E.2 Review)
- **Data Origin:** Phase E.1/E.2 utilized generated offline synthetic fixtures (`SYNTHETIC_TEST_DATA`) to validate pipeline code logic, rather than live public datasets (`ACCESS_REQUIRED`).
- **Preprocessing:** Standard scalar / rule-based cleaning, with strict preservation of missing states without automatic zero imputation.
- **Baselines:** Threshold rule-based classifiers for HVAC/PAC and linear degradation models for battery/UPS.
- **Evaluation Splits:** Temporal splitting for time-series / HVAC data and sequential splitting for battery degradation, preventing train/test data leakage.
- **Metric Definitions:** Programmatically computed Precision, Recall, F1, False Alarm Rate, MAE, and RMSE from test arrays.

## 2. Facility Telemetry Scope & Asset Taxonomy
- **UPS Assets:** `ME_UPS1`, `ME_UPS2`, `ME_UPS3`
- **PAC Assets:** `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`
- **Data Taxonomy:** Distinguished between analog metrics (temperatures, voltages, currents, airflow), discrete status flags (operational state, alarm flags), cumulative counters, and derived health indices.

## 3. Readiness Status
**READY_FOR_READONLY_DATA_REVIEW**
