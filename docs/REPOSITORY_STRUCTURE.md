# Repository Structure — Audit Snapshot

Repository: `ddt-mmt/aiopspt`  
Branch: `main`  
Audit baseline: `9dbcf0e`  
Audit date: 5 November 2026

## Paths directly observed in GitHub

This is a non-exhaustive inventory of paths observed via GitHub file retrieval or repository search. It is not a complete recursive tree.

```text
aiopspt/
├── README.md
├── aio_all_in_one.sh
├── aio_audit_20261012_092412.log
├── docs/
│   ├── PHASE_HISTORY.md
│   ├── PROJECT_CURRENT_STATUS.md
│   └── REPOSITORY_STRUCTURE.md
├── reports/
│   ├── PHASE_81_DOCUMENTATION_AND_TEST_EVIDENCE_AUDIT_REPORT.md
│   ├── audit_archives/
│   │   ├── ROBUSTNESS_V5_README_CHANGELOG.md
│   │   └── AIOPS_V3_OPERATIONAL_METRICS.json
│   ├── phase83/
│   │   └── PHASE_83A_BASELINE.md
│   └── phase87/
│       ├── phase87_5/audit/phase87_4_evidence_audit.json
│       └── phase87_19/
│           ├── PHASE_87_19_FINAL_REPORT.md
│           └── PHASE_87_19_FINAL_REPORT.json
├── shadow_v5/
│   ├── CONTINUOUS_LEARNING_README.md
│   ├── SHADOW_V5_MANIFEST.json
│   └── outputs/SHADOW_SHA256SUMS.txt
└── staging_anomaly/SHA256SUMS.txt
```

## Historical workspace paths — not verified as Git paths

Older workspace documentation references `/root/grafan_aiops` and directories such as `src/`, `config/`, `phases/`, `tests/`, `real_data_validation/`, and `real_data_validation_365d/`. Their current presence in the GitHub branch has not been established here. They are therefore not represented as confirmed repository paths.

## Completeness limitation

A complete inventory requires a recursive Git tree export (GitHub Git Trees API) or `git ls-tree -r --name-only HEAD` from a clean clone. The audit interface used here did not return the full recursive tree. This document removes the previous ellipsis placeholder but deliberately labels its inventory as partial rather than inventing paths.

This documentation-only change does not deploy V12 or modify production V11, Zabbix, or Grafana. Production authorization remains `NOT_GRANTED`.
