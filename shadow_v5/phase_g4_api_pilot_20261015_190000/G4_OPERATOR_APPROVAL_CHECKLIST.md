# G.4 Operator Approval Checklist

## 1. Preflight Review
- [x] Credential file exists at `/root/.zabbix_shadow_token` with permissions `600`.
- [x] Zabbix API endpoint verified (`http://10.28.1.110/zabbix/api_jsonrpc.php`).
- [x] Bounded scope limited to `apiinfo.version` and `host.get` for 7 target hosts (`ME_UPS1-3`, `ME_PAC1-4`).
- [x] Mutation methods strictly banned (`*._create`, `*._update`, `*._delete`).
- [x] Zero network requests executed during preflight preparation phase.

## 2. Operator Authorization Sign-Off
- **Approved by:** ___________________________ (Operator Signature / Explicit Confirmation)
- **Date:** ___________________________
- **Action Authorized:** Proceed to execute bounded read-only Zabbix API pilot (`apiinfo.version` + `host.get`).
