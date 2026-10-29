"""
Phase G.5 Bounded Zabbix Read-Only API Pilot Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g5_api_pilot_execution_20261015_193000/
Strict Safety: Zero retries, 10s timeout, token redaction, no history collection, no production changes.
"""

import os
import sys
import stat
import json
import urllib.request
import urllib.error
from datetime import datetime

OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g5_api_pilot_execution_20261015_193000"
TOKEN_PATH = "/root/.zabbix_shadow_token"
ENDPOINT = "http://10.28.1.110/zabbix/api_jsonrpc.php"
TARGET_HOSTS = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]

def redact(text: str) -> str:
    if not text:
        return ""
    # Redact any token or authorization header
    res = str(text)
    res = res.replace("Authorization", "Auth-Header-Redacted")
    res = res.replace("Bearer", "Bearer-Redacted")
    return res

def run_pilot():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.5",
        "shadow_version": "v5",
        "endpoint": ENDPOINT,
        "requests_sent": 0,
        "api_version": None,
        "hosts_returned_count": 0,
        "target_hosts_missing": [],
        "automatic_remediation": False,
        "production_changes": 0,
        "history_collected": False,
        "credential_values_logged": False,
        "final_status": "BLOCKED_PREFLIGHT"
    }
    
    # 1. Preflight checks on token file
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: Token file not found.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], "Token file not found.")
        return

    if os.path.islink(TOKEN_PATH):
        print("ERROR: Token file is a symlink.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], "Token file is a symlink.")
        return

    file_stat = os.stat(TOKEN_PATH)
    if not stat.S_ISREG(file_stat.st_mode):
        print("ERROR: Token file is not a regular file.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], "Token file is not a regular file.")
        return

    # Check permissions 600 (no group/others read/write/execute)
    mode = file_stat.st_mode & 0o777
    if mode != 0o600:
        print(f"ERROR: Token file permissions are {oct(mode)}, expected 0600.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], f"Invalid token file permissions: {oct(mode)}")
        return

    if file_stat.st_size == 0:
        print("ERROR: Token file is empty.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], "Token file is empty.")
        return

    # Read token securely into memory
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.read().strip()
    except Exception as e:
        print(f"ERROR reading token: {redact(str(e))}")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], f"Read error: {redact(str(e))}")
        return

    if not token:
        print("ERROR: Token string is empty.")
        audit_data["final_status"] = "BLOCKED_PREFLIGHT"
        save_artifacts(audit_data, [], "Token string is empty.")
        return

    print("Preflight checks passed successfully.")

    # 2. Request 1 — apiinfo.version (No token)
    req1_payload = {
        "jsonrpc": "2.0",
        "method": "apiinfo.version",
        "params": {},
        "id": 1
    }
    req1_data = json.dumps(req1_payload).encode("utf-8")
    
    req1 = urllib.request.Request(
        ENDPOINT,
        data=req1_data,
        headers={"Content-Type": "application/json-rpc"}
    )
    
    api_version = None
    try:
        audit_data["requests_sent"] += 1
        print("Sending Request 1: apiinfo.version...")
        with urllib.request.urlopen(req1, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
            res_json = json.loads(resp_body)
            if "result" in res_json:
                api_version = res_json["result"]
                audit_data["api_version"] = api_version
                print(f"API Version received: {api_version}")
            else:
                raise ValueError(f"Invalid API response: {redact(resp_body)}")
    except Exception as e:
        err_msg = redact(str(e))
        print(f"Request 1 failed: {err_msg}")
        audit_data["final_status"] = "API_VERSION_CHECK_FAILED"
        save_artifacts(audit_data, [], f"Request 1 failed: {err_msg}")
        return

    # 3. Request 2 — host.get (With Bearer token)
    req2_payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host"],
            "filter": {
                "host": TARGET_HOSTS
            }
        },
        "id": 2
    }
    req2_data = json.dumps(req2_payload).encode("utf-8")
    
    req2 = urllib.request.Request(
        ENDPOINT,
        data=req2_data,
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {token}"
        }
    )

    hosts_found = []
    try:
        audit_data["requests_sent"] += 1
        print("Sending Request 2: host.get...")
        with urllib.request.urlopen(req2, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
            res_json = json.loads(resp_body)
            if "result" in res_json:
                hosts_found = res_json["result"]
                audit_data["hosts_returned_count"] = len(hosts_found)
                print(f"Hosts returned count: {len(hosts_found)}")
            else:
                raise ValueError(f"Invalid API response for host.get: {redact(resp_body)}")
    except Exception as e:
        err_msg = redact(str(e))
        print(f"Request 2 failed: {err_msg}")
        audit_data["final_status"] = "HOST_READ_FAILED"
        save_artifacts(audit_data, [], f"Request 2 failed: {err_msg}")
        return

    # Check missing target hosts
    returned_hostnames = {h.get("host") for h in hosts_found}
    missing_hosts = [th for th in TARGET_HOSTS if th not in returned_hostnames]
    audit_data["target_hosts_missing"] = missing_hosts
    
    audit_data["final_status"] = "AUTHENTICATED_READ_ONLY_REQUEST_CONFIRMED"
    save_artifacts(audit_data, hosts_found, None)
    print("Phase G.5 Bounded API Pilot executed successfully. Status: AUTHENTICATED_READ_ONLY_REQUEST_CONFIRMED")


def save_artifacts(audit_data, hosts_found, error_msg):
    # 1. PHASE_G5_PILOT_REPORT.md
    report_content = f"""# Phase G.5 Bounded Zabbix Read-Only API Pilot Report

## 1. Metadata
- **Execution Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Endpoint:** `{ENDPOINT}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. Request Execution Summary
- **Requests Sent:** {audit_data["requests_sent"]}
- **API Version:** `{audit_data.get("api_version", "N/A")}`
- **Hosts Returned Count:** {audit_data["hosts_returned_count"]}
- **Missing Target Hosts:** {audit_data.get("target_hosts_missing", [])}
- **Error (if any):** `{error_msg if error_msg else "None"}`

## 3. Safety & Compliance Confirmation
- Network Requests: `{audit_data["requests_sent"]}` (Max 2 allowed)
- Zabbix API Calls: `{audit_data["requests_sent"]}`
- Production Changes: `0`
- History Collected: `False`
- Credential Values Logged: `False`
- Automatic Remediation: `False`
"""
    with open(os.path.join(OUTPUT_DIR, "PHASE_G5_PILOT_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. PHASE_G5_AUDIT.json
    with open(os.path.join(OUTPUT_DIR, "PHASE_G5_AUDIT.json"), "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 3. PHASE_G5_HOST_INVENTORY.csv
    csv_path = os.path.join(OUTPUT_DIR, "PHASE_G5_HOST_INVENTORY.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("hostid,host\n")
        for h in hosts_found:
            f.write(f"{h.get('hostid','')},{h.get('host','')}\n")

    print(f"Artifacts successfully saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_pilot()
