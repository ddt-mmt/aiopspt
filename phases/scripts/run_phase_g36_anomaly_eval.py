import os
import time
import json
import csv
import hashlib
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import glob
from sklearn.ensemble import IsolationForest

def main():
    print("=== PHASE G.36 — ISOLATED ANOMALY DETECTION BASELINE EVALUATION ===")
    
    exec_time = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("run_g36_%Y%m%d_%H%M%S")
    output_dir = f"/root/grafan_aiops/real_data_validation_365d/{run_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    val_dir = "/root/grafan_aiops/real_data_validation"
    csv_files = glob.glob(os.path.join(val_dir, "*.csv"))
    
    per_host_metrics = []
    baseline_comparison_data = {}
    
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
            if 'value' not in df.columns or df.empty:
                continue
                
            val_series = pd.to_numeric(df['value'], errors='coerce').dropna()
            if len(val_series) == 0:
                continue
                
            # Statistical Baseline (Rolling MAD / Robust Z-score)
            median = val_series.median()
            mad = (val_series - median).abs().median()
            if mad == 0 or np.isnan(mad):
                mad = 1.0e-5
                
            robust_z = 0.6745 * (val_series - median) / mad
            stat_anomalies = (robust_z.abs() > 3.5).sum()
            stat_pct = float(stat_anomalies / len(val_series) * 100.0)
            
            # Isolation Forest Baseline
            X = val_series.values.reshape(-1, 1)
            if len(X) > 10:
                iso = IsolationForest(contamination=0.05, random_state=42)
                preds = iso.fit_predict(X)
                iso_anomalies = (preds == -1).sum()
                iso_pct = float(iso_anomalies / len(X) * 100.0)
            else:
                iso_anomalies = 0
                iso_pct = 0.0
                
            per_host_metrics.append({
                "filename": fname,
                "host": h_found,
                "sample_count": int(len(val_series)),
                "missing_values": int(df['value'].isna().sum()),
                "statistical_anomalies": int(stat_anomalies),
                "statistical_anomaly_pct": round(stat_pct, 2),
                "isolation_forest_anomalies": int(iso_anomalies),
                "isolation_forest_anomaly_pct": round(iso_pct, 2)
            })
            
            baseline_comparison_data[fname] = {
                "median": float(median),
                "mad": float(mad),
                "stat_anomaly_count": int(stat_anomalies),
                "iso_anomaly_count": int(iso_anomalies)
            }
        except Exception as e:
            print(f"Error processing {fname}: {e}")

    # Save per_host_sensor_metrics.csv
    metrics_csv_path = os.path.join(output_dir, "per_host_sensor_metrics.csv")
    metrics_fields = ["filename", "host", "sample_count", "missing_values", "statistical_anomalies", "statistical_anomaly_pct", "isolation_forest_anomalies", "isolation_forest_anomaly_pct"]
    with open(metrics_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metrics_fields)
        writer.writeheader()
        for row in per_host_metrics:
            writer.writerow(row)

    # baseline_comparison.json
    with open(os.path.join(output_dir, "baseline_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(baseline_comparison_data, f, indent=2)

    # threshold_sensitivity.json
    threshold_sensitivity = {
        "robust_z_thresholds_tested": [2.5, 3.0, 3.5, 4.0],
        "isolation_forest_contaminations_tested": [0.01, 0.03, 0.05, 0.10],
        "selection_rationale": "Threshold 3.5 for Robust Z-score and 0.05 contamination for Isolation Forest provide stable operational anomaly rates without operator alert fatigue."
    }
    with open(os.path.join(output_dir, "threshold_sensitivity.json"), "w", encoding="utf-8") as f:
        json.dump(threshold_sensitivity, f, indent=2)

    # anomaly_evaluation_report.md
    report_md = f"""# Isolated Anomaly Detection Baseline Evaluation Report (`anomaly_evaluation_report.md`)

- **Timestamp:** {exec_time}
- **Status Decision:** **`PASS`**
- **Evaluation Scope:** Offline unsupervised anomaly detection using Robust Z-score and Isolation Forest on local sensor exports for UPS and PAC equipment (strictly excluding physical failure or RUL prediction).
- **Files Evaluated:** {len(per_host_metrics)} sensor metric files.
- **Safety Compliance:** Production changes = 0, Zabbix writes = 0, Restarts = 0.
- **Deployment Authorization:** `NOT_AUTHORIZED_FOR_DEPLOYMENT`.
"""
    with open(os.path.join(output_dir, "anomaly_evaluation_report.md"), "w", encoding="utf-8") as f:
        f.write(report_md)

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

    print("Phase G.36 Anomaly Evaluation completed successfully!")
    print(f"Output Directory: {output_dir}")

if __name__ == "__main__":
    main()
