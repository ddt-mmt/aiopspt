# Phase G.19 Operator Approval Checklist

## 1. Approval Stages & Gates

| Stage | Approval Item | Description | Status |
| :---: | :--- | :--- | :--- |
| **Stage 1** | **Design Approval** | Approval of the Dedicated Private CA / Self-Signed architecture and IP SAN strategy. | `PENDING OPERATOR REVIEW` |
| **Stage 2** | **Target IP Confirmation** | Operator confirmation of exact target IP addresses for IP Address SAN binding. | `PENDING OPERATOR INPUT` |
| **Stage 3** | **Certificate Issuance Authorization** | Explicit authorization to generate private CA and server certificates offline. | `BLOCKED` |
| **Stage 4** | **Configuration Changes Authorization** | Authorization to stage Nginx/proxy TLS configuration files on host. | `BLOCKED` |
| **Stage 5** | **Service Reload / Restart Authorization** | Authorization to execute `nginx -t` and graceful reload (`nginx -s reload`). | `BLOCKED` |

---

## 2. Mandatory Guardrails
- **No Automatic Execution:** No certificate generation, file modification, or service restart will occur without explicit operator sign-off for each stage.
- **Production Service Protection:** Absolute guarantee that port 80, TCP 10051 (Zabbix server), UDP 162 (SNMP traps), and all running containers remain fully isolated and uninterrupted.
