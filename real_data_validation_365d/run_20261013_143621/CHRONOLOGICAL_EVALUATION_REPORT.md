# Chronological AIOps Evaluation Report

## Evaluation Methodology
Models were evaluated using chronological splits (70% train / 15% val / 15% holdout) to prevent data leakage.
Multivariate feature scaling and Isolation Forest training were conducted exclusively on the training slice.

## Results Summary
- **Stationarity & Numeric Stability:** Continuous sensor streams (`return.temp.c`, `supply.temp.c`, `output.load`) show stable distributions within operational thresholds.
- **Anomaly Scoring:** Isolation Forest produces stable anomaly scores consistent with expected facility baselines.
- **TTF Heuristics:** Time-to-Failure estimation successfully abstains (`None`) during flat or stable trends, preventing false alarms.
