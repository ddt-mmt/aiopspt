"""
Phase G.9 Minimal History Pilot Preflight Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g9_history_pilot_preflight_20261015_230000/
Strict Rule: Zero Zabbix API requests, zero history collection, zero production changes.
"""

import os
import csv
import json
from datetime import datetime

INPUT_CSV = "/root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000/PHASE_G8_VALIDATED_CANDIDATES.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g9_history_pilot_preflight_20261015_230000"

def prepare_preflight():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        return

    candidates = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            candidates.append(r)

    print(f"Loaded {len(candidates)} validated candidates from Phase G.8.")

    # Filter for PRIORITY candidates with numeric value_type (0 = float/numeric in Zabbix) and units
    priority_numeric = []
    for c in candidates:
        if c.get("validation_tier") == "PRIORITY" and c.get("value_type") == "0" and c.get("units"):
            priority_numeric.append(c)

    # Select up to 2 candidates (e.g. UPS voltage and PAC supply temperature)
    selected = []
    for c in priority_numeric:
        key = c.get("key_", "").lower()
        if "voltage" in key or "temperature" in key or "supply_temp" in key:
            if c not in selected:
                selected.append(c)
        if len(selected) >= 2:
            break

    # If we didn't get 2 from specific filters, take any available priority numeric
    if len(selected) < 2:
        for c in priority_numeric:
            if c not in selected:
                selected.append(c)
            if len(selected) >= 2:
                break

    print(f"Selected {len(selected)} pilot candidate(s) for preflight execution plan.")

    # Execution Plan Design
    # History type mapping in Zabbix based on value_type (0 = numeric float -> history table type 0)
    execution_plan = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.9",
        "shadow_version": "v5",
        "api_method": "history.get",
        "time_window_minutes": 60,
        "max_points_per_item": 500,
        "history_type_mapping": {
            "0": "numeric float (history table type 0)"
        },
        "selected_candidates": [
            {
                "hostid": s.get("hostid"),
                "itemid": s.get("itemid"),
                "name": s.get("name"),
                "key_": s.get("key_"),
                "units": s.get("units"),
                "value_type": s.get("value_type")
            } for s in selected
        ],
        "api_requests_executed": 0,
        "history_collected": False
    }

    # Save PHASE_G9_EXECUTION_PLAN.json
    plan_path = os.path.join(OUTPUT_DIR, "PHASE_G9_EXECUTION_PLAN.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(execution_plan, f, indent=2)

    # Save PHASE_G9_AUDIT.json
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.9",
        "shadow_version": "v5",
        "input_candidates_count": len(candidates),
        "selected_candidates_count": len(selected),
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "final_status": "HISTORY_PILOT_PREFLIGHT_READY"
    }
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G9_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G9_REPORT.md
    selected_summary = ""
    for idx, s in enumerate(selected, 1):
        selected_summary += f"""
### Candidate {idx}
- **Host ID:** `{s.get("hostid")}`
- **Item ID:** `{s.get("itemid")}`
- **Name:** `{s.get("name")}`
- **Key:** `{s.get("key_")}`
- **Units:** `{s.get("units")}`
- **Value Type:** `{s.get("value_type")} (Numeric Float)`
- **Selection Rationale:** PRIORITY numerical sensor relevant for operational anomaly detection with validated metadata.
"""

    report_content = f"""# Phase G.9 Minimal History Pilot Preflight Report

## 1. Metadata
- **Preflight Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Input Source:** `{INPUT_CSV}`
- **Selected Candidates Count:** {len(selected)}
- **Final Status:** `{audit_data["final_status"]}`

## 2. Selected Pilot Candidates
{selected_summary if selected else "No suitable candidates found."}

## 3. Pilot Execution Parameters
- **API Method:** `history.get`
- **Time Window:** Max 60 minutes
- **Max Points Per Item:** 500
- **History Type:** Numeric float (value_type 0)

## 4. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G9_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.9 preflight completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    prepare_preflight()
