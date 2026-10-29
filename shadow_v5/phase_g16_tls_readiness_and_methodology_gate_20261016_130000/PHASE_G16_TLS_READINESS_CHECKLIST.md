# Phase G.16 TLS Readiness Checklist

| Prerequisite Item | Status | Evidence / Notes |
| :--- | :--- | :--- |
| **1. Port 443 Listener** | `UNBOUND` | Local socket inspection confirms port 443 is not listening. |
| **2. Certificates & Private Key** | `MISSING` | No server certificate, private key, or internal CA installed on host. |
| **3. Hostname & SAN Definition** | `PENDING` | Subject Alternative Names not yet formally defined for target endpoints. |
| **4. Network Path & Firewall** | `UNVERIFIED` | Ingress network paths and firewall rules for HTTPS not yet tested. |
| **5. Token-Free Pre-Testing Method** | `DESIGNED` | Pre-test curl commands planned but execution is deferred pending transport provisioning. |
| **6. Active vs Stored Config Distinction** | `VERIFIED` | `/root/nginx.conf.proxy` is a stored template; active runtime lacks TLS proxying. |

## Overall TLS Status
**`BLOCKED`** — TLS transport readiness is incomplete. No production modifications or certificate installations have been performed.
