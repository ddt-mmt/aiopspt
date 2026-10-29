# Phase G.19 Self-Signed & Private CA Trust Design

## 1. Architectural Options Comparison

### Option A: Direct Self-Signed Server Certificate
- **Mechanism:** A single server certificate is generated with the target server IP in its Subject Alternative Name (SAN), self-signed by its own private key.
- **Trust Distribution:** The server certificate itself must be distributed and trusted on every client monitoring node.
- **Security & Operational Consequences:**
  - *Pros:* Simple single-file setup; no intermediate CA infrastructure required.
  - *Cons:* High operational overhead for rotation (every certificate rotation requires re-distributing trust across all clients); lack of separation between issuing authority and end-entity certificate.

### Option B: Dedicated Private CA with Root Trust Anchor
- **Mechanism:** A lightweight private Root CA is established. The Root CA issues the server certificate for the AIOps host.
- **Trust Distribution:** Only the Root CA certificate (public key) is distributed and trusted once across all client monitoring nodes.
- **Security & Operational Consequences:**
  - *Pros:* Excellent scalability and lifecycle management; server certificates can be rotated freely without altering client trust anchors as long as signed by the same trusted CA.
  - *Cons:* Requires secure management of Root CA private key storage.
- **Recommendation:** **Option B (Dedicated Private CA)** is strongly recommended for operational maintainability and future extensibility.

---

## 2. IP Address SAN Requirement (Critical Constraint)
- **Fact:** Because access to the AIOps / Zabbix endpoints is currently performed via **IP addresses** rather than an FQDN:
  - **Common Name (CN)** matching is deprecated/ignored by modern TLS clients.
  - **DNS SAN** entries will fail validation when connecting via IP.
- **Mandatory Specification:** Any generated certificate **must** include an explicit **IP Address SAN** (`IP:10.x.x.x` or target management IP) matching the exact destination IP used by clients.
- **Status:** Target IP addresses are marked as `PENDING OPERATOR CONFIRMATION` and must be explicitly provided prior to certificate generation.

---

## 3. Client Validation & Trust Chain Verification
- Clients connecting via HTTPS must be configured with the appropriate trust anchor (`--cacert ca.crt` or system trust store addition).
- Verification commands must validate:
  - IP Address SAN match.
  - Certificate validity dates (notBefore / notAfter).
  - Complete trust chain integrity.
