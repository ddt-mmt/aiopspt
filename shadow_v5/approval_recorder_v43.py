"""
Interactive Manual Approval Recorder for Bounded Zabbix Shadow Test (Phase 43).
Isolated in /root/grafan_aiops/shadow_v5/
Zero network calls, zero production modifications, fail-closed live access status.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

FIXED_TEST_SCOPE = [
    "59609: ME_UPS1 output load (%)",
    "59604: ME_UPS1 battery voltage (V)",
    "90706: ME_UPS1 battery temperature (°C) - only after formal mapping confirmation",
    "60386: ME_PAC1 return temperature (°C)",
    "60387: ME_PAC1 supply temperature (°C)",
    "60385: ME_PAC1 return humidity (%RH)",
    "Maximum 100 samples per item from the last 24 hours.",
    "No problem-event or trigger queries.",
    "No writes to Zabbix, InfluxDB, Grafana, or alerting systems.",
    "Staging output and 7-day retention require separate storage approval.",
    "Item 59603 remains excluded."
]

TARGET_DIR = "/root/grafan_aiops/shadow_v5/outputs"

def display_scope():
    print("\n--- FIXED TEST SCOPE ---")
    for item in FIXED_TEST_SCOPE:
        print(f"  * {item}")
    print("------------------------\n")

def get_input(prompt: str, input_func=input) -> str:
    try:
        val = input_func(prompt)
        return val.strip() if val else ""
    except (EOFError, KeyboardInterrupt):
        return ""

def collect_approval_data(input_func=input) -> Optional[Dict[str, Any]]:
    display_scope()
    
    print("Please provide operator approval details:")
    name = get_input("1. Full Name / Identity: ", input_func)
    if not name:
        print("Error: Name cannot be empty.")
        return None

    title = get_input("2. Title and Authority Role: ", input_func)
    if not title:
        print("Error: Title cannot be empty.")
        return None

    org = get_input("3. Organization / Team (optional): ", input_func)

    decision_input = get_input("4. Decision [APPROVE / REJECT / REQUEST_CHANGES]: ", input_func).upper()
    if decision_input not in ["APPROVE", "REJECT", "REQUEST_CHANGES"]:
        print("Error: Invalid decision. Must be APPROVE, REJECT, or REQUEST_CHANGES.")
        return None

    q5 = get_input("5. Do you approve the bounded read-only shadow test within your authority? [yes/no]: ", input_func).lower()
    if q5 not in ["yes", "y"]:
        print("Approval aborted: Bounded test not approved.")
        return None

    q6 = get_input("6. Do you fully understand the item scope and test limits? [yes/no]: ", input_func).lower()
    if q6 not in ["yes", "y"]:
        print("Approval aborted: Scope and limits not confirmed.")
        return None

    q7 = get_input("7. Do you approve the staging output path and 7-day retention? [yes/no]: ", input_func).lower()
    if q7 not in ["yes", "y"]:
        print("Approval aborted: Staging output and retention not approved.")
        return None

    ref = get_input("8. Ticket or Supporting Document Reference: ", input_func)
    notes = get_input("9. Additional Notes or Constraints: ", input_func)

    # Summary display
    print("\n=== APPROVAL SUMMARY ===")
    print(f"Operator Name: {name}")
    print(f"Title / Role: {title}")
    print(f"Organization: {org if org else 'N/A'}")
    print(f"Decision: {decision_input}")
    print(f"Authority Agreement: {q5}")
    print(f"Scope Understood: {q6}")
    print(f"Staging / Retention Approved: {q7}")
    print(f"Reference: {ref if ref else 'N/A'}")
    print(f"Notes: {notes if notes else 'N/A'}")
    print("========================\n")

    confirm = get_input("10. Final Confirmation to Save Record? [yes/no (default no)]: ", input_func).lower()
    if confirm not in ["yes", "y"]:
        print("Approval record cancelled by operator.")
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "schema_version": "v43.0",
        "timestamp": timestamp,
        "operator_identity": name,
        "operator_title": title,
        "organization": org,
        "decision": decision_input,
        "agreements": {
            "authority_approval": q5,
            "scope_understood": q6,
            "staging_retention_approved": q7
        },
        "test_scope": FIXED_TEST_SCOPE,
        "ticket_reference": ref,
        "additional_notes": notes,
        "live_access_status": "BLOCKED",
        "hash_disclaimer": "SHA-256 hash helps detect data modification/tampering. It is NOT a digital signature and does NOT prove operator identity."
    }
    return record

def save_record(record: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Saves record to TARGET_DIR with exclusive file creation ('x').
    Verifies target directory exists without creating it.
    Returns (success, filepath, sha256_hash).
    """
    if not os.path.isdir(TARGET_DIR):
        msg = f"Error: Target staging directory does not exist or is not accessible: {TARGET_DIR}"
        print(msg)
        return False, "", msg

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"operator_approval_{timestamp_str}.json"
    filepath = os.path.join(TARGET_DIR, filename)

    if os.path.exists(filepath):
        msg = f"Error: File already exists: {filepath}"
        print(msg)
        return False, "", msg

    # Canonical JSON representation for SHA-256
    canonical_json = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    record_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    envelope = {
        "record": record,
        "sha256": record_hash
    }

    # Exclusive file creation ('x') to prevent overwriting
    try:
        with open(filepath, 'x', encoding='utf-8') as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
    except Exception as e:
        msg = f"Error saving approval record: {e}"
        print(msg)
        return False, "", msg

    return True, filepath, record_hash

def main():
    record = collect_approval_data()
    if not record:
        print("\nFINAL STATUS: APPROVAL NOT RECORDED")
        print("Live access remains BLOCKED.")
        return

    success, path, hash_val = save_record(record)
    if success:
        print(f"\nSUCCESS: OPERATOR APPROVAL RECORDED")
        print(f"Saved to: {path}")
        print(f"SHA-256: {hash_val}")
        print("\nFINAL STATUS: OPERATOR APPROVAL RECORDED")
        print("Live access remains BLOCKED until all mandatory owner approvals are secured.")
    else:
        print(f"\nFINAL STATUS: APPROVAL NOT RECORDED")
        print("Live access remains BLOCKED.")

if __name__ == "__main__":
    main()
