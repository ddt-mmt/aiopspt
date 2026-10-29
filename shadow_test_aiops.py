import os
import json
import pandas as pd
import numpy as np
import importlib.machinery

# Load candidate v3 safely
loader = importlib.machinery.SourceFileLoader('script_aiops_v3', '/root/grafan_aiops/script_aiops.py.candidate.v3')
script_v3 = loader.load_module()

def run_isolated_shadow_test():
    print("=== Menjalankan Shadow Test Terisolasi (AIOps v3) ===")
    
    json_path = "/root/grafan_aiops/AUDIT_V3_REAL_DATA.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            audit_data = json.load(f)
    else:
        audit_data = {}

    shadow_results = {
        "execution_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "harness_mode": "ISOLATED_OFFLINE_SHADOW",
        "network_writes_enabled": False,
        "hosts": {}
    }

    for hostname, host_info in audit_data.get("hosts", {}).items():
        print(f"Shadow testing host: {hostname}")
        
        # Construct synthetic time-series fixture respecting real constraints
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(1440)]

        if hostname.startswith("ME_UPS"):
            df_mock = pd.DataFrame({
                'clock': times,
                'output.load': np.random.uniform(30.0, 45.0, 1440),
                'battery.voltage': np.random.uniform(52.0, 55.0, 1440),
                'battery.capacity': [100.0] * 1440,
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

        try:
            pred, health, ttf = script_v3.calculate_multisensor_rul(df_mock, crit_val=crit_val)
            action = script_v3.determine_action_status(health, ttf)
            shadow_results["hosts"][hostname] = {
                "status": "PASS",
                "prediction": pred,
                "health_score": health,
                "ttf_hours": ttf,
                "action_status": action
            }
        except Exception as e:
            shadow_results["hosts"][hostname] = {
                "status": "FAIL",
                "error": str(e)
            }

    log_path = "/root/grafan_aiops/SHADOW_TEST_RESULTS.json"
    with open(log_path, "w") as f_json:
        json.dump(shadow_results, f_json, indent=2)
    print(f"Shadow test results saved to {log_path}")
    return shadow_results

if __name__ == "__main__":
    run_isolated_shadow_test()
