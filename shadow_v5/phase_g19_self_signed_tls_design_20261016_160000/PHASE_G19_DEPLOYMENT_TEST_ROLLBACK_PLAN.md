# Phase G.19 Deployment, Testing & Rollback Plan

## 1. Pre-Deployment Checks
1. Verify certificate and key file permissions (`chmod 600`).
2. Verify IP Address SAN matches target server IP.
3. Verify syntax validity of proposed proxy configuration (`nginx -t`).

---

## 2. Token-Free HTTPS Testing Protocol
- Execute secure curl test without transmitting sensitive credentials:
  ```bash
  curl -Iv https://<TARGET_IP>/ --cacert /path/to/ca.crt
  ```
- Validate:
  - TLS 1.2 or TLS 1.3 handshake success.
  - IP SAN match confirmation.
  - Zero SSL handshake errors or untrusted anchor warnings.

---

## 3. Existing Service Verification
Confirm that following services are operating normally post-reload:
- Port 80 (HTTP web traffic).
- TCP 10051 (Zabbix server daemon).
- UDP 162 (SNMP trap daemon).
- Running Docker containers (`grafana`, `influxdb`, `netbox`, `aiops_predictor_hpc`).

---

## 4. Rollback Procedure
If any anomaly or failure is detected:
1. Revert Nginx configuration to baseline backup.
2. Execute syntax check (`nginx -t`).
3. Perform graceful reload (`nginx -s reload`).
4. Verify port 443 listeners are unbound and all baseline services are fully verified.

---

## 5. Abort Conditions
Immediate abort triggered if:
- Port 443 conflict occurs with an unknown service.
- Certificate IP SAN mismatch is detected.
- Zabbix server or container network connectivity is interrupted.
- Rollback integrity cannot be confirmed.
