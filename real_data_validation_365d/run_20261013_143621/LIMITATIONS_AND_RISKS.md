# Limitations and Risks

1. **Absence of Failure Ground Truth:** Zero failure events in the 365-day dataset prevent empirical calculation of Precision, Recall, and Lead Time.
2. **Sparse Sensor Data:** UPS `battery.capacity` updates infrequently (few hundred samples/year), requiring careful handling (`ffill(limit=2)` or skipping) to avoid false interpolation.
3. **Health Score Interpretation:** Health Score is a multivariate anomaly index (0-100), not a statistical probability of survival.
4. **TTF Heuristic:** Linear regression slope TTF is an experimental heuristic, not a certified Remaining Useful Life (RUL).
