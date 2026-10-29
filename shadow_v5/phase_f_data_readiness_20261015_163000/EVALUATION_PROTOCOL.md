# Evaluation Protocol — Phase F

## 1. Temporal Split & Anti-Leakage
- All time-series facility telemetry must be split temporally (e.g., historical training window preceding evaluation validation/test window).
- Random shuffling across time is strictly prohibited to prevent data leakage.

## 2. Missing Value Handling
- Missing or stale telemetry values must be preserved as missing/null status or explicitly flagged; they must **never** be automatically imputed with zero.

## 3. Ground Truth & Metrics
- In the absence of verified incident ground truth, supervised metrics (Precision, Recall, F1) shall be marked as `NOT_VERIFIED` or restricted to synthetic fixture evaluations (`SYNTHETIC_ONLY`).
- Operational validation will rely on anomaly scoring distribution checks, false alarm rate bounds, and domain baseline comparisons.

## 4. Asset Isolation
- UPS models (`ME_UPS1-3`) and PAC models (`ME_PAC1-4`) maintain independent feature spaces and must not be combined into a single unified model without explicit cross-domain compatibility proof.
