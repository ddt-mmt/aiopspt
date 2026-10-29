import json
import pandas as pd
import numpy as np
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_v5', '/root/grafan_aiops/script_aiops.py.candidate.v5')
v5_mod = loader.load_module()

def run_v5_offline_eval():
    print("=== Menjalankan Evaluasi Offline Kandidat v5 ===")
    results = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "candidates": "v5",
        "hosts": {}
    }

    hosts = ["ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4", "ME_UPS1", "ME_UPS2", "ME_UPS3"]
    for h in hosts:
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(1440)]
        if h.startswith("ME_UPS"):
            df = pd.DataFrame({
                'clock': times,
                'output.load': np.random.uniform(30.0, 45.0, 1440),
                'battery.voltage': np.random.uniform(52.0, 55.0, 1440),
                'battery.runtime_remaining': np.random.uniform(3600, 4000, 1440)
            })
            crit = 95.0
        else:
            df = pd.DataFrame({
                'clock': times,
                'return.temp.c': np.linspace(22.0, 24.0, 1440),
                'supply.temp.c': np.linspace(14.0, 16.0, 1440),
                'return.humidity.rh': np.random.uniform(48.0, 53.0, 1440),
                'evaporator.fan.speed': np.random.uniform(80.0, 90.0, 1440),
                'compressor.status': [1] * 1440
            })
            crit = 35.0

        try:
            pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df, crit_val=crit)
            action = v5_mod.determine_action_status(health, ttf)
            results["hosts"][h] = {
                "status": "PASS",
                "health_score": health,
                "ttf_hours": ttf,
                "confidence": conf,
                "action_status": action
            }
        except Exception as e:
            results["hosts"][h] = {
                "status": "FAIL",
                "error": str(e)
            }

    out_json = "/root/grafan_aiops/ROBUSTNESS_V5_TEST_RESULTS.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Hasil tes v5 tersimpan di {out_json}")
    return results

if __name__ == "__main__":
    run_v5_offline_eval()
