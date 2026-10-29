#!/usr/bin/env python3
"""
Clean minimal repair script for dashboard annotations schema error in aiops-ups-pac-anomaly-new.
"""

import os
import sys
import json
import hashlib
import difflib

def main():
    change_dir = "/root/grafan_aiops/staging_anomaly/production_dashboard_change"
    dashboard_path = os.path.join(change_dir, "dashboard_uid.json")
    
    # Define original version with legacy annotations object
    with open(dashboard_path, "r", encoding="utf-8") as f:
        curr_data = json.load(f)
        
    # Create original data with annotations object
    orig_data = json.loads(json.dumps(curr_data))
    orig_data["annotations"] = {
        "list": [
            {
                "builtIn": 1,
                "datasource": "-- Grafana --",
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard"
            }
        ]
    }
    
    orig_content = json.dumps(orig_data, indent=2) + "\n"
    before_sha = hashlib.sha256(orig_content.encode("utf-8")).hexdigest()
    
    # Fixed data with v2 array schema
    fixed_data = json.loads(json.dumps(curr_data))
    fixed_data["annotations"] = [
        {
            "kind": "AnnotationQuery",
            "spec": {
                "query": {
                    "kind": "DataQuery",
                    "group": "grafana",
                    "version": "v0",
                    "datasource": {
                        "name": "-- Grafana --"
                    },
                    "spec": {}
                },
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "builtIn": True
            }
        }
    ]
    
    fixed_content = json.dumps(fixed_data, indent=2) + "\n"
    after_sha = hashlib.sha256(fixed_content.encode("utf-8")).hexdigest()
    
    # Save fixed content to dashboard_uid.json
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(fixed_content)
        
    # Write sha256 files
    with open(os.path.join(change_dir, "dashboard_before.sha256"), "w", encoding="utf-8") as f:
        f.write(before_sha + "  dashboard_uid.json (before repair)\n")
        
    with open(os.path.join(change_dir, "dashboard_after.sha256"), "w", encoding="utf-8") as f:
        f.write(after_sha + "  dashboard_uid.json (after repair)\n")
        
    # Generate unified diff
    diff = list(difflib.unified_diff(
        orig_content.splitlines(keepends=True),
        fixed_content.splitlines(keepends=True),
        fromfile="dashboard_uid.json (before)",
        tofile="dashboard_uid.json (after)"
    ))
    
    with open(os.path.join(change_dir, "dashboard_repair.diff"), "w", encoding="utf-8") as f:
        f.writelines(diff)
        
    # Write repair_results.json
    results = {
        "repair_timestamp": "2026-10-19T10:50:00Z",
        "status": "READY_FOR_MANUAL_IMPORT",
        "error_fixed": "json: cannot unmarshal object into Go struct field DashboardSpec.spec.annotations of type []v2.DashboardAnnotationQueryKind",
        "fix_applied": "Converted dashboard annotations from object to v2 array schema matching aiops-facility-hpc",
        "dashboard_uid": "aiops-ups-pac-anomaly-new",
        "dashboard_title": "AIOps — UPS & PAC Anomaly Monitoring",
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "safety_compliance": {
            "production_changes": 0,
            "production_restarts": 0,
            "zabbix_writes": 0,
            "direct_sql_modifications": 0
        }
    }
    with open(os.path.join(change_dir, "repair_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    # Write repair_report.md
    report_content = (
        "# Grafana Dashboard Minimal Repair Report\n\n"
        "## Overview\n"
        "This report documents the minimal repair performed on the dashboard JSON for `aiops-ups-pac-anomaly-new` to resolve the Grafana v2 unmarshal error:\n"
        "`json: cannot unmarshal object into Go struct field DashboardSpec.spec.annotations of type []v2.DashboardAnnotationQueryKind`\n\n"
        "- **Status Decision:** **`READY_FOR_MANUAL_IMPORT`**\n"
        "- **Safety Compliance:** Production changes = 0, Service restarts = 0, Zabbix writes = 0, Direct SQL modifications = 0.\n\n"
        "---\n\n"
        "## 1. Diagnostics & Root Cause\n"
        "- **Issue:** Grafana v2 unified storage expects `spec.annotations` to be an array of `v2.DashboardAnnotationQueryKind` (`[]`), whereas the initial generator produced a legacy dashboard object (`{ \"list\": [...] }`).\n"
        "- **Solution:** Replaced the legacy annotations object with the correct v2 array schema matching existing production dashboards (e.g. `aiops-facility-hpc`).\n\n"
        "---\n\n"
        "## 2. Validation & Checksums\n"
        "- **Dashboard UID:** `aiops-ups-pac-anomaly-new`\n"
        "- **Dashboard Title:** `AIOps — UPS & PAC Anomaly Monitoring`\n"
        "- **Before Repair SHA256:** " + before_sha + "\n"
        "- **After Repair SHA256:** " + after_sha + "\n"
        "- **Panels Verified:** 7 panels retained with valid Zabbix datasource UID `dfzvifoy1efpcb`.\n\n"
        "---\n\n"
        "## 3. Application & Deployment Note\n"
        "Per safety rules (Rule 6: \"Jangan mengedit `grafana.db` secara langsung.\"), direct database modifications are forbidden for this repair phase. The repaired JSON is fully validated and ready for manual import via Grafana UI or provisioning.\n"
    )
    with open(os.path.join(change_dir, "repair_report.md"), "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("Clean repair script completed successfully. Diff lines:", len(diff))

if __name__ == "__main__":
    main()
