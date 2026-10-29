# Zabbix Read-Only Authentication Runbook

## 1. Operator Procedure for Minimum-Privilege API Token
1. **Log in to Zabbix UI** with administrator privileges.
2. Navigate to **Administration > Users** (or **Users > API tokens** depending on Zabbix version).
3. Create a dedicated service user (e.g., `aiops_shadow_readonly`).
4. Assign user permissions restricted strictly to **Read-only** access on host groups containing target assets (`ME_UPS1-3`, `ME_PAC1-4`).
5. Generate a dedicated API token with an appropriate expiration date.
6. Store the token securely out-of-band or in a restricted local file (e.g., `/root/.zabbix_shadow_token`, file permissions `600`).
7. **Never** log, print, or commit the token value.
