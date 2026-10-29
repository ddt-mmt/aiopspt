# Phase G.17 Testing & Rollback Plan

## 1. Staged Testing Protocol
1. **Pre-Deployment Syntax Check:**
   - Run `nginx -t` to guarantee zero syntax errors in staging/production configuration files.
2. **Token-Free HTTPS Pre-Testing:**
   - Execute secure curl commands to test TLS handshake and HTTP status without transmitting sensitive tokens:
     ```bash
     curl -Iv https://localhost/ --cacert /path/to/ca.crt
     ```
3. **Trust Chain & SAN Verification:**
   - Verify that certificate expiration, issuer trust chain, and Subject Alternative Names match expected parameters.
4. **Existing Service Verification:**
   - Confirm that Zabbix server (TCP 10051), Zabbix agent (TCP 10050), and HTTP (port 80) remain fully responsive during and after testing.

---

## 2. Rollback Procedure
If any anomaly, port conflict, or verification failure occurs:
1. Revert proxy configuration to the pre-tested baseline backup file.
2. Run `nginx -t` to confirm baseline syntax validity.
3. Execute graceful reload: `nginx -s reload`.
4. Verify port 443 listeners are unbound and standard services (ports 80, 10051) are fully operational.

---

## 3. Abort Conditions (Triggers for Immediate Abort)
Deployment and testing must be immediately aborted if:
- Port 443 is unexpectedly bound by an unmanaged third-party process.
- Active runtime proxy configuration is ambiguous or lacks proper upstream definitions.
- Valid certificates or trusted CA files are missing or expired.
- Any degradation or disruption occurs on existing monitoring services (Zabbix, SNMP traps).
- Rollback integrity cannot be guaranteed prior to making changes.
