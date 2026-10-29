# Phase G.15 Paper-to-AIOps Concept Mapping

## 1. Overview
This document maps concepts from the reference paper (*Chandrika Saha et al., IEEE ICC Workshops 2025*) to the AIOps Shadow v5 infrastructure monitoring domain (`ME_UPS1-3`, `ME_PAC1-4`), categorizing them into direct relevance, required adaptation, and non-applicability.

---

## 2. Detailed Mapping Matrix

### A. Directly Relevant Concepts (Adopt as-is)
1. **Rigorous Preprocessing & Scaling Isolation:**
   - *Paper Concept:* StandardScaler fitted strictly on training data subsets to prevent data leakage during normalization.
   - *AIOps Application:* Mandatory for all numerical sensor features (voltage, return temperature, humidity, load percentage) prior to statistical baseline comparison or model training.
2. **Comprehensive Evaluation Metrics:**
   - *Paper Concept:* Evaluation via Precision, Recall, F1-Score, and Confusion Matrix alongside Accuracy.
   - *AIOps Application:* Essential for infrastructural anomaly and failure detection where class imbalance (normal vs failure) renders raw accuracy misleading.
3. **Comparative Model Benchmark:**
   - *Paper Concept:* Evaluating linear models (Logistic Regression) against ensemble methods (Gradient Boosting) without assuming complex models are universally superior.
   - *AIOps Application:* Compare statistical baselines and Isolation Forest against Gradient Boosting and Logistic Regression when labeled data becomes available.

### B. Concepts Requiring Adaptation (Modify for Time-Series & Physical Assets)
1. **Feature Engineering:**
   - *Paper Concept:* Static network attributes (port utilization, device age, OS upgrades, misconfigurations).
   - *AIOps Application:* Transform raw sensor telemetry into sliding window time-series features:
     - Rolling means and standard deviations (1h, 6h, 24h).
     - Rate of change / degradation slope via Ordinary Least Squares (OLS) regression (e.g., battery voltage drop rate, compressor runtime efficiency).
2. **Failure Labeling & Ground Truth:**
   - *Paper Concept:* Synthetic failure labels generated from simulated topology disruption.
   - *AIOps Application:* Raw anomaly scores from unsupervised models (Isolation Forest) must **not** be treated as failure labels. Ground truth must be derived from operator-verified maintenance logs, Zabbix critical alarms, and confirmed hardware replacement records.
3. **Train-Test Splitting Strategy:**
   - *Paper Concept:* Standard random 80/20 train-test split.
   - *AIOps Application:* Inappropriate for time-series due to autocorrelation. Must employ chronological splitting (e.g., train on weeks 1–3, test on week 4) to prevent temporal data leakage.

### C. Concepts Not Applicable / Unsuitable
1. **Synthetic Accuracy Claims (97%–99%):**
   - *Paper Concept:* High accuracy achieved on simulated network node failures.
   - *AIOps Application:* Cannot be transferred to physical data center hardware. Real-world sensor noise, missing data points, and unrecorded maintenance events mean lower baseline expectancies that must be empirically verified.
2. **Network Topology Graph Metrics:**
   - *Paper Concept:* Edge counts, link connectivity, and port states.
   - *AIOps Application:* Irrelevant for standalone or parallel environmental units (UPS and PAC units operate with independent thermodynamic and electrical cycles).
3. **Unchecked Deep Neural Network Priority:**
   - *Paper Concept:* Evaluating DNNs as default complex predictors.
   - *AIOps Application:* Given limited historical data availability in the data center environment, complex DNNs risk severe overfitting. Simpler, interpretable models (Logistic Regression, Gradient Boosting) are preferred.
