"""
Phase G.14B Multi-Host UPS & PAC Expansion Plan Execution (Offline Only)
Isolated in /root/grafan_aiops/shadow_v5/phase_g14b_multi_host_expansion_20261015_300000/
Strict Rule: Zero API requests, zero history collection, zero production changes.
"""

import os
import csv
import json
from datetime import datetime

G8_CANDIDATES_CSV = "/root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000/PHASE_G8_VALIDATED_CANDIDATES.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g14b_multi_host_expansion_20261015_300000"

HOST_MAPPING = {
    "10688": "ME_UPS1",
    "10697": "ME_UPS2",
    "10701": "ME_UPS3",
    "10689": "ME_PAC1",
    "10690": "ME_PAC2",
    "10696": "ME_PAC3",
    "10698": "ME_PAC4"
}

def run_expansion_plan():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Running Phase G.14B Multi-Host Expansion Plan (Offline)...")

    if not os.path.exists(G8_CANDIDATES_CSV):
        print(f"ERROR: G.8 candidates CSV not found at {G8_CANDIDATES_CSV}")
        return

    candidates = []
    with open(G8_CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            candidates.append(r)

    print(f"Loaded {len(candidates)} candidates from Phase G.8.")

    host_summary = {hname: {"total": 0, "priority": 0, "secondary": 0, "disabled": 0, "deferred": 0, "included": 0} for hname in HOST_MAPPING.values()}
    
    processed_candidates = []

    for c in candidates:
        hid = c.get("hostid")
        hname = HOST_MAPPING.get(hid, hid)
        if hname not in host_summary:
            continue

        host_summary[hname]["total"] += 1
        tier = c.get("validation_tier")
        status = c.get("status", "0")
        name = c.get("name", "").lower()
        key_ = c.get("key_", "").lower()
        value_type = c.get("value_type", "")

        if status == "1":
            host_summary[hname]["disabled"] += 1
            inclusion = "EXCLUDE_DISABLED"
        elif tier == "PRIORITY" and value_type == "0":
            # Prioritize core numerical sensors (voltage, current, load, battery temp, humidity, airflow, power)
            # To respect total volume cap, select primary telemetry and defer redundant phase breakouts if desired, or include all priority numerical
            host_summary[hname]["priority"] += 1
            inclusion = "INCLUDED_PRIORITY"
            host_summary[hname]["included"] += 1
        elif tier == "SECONDARY":
            host_summary[hname]["secondary"] += 1
            inclusion = "INCLUDED_SECONDARY"
            host_summary[hname]["included"] += 1
        else:
            host_summary[hname]["deferred"] += 1
            inclusion = "DEFERRED_REVIEW"

        processed_candidates.append({
            "hostid": hid,
            "hostname": hname,
            "itemid": c.get("itemid"),
            "name": c.get("name"),
            "key_": c.get("key_"),
            "units": c.get("units"),
            "value_type": value_type,
            "status": status,
            "delay": c.get("delay"),
            "category": c.get("category"),
            "validation_tier": tier,
            "inclusion_status": inclusion
        })

    # Save PHASE_G14B_CANDIDATES.csv
    csv_path = os.path.join(OUTPUT_DIR, "PHASE_G14B_CANDIDATES.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hostid", "hostname", "itemid", "name", "key_", "units", "value_type", "status", "delay", "category", "validation_tier", "inclusion_status"
        ])
        writer.writeheader()
        for pc in processed_candidates:
            writer.writerow(pc)

    # Execution Plan JSON
    execution_plan = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.14B",
        "shadow_version": "v5",
        "target_hosts": list(HOST_MAPPING.values()),
        "time_window_seconds": 86400, # 24 hours
        "max_points_per_batch": 1000,
        "max_batches_per_item": 3,
        "api_method": "history.get",
        "history_type": 0,
        "transport_security": "BLOCKED_TRANSPORT_REVIEW (Unencrypted plain HTTP transport risk unmitigated)",
        "host_summary": host_summary,
        "api_requests": 0,
        "history_collected": False
    }

    plan_path = os.path.join(OUTPUT_DIR, "PHASE_G14B_EXECUTION_PLAN.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(execution_plan, f, indent=2)

    # Audit JSON
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.14B",
        "shadow_version": "v5",
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "model_training": False,
        "automatic_remediation": False,
        "credential_values_logged": False,
        "final_status": "BLOCKED_TRANSPORT_REVIEW"
    }

    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G14B_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Report MD
    summary_md = ""
    for hname, stats in host_summary.items():
        summary_md += f"""
- **{hname}:** Total = {stats["total"]}, Priority = {stats["priority"]}, Secondary = {stats["secondary"]}, Disabled = {stats["disabled"]}, Deferred = {stats["deferred"]}
"""

    report_content = f"""# Phase G.14B Multi-Host UPS & PAC Expansion Plan Report

## 1. Metadata
- **Plan Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Security Status:** `BLOCKED_TRANSPORT_REVIEW` (HTTP transport risk requires mitigation before live execution)
- **Final Status:** `{audit_data["final_status"]}`

## 2. Host Summary & Prioritization
{summary_md}

## 3. Execution Parameters & Limits
- **Time Window:** 24 hours (86,400 seconds)
- **Batch Limit:** Max 1,000 points per request (`limit: 1000`)
- **Pagination Strategy:** Forward pagination capped at max 3 batches per item (~3,000 points max per item).
- **Security Prerequisite:** Live extraction is blocked until secure transport is verified.

## 4. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
- Model Training: `False`
- Automatic Remediation: `False`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G14B_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.14B multi-host expansion plan completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_expansion_plan()
