import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone

STAGING_DIR = "/root/grafan_aiops/shadow_v5"
DATA_DIR = os.path.join(STAGING_DIR, "telemetry_store")

def run_evaluation_pipeline():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Memulai Continuous Evaluation Pipeline...")
    
    # 1. Periksa ketersediaan dataset telemetri tersimpan
    if not os.path.exists(DATA_DIR):
        print("Dataset store belum tersedia. Jalankan collector terlebih dahulu.")
        return {"status": "NO_DATA", "candidates_evaluated": 0}

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith("_telemetry.csv")]
    if not csv_files:
        print("Tidak ada file CSV telemetri ditemukan di store.")
        return {"status": "NO_CSV", "candidates_evaluated": 0}

    evaluation_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "datasets_analyzed": len(csv_files),
        "hosts": [],
        "pipeline_status": "SUCCESS"
    }

    for cf in csv_files:
        path = os.path.join(DATA_DIR, cf)
        try:
            df = pd.read_csv(path)
            host_name = cf.replace("_telemetry.csv", "")
            record_count = len(df)
            missing_vals = int(df.isnull().sum().sum())
            
            evaluation_report["hosts"].append({
                "host": host_name,
                "records": record_count,
                "missing_values": missing_vals,
                "data_quality_score": 100.0 if missing_vals == 0 else max(0.0, 100.0 - (missing_vals / record_count * 100))
            })
        except Exception as e:
            print(f"Gagal memproses {cf}: {e}")

    report_path = os.path.join(STAGING_DIR, "CONTINUOUS_EVALUATION_REPORT.json")
    with open(report_path, "w") as f:
        json.dump(evaluation_report, f, indent=2)
    print(f"Continuous Evaluation Report tersimpan di {report_path}")
    return evaluation_report

if __name__ == "__main__":
    run_evaluation_pipeline()
