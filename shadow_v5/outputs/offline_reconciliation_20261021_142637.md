# Zabbix Shadow — Offline Evidence Reconciliation

- Generated: 2026-10-21T14:26:37+07:00
- Mode: OFFLINE ONLY
- Network/API calls: NONE
- Production/config changes: NONE

## 1. Phase G5/G10 report discovery

### File: shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_AUDIT.json
a58a51996f9fd1d9d0e952aeb092ce0d194f83f8a49ac1a9636150344653b1b2  /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_AUDIT.json

7:  "requests_sent": 2,
8:  "successful_requests": 2,
9:  "failed_requests": 0,
13:      "status": "SUCCESS",
17:      "limit_reached": false
21:      "status": "SUCCESS",
25:      "limit_reached": false
30:  "credential_values_logged": false,
31:  "final_status": "HISTORY_PILOT_COLLECTED"

### File: shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_BATTERY_VOLTAGE.csv
efa12ccc3bde1db32da8d45c24b7a5abb2fcfbebca31a3419f8ed5978d8dd5d5  /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_BATTERY_VOLTAGE.csv

### File: shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv
fc55b3e82a0b3d9d364eb2867ecdc2be32df13451cb2ee43836bda7e90fe785a  /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv

### File: shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_REPORT.md
dd41129be77db90259f88819b81b273d7472acbacc5410a774a786e2172c6282  /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_REPORT.md

8:- **Final Status:** `HISTORY_PILOT_COLLECTED`
10:## 2. Request Execution Summary
11:- **Requests Sent:** 2
12:- **Successful Requests:** 2
13:- **Failed Requests:** 0
18:- **Status:** `SUCCESS`
22:- **Limit Reached (500 max):** False
26:- **Status:** `SUCCESS`
30:- **Limit Reached (500 max):** False
35:- API Requests: `2` (Max 2 allowed)
38:- Credential Values Logged: `False`

### File: shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_AUDIT.json
0979ea286e93c30f529e467ead58d052b34b77718ded6b5bc9bf18f6653c7f6b  /root/grafan_aiops/shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_AUDIT.json

6:  "requests_sent": 2,
13:  "credential_values_logged": false,
14:  "final_status": "AUTHENTICATED_READ_ONLY_REQUEST_CONFIRMED"

### File: shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_HOST_INVENTORY.csv
31310a7e4afb5ec2bbe5a15c057d5d0d81497f9a670b60f087e40bf388b14527  /root/grafan_aiops/shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_HOST_INVENTORY.csv

### File: shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_PILOT_REPORT.md
8f19fcaf7513a32bed66d78f633ad7277730c4b239b59d4a948163d26c160690  /root/grafan_aiops/shadow_v5/phase_g5_api_pilot_execution_20261015_193000/PHASE_G5_PILOT_REPORT.md

7:- **Final Status:** `AUTHENTICATED_READ_ONLY_REQUEST_CONFIRMED`
9:## 2. Request Execution Summary
10:- **Requests Sent:** 2
17:- Network Requests: `2` (Max 2 allowed)
21:- Credential Values Logged: `False`

## 2. Phase G10 CSV inventory and quality

### shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_BATTERY_VOLTAGE.csv
- Size bytes: 53
- SHA-256: efa12ccc3bde1db32da8d45c24b7a5abb2fcfbebca31a3419f8ed5978d8dd5d5
- Headers: itemid, clock, value, ns
- Data rows: 1
- Time-like column 'clock': empty=0, duplicate_values=0
  - Lexical min/max: 1792034604 / 1792034604

### shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv
- Size bytes: 1845
- SHA-256: fc55b3e82a0b3d9d364eb2867ecdc2be32df13451cb2ee43836bda7e90fe785a
- Headers: itemid, clock, value, ns
- Data rows: 47
- Time-like column 'clock': empty=0, duplicate_values=0
  - Lexical min/max: 1792033827 / 1792037367

Note: CSV statistics do not prove that the source token is currently valid
or that the Zabbix role is restricted to read-only permissions.

## 3. Static pilot script inspection

- File: shadow_v5/phase_g10_history_pilot_20261015_240000/execute_history_pilot.py
3a2ee8dec037e0d396a69c1a42bfee75e1abd963af84d9f608057c042c3e206c  /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/execute_history_pilot.py

Relevant static lines (credentials redacted; script NOT executed):
4:Strict Execution: Max 2 history.get requests (one per item), last 60 minutes window, limit 500, zero retries, zero production changes.
12:import urllib.request
13:import urllib.error
17:TOKEN_PATH = "/root/.zabbix_shadow_token"
22:        "itemid": "59604",
27:        "itemid": "59607",
37:    res = res.replace("Authorization", "Auth-Header-Redacted")
38:    res = res.replace("Bearer", "Bearer-Redacted")
60:    # 1. Preflight token checks
61:    if not os.path.exists(TOKEN_PATH):
62:        print("ERROR: Token file not found.")
66:    file_stat = os.stat(TOKEN_PATH)
69:        print(f"ERROR: Token permissions {oct(mode)}, expected 0600.")
74:        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
75:            token = [REDACTED]
77:        print(f"ERROR reading token: [REDACTED]}")
81:    if not token:
82:        print("ERROR: Token is empty.")
86:    print("Preflight token validation passed.")
89:    time_till = int(time.time())
90:    time_from = time_till - 3600  # 60 minutes ago
91:    print(f"Time window: from {time_from} to {time_till} (60 minutes)")
97:        itemid = target["itemid"]
103:            "method": "history.get",
107:                "itemids": [itemid],
108:                "time_from": time_from,
109:                "time_till": time_till,
112:                "limit": 500
118:        req = urllib.request.Request(
123:                "Authorization": [REDACTED]"Bearer {token}"
128:        print(f"Request {idx}: history.get for item {itemid} ({name})...")
131:            with urllib.request.urlopen(req, timeout=10) as resp:
141:                    limit_reached = (point_count >= 500)
143:                    item_results[itemid] = {
149:                        "limit_reached": limit_reached
158:            item_results[itemid] = {
184:    for itemid, res in audit_data.get("item_results", {}).items():
186:### Item {itemid} ({res.get("name")})
191:- **Limit Reached (500 max):** {res.get("limit_reached", False)}
229:            f.write("itemid,clock,value,ns\n")
231:                f.write(f"{p.get('itemid','')},{p.get('clock','')},{p.get('value','')},{p.get('ns','')}\n")

## 4. Conclusions and limitations

- Historical API success: confirm only if the G5/G10 reports or audit files explicitly support it.
- Current Gemini CLI token/quota: NOT CHECKED by this script.
- Current Zabbix token status: NOT VERIFIED.
- Effective Zabbix read-only role: NOT VERIFIED by historical successful reads alone.
- Current network/API calls: NONE.
- Data limit: compare observed CSV row counts and the static pilot limit with the current target of at most 100 records per item.

## 5. Suggested status

Use OFFLINE_DATA_READY only if CSV parsing, timestamps, required columns, and provenance are adequate.
Use RECOLLECTION_REQUIRED_MAX_100 if fresh data is needed to meet the 100-record/item target.
