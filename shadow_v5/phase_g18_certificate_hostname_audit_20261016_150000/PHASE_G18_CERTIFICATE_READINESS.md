# Phase G.18 Certificate Readiness Assessment

## 1. Current Certificate Status
- **Files Found:** None (`.crt`, `.pem`, `.key` files absent from workspace).
- **Private Key Status:** Not generated, read, or displayed.
- **Readiness Classification:** `UNREADY / MISSING`

---

## 2. Conceptual CA Options Analysis
1. **Existing Enterprise Internal CA:**
   - *Pros:* Automatically trusted by corporate clients and monitoring nodes if root/intermediate CA is pre-installed.
   - *Cons:* Requires coordination with enterprise PKI team and formal CSR generation.
2. **Dedicated New Internal CA:**
   - *Pros:* Full control over issuance lifecycle for AIOps shadow environment.
   - *Cons:* Requires explicit distribution and trust establishment across all Zabbix/client endpoints.
3. **Controlled Self-Signed Trust Anchor:**
   - *Pros:* Rapid offline setup for testing.
   - *Cons:* Requires manual trust pinning on every monitoring client and lacks enterprise lifecycle management.

---

## 3. Validation Requirements
Before any TLS deployment proceeds, the following evidence must be provided:
- Valid X.509 server certificate file (`.crt` / `.pem`).
- Protected private key file (`.key` with `600` permissions).
- Root/Intermediate CA bundle for trust chain verification.
- Expiration date audit and SAN coverage confirmation.
