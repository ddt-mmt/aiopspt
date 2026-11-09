# Data Quality and Uncertainty Policy

## 1. Principles
- **No Silent Imputation:** Missing values, NaN, and Inf must never be silently fabricated.
- **Staleness Tracking:** Predictions based on stale telemetry must be flagged or withheld.
- **Uncertainty States:** The system must explicitly output confidence categories (`HIGH_CONFIDENCE`, `MODERATE_CONFIDENCE`, `LOW_CONFIDENCE`, `UNRELIABLE_INPUT`, `OUT_OF_DISTRIBUTION`, `INSUFFICIENT_DATA`).
