"""
Phase G.12 Offline Anomaly Detection Experiment Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g12_offline_anomaly_experiment_20261015_260000/
Strict Rule: Zero API requests, zero production changes, zero remediation.
"""

import os
import csv
import json
import statistics
from datetime import datetime

INPUT_CSV = "/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g12_offline_anomaly_experiment_20261015_260000"

def run_experiment():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        return

    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    print(f"Loaded {len(rows)} input voltage points from Phase G.10.")

    # Sort chronologically by clock
    rows.sort(key=lambda x: int(x.get("clock", 0)))

    values = []
    for r in rows:
        try:
            values.append(float(r.get("value", 0)))
        except ValueError:
            values.append(0.0)

    n = len(values)
    mean_val = statistics.mean(values) if n > 0 else 0.0
    stdev_val = statistics.stdev(values) if n > 1 else 0.0
    median_val = statistics.median(values) if n > 0 else 0.0

    # Calculate MAD (Median Absolute Deviation)
    abs_devs = [abs(v - median_val) for v in values]
    mad_val = statistics.median(abs_devs) if n > 0 else 0.0

    results = []
    outlier_z_count = 0
    outlier_mad_count = 0

    for idx, r in enumerate(rows):
        val = values[idx]
        
        # Z-score with zero stdev check
        if stdev_val > 0:
            z_score = round((val - mean_val) / stdev_val, 4)
        else:
            z_score = 0.0

        # Robust MAD score (scaled by 0.6745 for normal distribution consistency) with zero MAD check
        if mad_val > 0:
            mad_score = round(0.6745 * (val - median_val) / mad_val, 4)
        else:
            mad_score = 0.0

        outlier_z = abs(z_score) > 3.0
        outlier_mad = abs(mad_score) > 3.5

        if outlier_z:
            outlier_z_count += 1
        if outlier_mad:
            outlier_mad_count += 1

        results.append({
            "itemid": r.get("itemid", ""),
            "clock": r.get("clock", ""),
            "value": r.get("value", ""),
            "ns": r.get("ns", ""),
            "z_score": z_score,
            "mad_score": mad_score,
            "outlier_z": outlier_z,
            "outlier_mad": outlier_mad
        })

    # Save PHASE_G12_RESULTS.csv
    csv_path = os.path.join(OUTPUT_DIR, "PHASE_G12_RESULTS.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "itemid", "clock", "value", "ns", "z_score", "mad_score", "outlier_z", "outlier_mad"
        ])
        writer.writeheader()
        for res in results:
            writer.writerow(res)

    # Save PHASE_G12_AUDIT.json
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.12",
        "shadow_version": "v5",
        "input_points_count": n,
        "statistics": {
            "mean": round(mean_val, 4),
            "stdev": round(stdev_val, 4),
            "median": round(median_val, 4),
            "mad": round(mad_val, 4)
        },
        "outlier_counts": {
            "outlier_z": outlier_z_count,
            "outlier_mad": outlier_mad_count
        },
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "automatic_remediation": False,
        "credential_values_logged": False,
        "final_status": "OFFLINE_ANOMALY_EXPERIMENT_COMPLETED"
    }
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G12_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G12_REPORT.md
    report_content = f"""# Phase G.12 Offline Anomaly Detection Experiment Report

## 1. Metadata
- **Experiment Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Input Source:** `{INPUT_CSV}`
- **Total Points Analyzed:** {n}
- **Final Status:** `{audit_data["final_status"]}`

## 2. Statistical Baseline
- **Mean:** `{audit_data["statistics"]["mean"]} V`
- **Standard Deviation:** `{audit_data["statistics"]["stdev"]} V`
- **Median:** `{audit_data["statistics"]["median"]} V`
- **MAD (Median Absolute Deviation):** `{audit_data["statistics"]["mad"]} V`

## 3. Outlier Detection Results
- **Z-Score Outliers (> 3.0):** {outlier_z_count}
- **Robust MAD Outliers (> 3.5):** {outlier_mad_count}
- **Baseline Limitation:** The baseline consists of only {n} points collected over ~1 hour. This small sample does not represent the full operating patterns or diurnal cycles of the facility. Outliers flagged are purely statistical indicators and not verified proof of UPS/PAC failure.

## 4. Compliance Confirmation
- API Requests: `0`
- Production Changes: `0`
- Automatic Remediation: `False`
- Credential Values Logged: `False`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G12_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.12 experiment completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_experiment()
