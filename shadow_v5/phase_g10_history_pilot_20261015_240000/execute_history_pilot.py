"""
Phase G.10 Bounded Zabbix Read-Only History Pilot Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/
Strict Execution: Max 2 history.get requests (one per item), last 60 minutes window, limit 500, zero retries, zero production changes.
"""

import os
import sys
import stat
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000"
TOKEN_PATH = "/root/.zabbix_shadow_token"
ENDPOINT = "http://10.28.1.110/zabbix/api_jsonrpc.php"

ITEMS_TO_PULL = [
    {
        "itemid": "59604",
        "name": "Battery voltage",
        "csv_filename": "PHASE_G10_BATTERY_VOLTAGE.csv"
    },
    {
        "itemid": "59607",
        "name": "Input voltage",
        "csv_filename": "PHASE_G10_INPUT_VOLTAGE.csv"
    }
]

def redact(text: str) -> str:
    if not text:
        return ""
    res = str(text)
    res = res.replace("Authorization", "Auth-Header-Redacted")
    res = res.replace("Bearer", "Bearer-Redacted")
    return res

def run_history_pilot():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.10",
        "shadow_version": "v5",
        "endpoint": ENDPOINT,
        "transport_risk": "TRANSPORT_HTTP_RISK (Unencrypted plain HTTP used per pilot spec)",
        "requests_sent": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "item_results": {},
        "production_changes": 0,
        "automatic_remediation": False,
        "credential_values_logged": False,
        "final_status": "BLOCKED_PREFLIGHT"
    }

    # 1. Preflight token checks
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: Token file not found.")
        save_artifacts(audit_data, {})
        return

    file_stat = os.stat(TOKEN_PATH)
    mode = file_stat.st_mode & 0o777
    if mode != 0o600:
        print(f"ERROR: Token permissions {oct(mode)}, expected 0600.")
        save_artifacts(audit_data, {})
        return

    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.read().strip()
    except Exception as e:
        print(f"ERROR reading token: {redact(str(e))}")
        save_artifacts(audit_data, {})
        return

    if not token:
        print("ERROR: Token is empty.")
        save_artifacts(audit_data, {})
        return

    print("Preflight token validation passed.")

    # 2. Compute 60 minutes window
    time_till = int(time.time())
    time_from = time_till - 3600  # 60 minutes ago
    print(f"Time window: from {time_from} to {time_till} (60 minutes)")

    item_results = {}
    csv_data_map = {}

    for idx, target in enumerate(ITEMS_TO_PULL, 1):
        itemid = target["itemid"]
        name = target["name"]
        csv_filename = target["csv_filename"]
        
        payload = {
            "jsonrpc": "2.0",
            "method": "history.get",
            "params": {
                "output": "extend",
                "history": 0,
                "itemids": [itemid],
                "time_from": time_from,
                "time_till": time_till,
                "sortfield": "clock",
                "sortorder": "ASC",
                "limit": 500
            },
            "id": 100 + idx
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

        audit_data["requests_sent"] += 1
        print(f"Request {idx}: history.get for item {itemid} ({name})...")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode("utf-8")
                res_json = json.loads(resp_body)
                if "result" in res_json:
                    history_points = res_json["result"]
                    audit_data["successful_requests"] += 1
                    
                    point_count = len(history_points)
                    earliest_clock = history_points[0].get("clock") if point_count > 0 else None
                    latest_clock = history_points[-1].get("clock") if point_count > 0 else None
                    limit_reached = (point_count >= 500)
                    
                    item_results[itemid] = {
                        "name": name,
                        "status": "SUCCESS",
                        "point_count": point_count,
                        "earliest_clock": earliest_clock,
                        "latest_clock": latest_clock,
                        "limit_reached": limit_reached
                    }
                    csv_data_map[csv_filename] = history_points
                    print(f"  -> SUCCESS: Retrieved {point_count} points.")
                else:
                    raise ValueError(f"Invalid API response: {redact(resp_body)}")
        except Exception as e:
            err_msg = redact(str(e))
            audit_data["failed_requests"] += 1
            item_results[itemid] = {
                "name": name,
                "status": "ERROR",
                "error_message": err_msg,
                "point_count": 0
            }
            csv_data_map[csv_filename] = []
            print(f"  -> ERROR: {err_msg}")

    audit_data["item_results"] = item_results

    # Determine final status
    if audit_data["successful_requests"] == len(ITEMS_TO_PULL):
        audit_data["final_status"] = "HISTORY_PILOT_COLLECTED"
    elif audit_data["successful_requests"] > 0:
        audit_data["final_status"] = "PARTIAL_SUCCESS"
    else:
        audit_data["final_status"] = "HISTORY_READ_FAILED"

    save_artifacts(audit_data, csv_data_map)
    print(f"Phase G.10 History Pilot execution completed. Final Status: {audit_data['final_status']}")


def save_artifacts(audit_data, csv_data_map):
    # 1. PHASE_G10_REPORT.md
    results_summary = ""
    for itemid, res in audit_data.get("item_results", {}).items():
        results_summary += f"""
### Item {itemid} ({res.get("name")})
- **Status:** `{res.get("status")}`
- **Points Collected:** {res.get("point_count", 0)}
- **Earliest Clock:** {res.get("earliest_clock", "N/A")}
- **Latest Clock:** {res.get("latest_clock", "N/A")}
- **Limit Reached (500 max):** {res.get("limit_reached", False)}
- **Error (if any):** `{res.get("error_message", "None")}`
"""

    report_content = f"""# Phase G.10 Bounded Zabbix Read-Only History Pilot Report

## 1. Metadata
- **Execution Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Endpoint:** `{audit_data["endpoint"]}`
- **Transport Security Note:** `{audit_data["transport_risk"]}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. Request Execution Summary
- **Requests Sent:** {audit_data["requests_sent"]}
- **Successful Requests:** {audit_data["successful_requests"]}
- **Failed Requests:** {audit_data["failed_requests"]}

## 3. Item-Specific Results
{results_summary if results_summary else "No results recorded."}

## 4. Compliance Confirmation
- API Requests: `{audit_data["requests_sent"]}` (Max 2 allowed)
- Production Changes: `{audit_data["production_changes"]}`
- Automatic Remediation: `{audit_data["automatic_remediation"]}`
- Credential Values Logged: `{audit_data["credential_values_logged"]}`
"""
    with open(os.path.join(OUTPUT_DIR, "PHASE_G10_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. PHASE_G10_AUDIT.json
    with open(os.path.join(OUTPUT_DIR, "PHASE_G10_AUDIT.json"), "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 3. CSV files (PHASE_G10_BATTERY_VOLTAGE.csv, PHASE_G10_INPUT_VOLTAGE.csv)
    for csv_filename, points in csv_data_map.items():
        csv_path = os.path.join(OUTPUT_DIR, csv_filename)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("itemid,clock,value,ns\n")
            for p in points:
                f.write(f"{p.get('itemid','')},{p.get('clock','')},{p.get('value','')},{p.get('ns','')}\n")

    print(f"Artifacts successfully saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_history_pilot()
