# Nginx TLS Pre-Implementation Safety Plan — Phase G.14E

## 1. Safety Rollout Procedure
1. **Pre-Implementation Backup:** Create a timestamped copy of `/root/nginx.conf.proxy` prior to any modification.
2. **Syntax Validation:** Execute `nginx -t` to verify syntax integrity before reloading.
3. **Token-Free Testing:** Test HTTPS connectivity (`apiinfo.version` over port 443) using certificate verification without transmitting tokens.
4. **Operator Approval Gate:** Require explicit operator review of test results before applying changes to production proxy.
5. **Rollback Procedure:** In case of failure or syntax error, immediately restore the backup configuration (`cp /root/nginx.conf.proxy.bak /root/nginx.conf.proxy && nginx -s reload`).

## 2. Unmet Prerequisites
- Internal CA certificate and private key issuance.
- Verification of TCP port 443 availability on the proxy host.
- Operator authorization sign-off.
