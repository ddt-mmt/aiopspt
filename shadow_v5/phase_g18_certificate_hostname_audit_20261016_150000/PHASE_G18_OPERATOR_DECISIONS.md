# Phase G.18 Operator Decisions & Gating

## 1. Decisions Required from Operators
1. **CA Selection:** Approval of whether to use the enterprise internal CA, a dedicated shadow CA, or self-signed trust anchors.
2. **SAN Definition:** Formal confirmation of the required Fully Qualified Domain Names (FQDNs) and IP addresses for certificate issuance.
3. **Certificate Provisioning Authorization:** Formal authorization to generate, sign, and install certificates onto the production host (when ready).

---

## 2. Production Service Protection Mandate
- All existing production services (HTTP port 80, Zabbix TCP 10051, SNMP trap UDP 162, containerized services) remain strictly protected and unmodified.

---

## 3. Final Gate Decision
**`BLOCKED`** — Certificate assets are missing, SANs are unconfirmed, and operator provisioning authorization is pending.
