# PRODUCTION RISK ACCEPTANCE MATRIX

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigating Controls | Acceptance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | Unencrypted HTTP transport for Zabbix API polling | Medium | Medium | Medium | Network segmentation, read-only token, strict local namespace | Pending Security Approval (`SEC-EXC-2026-087-HTTP`) |
| **RSK-02** | Resource contention on monitoring server during polling | Low | Low | Low | Conservative polling intervals (60s), lightweight request payload | Accepted |
| **RSK-03** | Erroneous writeback to Zabbix production | Low | High | High | Zero write credentials provided; architecture strictly read-only | Accepted |
| **RSK-04** | Partial equipment identity mapping affecting precision | Medium | Low | Low | Conservative RUL thresholds; restriction from automated control | Accepted |
