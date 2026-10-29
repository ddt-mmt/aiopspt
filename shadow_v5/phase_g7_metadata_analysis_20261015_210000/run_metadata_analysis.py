"""
Phase G.7 Local Item Metadata Analysis Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g7_metadata_analysis_20261015_210000/
Strict Rule: Zero API requests, zero history collection, zero production changes.
"""

import os
import csv
import json
from datetime import datetime

INPUT_CSV = "/root/grafan_aiops/shadow_v5/phase_g6_item_metadata_20261015_200000/PHASE_G6_ITEMS.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g7_metadata_analysis_20261015_210000"

def classify_item(name: str, key: str, units: str) -> tuple:
    name_l = name.lower()
    key_l = key.lower()
    
    if "ping" in key_l or "availability" in key_l or "icmp" in name_l:
        return "Availability & Ping", "Measures host reachability and network availability."
    elif any(w in name_l or w in key_l for w in ["temperature", "humidity", "voltage", "current", "load", "battery", "frequency", "power", "capacity", "runtime"]):
        return "Environmental & Electrical Sensor", "Critical analog sensor metric for UPS/PAC thermal and electrical monitoring."
    elif any(w in name_l or w in key_l for w in ["fan", "compressor", "status", "state", "indicator", "fail", "bad"]):
        return "Device Status & Operational State", "Discrete status flag indicating equipment health or component operational state."
    elif any(w in name_l or w in key_l for w in ["uptime", "model", "serial", "description", "contact", "location", "objectid", "snmptrap"]):
        return "Device Inventory & System Info", "Static or informational metadata describing the system."
    else:
        return "Unclassified Metric", "General telemetry metric requiring further domain mapping."

def run_analysis():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        return

    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            
    input_count = len(rows)
    print(f"Loaded {input_count} items from Phase G.6 CSV.")

    candidates = []
    host_distribution = {}
    category_distribution = {}
    disabled_count = 0
    unitless_count = 0
    duplicates_count = 0

    seen_keys = set()

    for r in rows:
        hostid = r.get("hostid", "")
        itemid = r.get("itemid", "")
        name = r.get("name", "")
        key_ = r.get("key_", "")
        units = r.get("units", "")
        value_type = r.get("value_type", "")
        status = r.get("status", "0")
        delay = r.get("delay", "")

        # Host distribution
        host_distribution[hostid] = host_distribution.get(hostid, 0) + 1

        # Check disabled (Zabbix status 1 typically means disabled)
        if status == "1":
            disabled_count += 1

        # Check unitless
        if not units:
            unitless_count += 1

        # Check duplicates (same hostid and key_)
        dupe_key = (hostid, key_)
        if dupe_key in seen_keys:
            duplicates_count += 1
        else:
            seen_keys.add(dupe_key)

        category, rationale = classify_item(name, key_, units)
        category_distribution[category] = category_distribution.get(category, 0) + 1

        # Include as candidate if useful for AIOps (everything classified)
        candidates.append({
            "hostid": hostid,
            "itemid": itemid,
            "name": name,
            "key_": key_,
            "units": units,
            "value_type": value_type,
            "status": status,
            "delay": delay,
            "category": category,
            "rationale": rationale
        })

    # Save PHASE_G7_CANDIDATES.csv
    candidates_csv_path = os.path.join(OUTPUT_DIR, "PHASE_G7_CANDIDATES.csv")
    with open(candidates_csv_path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hostid", "itemid", "name", "key_", "units", "value_type", "status", "delay", "category", "rationale"
        ])
        writer.writeheader()
        for c in candidates:
            writer.writerow(c)

    # Save PHASE_G7_AUDIT.json
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.7",
        "shadow_version": "v5",
        "input_items_count": input_count,
        "output_candidates_count": len(candidates),
        "analysis_method": "Local static metadata classification and grouping",
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "host_distribution": host_distribution,
        "category_distribution": category_distribution,
        "quality_flags": {
            "disabled_items": disabled_count,
            "unitless_items": unitless_count,
            "duplicate_keys": duplicates_count
        },
        "final_status": "METADATA_ANALYSIS_COMPLETED"
    }
    audit_json_path = os.path.join(OUTPUT_DIR, "PHASE_G7_AUDIT.json")
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G7_REPORT.md
    report_content = f"""# Phase G.7 Local Item Metadata Analysis Report

## 1. Metadata
- **Analysis Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Input Source:** `{INPUT_CSV}`
- **Total Items Analyzed:** {input_count}
- **Final Status:** `{audit_data["final_status"]}`

## 2. Distribution Per Host
{json.dumps(host_distribution, indent=2)}

## 3. Metric Categories
{json.dumps(category_distribution, indent=2)}

## 4. Data Quality & Limitations
- **Disabled Items:** {disabled_count}
- **Unitless Items:** {unitless_count}
- **Duplicate Keys Detected:** {duplicates_count}
- **Limitations:** Metadata analysis only describes item definitions. Zero history has been collected; therefore, no claims regarding metric values, trends, anomaly distributions, or operational thresholds can be made at this stage.

## 5. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G7_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.7 analysis completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_analysis()
