# Audit Finding Register (Phase 87.24)

- **Audit Date:** 2026-11-06
- **Baseline Commit:** `1310f47b0b98afb58030de2b748d69fba61fb5ef`

| Finding ID | Phase | Description | Severity | Source Evidence | Remediation Action | Status |
|---|---|---|---|---|---|---|
| 87.24-F001 | 87.23 | Git commit author identity vs. Organizational Change Owner terminology ambiguity. | Low | Git metadata vs. Project declarations | Explicitly decouple Git author/committer identity from organizational Change Owner role in Phase 87.24 documentation. | REMEDIATED |
| 87.24-F002 | 87.23 | Git commits are unsigned (`UNVERIFIED`). | Medium | Git commit verification | Document signing readiness and constraints; maintain explicit unverified status without breaking workflows. | REMEDIATED |
| 87.24-F003 | 87.23 | Deployment eligibility matrix pass criteria listed `APPROVED_UNVERIFIED` as verified. | Medium | Phase 87.23 CSV matrix | Correct matrix pass criteria to enforce fail-closed distinction (`APPROVED_UNVERIFIED` is not satisfied). | REMEDIATED |
| 87.24-F004 | 87.23 | Change Owner organizational authority lacks independent HR/charter verification. | High | Change Owner review | Retain `APPROVED_UNVERIFIED` status until formal organizational sign-off is established. | REMEDIATED |
| 87.24-F005 | 87.23 | Zabbix API transport utilizes plaintext HTTP without formal security exception sign-off. | High | Security assessment | Retain `HTTP_SECURITY_EXCEPTION_PENDING` and require formal InfoSec sign-off. | REMEDIATED |
