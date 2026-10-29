# Phase G.18 Hostname & SAN Review

## 1. Candidate Hostnames Identified from Discovery
- **Infrastructure Targets:** `ME_UPS1`, `ME_UPS2`, `ME_UPS3`, `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`
- **Host System Identifiers:** Local server hostname and IP bindings identified in discovery scripts.

---

## 2. SAN (Subject Alternative Name) Requirements
- To pass strict TLS client validation without hostname mismatch errors, the server certificate must include:
  - The exact FQDN of the AIOps/Zabbix server.
  - IP address entries (if accessed via direct IP).
  - Internal alias identifiers used by monitoring agents.

---

## 3. Review Status
- **Status:** `PENDING OPERATOR SPECIFICATION`
- No hostnames or SANs have been hardcoded or modified during this read-only phase.
