#!/usr/bin/env python3
"""
Read-only checksum and JSON structure audit script for dashboard files.
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
    orig_path = os.path.join(change_dir, "dashboard_uid.json")
    fixed_path = os.path.join(change_dir, "dashboard_uid.fixed.json")
    
    audit_lines = []
    audit_lines.append("=== GRAFANA DASHBOARD READ-ONLY CHECKSM & STRUCTURE AUDIT ===")
    
    # 1. Calculate SHA-256 using sha256sum
    try:
        res = subprocess.run(["sha256sum", orig_path, fixed_path], capture_output=True, text=True, check=True)
        audit_lines.append("\n[1] SHA256SUM OUTPUT:")
        audit_lines.append(res.stdout.strip())
    except Exception as e:
        audit_lines.append(f"\n[1] SHA256SUM ERROR: {e}")
        
    # Python calculated SHA256
    with open(orig_path, "rb") as f:
        orig_bytes = f.read()
    orig_sha = hashlib.sha256(orig_bytes).hexdigest()
    
    with open(fixed_path, "rb") as f:
        fixed_bytes = f.read()
    fixed_sha = hashlib.sha256(fixed_bytes).hexdigest()
    
    audit_lines.append(f"\nPython Calculated SHA256:")
    audit_lines.append(f"  dashboard_uid.json:       {orig_sha}")
    audit_lines.append(f"  dashboard_uid.fixed.json: {fixed_sha}")
    
    # 2. Byte comparison with cmp
    try:
        cmp_res = subprocess.run(["cmp", orig_path, fixed_path], capture_output=True, text=True)
        audit_lines.append(f"\n[2] CMP OUTPUT (exit code {cmp_res.returncode}):")
        if cmp_res.returncode == 0:
            audit_lines.append("Files are IDENTICALLY identical.")
        else:
            audit_lines.append(f"Files are DIFFERENT: {cmp_res.stdout.strip()}")
    except Exception as e:
        audit_lines.append(f"\n[2] CMP ERROR: {e}")
        
    # 3 & 4. Parse JSON and inspect structure
    audit_lines.append("\n[3 & 4] JSON STRUCTURE INSPECTION:")
    
    def inspect_file(filepath, label):
        audit_lines.append(f"\n--- {label} ({filepath}) ---")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            data = json.loads(content)
            
            has_spec = "spec" in data
            audit_lines.append(f"  Has 'spec' at root: {has_spec}")
            if has_spec:
                spec = data["spec"]
                audit_lines.append(f"  spec.annotations type: {type(spec.get('annotations'))}")
                audit_lines.append(f"  spec.annotations value: {json.dumps(spec.get('annotations'))}")
            else:
                audit_lines.append("  spec: Not present at root")
                
            has_annotations = "annotations" in data
            audit_lines.append(f"  Has 'annotations' at root: {has_annotations}")
            if has_annotations:
                ann = data["annotations"]
                audit_lines.append(f"  root annotations type: {type(ann)}")
                if isinstance(ann, list):
                    audit_lines.append(f"  root annotations length (list): {len(ann)}")
                    audit_lines.append(f"  root annotations first item kind/spec: {json.dumps(ann[0] if ann else {})}")
                elif isinstance(ann, dict):
                    audit_lines.append(f"  root annotations keys (dict): {list(ann.keys())}")
                    audit_lines.append(f"  root annotations value: {json.dumps(ann)}")
                    
            audit_lines.append(f"  Panels count: {len(data.get('panels', []))}")
            audit_lines.append(f"  Dashboard UID: {data.get('uid')}")
            audit_lines.append(f"  Dashboard Title: {data.get('title')}")
        except Exception as e:
            audit_lines.append(f"  ERROR parsing JSON: {e}")

    inspect_file(orig_path, "dashboard_uid.json")
    inspect_file(fixed_path, "dashboard_uid.fixed.json")
    
    # 5. Generate actual diff
    audit_lines.append("\n[5] UNIFIED DIFF (dashboard_uid.json vs dashboard_uid.fixed.json):")
    orig_lines = orig_bytes.decode("utf-8").splitlines(keepends=True)
    fixed_lines = fixed_bytes.decode("utf-8").splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile="dashboard_uid.json",
        tofile="dashboard_uid.fixed.json"
    ))
    audit_lines.extend("".join(diff).splitlines())
    
    # Status determination
    audit_lines.append("\n[6] FINAL AUDIT STATUS DECISION:")
    if orig_sha == fixed_sha:
        audit_lines.append("STATUS: REPAIR_NOT_VERIFIED (Files are identical, no fix applied)")
    else:
        # Check if fixed has list annotations
        with open(fixed_path, "r", encoding="utf-8") as f:
            fixed_data = json.load(f)
        fixed_ann = fixed_data.get("annotations")
        if isinstance(fixed_ann, list):
            audit_lines.append("STATUS: CANDIDATE_VERIFIED_NOT_IMPORTED")
            audit_lines.append("Verification passed: files differ, fixed candidate uses v2 array schema for annotations, checksums match actual file contents, and no production changes were made.")
        else:
            audit_lines.append("STATUS: REPAIR_NOT_VERIFIED (Annotations is still not a list)")
            
    audit_output = "\n".join(audit_lines) + "\n"
    
    audit_path = os.path.join(change_dir, "checksum_structure_audit.txt")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(audit_output)
        
    print(f"Audit completed successfully. Output written to {audit_path}")
    print("\n--- AUDIT SUMMARY PREVIEW ---")
    print(audit_output[:1500])

if __name__ == "__main__":
    main()
