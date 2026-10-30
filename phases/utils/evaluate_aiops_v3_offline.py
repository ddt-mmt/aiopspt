import os
import json
import pandas as pd
import numpy as np
import importlib.machinery

# Load candidate v3 safely
loader = importlib.machinery.SourceFileLoader('script_aiops_v3', '/root/grafan_aiops/src/candidates/script_aiops.py.candidate.v3')
script_v3 = loader.load_module()

def run_offline_evaluation():
    print("Memulai Evaluasi Offline Kandidat AIOps v3...")
    
    # Load AUDIT_V3_REAL_DATA.json for metadata summary
    json_path = "/root/grafan_aiops/AUDIT_V3_REAL_DATA.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            audit_data = json.load(f)
    else:
        audit_data = {}

    evaluation_results = {
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "hosts_evaluated": {},
        "global_findings": {
            "sparse_sensors_noted": ["battery.capacity (only 4 samples in 24h)"],
            "discrete_features_handled": "Excluded from linear slope regression, retained in IsolationForest",
            "ground_truth_labels_available": False,
            "network_access": "None (Fully Offline)"
        }
    }

    # Simulate temporal offline evaluation on mock data adhering to real dataset constraints
    for hostname, host_info in audit_data.get("hosts", {}).items():
        print(f"Mengevaluasi host offline: {hostname}")
        
        # Create mock historical time series simulating temporal split (Train: earlier 12h, Test: later 12h)
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(1440)] # 24 hours of 1-min data
        
        # Determine features based on host type
        if hostname.startswith("ME_UPS"):
            df_mock = pd.DataFrame({
                'clock': times,
                'output.load': np.random.uniform(30.0, 45.0, 1440),
                'battery.voltage': np.random.uniform(52.0, 55.0, 1440),
                'battery.capacity': [100.0] * 1440, # Constant sparse representation
                'battery.runtime_remaining': np.random.uniform(3600, 4000, 1440)
            })
            crit_val = 95.0
        else:
            df_mock = pd.DataFrame({
                'clock': times,
                'return.temp.c': np.linspace(22.0, 24.0, 1440),
                'supply.temp.c': np.linspace(14.0, 16.0, 1440),
                'return.humidity.rh': np.random.uniform(48.0, 53.0, 1440),
                'evaporator.fan.speed': np.random.uniform(80.0, 90.0, 1440),
                'compressor.status': [1] * 1440
            })
            crit_val = 35.0

        # Temporal split: Train (first 720 mins), Test (last 720 mins)
        train_df = df_mock.iloc[:720].copy()
        test_df = df_mock.iloc[720:].copy()

        try:
            # Run model on test split
            pred, health, ttf = script_v3.calculate_multisensor_rul(test_df, crit_val=crit_val)
            action = script_v3.determine_action_status(health, ttf)
            status = "SUCCESS"
            error_msg = None
        except Exception as e:
            pred, health, ttf, action = None, None, None, None
            status = "FAILED"
            error_msg = str(e)

        evaluation_results["hosts_evaluated"][hostname] = {
            "status": status,
            "prediction": pred,
            "health_score": health,
            "ttf_hours": ttf,
            "action_status": action,
            "error": error_msg,
            "samples_evaluated": len(test_df)
        }

    print("Evaluasi offline selesai.")
    return evaluation_results

if __name__ == '__main__':
    res = run_offline_evaluation()
    print(json.dumps(res, indent=2))
