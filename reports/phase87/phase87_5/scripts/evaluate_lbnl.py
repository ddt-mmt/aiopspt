"""
Phase 87.5 LBNL RTU Evaluation & Generalization Validation
Computes rigorous anomaly detection metrics (Precision, Recall, F1, False Positive Rate, Confusion Matrix)
across multiple fault types and severities comparing Isolation Forest vs Statistical Baseline.
"""

import os
import glob
import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest

LBNL_DIR = "/tmp/aiops_phase87_4/extracted/lbnl_rtu"
OUT_DIR = "/root/grafan_aiops/reports/phase87/phase87_5/lbnl"

def load_data(path, max_rows=3000):
    data = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            try:
                vals = [float(x) for x in row[1:10] if x.strip() != ""]
                if len(vals) == 9:
                    data.append(vals)
            except ValueError:
                continue
    return np.array(data)

def evaluate_lbnl():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    baseline_matches = glob.glob(os.path.join(LBNL_DIR, "**/RTU_sim_baseline.csv"), recursive=True)
    if not baseline_matches:
        print("Baseline not found.")
        return
        
    baseline_path = baseline_matches[0]
    raw_data = load_data(baseline_path, max_rows=6000)
    
    if len(raw_data) < 4000:
        print("Not enough baseline samples.")
        return
        
    X_train = raw_data[:3000]
    X_val_normal = raw_data[3000:4500]
    X_test_normal = raw_data[4500:6000]
    
    # 1. Train Isolation Forest
    iforest = IsolationForest(contamination=0.05, random_state=42)
    iforest.fit(X_train)
    
    # Evaluate false positive rate on normal test set
    val_preds = iforest.predict(X_val_normal)
    test_normal_preds = iforest.predict(X_test_normal)
    
    fp_rate_val = float(np.mean(val_preds == -1))
    fp_rate_test = float(np.mean(test_normal_preds == -1))
    
    # Statistical Threshold Baseline (z-score on feature 0 compressor power)
    mean_val = np.mean(X_train[:, 0])
    std_val = np.std(X_train[:, 0])
    if std_val == 0:
        std_val = 1.0
        
    def stat_predict(X):
        z = np.abs((X[:, 0] - mean_val) / std_val)
        return np.where(z > 2.5, -1, 1)
        
    stat_normal_preds = stat_predict(X_test_normal)
    stat_fp_rate = float(np.mean(stat_normal_preds == -1))
    
    # Fault files to evaluate
    fault_files = [
        ("condenser_fouling_10pct", "RTU_sim_condfouling10.csv"),
        ("condenser_fouling_30pct", "RTU_sim_condfouling30.csv"),
        ("condenser_fouling_50pct", "RTU_sim_condfouling50.csv"),
        ("undercharge_20pct", "RTU_sim_undercharge20.csv")
    ]
    
    fault_results = []
    fault_coverage_rows = []
    
    for fault_name, fname in fault_files:
        matches = glob.glob(os.path.join(LBNL_DIR, f"**/{fname}"), recursive=True)
        if not matches:
            continue
        X_fault = load_data(matches[0], max_rows=1500)
        if len(X_fault) == 0:
            continue
            
        # IF predictions on fault
        if_fault_preds = iforest.predict(X_fault)
        detection_rate_if = float(np.mean(if_fault_preds == -1))
        
        # Stat predictions on fault
        stat_fault_preds = stat_predict(X_fault)
        detection_rate_stat = float(np.mean(stat_fault_preds == -1))
        
        # Confusion matrix for IF (Normal test vs Fault)
        # TP = fault predicted as anomaly (-1)
        # FN = fault predicted as normal (1)
        # FP = normal test predicted as anomaly (-1)
        # TN = normal test predicted as normal (1)
        tp = int(np.sum(if_fault_preds == -1))
        fn = int(np.sum(if_fault_preds == 1))
        fp = int(np.sum(test_normal_preds == -1))
        tn = int(np.sum(test_normal_preds == 1))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        res = {
            "fault_scenario": fault_name,
            "filename": fname,
            "samples": len(X_fault),
            "isolation_forest": {
                "detection_rate": detection_rate_if,
                "tp": tp,
                "fn": fn,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            "statistical_baseline": {
                "detection_rate": detection_rate_stat
            },
            "baseline_false_positive_rate": fp_rate_test
        }
        fault_results.append(res)
        
        fault_coverage_rows.append({
            "Fault Type": fault_name,
            "Severity": fname.split("_")[-1].replace(".csv", ""),
            "Scenarios": 1,
            "Records": len(X_fault),
            "Evaluation Possible": "YES",
            "IF Detection Rate": f"{detection_rate_if*100:.2f}%",
            "Precision": f"{precision:.3f}",
            "Recall": f"{recall:.3f}",
            "F1-Score": f"{f1:.3f}"
        })
        
    # Save isolation forest results
    with open(os.path.join(OUT_DIR, "isolation_forest_results.json"), "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "baseline_fp_rate_val": fp_rate_val,
            "baseline_fp_rate_test": fp_rate_test,
            "statistical_fp_rate_test": stat_fp_rate,
            "fault_evaluations": fault_results
        }, f, indent=2)
        
    # Save fault coverage matrix CSV
    csv_path = os.path.join(OUT_DIR, "fault_coverage_matrix.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Fault Type", "Severity", "Scenarios", "Records", "Evaluation Possible", "IF Detection Rate", "Precision", "Recall", "F1-Score"])
        writer.writeheader()
        for row in fault_coverage_rows:
            writer.writerow(row)
            
    print("LBNL Advanced Evaluation complete.")

if __name__ == "__main__":
    evaluate_lbnl()
