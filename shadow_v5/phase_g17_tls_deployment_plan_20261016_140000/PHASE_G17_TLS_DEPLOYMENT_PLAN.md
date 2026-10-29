# Phase G.17 Production-Safe TLS Deployment Plan

## 1. Deployment Objectives
To establish secure HTTPS / TLS termination on port 443 for Zabbix and AIOps endpoints without interrupting existing HTTP (port 80), Zabbix TCP (10051), SNMP (UDP 162), or containerized services.

---

## 2. Additive Architecture & Port Isolation
- **Port Separation:** Port 80 remains dedicated to plain HTTP (with optional 301 redirect to HTTPS for approved paths). Port 443 is introduced exclusively for TLS termination.
- **Service Isolation:** Zabbix server (TCP 10051) and Zabbix agent (TCP 10050) operate on dedicated native ports and are unaffected by web proxy TLS configurations.
- **Container Isolation:** Docker containers (`grafana`, `influxdb`, `netbox`, etc.) continue operating on their respective ports (`3000`, `8086`, `8001`, etc.) behind the reverse proxy layer.

---

## 3. Certificate & CA Prerequisites
- **Certificate Requirements:** A valid X.509 server certificate and private key matching the exact Subject Alternative Name (SAN) and DNS hostname of the server.
- **Trusted CA:** Must be signed by an internal corporate CA or trusted authority already recognized by client monitoring nodes.
- **Absence Handling:** If certificates are unavailable, deployment must abort prior to applying proxy configurations.

---

## 4. Step-by-Step Execution Procedure (Future Operator Action)
1. **Prerequisite Check:** Verify certificate and key file presence and correct file permissions (`chmod 600`).
2. **Config Staging:** Place validated Nginx/proxy configuration in `/etc/nginx/conf.d/` (or update proxy container volume mount).
3. **Syntax Validation:** Execute `nginx -t` (or container config test) prior to restarting or reloading any service.
4. **Additive Binding:** Bind port 443 with TLS 1.2 and TLS 1.3 ciphers only (disable legacy SSLv3/TLS1.0/TLS1.1).
5. **Service Reload:** Perform a graceful reload (`nginx -s reload`) only after successful syntax validation.
