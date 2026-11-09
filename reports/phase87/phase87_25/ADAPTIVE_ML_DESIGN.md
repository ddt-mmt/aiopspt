# Adaptive ML Design

## 1. Architectural Objectives
The Adaptive ML Engine provides:
- **State Detection:** Normal, Degraded, Abnormal, Maintenance, Unknown, Insufficient Data.
- **Operating Regime Recognition:** Differentiating load states, startup/shutdown, and environmental shifts.
- **Manufacturer Baseline Deviation:** Evaluating telemetry against recommended vs. safety limits.
- **Unsupervised Anomaly Detection:** Isolation forest, EWMA, and rolling statistics for change-point and trend deviation detection.
- **Multi-Horizon Prediction:** 5m, 15m, 30m, 1h, 6h, 24h horizons with explicit confidence and uncertainty metrics.
