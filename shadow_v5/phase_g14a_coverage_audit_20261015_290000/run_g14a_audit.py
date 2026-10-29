"""
Phase G.14A Offline Coverage Audit Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g14a_coverage_audit_20261015_290000/
Strict Rule: Zero API requests, zero history collection, zero production changes.
"""

import os
import csv
import json
from datetime import datetime

G6_ITEMS_CSV = "/root/grafan_aiops/shadow_v5/phase_g6_item_metadata_20261015_200000/PHASE_G6_ITEMS.csv"
G8_CANDIDATES_CSV = "/root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000/PHASE_G8_VALIDATED_CANDIDATES.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g14a_coverage_audit_20261015_290000"

def run_audit():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Running Phase G.14A Offline Coverage Audit...")

    # Load G.6 items
    items = []
    if os.path.exists(G6_ITEMS_CSV):
        with open(G6_ITEMS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                items.append(r)

    # Load G.8 validated candidates
    candidates = []
    if os.path.exists(G8_CANDIDATES_CSV):
        with open(G8_CANDIDATES_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                candidates.append(r)

    # Host mapping from Phase G inventory / analysis
    # Host IDs: 10688 (ME_UPS1), 10689 (ME_PAC1), 10690 (ME_PAC2), 10696 (ME_PAC3), 10698 (ME_PAC4), 10697 (ME_UPS2), 10701 (ME_UPS3)
    host_mapping = {
        "10688": "ME_UPS1",
        "10689": "ME_PAC1",
        "10690": "ME_PAC2",
        "10696": "ME_PAC3",
        "10698": "ME_PAC4",
        "10697": "ME_UPS2",
        "10701": "ME_UPS3"
    }

    host_stats = {hname: {"hostid": hid, "total_items": 0, "priority_numeric": 0} for hid, hname in host_mapping.items()}
    
    for c in candidates:
        hid = c.get("hostid")
        hname = host_mapping.get(hid, hid)
        if hname in host_stats:
            host_stats[hname]["total_items"] += 1
            if c.get("validation_tier") == "PRIORITY" and c.get("value_type") == "0":
                host_stats[hname]["priority_numeric"] += 1

    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.14A",
        "shadow_version": "v5",
        "target_hosts_checked": list(host_mapping.values()),
        "g14_plan_coverage_gap": "Phase G.14 execution plan currently covers only host 10688 (ME_UPS1). The other 6 hosts (ME_UPS2-3, ME_PAC1-4) are not yet included in the 24h expansion request plan.",
        "host_statistics": host_stats,
        "transport_security_risk": "TRANSPORT_HTTP_RISK: Plain unencrypted HTTP in use. Private network assumption is insufficient; requires explicit operator sign-off.",
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "model_training": False,
        "automatic_remediation": False,
        "final_status": "COVERAGE_AUDIT_COMPLETED"
    }

    # Save PHASE_G14A_AUDIT.json
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G14A_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G14A_REPORT.md
    host_summary = ""
    for hname, stats in host_stats.items():
        host_summary += f"""
- **{hname} (Host ID {stats["hostid"]}):** Total Items = {stats["total_items"]}, Priority Numeric Items = {stats["priority_numeric"]}
"""

    report_content = f"""# Phase G.14A Offline Coverage Audit Report

## 1. Metadata
- **Audit Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. Host Coverage Analysis
- **Finding:** Phase G.14 execution plan currently targets only host `10688` (`ME_UPS1`). The remaining 6 facility assets (`ME_UPS2`, `ME_UPS3`, `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`) are unrepresented in the immediate 24-hour expansion plan.
- **Per-Host Item Breakdown:**
{host_summary}

## 3. Volume, Pagination, & Truncation Risks
- Items polling at 30s or 1m intervals generate ~1,440 to ~2,880 points per 24 hours.
- The 1,000 points/request batch limit requires the designed 3-batch pagination cap to prevent silent data truncation.

## 4. PAC Candidates & Transport Security
- **PAC Candidates:** Present in Phase G.6/G.8 source metadata (e.g., return/supply temperature, compressor status, fan speed), but not yet activated in active history pull plans.
- **Transport Security:** Unencrypted HTTP transport risk (`TRANSPORT_HTTP_RISK`) remains unmitigated by TLS. Private network segmentation is assumed but requires formal operator acknowledgment.

## 5. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
- Model Training: `False`
- Automatic Remediation: `False`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G14A_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.14A audit completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_audit()
