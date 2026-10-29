# G.2 Next Step Runbook: Operator Credential Setup & Pre-Connection Verification

## 1. Operator Provisioning Steps
1. **Provision Token:** Create a read-only API token in Zabbix with minimum privileges for target assets (`ME_UPS1-3`, `ME_PAC1-4`).
2. **Local Storage:** Store the token in `/root/.zabbix_shadow_token`.
3. **Secure Permissions:** Run `chmod 600 /root/.zabbix_shadow_token`.

## 2. Pre-Connection Verification Checks
- Verify file exists and permissions are `600` or stricter using `ls -la /root/.zabbix_shadow_token`.
- Verify no network calls are initiated by running offline tests: `python3 test_phase_g2_offline.py`.
- Review Phase G.2 Preflight Report and Audit JSON.
- Provide explicit operator approval before executing any read-only Zabbix API script.
