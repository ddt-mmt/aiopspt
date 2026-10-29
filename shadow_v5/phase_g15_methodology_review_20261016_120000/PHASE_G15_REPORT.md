# Phase G.15 Research-Informed AIOps Methodology Review Report

## 1. Metadata & Execution Context
- **Review Timestamp:** 2026-10-16T12:00:00Z
- **Phase ID:** G.15
- **Mode:** OFFLINE ONLY (Zero Zabbix API requests, zero database interactions, zero production code modifications)
- **Target Infrastructure:** UPS and PAC monitoring (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`, `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`)
- **Reference Research Paper:** *Modeling and Prediction of Network Failures: A Machine Learning Approach* (IEEE ICC Workshops 2025, Chandrika Saha, Sajal Saha, Anwar Haque)
- **Status:** `OFFLINE_REVIEW_COMPLETED`

---

## 2. Executive Summary
Phase G.15 provides an exhaustive offline methodology review assessing how the machine learning and prediction principles from the IEEE ICC Workshops 2025 paper can be adapted to enhance AIOps Shadow v5 for data center power and cooling systems (UPS and PAC). 

While the source paper focuses on simulated network topology failures using tabular and structural attributes, AIOps Shadow v5 deals with continuous time-series sensor telemetry from physical data center assets. This report maps paper methodologies, identifies necessary adaptations, establishes strict data insufficiency criteria, designs a rigorous time-series evaluation pipeline, and outlines a safe roadmap for future experimentation.

---

## 3. Summary of Reference Paper Methodology
The reference paper (*Chandrika Saha et al., IEEE ICC Workshops 2025*) investigates network failure prediction using:
1. **Synthetic Data Generation:** Failure datasets derived from simulated 100-node and 200-node network topologies.
2. **Feature Space:** Port utilization, device age/replacements, power supply risk, CPU utilization, memory, card status, link status, location, OS upgrades, and misconfigurations.
3. **Model Portfolio:** Evaluation and comparison of Logistic Regression, Naive Bayes, Gradient Boosting, Quadratic Discriminant Analysis (QDA), and Deep Neural Network (DNN).
4. **Preprocessing:** StandardScaler fitted exclusively on training splits to prevent data leakage.
5. **Evaluation Metrics:** Accuracy, Precision, Recall, F1-score, and Confusion Matrix.
6. **Validation Split:** Standard 80/20 train-test split (noting the limitation of synthetic assumptions and class imbalance).

---

## 4. Applicability to AIOps Shadow v5 (UPS & PAC)
Data center infrastructure monitoring differs fundamentally from static network topology anomaly detection:
- **Nature of Data:** UPS and PAC telemetry are high-frequency, continuous time-series (e.g., voltage, load, temperature, humidity, fan speed) rather than discrete network event logs.
- **Failure Characteristics:** Physical degradation (battery aging, compressor wear) exhibits gradual temporal trends rather than sudden packet loss or link down events.
- **Current Shadow v5 State:** Transport is currently `BLOCKED_TRANSPORT_REVIEW`, historical data collection is incomplete (previous pilot showed single-point battery voltage for UPS1), and verified ground-truth incident labels are scarce.

---

## 5. Compliance & Safety Verification
- **Zabbix API Requests:** `0` (Confirmed)
- **History Collected:** `false` (Confirmed)
- **Production Changes:** `0` (Confirmed, `/root/grafan_aiops/script_aiops.py` untouched)
- **Model Training:** `false` (Confirmed)
- **Automatic Remediation:** `false` (Confirmed)

---

## 6. Key Recommendations & Next Steps
1. **Adopt Chronological Splits:** Never use random shuffling for time-series evaluation; always use rolling window or time-based splits.
2. **Enforce Strict Data Prerequisites:** Require at least 30 days of continuous telemetry and verified maintenance logs before initiating supervised model training.
3. **Maintain Isolation Guardrails:** Keep all R&D isolated within `shadow_v5/` until transport review, TLS security gates, and operator approvals are formally completed.
