"""
Phase G.11 Local History Quality Analysis Execution
Isolated in /root/grafan_aiops/shadow_v5/phase_g11_local_history_analysis_20261015_250000/
Strict Rule: Zero API requests, zero production changes, zero remediation.
"""

import os
import csv
import json
import statistics
from datetime import datetime

BATTERY_CSV = "/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_BATTERY_VOLTAGE.csv"
INPUT_CSV = "/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/PHASE_G10_INPUT_VOLTAGE.csv"
OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g11_local_history_analysis_20261015_250000"

def load_csv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def analyze_history():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    battery_rows = load_csv(BATTERY_CSV)
    input_rows = load_csv(INPUT_CSV)
    
    print(f"Loaded {len(battery_rows)} battery voltage points and {len(input_rows)} input voltage points.")

    # Validate Battery Voltage
    battery_analysis = {
        "itemid": "59604",
        "name": "Battery voltage",
        "unit": "V",
        "valid_points_count": len(battery_rows),
        "limitations": "Only a single data point collected. Trends, volatility, and anomaly detection cannot be computed from one point."
    }
    if battery_rows:
        val = float(battery_rows[0].get("value", 0))
        battery_analysis["single_value"] = val
        battery_analysis["clock"] = battery_rows[0].get("clock")

    # Validate Input Voltage
    input_values = []
    input_clocks = []
    for r in input_rows:
        try:
            v = float(r.get("value", 0))
            c = int(r.get("clock", 0))
            input_values.append(v)
            input_clocks.append(c)
        except ValueError:
            pass

    input_analysis = {
        "itemid": "59607",
        "name": "Input voltage",
        "unit": "V",
        "valid_points_count": len(input_values)
    }

    if input_values:
        input_analysis["min_value"] = round(min(input_values), 4)
        input_analysis["max_value"] = round(max(input_values), 4)
        input_analysis["mean_value"] = round(statistics.mean(input_values), 4)
        input_analysis["median_value"] = round(statistics.median(input_values), 4)
        input_analysis["earliest_clock"] = min(input_clocks)
        input_analysis["latest_clock"] = max(input_clocks)
        input_analysis["time_range_seconds"] = max(input_clocks) - min(input_clocks)
        
        # Calculate average interval if multiple points
        if len(input_clocks) > 1:
            diffs = [input_clocks[i] - input_clocks[i-1] for i in range(1, len(input_clocks))]
            input_analysis["avg_interval_seconds"] = round(statistics.mean(diffs), 2)
        else:
            input_analysis["avg_interval_seconds"] = 0

    metrics_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.11",
        "shadow_version": "v5",
        "battery_voltage_analysis": battery_analysis,
        "input_voltage_analysis": input_analysis
    }

    # Save PHASE_G11_METRICS.json
    metrics_path = os.path.join(OUTPUT_DIR, "PHASE_G11_METRICS.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    # Save PHASE_G11_AUDIT.json
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.11",
        "shadow_version": "v5",
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "automatic_remediation": False,
        "credential_values_logged": False,
        "final_status": "LOCAL_HISTORY_ANALYSIS_COMPLETED"
    }
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G11_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G11_REPORT.md
    report_content = f"""# Phase G.11 Local History Quality Analysis Report

## 1. Metadata
- **Analysis Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. Battery Voltage Analysis (Item 59604)
- **Valid Points:** {battery_analysis["valid_points_count"]}
- **Recorded Value:** `{battery_analysis.get("single_value", "N/A")} V`
- **Limitations:** {battery_analysis["limitations"]}

## 3. Input Voltage Analysis (Item 59607)
- **Valid Points:** {input_analysis["valid_points_count"]}
- **Minimum Value:** `{input_analysis.get("min_value", "N/A")} V`
- **Maximum Value:** `{input_analysis.get("max_value", "N/A")} V`
- **Average (Mean):** `{input_analysis.get("mean_value", "N/A")} V`
- **Median:** `{input_analysis.get("median_value", "N/A")} V`
- **Time Range (seconds):** {input_analysis.get("time_range_seconds", 0)}
- **Average Measurement Interval (seconds):** {input_analysis.get("avg_interval_seconds", 0)}
- **Threshold Note:** Values are reported in Volts (V). No claims regarding normal vs. abnormal state are made without validated vendor thresholds.

## 4. Compliance Confirmation
- API Requests: `0`
- Production Changes: `0`
- Automatic Remediation: `False`
- Credential Values Logged: `False`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G11_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.11 analysis completed successfully. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    analyze_history()
