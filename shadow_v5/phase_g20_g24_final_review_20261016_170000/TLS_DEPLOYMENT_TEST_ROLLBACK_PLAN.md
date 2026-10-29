# TLS Deployment, Test & Rollback Plan

## 1. Pre-Deployment Validation
1. Verify file presence and permissions (`chmod 600` for private keys, `644` for certificates).
2. Validate IP SAN matches `10.28.1.110` using `openssl x509 -text -noout -in server.crt`.
3. Run configuration syntax check (`nginx -t`).

---

## 2. Additive Port 443 Deployment
- Introduce TLS server block listening on port `443` without modifying existing HTTP listeners (port 80), Zabbix server (TCP 10051), or SNMP traps (UDP 162).
- Enforce modern TLS protocols (TLS 1.2 and TLS 1.3 only) with secure cipher suites.

---

## 3. Token-Free HTTPS Testing Protocol
- Execute secure verification test without transmitting sensitive credentials:
  ```bash
  curl -Iv https://10.28.1.110/ --cacert /path/to/ca.crt
  ```
- Confirm:
  - Successful TLS handshake.
  - IP SAN match for `10.28.1.110`.
  - Zero trust verification errors.

---

## 4. Existing Service Verification
Ensure uninterrupted operation of:
- HTTP web traffic (port 80).
- Zabbix server daemon (TCP 10051).
- SNMP trap receiver (UDP 162).
- All running Docker containers (`grafana`, `influxdb`, `netbox`, `aiops_predictor_hpc`).

---

## 5. Abort Criteria & Rollback Procedure
- **Abort Triggers:** Port 443 binding failure, syntax error on `nginx -t`, SAN mismatch, or Zabbix connection interruption.
- **Rollback Steps:**
  1. Revert Nginx configuration file to pre-change backup.
  2. Run `nginx -t`.
  3. Execute graceful reload (`nginx -s reload`).
  4. Verify port 443 is unbound and baseline services are fully verified.
