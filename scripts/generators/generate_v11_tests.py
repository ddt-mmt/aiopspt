#!/usr/bin/env python3
import os

test_path = "/tmp/aiops_staging_v8/shadow_v11/test_regression_v11.py"

code = '''#!/usr/bin/env python3
import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
import script_aiops_v11 as v11

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase48_regression_harness")

test_records = []

def record_result(test_id, category, description, expected, actual, passed, details=None):
    record = {
        "test_id": test_id,
        "category": category,
        "description": description,
        "expected": str(expected),
        "actual": str(actual),
        "passed": bool(passed),
        "details": details or {}
    }
    test_records.append(record)
    status_str = "PASS" if passed else "FAIL"
    logger.info(f"[{status_str}] {test_id} - {description}")

def run_tests():
    now_utc = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    base_time = now_utc - timedelta(minutes=5)

    # 1. DATA VALID DENGAN SAMPEL MENCUKUPI
    timestamps = [base_time + timedelta(seconds=i * 2) for i in range(65)]
    series_by_name = {
        "output.load": pd.Series([50.0 + (i % 3) for i in range(65)], index=timestamps, name="output.load"),
        "battery.voltage": pd.Series([54.0 - 0.01 * i for i in range(65)], index=timestamps, name="battery.voltage"),
        "battery.temp": pd.Series([25.0 + 0.1 * i for i in range(65)], index=timestamps, name="battery.temp"),
    }
    latest_by_name = {k: timestamps[-1] for k in series_by_name}
    sample_counts = {k: 65 for k in series_by_name}

    merged, status, msg = v11.process_sensor_history_hardened(
        series_by_name, latest_by_name, sample_counts, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    is_valid_merged = merged is not None and len(merged) == 65 and status == "NORMAL"
    record_result("TEST-01", "Quality Gate", "Data valid dengan sampel mencukupi", True, is_valid_merged, is_valid_merged, {"status": status, "rows": len(merged) if merged is not None else 0})

    if merged is not None:
        pred, raw_score, health, ttf, conf, exc = v11.calculate_multisensor_rul_v11(merged)
        action = v11.determine_action_status_hardened_v11(health, ttf, pred, exc)
        record_result("TEST-01B", "Pipeline Valid", "Inferensi RUL dan status pada data valid V11", "Action in [0, 1, 2]", f"Action={action}, Health={health}, TTF={ttf}, Conf={conf}, Exc={exc}", action in (0, 1, 2), {"pred": pred, "health": health, "ttf": ttf, "conf": conf, "action": action, "exc": exc})

    # 2. FITUR WAJIB HILANG
    series_missing = {
        "output.load": pd.Series([50.0] * 20, index=timestamps[:20], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=timestamps[:20], name="battery.voltage")
    }
    latest_missing = {k: timestamps[19] for k in series_missing}
    counts_missing = {k: 20 for k in series_missing}

    merged_m, status_m, msg_m = v11.process_sensor_history_hardened(
        series_missing, latest_missing, counts_missing, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    passed_m = merged_m is None and status_m == "INSUFFICIENT_DATA"
    record_result("TEST-02", "Quality Gate", "Fitur wajib hilang harus fail-closed (INSUFFICIENT_DATA)", True, passed_m, passed_m, {"status": status_m, "msg": msg_m})

    # 3. DATA STALE (>300s)
    stale_time = now_utc - timedelta(seconds=600)
    timestamps_stale = [stale_time + timedelta(seconds=i) for i in range(20)]
    series_stale = {
        "output.load": pd.Series([50.0] * 20, index=timestamps_stale, name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=timestamps_stale, name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 20, index=timestamps_stale, name="battery.temp")
    }
    latest_stale = {k: timestamps_stale[-1] for k in series_stale}
    counts_stale = {k: 20 for k in series_stale}

    merged_st, status_st, msg_st = v11.process_sensor_history_hardened(
        series_stale, latest_stale, counts_stale, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    passed_st = merged_st is None and status_st == "STALE_DATA"
    record_result("TEST-03", "Quality Gate", "Data stale (>300s) harus fail-closed (STALE_DATA)", True, passed_st, passed_st, {"status": status_st, "msg": msg_st})

    # 4. SAMPEL KURANG DARI MINIMUM (<10)
    timestamps_few = [base_time + timedelta(seconds=i) for i in range(5)]
    series_few = {
        "output.load": pd.Series([50.0] * 5, index=timestamps_few, name="output.load"),
        "battery.voltage": pd.Series([54.0] * 5, index=timestamps_few, name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 5, index=timestamps_few, name="battery.temp")
    }
    latest_few = {k: timestamps_few[-1] for k in series_few}
    counts_few = {k: 5 for k in series_few}

    merged_few, status_few, msg_few = v11.process_sensor_history_hardened(
        series_few, latest_few, counts_few, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    passed_few = merged_few is None and status_few == "INSUFFICIENT_DATA"
    record_result("TEST-04", "Quality Gate", "Sampel kurang dari minimum (<10) harus fail-closed", True, passed_few, passed_few, {"status": status_few, "msg": status_few})

    # 5. TIMESTAMP TIDAK VALID / NAT
    df_invalid_clock = pd.DataFrame({
        "clock": ["2026-10-22 12:00:00", "INVALID_TIME", "2026-10-22 12:02:00", None] + ["2026-10-22 12:03:00"] * 10,
        "battery.temp": [25.0] * 14,
        "battery.voltage": [54.0] * 14,
        "output.load": [50.0] * 14
    })
    try:
        pred, raw_score, health, ttf, conf, exc = v11.calculate_multisensor_rul_v11(df_invalid_clock)
        record_result("TEST-05", "Data Cleaning", "Handling timestamp invalid dan non-unique", "ValueError on insufficient unique timestamps", "Executed without error", False)
    except ValueError as e:
        record_result("TEST-05", "Data Cleaning", "Handling timestamp invalid dan non-unique", "ValueError on insufficient unique timestamps", f"ValueError: {e}", True, {"exception": str(e)})

    # 5B. TIMESTAMP DI MASA DEPAN (Future Timestamp Remediasi V11)
    future_time = now_utc + timedelta(hours=2)
    series_future = {
        "output.load": pd.Series([50.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="battery.temp")
    }
    latest_future = {k: future_time + timedelta(seconds=14) for k in series_future}
    counts_future = {k: 15 for k in series_future}

    q_stat, q_msg = v11.validate_schema_and_quality(
        series_future, latest_future, counts_future, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    is_future_blocked = (q_stat == "FUTURE_DATA")
    record_result("TEST-05B", "Remediation Gate", "Deteksi timestamp di masa depan menghasilkan FUTURE_DATA", "FUTURE_DATA", f"Status={q_stat}, Msg={q_msg}", is_future_blocked, {"status": q_stat, "msg": q_msg})

    # 6. NILAI NAN DAN INFINITY
    df_nan_inf = pd.DataFrame({
        "clock": [base_time + timedelta(seconds=i * 5) for i in range(25)],
        "output.load": [50.0] * 25,
        "battery.voltage": [54.0 if i % 2 == 0 else np.nan for i in range(25)],
        "battery.temp": [np.inf if i == 5 else 25.0 + 0.1 * i for i in range(25)]
    })
    try:
        pred, raw_score, health, ttf, conf, exc = v11.calculate_multisensor_rul_v11(df_nan_inf)
        record_result("TEST-06", "Data Cleaning", "Handling nilai NaN dan Infinity dalam calculate_multisensor_rul_v11", "Success after cleaning", f"Cleaned successfully: conf={conf}, health={health}", True)
    except Exception as e:
        record_result("TEST-06", "Data Cleaning", "Handling nilai NaN dan Infinity dalam calculate_multisensor_rul_v11", "Success after cleaning", f"Exception: {e}", False)

    # 7. TIMESTAMP DUPLIKAT
    dup_times = [base_time + timedelta(seconds=i // 2 * 10) for i in range(30)]
    df_dup = pd.DataFrame({
        "clock": dup_times,
        "output.load": [50.0 + i for i in range(30)],
        "battery.voltage": [54.0] * 30,
        "battery.temp": [25.0 + 0.1 * i for i in range(30)]
    })
    try:
        pred, raw_score, health, ttf, conf, exc = v11.calculate_multisensor_rul_v11(df_dup)
        record_result("TEST-07", "Data Cleaning", "Handling duplikasi timestamp (drop_duplicates)", "Deduplicated safely", f"Health={health}, TTF={ttf}", True)
    except Exception as e:
        record_result("TEST-07", "Data Cleaning", "Handling duplikasi timestamp (drop_duplicates)", "Deduplicated safely", f"Exception: {e}", False)

    # 8. SLOPE POSITIF, NEGATIF, DAN AMBANG KRITIS
    times_pos = [base_time + timedelta(minutes=i) for i in range(20)]
    
    # A. Slope positif (battery.temp -> crit_high=40)
    df_slope_pos = pd.DataFrame({
        "clock": times_pos,
        "battery.temp": [25.0 + 0.5 * i for i in range(20)]
    })
    _, _, _, ttf_pos, _, exc_pos = v11.calculate_multisensor_rul_v11(df_slope_pos)
    passed_pos = ttf_pos is not None and ttf_pos > 0
    record_result("TEST-08A", "RUL Remediation", "Slope positif battery.temp menghasilkan TTF valid", "TTF > 0", f"TTF={ttf_pos}", passed_pos)

    # B. Slope negatif untuk sensor degradasi batas bawah (battery.voltage -> crit_low=44) [Remediasi Defect 2]
    df_slope_neg = pd.DataFrame({
        "clock": times_pos,
        "battery.voltage": [52.0 - 0.2 * i for i in range(20)]
    })
    _, _, _, ttf_neg, _, exc_neg = v11.calculate_multisensor_rul_v11(df_slope_neg)
    passed_neg = ttf_neg is not None and ttf_neg > 0
    record_result("TEST-08C", "RUL Remediation", "Degradasi sensor menurun (battery voltage drop ke crit_low 44V) didukung dengan TTF valid", "TTF > 0", f"TTF={ttf_neg}", passed_neg)

    # C. Nilai telah melampaui crit_high [Remediasi Defect 3]
    df_already_failed = pd.DataFrame({
        "clock": times_pos,
        "battery.temp": [41.0 + 0.1 * i for i in range(20)]
    })
    _, _, _, ttf_over, _, exc_over = v11.calculate_multisensor_rul_v11(df_already_failed)
    passed_over = exc_over == True and ttf_over == 0.0
    record_result("TEST-08D", "RUL Remediation", "Sensor melampaui crit_high menghasilkan exceeded_critical=True dan TTF=0.0", "exceeded_critical=True, TTF=0.0", f"Exc={exc_over}, TTF={ttf_over}", passed_over)

    # 9. ACTION STATUS DENGAN EXCEEDED CRITICAL DAN TTF=NONE [Remediasi Defect 4]
    act_crit_exc = v11.determine_action_status_hardened_v11(health=75, ttf=None, prediction=1, exceeded_critical=True)
    record_result("TEST-09C", "Action Status Remediation", "Status kritis saat exceeded_critical=True meskipun health=75 dan ttf=None", 2, act_crit_exc, act_crit_exc == 2)

    # 10. HEALTH = NONE
    act_unavail = v11.determine_action_status_hardened_v11(health=None, ttf=10, prediction=1, exceeded_critical=False)
    record_result("TEST-10", "Action Status", "Health is None menghasilkan status tidak tersedia (-1)", -1, act_unavail, act_unavail == -1)

    # 11. ISOLATION FOREST ANOMALY PREDICTION INTEGRATION [Remediasi Defect 5]
    act_anomaly = v11.determine_action_status_hardened_v11(health=80, ttf=None, prediction=-1, exceeded_critical=False)
    record_result("TEST-11B", "Action Status Remediation", "Prediction -1 (anomali) memicu status WARNING (1) meskipun health=80", 1, act_anomaly, act_anomaly == 1)

    # 12. ALIGNMENT (pastikan latest timestamps valid masa lalu)
    t_s1 = [base_time + timedelta(seconds=i * 10) for i in range(20)]
    t_s2 = [base_time + timedelta(seconds=i * 10 + 2) for i in range(20)]
    t_s3 = [base_time + timedelta(seconds=i * 10 + 4) for i in range(20)]

    series_misaligned = {
        "output.load": pd.Series([50.0] * 20, index=t_s1, name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=t_s2, name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 20, index=t_s3, name="battery.temp")
    }
    latest_mis = {k: t_s1[-1] for k in series_misaligned}
    counts_mis = {k: 20 for k in series_misaligned}

    merged_mis, status_mis, msg_mis = v11.process_sensor_history_hardened(
        series_misaligned, latest_mis, counts_mis, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    record_result("TEST-12", "Alignment", "Penyelarasan sensor interleaved V11 dengan timestamp valid", "Valid merged df", f"Status={status_mis}, Rows={len(merged_mis) if merged_mis is not None else 0}", merged_mis is not None)

    # 13. IMMUTABILITY DICTIONARY INPUT [Remediasi Defect 6]
    input_dict = {
        "output.load": pd.Series([50.0] * 20, index=timestamps[:20], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=timestamps[:20], name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 20, index=timestamps[:20], name="battery.temp"),
        "battery.capacity": pd.Series([99.0] * 5, index=timestamps[:5], name="battery.capacity")
    }
    input_keys_before = set(input_dict.keys())
    sample_counts_sparse = {"output.load": 20, "battery.voltage": 20, "battery.temp": 20, "battery.capacity": 5}
    latest_sparse = {k: timestamps[19] for k in input_dict}

    v11.validate_schema_and_quality(
        input_dict, latest_sparse, sample_counts_sparse, v11.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    input_keys_after = set(input_dict.keys())
    dict_not_mutated = (input_keys_before == input_keys_after)
    record_result("TEST-14", "Immutability Remediation", "Fungsi validate_schema_and_quality tidak memutasi dictionary caller", True, dict_not_mutated, dict_not_mutated, {"keys_after": list(input_keys_after)})

    out_file = os.path.join(CURRENT_DIR, "test_results_v11.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(test_records, f, indent=2)

    total_tests = len(test_records)
    passed_tests = sum(1 for r in test_records if r["passed"])
    failed_tests = total_tests - passed_tests

    print("\\n" + "="*60)
    print("RINGKASAN PENGUJIAN REGRESI V11 (FASE 48)")
    print(f"Total Pengujian  : {total_tests}")
    print(f"Lulus (PASS)     : {passed_tests}")
    print(f"Gagal/Cacat      : {failed_tests}")
    print(f"Hasil disimpan di: {out_file}")
    print("="*60)

if __name__ == "__main__":
    run_tests()
'''

with open(test_path, "w", encoding="utf-8") as f:
    f.write(code)
print("Generated regression test harness:", test_path)
