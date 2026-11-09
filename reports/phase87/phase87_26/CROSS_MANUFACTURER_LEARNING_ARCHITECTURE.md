# Hierarchical Cross-Manufacturer Learning Architecture

## 1. Six-Level Learning Hierarchy
1. **Level 1 — General Equipment Intelligence:** Cross-domain general patterns.
2. **Level 2 — Equipment Category Intelligence:** Category-specific splits (UPS vs PAC).
3. **Level 3 — Manufacturer Intelligence:** Manufacturer-specific behavior.
4. **Level 4 — Equipment Family Intelligence:** Compatible model-family groupings.
5. **Level 5 — Equipment Model Intelligence:** Specific model-level tuning.
6. **Level 6 — Individual Device Intelligence:** Per-device baseline and anomaly profiling.

## 2. Guardrails
Strict separation prevents mixing UPS and PAC models or dissimilar chemistries.
