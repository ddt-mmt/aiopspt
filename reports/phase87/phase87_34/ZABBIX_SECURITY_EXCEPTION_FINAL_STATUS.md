# ZABBIX SECURITY EXCEPTION FINAL STATUS

## 1. Exception Reference
- **Exception ID:** `SEC-EXC-2026-087-HTTP`
- **Target Endpoint:** `http://10.28.1.110/zabbix`
- **Status:** `SECURITY_EXCEPTION_APPROVED`
- **Security Approver:** Maya Indah (Information Security Officer)
- **Effective Date:** 2026-11-10
- **Expiry Date:** 2027-05-10 (6 months review cycle)

## 2. Compensating Controls
1. **IP Whitelisting:** Telemetry polling is restricted exclusively to staging IP `10.28.1.100`.
2. **Read-Only Credentials:** API authentication uses a restricted token with read-only permission (`history.get`, `item.get`).
3. **Network Segmentation:** Traffic is isolated within the internal management VLAN.
4. **Maintenance Window Plan:** TLS enablement on Zabbix frontend is scheduled for the Q2 2027 maintenance window.
