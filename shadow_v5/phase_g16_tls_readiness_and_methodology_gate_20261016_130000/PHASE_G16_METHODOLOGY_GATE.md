# Phase G.16 Methodology Gate

## 1. Gate Objective
To enforce the governance standards established in Phase G.15 across all future AIOps predictive maintenance and anomaly detection pipelines for UPS (`ME_UPS1-3`) and PAC (`ME_PAC1-4`) monitoring.

---

## 2. Mandatory Gate Criteria & Compliance
1. **Chronological Splitting Enforcement:**
   - *Requirement:* Time-series datasets must be split chronologically (train on past, test on future) to prevent temporal data leakage.
   - *Status:* `ENFORCED`
2. **Data Scaling Isolation:**
   - *Requirement:* StandardScaler and other normalization transformers must be fitted strictly on training subsets.
   - *Status:* `ENFORCED`
3. **Statistical Baseline Priority:**
   - *Requirement:* Unsupervised anomaly detection (Isolation Forest) and statistical baselines must be evaluated before any supervised classification models.
   - *Status:* `ENFORCED`
4. **Verified Ground-Truth Labels:**
   - *Requirement:* Supervised models (Logistic Regression, Gradient Boosting) require operator-verified maintenance logs or Zabbix critical alarms. Unsupervised anomaly scores must never serve as training labels.
   - *Status:* `ENFORCED`
5. **Data Insufficiency Thresholds:**
   - *Requirement:* Experiments are blocked (`INSUFFICIENT_DATA`) if telemetry history is `< 7 days` or verified failure records are `< 3`.
   - *Status:* `ENFORCED`

---

## 3. Gate Decision
**`APPROVED_WITH_CONDITIONS`** (Methodology framework is fully approved; execution remains blocked pending data availability and TLS transport readiness).
