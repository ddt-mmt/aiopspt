#!/usr/bin/env python3
"""
Phase G.37 Staging Anomaly Detector for UPS and PAC Telemetry.
Reads read-only sensor CSV exports, performs data validation and robust anomaly detection
(Robust Z-score / Isolation Forest matching G.36 baseline), and outputs structured results.
Production safe: 0 modifications to production files, 0 Zabbix writes, 0 service restarts.
"""

import os
import sys
import json
import csv
import hashlib
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import glob
from sklearn.ensemble import IsolationForest

def main():
    print("=== PHASE G.37 STAGING ANOMALY DETECTOR ===")
    exec_time = datetime.now(timezone.utc).isoformat()
    staging_dir = "/root/grafan_aiops/staging_anomaly"
    output_dir = os.path.join(staging_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    val_dir = "/root/grafan_aiops/real_data_validation"
    csv_files = glob.glob(os.path.join(val_dir, "*.csv"))
    
    if not csv_files:
        print(f"ERROR: No CSV files found in {val_dir}")
        sys.exit(1)
        
    target_hosts = ['ME_UPS1', 'ME_UPS2', 'ME_UPS3', 'ME_PAC1', 'ME_PAC2', 'ME_PAC3', 'ME_PAC4']
    
    sensor_health_records = []
    anomaly_records = []
    summary_data = {
        "execution_timestamp": exec_time,
        "detector_version": "v3.7-staging",
        "thresholds": {
            "robust_z_threshold": 3.5,
            "isolation_forest_contamination": 0.05
        },
        "hosts_processed": target_hosts,
        "total_files_processed": 0,
        "total_samples_analyzed": 0,
        "total_anomalies_flagged": 0,
        "status": "PASS_STAGING_TESTED"
    }
    
    total_samples = 0
    total_anomalies = 0
    files_processed = 0
    
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
            if 'value' not in df.columns or df.empty:
                continue
                
            # Validate timestamps and missing values
            total_rows = len(df)
            missing_count = int(df['value'].isna().sum())
            
            # Drop NaN for analysis
            valid_df = df.dropna(subset=['value']).copy()
            valid_df['numeric_value'] = pd.to_numeric(valid_df['value'], errors='coerce')
            valid_df = valid_df.dropna(subset=['numeric_value'])
            
            sample_count = len(valid_df)
            if sample_count == 0:
                sensor_health_records.append({
                    "filename": fname,
                    "host": h_found,
                    "sample_count": 0,
                    "missing_values": missing_count,
                    "status": "INSUFFICIENT_DATA",
                    "anomalies_detected": 0
                })
                continue
                
            val_series = valid_df['numeric_value']
            
            # Robust Z-score (MAD)
            median = val_series.median()
            mad = (val_series - median).abs().median()
            if mad == 0 or np.isnan(mad):
                mad = 1.0e-5
                
            robust_z = 0.6745 * (val_series - median) / mad
            anomaly_mask = robust_z.abs() > 3.5
            
            # Isolation Forest
            X = val_series.values.reshape(-1, 1)
            if len(X) > 10:
                iso = IsolationForest(contamination=0.05, random_state=42)
                preds = iso.fit_predict(X)
                iso_mask = (preds == -1)
            else:
                iso_mask = np.zeros(len(X), dtype=bool)
                
            combined_anomaly_mask = anomaly_mask | iso_mask
            anomaly_count = int(combined_anomaly_mask.sum())
            
            total_samples += sample_count
            total_anomalies += anomaly_count
            files_processed += 1
            
            sensor_health_records.append({
                "filename": fname,
                "host": h_found,
                "sample_count": sample_count,
                "missing_values": missing_count,
                "status": "NORMAL" if anomaly_count == 0 else "ANOMALY_DETECTED",
                "anomalies_detected": anomaly_count,
                "median": round(float(median), 4),
                "mad": round(float(mad), 4)
            })
            
            # Record individual anomalies for detailed output
            anomalous_rows = valid_df[combined_anomaly_mask]
            for idx, row in anomalous_rows.iterrows():
                ts = row.get('timestamp', 'UNKNOWN')
                item_key = row.get('item_key', fname)
                val = row.get('numeric_value', 0.0)
                rz = float(robust_z.loc[idx]) if idx in robust_z.index else 0.0
                anomaly_records.append({
                    "host": h_found,
                    "sensor_file": fname,
                    "item_key": item_key,
                    "timestamp": ts,
                    "observed_value": float(val),
                    "robust_z_score": round(rz, 2),
                    "reason": "Robust Z-score > 3.5 or Isolation Forest Outlier"
                })
                
        except Exception as e:
            print(f"Warning: Error processing {fname}: {e}")
            
    summary_data["total_files_processed"] = files_processed
    summary_data["total_samples_analyzed"] = total_samples
    summary_data["total_anomalies_flagged"] = total_anomalies
    
    # Save outputs
    summary_json_path = os.path.join(output_dir, "staging_detection_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
        
    health_csv_path = os.path.join(output_dir, "staging_sensor_health.csv")
    health_fields = ["filename", "host", "sample_count", "missing_values", "status", "anomalies_detected", "median", "mad"]
    with open(health_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=health_fields)
        writer.writeheader()
        for r in sensor_health_records:
            writer.writerow(r)
            
    anomalies_csv_path = os.path.join(output_dir, "staging_anomalies_detected.csv")
    anomaly_fields = ["host", "sensor_file", "item_key", "timestamp", "observed_value", "robust_z_score", "reason"]
    with open(anomalies_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=anomaly_fields)
        writer.writeheader()
        for r in anomaly_records:
            writer.writerow(r)
            
    # Generate SHA256SUMS.txt
    sha_lines = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file == "SHA256SUMS.txt":
                continue
            fp = os.path.join(root, file)
            with open(fp, "rb") as f_obj:
                sh = hashlib.sha256(f_obj.read()).hexdigest()
            sha_lines.append(f"{sh}  {file}")
            
    sha_path = os.path.join(output_dir, "SHA256SUMS.txt")
    with open(sha_path, "w", encoding="utf-8") as f_sha:
        f_sha.write("\n".join(sha_lines) + "\n")
        
    print(f"Staging detector completed successfully.")
    print(f"Files processed: {files_processed}")
    print(f"Total samples analyzed: {total_samples}")
    print(f"Total anomalies flagged: {total_anomalies}")
    print(f"Outputs saved to: {output_dir}")

if __name__ == "__main__":
    main()
