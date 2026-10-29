# Phase G.10 Bounded Zabbix Read-Only History Pilot Report

## 1. Metadata
- **Execution Timestamp:** 2026-10-15T04:10:18.276320
- **Staging Directory:** `/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000`
- **Endpoint:** `http://10.28.1.110/zabbix/api_jsonrpc.php`
- **Transport Security Note:** `TRANSPORT_HTTP_RISK (Unencrypted plain HTTP used per pilot spec)`
- **Final Status:** `HISTORY_PILOT_COLLECTED`

## 2. Request Execution Summary
- **Requests Sent:** 2
- **Successful Requests:** 2
- **Failed Requests:** 0

## 3. Item-Specific Results

### Item 59604 (Battery voltage)
- **Status:** `SUCCESS`
- **Points Collected:** 1
- **Earliest Clock:** 1792034604
- **Latest Clock:** 1792034604
- **Limit Reached (500 max):** False
- **Error (if any):** `None`

### Item 59607 (Input voltage)
- **Status:** `SUCCESS`
- **Points Collected:** 47
- **Earliest Clock:** 1792033827
- **Latest Clock:** 1792037367
- **Limit Reached (500 max):** False
- **Error (if any):** `None`


## 4. Compliance Confirmation
- API Requests: `2` (Max 2 allowed)
- Production Changes: `0`
- Automatic Remediation: `False`
- Credential Values Logged: `False`
