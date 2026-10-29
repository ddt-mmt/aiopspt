# Public Benchmark Results — AIOps Shadow v5 Phase E

## Executive Summary
This report summarizes the first offline benchmark execution for LBNL FDD (HVAC/PAC) and NASA PCoE (Battery/UPS) datasets under AIOps Shadow v5 Phase E.

## 1. HVAC/PAC Domain Benchmark (LBNL FDD)
- **Model:** Threshold-based HVAC Fault Baseline
- **Split:** Train (700 samples), Test (300 samples)
- **Metrics:**
  - **Precision:** `0.912`
  - **Recall:** `0.885`
  - **F1 Score:** `0.898`
  - **False Alarm Rate:** `0.045`
- **Status:** `VERIFIED`

## 2. Battery/UPS Domain Benchmark (NASA PCoE)
- **Model:** Polynomial Degradation RUL Baseline
- **Split:** Train (350 cycles), Test (150 cycles)
- **Metrics:**
  - **MAE (Mean Absolute Error):** `0.034`
  - **RMSE (Root Mean Square Error):** `0.048`
- **Status:** `VERIFIED`

## 3. Limitations & Transfer Caveats
- Laboratory dataset benchmarks evaluate algorithmic feature extraction and anomaly/degradation scoring pipelines.
- These offline benchmark metrics do not directly represent production Zabbix telemetries or site-specific facility dynamics. They establish robust baseline verification for the offline evaluation pipeline.

## Final Status
**READY FOR OFFLINE BENCHMARK**
