# SECURITY EXCEPTION REQUEST: ZABBIX HTTP TRANSPORT

## Exception Details
- **Exception ID:** SEC-EXC-2026-087-HTTP
- **Target System:** Zabbix API Telemetry Polling (`http://10.28.1.110/zabbix`)
- **Requested By:** AIOps Engineering Team
- **Reviewing Authority:** Security Approver
- **Date:** November 10, 2026

## 1. Business Justification
The AIOps V12 shadow runtime requires read-only metric ingestion from Zabbix to evaluate predictive models. The existing Zabbix deployment operates on internal network segments without native HTTPS binding enabled.

## 2. Technical Limitation
Zabbix frontend web server is configured for HTTP traffic only (`http://10.28.1.110/zabbix`). Enabling TLS requires infrastructure outages and certificate management coordination outside the scope of AIOps V12 staging.

## 3. Threat Assessment & Risk Severity
- **Risk:** Potential interception of read-only API authentication credentials or telemetry data in transit.
- **Severity:** Medium (mitigated by isolated network segment and read-only token permissions).

## 4. Compensating Controls
1. **Network Segmentation:** V12 shadow runner operates within an isolated local network namespace with restricted routing to the Zabbix server IP.
2. **Read-Only Credentials:** API tokens used by V12 have strictly read-only permissions (no administrative or write capabilities).
3. **Credential Vaulting:** Tokens are injected via secure environment variables, never hardcoded or logged.

## 5. Exception Validity & Review
- **Expiration Date:** May 10, 2027 (6 months) or upon migration to Zabbix HTTPS.
- **Status:** `PENDING_SECURITY_APPROVAL`
