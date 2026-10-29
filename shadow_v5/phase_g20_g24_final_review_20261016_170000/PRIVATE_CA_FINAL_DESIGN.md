# Private CA Final Design Specification

## 1. Architecture & Key Separation
- **Separation Principle:** The Dedicated Private CA private key must be generated and stored on a secure, offline, or restricted administrative workstation/vault, completely separate from the AIOps production host (`10.28.1.110`).
- **End-Entity Generation:** Only the signed server certificate and its corresponding private key (generated securely with strict file permissions) are deployed to the AIOps proxy/host.

---

## 2. Cryptographic Parameters & Validity
- **Algorithm & Key Size:** RSA 4096-bit (or ECDSA secp384r1) for Root CA; RSA 2048-bit (or ECDSA p256) for server certificates.
- **Signature Algorithm:** SHA-256 with RSA (or ecdsa-with-SHA256).
- **Validity Periods:**
  - Root CA: 10 years (3650 days).
  - Server Certificate: 1 year (365 days) to comply with modern TLS lifecycle best practices and facilitate regular rotation.

---

## 3. IP Address SAN Binding (`10.28.1.110`)
- **Mandatory Extension:** Because clients connect directly via IP, the server certificate must include:
  - `IP Address: 10.28.1.110`
- **Exclusions:** Common Name (CN) matching alone is insufficient for IP-based validation; explicit `subjectAltName = IP:10.28.1.110` is mandatory.

---

## 4. Trust Anchor Distribution & Revocation
- **Trust Distribution:** The public Root CA certificate (`ca.crt`) is explicitly installed into the trust store of authorized monitoring clients and Zabbix servers.
- **Revocation Mechanism:** Certificate Revocation Lists (CRL) or Online Certificate Status Protocol (OCSP) URIs embedded during issuance, or manual certificate replacement upon rotation.

---

## 5. Rotation, Backup, Access Rights & Audit
- **Rotation Schedule:** Annual server certificate renewal; Root CA rotation every 5–10 years.
- **Access Rights:** Private keys restricted to `root` with `600` permissions; CA private keys stored in encrypted offline storage.
- **Backup & Recovery:** Secure encrypted backup of CA keystore and metadata in designated administrative recovery vaults.
- **Audit Logging:** All certificate issuance, renewal, and deployment actions must be logged in formal administrative audit trails.
