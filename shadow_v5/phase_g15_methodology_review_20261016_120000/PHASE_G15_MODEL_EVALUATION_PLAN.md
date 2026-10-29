# Phase G.15 Model Evaluation & Pipeline Plan

## 1. Staged Pipeline Design
To transition from unsupervised anomaly detection to robust predictive maintenance for UPS (`ME_UPS1-3`) and PAC (`ME_PAC1-4`) units, the following staged pipeline is established:

1. **Phase 1: Data Quality & Hygiene Validation**
   - Inspect incoming sensor streams for missing values, flatlines, stuck sensors, and extreme outliers.
   - Flag gaps or irregularities before feature engineering.
2. **Phase 2: Time-Series Feature Extraction**
   - Compute rolling window aggregations (mean, std, min, max over 1h, 6h, 24h).
   - Estimate degradation trends using Ordinary Least Squares (OLS) slope fitting (e.g., battery voltage decay rate, return temperature drift).
3. **Phase 3: Statistical Baseline & Unsupervised Anomaly Detection**
   - Utilize Isolation Forest (current AIOps Shadow v5 mechanism) and Z-score thresholding as baseline anomaly detectors.
4. **Phase 4: Supervised Classification & Failure Prediction (Conditional)**
   - Train Logistic Regression and Gradient Boosting classifiers only when sufficient verified historical incident labels are present.
   - Never use unsupervised anomaly scores as proxy training labels.

---

## 2. Chronological Split Strategy
- **Principle:** Strictly prohibit random train-test splitting.
- **Implementation:** Implement rolling time-based splits (e.g., Train on Days 1–21, Validate on Days 22–28, Test on Days 29–35) to prevent temporal data leakage and simulate real-world prospective forecasting.

---

## 3. Evaluation Metrics & Performance Criteria
- **Primary Metrics:** Precision, Recall, F1-Score, and False Positive Rate (FPR).
- **Secondary Metrics:** Precision-Recall Area Under Curve (PR-AUC) for handling class imbalance, Missed Incident Rate, and Lead Time (warning horizon prior to equipment failure).
- **Diagnostic Output:** Confusion matrix evaluated per host and per sensor category.

---

## 4. Data Insufficiency Criteria (`INSUFFICIENT_DATA`)
An experiment or model training run is strictly prohibited and classified as `INSUFFICIENT_DATA` if any of the following conditions are met:
- Continuous historical telemetry is `< 7 days` per host.
- Fewer than `3` verified historical failure or maintenance events exist in the ground truth audit logs.
- Sensor data contains persistent single-point recordings or massive gaps (e.g., previous pilot observation where UPS1 battery voltage yielded only one timestamp).

---

## 5. Safe Deployment Roadmap
1. **Offline Evaluation:** Conduct all experiments and metric analyses using historical CSV dumps within `shadow_v5/`.
2. **Shadow Scoring Mode:** Run models alongside production without emitting actuation or remediation commands.
3. **Pre-Promotion Verification:** Require independent audit sign-off, TLS readiness, and operator approval before any model component is considered for production integration.
