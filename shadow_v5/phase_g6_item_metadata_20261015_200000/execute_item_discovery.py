"""
Phase G.6 Zabbix Item Metadata Discovery Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g6_item_metadata_20261015_200000/
Strict Execution: Exactly 1 item.get request, max 500 items, zero history collection, zero production changes.
"""

import os
import sys
import stat
import json
import urllib.request
import urllib.error
from datetime import datetime

OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g6_item_metadata_20261015_200000"
TOKEN_PATH = "/root/.zabbix_shadow_token"
ENDPOINT = "http://10.28.1.110/zabbix/api_jsonrpc.php"
HOST_IDS = ["10689", "10690", "10696", "10698", "10688", "10697", "10701"]
OUTPUT_FIELDS = ["itemid", "hostid", "name", "key_", "units", "value_type", "status", "delay"]

def redact(text: str) -> str:
    if not text:
        return ""
    res = str(text)
    res = res.replace("Authorization", "Auth-Header-Redacted")
    res = res.replace("Bearer", "Bearer-Redacted")
    return res

def run_discovery():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.6",
        "shadow_version": "v5",
        "endpoint": ENDPOINT,
        "requests_sent": 0,
        "total_items": 0,
        "items_per_host": {},
        "limit_reached": False,
        "history_collected": False,
        "production_changes": 0,
        "credential_values_logged": False,
        "final_status": "BLOCKED_PREFLIGHT"
    }
    
    # 1. Preflight checks on token file
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: Token file not found.")
        save_artifacts(audit_data, [], "Token file not found.")
        return

    file_stat = os.stat(TOKEN_PATH)
    mode = file_stat.st_mode & 0o777
    if mode != 0o600:
        print(f"ERROR: Token file permissions are {oct(mode)}, expected 0600.")
        save_artifacts(audit_data, [], f"Invalid permissions: {oct(mode)}")
        return

    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.read().strip()
    except Exception as e:
        print(f"ERROR reading token: {redact(str(e))}")
        save_artifacts(audit_data, [], f"Read error: {redact(str(e))}")
        return

    if not token:
        print("ERROR: Token string is empty.")
        save_artifacts(audit_data, [], "Token string is empty.")
        return

    print("Preflight checks passed. Executing 1 item.get request...")

    # 2. Exactly 1 request: item.get
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": OUTPUT_FIELDS,
            "hostids": HOST_IDS,
            "limit": 500
        },
        "id": 1
    }
    req_data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        ENDPOINT,
        data=req_data,
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {token}"
        }
    )

    items = []
    try:
        audit_data["requests_sent"] += 1
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
            res_json = json.loads(resp_body)
            if "result" in res_json:
                items = res_json["result"]
                audit_data["total_items"] = len(items)
                if len(items) >= 500:
                    audit_data["limit_reached"] = True
                    audit_data["final_status"] = "TRUNCATED_LIMIT_REACHED"
                else:
                    audit_data["final_status"] = "ITEM_METADATA_COLLECTED"
            else:
                raise ValueError(f"Invalid API response: {redact(resp_body)}")
    except Exception as e:
        err_msg = redact(str(e))
        print(f"item.get request failed: {err_msg}")
        audit_data["final_status"] = "ITEM_READ_FAILED"
        save_artifacts(audit_data, [], f"Request failed: {err_msg}")
        return

    # Count items per host
    items_per_host = {}
    for hid in HOST_IDS:
        items_per_host[hid] = 0
    for itm in items:
        hid = str(itm.get("hostid", "unknown"))
        items_per_host[hid] = items_per_host.get(hid, 0) + 1
    audit_data["items_per_host"] = items_per_host

    save_artifacts(audit_data, items, None)
    print(f"Phase G.6 item discovery completed successfully. Total items: {len(items)}, Status: {audit_data['final_status']}")


def save_artifacts(audit_data, items, error_msg):
    # 1. PHASE_G6_REPORT.md
    report_content = f"""# Phase G.6 Zabbix Item Metadata Discovery Report

## 1. Metadata
- **Execution Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Endpoint:** `{ENDPOINT}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. Execution Summary
- **Requests Sent:** {audit_data["requests_sent"]} (Exactly 1 item.get)
- **Total Items Retrieved:** {audit_data["total_items"]}
- **Limit Reached (500 max):** {audit_data["limit_reached"]}
- **Items Per Host ID:** {json.dumps(audit_data["items_per_host"], indent=2)}
- **Error (if any):** `{error_msg if error_msg else "None"}`

## 3. Safety & Compliance Confirmation
- Network Requests: `{audit_data["requests_sent"]}`
- Zabbix API Calls: `{audit_data["requests_sent"]}`
- Production Changes: `0`
- History Collected: `False`
- Credential Values Logged: `False`
"""
    with open(os.path.join(OUTPUT_DIR, "PHASE_G6_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. PHASE_G6_AUDIT.json
    with open(os.path.join(OUTPUT_DIR, "PHASE_G6_AUDIT.json"), "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 3. PHASE_G6_ITEMS.csv
    csv_path = os.path.join(OUTPUT_DIR, "PHASE_G6_ITEMS.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(OUTPUT_FIELDS) + "\n")
        for itm in items:
            row = [str(itm.get(field, "")) for field in OUTPUT_FIELDS]
            f.write(",".join(row) + "\n")

    print(f"Artifacts successfully saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_discovery()
