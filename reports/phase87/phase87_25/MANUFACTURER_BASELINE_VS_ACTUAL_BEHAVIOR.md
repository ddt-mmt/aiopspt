# Manufacturer Baseline vs. Actual Behavior Comparison Framework

## 1. Principle
Manufacturer specifications provide theoretical design bounds and aging estimates (e.g., design life of 5 years). Actual operational telemetry (temperature exposure, cycle frequency, load profile) determines the device's true condition.

## 2. Rule Enforcement
- Reaching design life does not automatically declare a component failed.
- Operating near recommended limits triggers a warning, whereas exceeding safety limits triggers critical advisories.
- The engine separates observed sensor facts from model inferences.
