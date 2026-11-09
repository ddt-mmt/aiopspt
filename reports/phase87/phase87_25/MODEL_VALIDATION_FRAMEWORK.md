# Model Validation Framework

## 1. Success Criteria
Success is measured across multiple dimensions:
- **Predictive Quality:** MAE, RMSE, prediction interval coverage.
- **Detection Quality:** Precision, Recall, F1, false positive rate.
- **Adaptive Behavior:** Adaptation latency, stability, change-point responsiveness.
- **Reliability:** Inference latency, data coverage, drift detection.
- **Calibration:** Verification that confidence scores align with observed error rates.

## 2. Non-Fabrication Mandate
When ground truth is absent, RUL and accuracy metrics are marked `NOT_MEASURABLE`. Accuracy is never fabricated.
