# Phase G.17 Production-Safe TLS Deployment Plan Report

## 1. Metadata & Execution Context
- **Planning Timestamp:** 2026-10-16T14:00:00Z
- **Phase ID:** G.17
- **Mode:** PLAN ONLY / AUDIT ONLY (Zero Zabbix API requests, zero history collection, zero production changes, zero container restarts, zero TLS deployment execution)
- **Target Infrastructure:** UPS and PAC monitoring (`ME_UPS1-3`, `ME_PAC1-4`)
- **Final Status Decision:** `BLOCKED` (TLS deployment plan designed but pending operator review, certificate provisioning, and port 443 availability)

---

## 2. Executive Summary
Phase G.17 establishes a rigorous, production-safe TLS deployment plan for the AIOps Shadow v5 environment. Operating strictly in PLAN ONLY mode, this phase constructs a comprehensive read-only service inventory, differentiates verified runtime facts from stored template configurations (e.g., `/root/nginx.conf.proxy`), designs additive HTTPS termination on port 443 without disrupting existing web or monitoring services (port 80, TCP 10051, UDP 162), and formulates a bulletproof testing and rollback strategy. 

No production modifications, service restarts, or certificate installations are performed.

---

## 3. Key Findings & Fact Distinction
- **Verified Facts:** 
  - Port 443 is currently unbound and inactive on the host.
  - Active web listeners include httpd on ports 80 and 8080, and Docker proxies on ports 3000, 3001, 8001, 8086, 9001.
  - Zabbix server is actively listening on TCP 10051; Zabbix agent on TCP 10050.
  - `/root/nginx.conf.proxy` exists as a stored template file but is not actively binding port 443 in the current host runtime.
- **Assumptions & Unknowns:**
  - Presence of a valid internal CA certificate and private key on the host is unverified.
  - Exact Subject Alternative Name (SAN) and DNS hostname bindings for the target server are pending formal operator specification.

---

## 4. Compliance Confirmation
- **API Requests:** `0`
- **History Collection:** `false`
- **Model Training:** `false`
- **Production Changes:** `0`
- **Service/Container Restarts:** `0`
- **TLS Deployment:** `Not Performed`
