# Negative Transfer Policy

## 1. Detection Mechanism
Monitors prediction error, false positive rates, and anomaly detection stability after knowledge transfer.

## 2. Mitigation
If performance degrades or errors increase, the platform immediately rejects the transfer, isolates the model, falls back to individual-device baselines, and logs an audit record.
