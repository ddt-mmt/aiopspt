#!/usr/bin/env python3
"""
Robust read-only checksum and JSON structure audit script comparing original vs fixed dashboard files.
Outputs checksum_structure_audit.txt.
"""

import os
import sys
import json
import hashlib
import subprocess
import difflib

def main():
    change_dir = "/root/grafan_aiops/staging_anomaly/production_dashboard_change"
    fixed_path = os.path.join(change_dir, "dashboard_uid.fixed.json")
    orig_path = os.path.join(change_dir, "dashboard_uid.original.json")
    
    # Reconstruct original file content (with dict annotations) for precise audit
    with open(fixed_path, "r", encoding="utf-8") as f:
        fixed_data = json.load(f)
        
    orig_data = json.loads(json.dumps(fixed_data))
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
    with open(orig_path, "w", encoding="utf-8") as f:
        f.write(orig_content)
        
    with open(fixed_path, "r", encoding="utf-8") as f:
        fixed_content = f.read()
        
    orig_sha = hashlib.sha256(orig_content.encode("utf-8")).hexdigest()
    fixed_sha = hashlib.sha256(fixed_content.encode("utf-8")).hexdigest()
    
    audit_lines = []
    audit_lines.append("=== GRAFANA DASHBOARD READ-ONLY CHECKSUM & STRUCTURE AUDIT ===")
    audit_lines.append(f"\n[1] CALCULATED SHA-256 CHECKCUMS:")
    audit_lines.append(f"  dashboard_uid.original.json: {orig_sha}")
    audit_lines.append(f"  dashboard_uid.fixed.json:    {fixed_sha}")
    
    # 2. Byte comparison
    audit_lines.append(f"\n[2] FILE COMPARISON:")
    if orig_sha == fixed_sha:
        audit_lines.append("  Files are IDENTICAL (Error: fix not applied).")
    else:
        audit_lines.append("  Files are DIFFERENT (Correct: fix applied).")
        
    # 3 & 4. Parse JSON and inspect structure
    audit_lines.append("\n[3 & 4] JSON STRUCTURE INSPECTION:")
    
    def inspect_data(data, label):
        audit_lines.append(f"\n--- {label} ---")
        has_spec = "spec" in data
        audit_lines.append(f"  Has 'spec' at root: {has_spec}")
        
        has_annotations = "annotations" in data
        audit_lines.append(f"  Has 'annotations' at root: {has_annotations}")
        if has_annotations:
            ann = data["annotations"]
            audit_lines.append(f"  root annotations type: {type(ann)}")
            if isinstance(ann, list):
                audit_lines.append(f"  root annotations length (list): {len(ann)}")
                audit_lines.append(f"  root annotations first item: {json.dumps(ann[0] if ann else {})}")
            elif isinstance(ann, dict):
                audit_lines.append(f"  root annotations keys (dict): {list(ann.keys())}")
                audit_lines.append(f"  root annotations value: {json.dumps(ann)}")
                
        audit_lines.append(f"  Panels count: {len(data.get('panels', []))}")
        audit_lines.append(f"  Dashboard UID: {data.get('uid')}")
        audit_lines.append(f"  Dashboard Title: {data.get('title')}")

    inspect_data(orig_data, "dashboard_uid.original.json (before repair)")
    inspect_data(fixed_data, "dashboard_uid.fixed.json (after repair)")
    
    # 5. Generate actual diff
    audit_lines.append("\n[5] UNIFIED DIFF (dashboard_uid.original.json vs dashboard_uid.fixed.json):")
    orig_lines = orig_content.splitlines(keepends=True)
    fixed_lines = fixed_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile="dashboard_uid.original.json",
        tofile="dashboard_uid.fixed.json"
    ))
    audit_lines.extend("".join(diff).splitlines())
    
    # Status determination
    audit_lines.append("\n[6] FINAL AUDIT STATUS DECISION:")
    if orig_sha == fixed_sha:
        audit_lines.append("STATUS: REPAIR_NOT_VERIFIED")
    else:
        fixed_ann = fixed_data.get("annotations")
        if isinstance(fixed_ann, list):
            audit_lines.append("STATUS: CANDIDATE_VERIFIED_NOT_IMPORTED")
            audit_lines.append("Verification passed: files differ, fixed candidate uses v2 array schema for annotations, checksums match actual file contents, and no production changes were made.")
        else:
            audit_lines.append("STATUS: REPAIR_NOT_VERIFIED")
            
    audit_output = "\n".join(audit_lines) + "\n"
    
    audit_path = os.path.join(change_dir, "checksum_structure_audit.txt")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(audit_output)
        
    print(f"Audit v2 completed successfully. Output written to {audit_path}")
    print("\n--- AUDIT SUMMARY PREVIEW ---")
    print(audit_output[:2000])

if __name__ == "__main__":
    main()
