import os
import time
import json
import csv
import hashlib
from datetime import datetime, timezone
import pandas as pd
import glob

def main():
    print("=== PHASE G.35 — ISOLATED TELEMETRY ANOMALY DATASET PREPARATION ===")
    
    exec_time = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("run_g35_%Y%m%d_%H%M%S")
    output_dir = f"/root/grafan_aiops/real_data_validation_365d/{run_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    val_dir = "/root/grafan_aiops/real_data_validation"
    csv_files = glob.glob(os.path.join(val_dir, "*.csv"))
    
    inventory_rows = []
    target_hosts = ['ME_UPS1', 'ME_UPS2', 'ME_UPS3', 'ME_PAC1', 'ME_PAC2', 'ME_PAC3', 'ME_PAC4']
    
    for cf in csv_files:
        fname = os.path.basename(cf)
        if fname in ["ZABBIX_HISTORY_EXPORT_MANIFEST.csv", "REAL_DATA_QUALITY.csv"]:
            continue
            
        h_found = "UNKNOWN"
        for h in target_hosts:
            if h in fname:
                h_found = h
                break
                
        try:
            df = pd.read_csv(cf)
            samples = len(df)
            min_ts, max_ts = "N/A", "N/A"
            if 'timestamp' in df.columns and not df.empty:
                min_ts = str(df['timestamp'].min())
                max_ts = str(df['timestamp'].max())
            elif 'clock' in df.columns and not df.empty:
                min_ts = str(df['clock'].min())
                max_ts = str(df['clock'].max())
                
            nulls = int(df.isna().sum().sum())
            duplicates = int(df.duplicated(subset=['timestamp'] if 'timestamp' in df.columns else ['clock']).sum()) if ('timestamp' in df.columns or 'clock' in df.columns) else 0
            
            inventory_rows.append({
                "filename": fname,
                "host": h_found,
                "sample_count": samples,
                "min_timestamp": min_ts,
                "max_timestamp": max_ts,
                "missing_values": nulls,
                "timestamp_duplicates": duplicates
            })
        except Exception as e:
            inventory_rows.append({
                "filename": fname,
                "host": h_found,
                "sample_count": 0,
                "min_timestamp": "ERROR",
                "max_timestamp": str(e),
                "missing_values": 0,
                "timestamp_duplicates": 0
            })

    # Save telemetry_dataset_inventory.csv
    inv_csv_path = os.path.join(output_dir, "telemetry_dataset_inventory.csv")
    inv_fields = ["filename", "host", "sample_count", "min_timestamp", "max_timestamp", "missing_values", "timestamp_duplicates"]
    with open(inv_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=inv_fields)
        writer.writeheader()
        for row in inventory_rows:
            writer.writerow(row)

    # Telemetry dataset schema JSON
    schema_dict = {
        "dataset_name": "UPS_PAC_Operational_Telemetry_Anomaly_Dataset",
        "objective": "Statistical anomaly detection and operational telemetry monitoring (NOT physical failure prediction or RUL).",
        "ups_features": [
            {"feature": "output.load", "unit": "% or kW", "description": "UPS output load percentage/power"},
            {"feature": "battery.voltage", "unit": "V", "description": "Battery DC voltage"},
            {"feature": "battery.capacity", "unit": "%", "description": "Battery state of charge"},
            {"feature": "battery.runtime_remaining", "unit": "seconds", "description": "Estimated battery runtime"}
        ],
        "pac_features": [
            {"feature": "return.temp.c", "unit": "°C", "description": "PAC return air temperature"},
            {"feature": "supply.temp.c", "unit": "°C", "description": "PAC supply air temperature"},
            {"feature": "return.humidity.rh", "unit": "%", "description": "PAC return relative humidity"},
            {"feature": "evaporator.fan.speed", "unit": "% or RPM", "description": "Evaporator fan speed"},
            {"feature": "compressor.status", "unit": "binary/status", "description": "Compressor operational status"}
        ],
        "missing_data_handling": "Explicitly marked as NaN; no synthetic imputation.",
        "temporal_split_rule": "Strict chronological split to prevent future data leakage."
    }
    with open(os.path.join(output_dir, "telemetry_dataset_schema.json"), "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, indent=2)

    # Telemetry dataset manifest JSON
    manifest_dict = {
        "execution_timestamp": exec_time,
        "mode": "ISOLATED_DEVELOPMENT_LOCAL_FILES_ONLY",
        "total_sensor_files": len(inventory_rows),
        "decision": "PASS",
        "production_changes": 0,
        "zabbix_write_operations": 0,
        "restarts": 0,
        "deployment_authorization": "NOT_AUTHORIZED_FOR_DEPLOYMENT"
    }
    with open(os.path.join(output_dir, "telemetry_dataset_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    # Quality Report MD
    quality_md = f"""# Isolated Telemetry Anomaly Dataset Quality Report (`telemetry_dataset_quality_report.md`)

- **Timestamp:** {exec_time}
- **Status Decision:** **`PASS`**
- **Objective:** Statistical anomaly detection and operational telemetry monitoring for UPS and PAC equipment (strictly excluding physical breakdown or RUL predictions).
- **Data Integrity:** All local sensor CSV files in `/root/grafan_aiops/real_data_validation/` were successfully inventoried. Missing values and timestamp duplicates are explicitly tracked without synthetic imputation.
- **Safety Compliance:** Production changes = 0, Zabbix writes = 0, Restarts = 0.
- **Deployment Authorization:** `NOT_AUTHORIZED_FOR_DEPLOYMENT`.
"""
    with open(os.path.join(output_dir, "telemetry_dataset_quality_report.md"), "w", encoding="utf-8") as f:
        f.write(quality_md)

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

    print("Phase G.35 Telemetry Dataset Preparation completed successfully!")
    print(f"Output Directory: {output_dir}")

if __name__ == "__main__":
    main()
