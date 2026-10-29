"""
Phase G.8 Candidate Quality Validation Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000/
Strict Rule: Zero API requests, zero history collection, zero production changes.
"""

import os
import csv
import json
from datetime import datetime

INPUT_CANDIDATES = "/root/grafan_aiops/shadow_v5/phase_g7_metadata_analysis_20261015_210000/PHASE_G7_CANDIDATES.csv"
SOURCE_G6 = "/root/grafan_aiops/shadow_v5/phase_g6_item_metadata_20261015_200000/PHASE_G6_ITEMS.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000"

def validate_and_classify():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_CANDIDATES) or not os.path.exists(SOURCE_G6):
        print("ERROR: Input files not found.")
        return

    # Load G.6 source items for cross-validation
    g6_items = {}
    with open(SOURCE_G6, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            g6_items[r.get("itemid")] = r

    # Load G.7 candidates
    candidates = []
    with open(INPUT_CANDIDATES, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            candidates.append(r)

    print(f"Loaded {len(candidates)} candidates for validation against {len(g6_items)} G.6 source items.")

    # Track hostid+key occurrences for duplicate detection per host
    host_key_counts = {}
    for c in candidates:
        hk = (c.get("hostid"), c.get("key_"))
        host_key_counts[hk] = host_key_counts.get(hk, 0) + 1

    validated_rows = []
    tier_counts = {
        "PRIORITY": 0,
        "SECONDARY": 0,
        "EXCLUDE_DISABLED": 0,
        "REVIEW_DUPLICATE": 0,
        "REVIEW_UNCLASSIFIED": 0
    }

    for c in candidates:
        itemid = c.get("itemid")
        hostid = c.get("hostid")
        name = c.get("name", "")
        key_ = c.get("key_", "")
        units = c.get("units", "")
        value_type = c.get("value_type", "")
        status = c.get("status", "0")
        delay = c.get("delay", "")
        category = c.get("category", "")
        
        # Verify consistency against G.6 source
        source_row = g6_items.get(itemid)
        if not source_row:
            print(f"WARNING: Item {itemid} not found in G.6 source items.")
        
        # 1. Check if disabled (status == 1)
        if status == "1":
            tier = "EXCLUDE_DISABLED"
            rationale = "Item status is disabled in Zabbix."
            confidence = "High"
        # 2. Check if duplicate per host (hostid + key_ appears > 1 time)
        elif host_key_counts.get((hostid, key_), 0) > 1:
            tier = "REVIEW_DUPLICATE"
            rationale = "Duplicate key detected for the same host ID."
            confidence = "High"
        # 3. Check unclassified
        elif category == "Unclassified Metric" or not category:
            tier = "REVIEW_UNCLASSIFIED"
            rationale = "Metric category is unclassified and requires domain review."
            confidence = "Medium"
        # 4. Check priority (numerical environmental/electrical sensors, active ping/availability)
        elif category in ["Environmental & Electrical Sensor", "Availability & Ping"]:
            tier = "PRIORITY"
            rationale = "Relevant numerical sensor or availability metric suitable for operational anomaly detection."
            confidence = "High"
        # 5. Check secondary (device status, operational states, system info)
        elif category in ["Device Status & Operational State", "Device Inventory & System Info"]:
            tier = "SECONDARY"
            rationale = "Device status, operational state, or supporting inventory metric useful for correlation."
            confidence = "Medium"
        else:
            tier = "REVIEW_UNCLASSIFIED"
            rationale = "Default fallback for unassigned category."
            confidence = "Low"

        tier_counts[tier] += 1

        validated_rows.append({
            "hostid": hostid,
            "itemid": itemid,
            "name": name,
            "key_": key_,
            "units": units,
            "value_type": value_type,
            "status": status,
            "delay": delay,
            "category": category,
            "validation_tier": tier,
            "rationale": rationale,
            "confidence": confidence
        })

    # Save PHASE_G8_VALIDATED_CANDIDATES.csv
    csv_path = os.path.join(OUTPUT_DIR, "PHASE_G8_VALIDATED_CANDIDATES.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hostid", "itemid", "name", "key_", "units", "value_type", "status", "delay", "category", "validation_tier", "rationale", "confidence"
        ])
        writer.writeheader()
        for vr in validated_rows:
            writer.writerow(vr)

    # Save PHASE_G8_AUDIT.json
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.8",
        "shadow_version": "v5",
        "input_candidates_count": len(candidates),
        "source_g6_items_count": len(g6_items),
        "validation_tier_breakdown": tier_counts,
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "final_status": "CANDIDATE_VALIDATION_COMPLETED"
    }
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G8_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G8_REPORT.md
    report_content = f"""# Phase G.8 Candidate Quality Validation Report

## 1. Metadata
- **Validation Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Source Input:** `{INPUT_CANDIDATES}`
- **Total Candidates Validated:** {len(candidates)}
- **Final Status:** `{audit_data["final_status"]}`

## 2. Validation Tier Breakdown
- **PRIORITY:** {tier_counts["PRIORITY"]}
- **SECONDARY:** {tier_counts["SECONDARY"]}
- **EXCLUDE_DISABLED:** {tier_counts["EXCLUDE_DISABLED"]}
- **REVIEW_DUPLICATE:** {tier_counts["REVIEW_DUPLICATE"]}
- **REVIEW_UNCLASSIFIED:** {tier_counts["REVIEW_UNCLASSIFIED"]}
- **Total Review (`REVIEW_DUPLICATE` + `REVIEW_UNCLASSIFIED`):** {tier_counts["REVIEW_DUPLICATE"] + tier_counts["REVIEW_UNCLASSIFIED"]}

## 3. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G8_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.8 validation completed successfully.")
    print(f"Counts -> PRIORITY: {tier_counts['PRIORITY']}, SECONDARY: {tier_counts['SECONDARY']}, EXCLUDE_DISABLED: {tier_counts['EXCLUDE_DISABLED']}, REVIEW: {tier_counts['REVIEW_DUPLICATE'] + tier_counts['REVIEW_UNCLASSIFIED']}")


if __name__ == "__main__":
    validate_and_classify()
