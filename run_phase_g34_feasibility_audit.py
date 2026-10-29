import os
import time
import json
import csv
import hashlib
from datetime import datetime, timezone
import pandas as pd
import glob

def main():
    print("=== PHASE G.34 — ISOLATED MULTI-SENSOR DATASET FEASIBILITY AUDIT ===")
    
    exec_time = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("run_g34_%Y%m%d_%H%M%S")
    output_dir = f"/root/grafan_aiops/real_data_validation_365d/{run_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    val_dir = "/root/grafan_aiops/real_data_validation"
    csv_files = glob.glob(os.path.join(val_dir, "*.csv"))
    
    inventory_rows = []
    host_sensor_summary = {}
    
    target_hosts = ['ME_UPS1', 'ME_UPS2', 'ME_UPS3', 'ME_PAC1', 'ME_PAC2', 'ME_PAC3', 'ME_PAC4']
    
    for h in target_hosts:
        host_sensor_summary[h] = {"files_found": 0, "total_samples": 0}
        
    for cf in csv_files:
        fname = os.path.basename(cf)
        if fname in ["ZABBIX_HISTORY_EXPORT_MANIFEST.csv", "REAL_DATA_QUALITY.csv"]:
            continue
            
        # Determine host from filename
        h_found = "UNKNOWN"
        for h in target_hosts:
            if h in fname:
                h_found = h
                break
                
        try:
            df = pd.read_csv(cf)
            samples = len(df)
            cols = list(df.columns)
            min_ts, max_ts = "N/A", "N/A"
            if 'timestamp' in df.columns and not df.empty:
                min_ts = str(df['timestamp'].min())
                max_ts = str(df['timestamp'].max())
            elif 'clock' in df.columns and not df.empty:
                min_ts = str(df['clock'].min())
                max_ts = str(df['clock'].max())
                
            nulls = int(df.isna().sum().sum())
            
            inventory_rows.append({
                "filename": fname,
                "host": h_found,
                "sample_count": samples,
                "min_timestamp": min_ts,
                "max_timestamp": max_ts,
                "null_values": nulls,
                "columns": str(cols)
            })
            
            if h_found in host_sensor_summary:
                host_sensor_summary[h_found]["files_found"] += 1
                host_sensor_summary[h_found]["total_samples"] += samples
        except Exception as e:
            inventory_rows.append({
                "filename": fname,
                "host": h_found,
                "sample_count": 0,
                "min_timestamp": "ERROR",
                "max_timestamp": str(e),
                "null_values": 0,
                "columns": "[]"
            })

    # Save sensor_inventory.csv
    inv_csv_path = os.path.join(output_dir, "sensor_inventory.csv")
    inv_fields = ["filename", "host", "sample_count", "min_timestamp", "max_timestamp", "null_values", "columns"]
    with open(inv_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=inv_fields)
        writer.writeheader()
        for row in inventory_rows:
            writer.writerow(row)

    # Dataset feasibility JSON
    feasibility_dict = {
        "execution_timestamp": exec_time,
        "target_hosts": target_hosts,
        "host_sensor_summary": host_sensor_summary,
        "critical_finding": "Equipment is newly installed and lacks historical physical failure/breakdown ground truth logs (both manual and machine logs). Therefore, ML scope is strictly constrained to Zabbix alarm event and operational telemetry anomaly detection, NOT physical equipment failure prediction.",
        "decision": "PARTIAL",
        "production_changes": 0,
        "zabbix_write_operations": 0,
        "restarts": 0,
        "deployment_authorization": "NOT_AUTHORIZED_FOR_DEPLOYMENT"
    }
    with open(os.path.join(output_dir, "dataset_feasibility.json"), "w", encoding="utf-8") as f:
        json.dump(feasibility_dict, f, indent=2)

    # Sensor coverage report MD
    coverage_md = f"""# Isolated Multi-Sensor Dataset Feasibility Audit (`sensor_coverage_report.md`)

- **Timestamp:** {exec_time}
- **Status Decision:** **`PARTIAL`**
- **Critical Real-World Constraint:** As noted by engineering review, these UPS and PAC units are newly deployed and lack historical physical breakdown/failure logs over the past year (both manual maintenance logs and machine logs). 
- **Methodological Impact:** 
  1. *Physical Failure Prediction:* Infeasible due to total absence of physical breakdown ground truth.
  2. *Zabbix Alarm & Operational Telemetry Monitoring:* Feasible and valuable, using historical sensor telemetry and Zabbix trigger events as operational indicators.
- **Host Sensor Coverage Summary:**
"""
    for h, info in host_sensor_summary.items():
        coverage_md += f"  - `{h}`: Files Found = {info['files_found']}, Total Samples = {info['total_samples']}\n"

    coverage_md += f"""
- **Safety Compliance:** Production changes = 0, Zabbix writes = 0, Restarts = 0.
- **Deployment Authorization:** `NOT_AUTHORIZED_FOR_DEPLOYMENT`.
"""
    with open(os.path.join(output_dir, "sensor_coverage_report.md"), "w", encoding="utf-8") as f:
        f.write(coverage_md)

    # Checksums
    sha_lines = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file == "SHA256SUMS.txt":
                continue
            fp = os.path.join(root, file)
            with open(fp, "rb") as f_obj:
                sh = hashlib.sha256(f_obj.read()).hexdigest()
            sha_lines.append(f"{sh}  {file}")
            
    with open(os.path.join(output_dir, "SHA256SUMS.txt"), "w", encoding="utf-8") as f_sha:
        f_sha.write("\n".join(sha_lines) + "\n")

    print("Phase G.34 Feasibility Audit completed successfully!")
    print(f"Output Directory: {output_dir}")

if __name__ == "__main__":
    main()
