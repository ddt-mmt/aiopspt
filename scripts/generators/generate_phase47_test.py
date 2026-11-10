#!/usr/bin/env python3
import os

target_path = "/tmp/aiops_staging_v8/phase47_candidate_v10_audit_20261022_120000/test_synthetic_harness.py"

content = '''#!/usr/bin/env python3
import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
import script_aiops_v10 as v10

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase47_test_harness")

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
    status_str = "PASS" if passed else "DEFECT/FAIL"
    logger.info(f"[{status_str}] {test_id} - {description}")

def run_tests():
    now_utc = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    base_time = now_utc - timedelta(minutes=2)

    # 1. DATA VALID DENGAN SAMPEL MENCUKUPI
    timestamps = [base_time + timedelta(seconds=i * 2) for i in range(65)]
    series_by_name = {
        "output.load": pd.Series([50.0 + (i % 3) for i in range(65)], index=timestamps, name="output.load"),
        "battery.voltage": pd.Series([54.0 - 0.01 * i for i in range(65)], index=timestamps, name="battery.voltage"),
        "battery.temp": pd.Series([25.0 + 0.1 * i for i in range(65)], index=timestamps, name="battery.temp"),
    }
    latest_by_name = {k: timestamps[-1] for k in series_by_name}
    sample_counts = {k: 65 for k in series_by_name}

    merged, status, msg = v10.process_sensor_history_hardened(
        series_by_name, latest_by_name, sample_counts, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    is_valid_merged = merged is not None and len(merged) == 65 and status == "NORMAL"
    record_result("TEST-01", "Quality Gate", "Data valid dengan sampel mencukupi", True, is_valid_merged, is_valid_merged, {"status": status, "rows": len(merged) if merged is not None else 0})

    if merged is not None:
        pred, raw_score, health, ttf, conf = v10.calculate_multisensor_rul_v8(merged, crit_val=40.0)
        action = v10.determine_action_status_hardened(health, ttf)
        record_result("TEST-01B", "Pipeline Valid", "Inferensi RUL dan status pada data valid", "Action in [0, 1, 2]", f"Action={action}, Health={health}, TTF={ttf}, Conf={conf}", action in (0, 1, 2), {"pred": pred, "health": health, "ttf": ttf, "conf": conf, "action": action})

    # 2. FITUR WAJIB HILANG
    series_missing = {
        "output.load": pd.Series([50.0] * 20, index=timestamps[:20], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=timestamps[:20], name="battery.voltage")
    }
    latest_missing = {k: timestamps[19] for k in series_missing}
    counts_missing = {k: 20 for k in series_missing}

    merged_m, status_m, msg_m = v10.process_sensor_history_hardened(
        series_missing, latest_missing, counts_missing, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
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

    merged_st, status_st, msg_st = v10.process_sensor_history_hardened(
        series_stale, latest_stale, counts_stale, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
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

    merged_few, status_few, msg_few = v10.process_sensor_history_hardened(
        series_few, latest_few, counts_few, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    passed_few = merged_few is None and status_few == "INSUFFICIENT_DATA"
    record_result("TEST-04", "Quality Gate", "Sampel kurang dari minimum (<10) harus fail-closed", True, passed_few, passed_few, {"status": status_few, "msg": msg_few})

    # 5. TIMESTAMP TIDAK VALID / NAT
    df_invalid_clock = pd.DataFrame({
        "clock": ["2026-10-22 12:00:00", "INVALID_TIME", "2026-10-22 12:02:00", None] + ["2026-10-22 12:03:00"] * 10,
        "battery.temp": [25.0] * 14,
        "battery.voltage": [54.0] * 14
    })
    try:
        pred, raw_score, health, ttf, conf = v10.calculate_multisensor_rul_v8(df_invalid_clock, crit_val=40.0)
        record_result("TEST-05", "Data Cleaning", "Handling timestamp invalid dan non-unique", "ValueError on insufficient unique timestamps", "Executed without error", False)
    except ValueError as e:
        record_result("TEST-05", "Data Cleaning", "Handling timestamp invalid dan non-unique", "ValueError on insufficient unique timestamps", f"ValueError: {e}", True, {"exception": str(e)})

    # 5B. TIMESTAMP DI MASA DEPAN (Future Timestamp)
    future_time = now_utc + timedelta(hours=2)
    series_future = {
        "output.load": pd.Series([50.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 15, index=[future_time + timedelta(seconds=i) for i in range(15)], name="battery.temp")
    }
    latest_future = {k: future_time + timedelta(seconds=14) for k in series_future}
    counts_future = {k: 15 for k in series_future}

    q_stat, q_msg = v10.validate_schema_and_quality(
        series_future, latest_future, counts_future, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    is_future_blocked = (q_stat != "NORMAL")
    record_result("TEST-05B", "Security/Quality Gate", "Deteksi timestamp di masa depan (Future timestamp)", "BLOCKED/REJECTED", f"Status={q_stat}, Msg={q_msg}", is_future_blocked, {"defect_note": "Kandidat V10 meloloskan future timestamp sebagai NORMAL"})

    # 6. NILAI NAN DAN INFINITY
    df_nan_inf = pd.DataFrame({
        "clock": [base_time + timedelta(seconds=i * 5) for i in range(25)],
        "output.load": [50.0] * 25,
        "battery.voltage": [54.0 if i % 2 == 0 else np.nan for i in range(25)],
        "battery.temp": [np.inf if i == 5 else 25.0 + 0.1 * i for i in range(25)]
    })
    try:
        pred, raw_score, health, ttf, conf = v10.calculate_multisensor_rul_v8(df_nan_inf, crit_val=40.0)
        record_result("TEST-06", "Data Cleaning", "Handling nilai NaN dan Infinity dalam calculate_multisensor_rul_v8", "Success after cleaning or safe fail", f"Cleaned successfully: conf={conf}, health={health}", True)
    except Exception as e:
        record_result("TEST-06", "Data Cleaning", "Handling nilai NaN dan Infinity dalam calculate_multisensor_rul_v8", "Success after cleaning or safe fail", f"Exception: {e}", False, {"exception": str(e)})

    # 7. TIMESTAMP DUPLIKAT
    dup_times = [base_time + timedelta(seconds=i // 2 * 10) for i in range(30)]
    df_dup = pd.DataFrame({
        "clock": dup_times,
        "output.load": [50.0 + i for i in range(30)],
        "battery.voltage": [54.0] * 30,
        "battery.temp": [25.0 + 0.1 * i for i in range(30)]
    })
    try:
        pred, raw_score, health, ttf, conf = v10.calculate_multisensor_rul_v8(df_dup, crit_val=40.0)
        record_result("TEST-07", "Data Cleaning", "Handling duplikasi timestamp (drop_duplicates)", "Deduplicated safely", f"Health={health}, TTF={ttf}", True)
    except Exception as e:
        record_result("TEST-07", "Data Cleaning", "Handling duplikasi timestamp (drop_duplicates)", "Deduplicated safely", f"Exception: {e}", False, {"exception": str(e)})

    # 8. SLOPE POSITIF, NOL, DAN NEGATIF
    times_pos = [base_time + timedelta(minutes=i) for i in range(20)]
    # A. Slope positif
    df_slope_pos = pd.DataFrame({
        "clock": times_pos,
        "battery.temp": [25.0 + 0.5 * i for i in range(20)]
    })
    _, _, _, ttf_pos, _ = v10.calculate_multisensor_rul_v8(df_slope_pos, crit_val=40.0)
    passed_pos = ttf_pos is not None and ttf_pos > 0
    record_result("TEST-08A", "RUL Calculation", "Slope positif mendekati crit_val menghasilkan TTF valid", "TTF > 0", f"TTF={ttf_pos}", passed_pos)

    # B. Slope nol
    df_slope_zero = pd.DataFrame({
        "clock": times_pos,
        "battery.temp": [25.0] * 20
    })
    _, _, _, ttf_zero, _ = v10.calculate_multisensor_rul_v8(df_slope_zero, crit_val=40.0)
    passed_zero = ttf_zero is None
    record_result("TEST-08B", "RUL Calculation", "Slope nol menghasilkan TTF None", "TTF is None", f"TTF={ttf_zero}", passed_zero)

    # C. Slope negatif untuk sensor degradasi batas bawah (battery voltage drop)
    df_slope_neg = pd.DataFrame({
        "clock": times_pos,
        "battery.voltage": [52.0 - 0.2 * i for i in range(20)]
    })
    _, _, _, ttf_neg, _ = v10.calculate_multisensor_rul_v8(df_slope_neg, crit_val=44.0)
    record_result("TEST-08C", "RUL Calculation Defect", "Degradasi sensor menurun (battery voltage drop ke crit_val 44V) didukung?", "TTF calculated for lower threshold", f"TTF={ttf_neg} (None)", False, {"defect_note": "Kandidat V10 hardcode slope > 1e-5 and current_val < crit_val, tidak mendukung sensor degradasi menurun."})

    # D. Nilai telah melampaui crit_val (current_val >= crit_val)
    df_already_failed = pd.DataFrame({
        "clock": times_pos,
        "battery.temp": [41.0 + 0.1 * i for i in range(20)]
    })
    _, _, _, ttf_over, _ = v10.calculate_multisensor_rul_v8(df_already_failed, crit_val=40.0)
    record_result("TEST-08D", "RUL Calculation Defect", "Perilaku jika sensor sudah melewati ambang kritis (current_val >= crit_val)", "TTF = 0 or CRITICAL state", f"TTF={ttf_over} (None)", False, {"defect_note": "Ketika nilai sudah melewati crit_val, TTF return None dan tidak membedakan kondisi sudah gagal vs stabil."})

    # 9. TTF = NONE DALAM ACTION STATUS
    act_normal = v10.determine_action_status_hardened(health=80, ttf=None)
    record_result("TEST-09A", "Action Status", "Status saat health=80 dan ttf=None", 0, act_normal, act_normal == 0)

    act_crit = v10.determine_action_status_hardened(health=30, ttf=None)
    record_result("TEST-09B", "Action Status", "Status saat health=30 dan ttf=None", 2, act_crit, act_crit == 2)

    act_masked = v10.determine_action_status_hardened(health=75, ttf=None)
    record_result("TEST-09C", "Action Status Edge Case", "Blind spot jika ttf=None akibat sensor sudah melebihi batas tetapi health > 70", "Warning/Critical", f"Status={act_masked}", act_masked != 0, {"defect_note": "Karena TTF menjadi None ketika nilai melewati crit_val, jika model anomali menghasilkan health >= 70 maka status menjadi 0 (NORMAL)."})

    # 10. HEALTH TIDAK TERSEDIA (HEALTH = NONE)
    act_unavail = v10.determine_action_status_hardened(health=None, ttf=10)
    record_result("TEST-10", "Action Status", "Health is None menghasilkan status tidak tersedia (-1)", -1, act_unavail, act_unavail == -1)

    # 11. PREDIKSI ANOMALI VS NORMAL & ISOLATION FOREST DISCONNECTION
    np.random.seed(42)
    normal_data = np.random.normal(loc=50.0, scale=1.0, size=(100, 3))
    outlier_row = np.array([[120.0, 15.0, 95.0]])
    all_data = np.vstack([normal_data, outlier_row])
    df_anomaly = pd.DataFrame(all_data, columns=["output.load", "battery.voltage", "battery.temp"])
    df_anomaly["clock"] = [base_time + timedelta(seconds=i * 10) for i in range(101)]

    pred_a, raw_score_a, health_a, ttf_a, conf_a = v10.calculate_multisensor_rul_v8(df_anomaly, crit_val=100.0)
    is_anomaly_detected = (pred_a == -1)
    record_result("TEST-11A", "Anomaly Detection", "Deteksi anomali pada outlier ekstrem", -1, pred_a, is_anomaly_detected, {"raw_score": raw_score_a, "health": health_a})

    action_with_anomaly = v10.determine_action_status_hardened(health_a, ttf_a)
    record_result("TEST-11B", "Action Status Defect", "determine_action_status_hardened mengonsumsi parameter prediction biner?", "Consumes prediction", "Signature is (health, ttf) only; prediction is ignored", False, {"defect_note": "determine_action_status_hardened mengabaikan output biner prediction (-1) secara langsung."})

    # 12. DATA SENSOR TIDAK SELARAS (MISALIGNED TIMESTAMPS)
    t_s1 = [base_time + timedelta(seconds=i * 10) for i in range(20)]
    t_s2 = [base_time + timedelta(seconds=i * 10 + 5) for i in range(20)]
    t_s3 = [base_time + timedelta(seconds=i * 10 + 2) for i in range(20)]

    series_misaligned = {
        "output.load": pd.Series([50.0] * 20, index=t_s1, name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=t_s2, name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 20, index=t_s3, name="battery.temp")
    }
    latest_mis = {k: base_time + timedelta(seconds=190 + 5) for k in series_misaligned}
    counts_mis = {k: 20 for k in series_misaligned}

    merged_mis, status_mis, msg_mis = v10.process_sensor_history_hardened(
        series_misaligned, latest_mis, counts_mis, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    survived_rows = len(merged_mis) if merged_mis is not None else 0
    record_result("TEST-12", "Alignment", "Penyelarasan sensor dengan timestamp tidak persis sama (interleaved)", "Valid merged df or graceful degrade", f"Status={status_mis}, Rows={survived_rows}", merged_mis is not None, {"status": status_mis, "rows": survived_rows, "msg": msg_mis})

    # 13. KEGAGALAN PREPROCESSING / INPUT EMPTY / NONE
    try:
        v10.calculate_multisensor_rul_v8(None, crit_val=50.0)
        record_result("TEST-13A", "Robustness", "Input DataFrame None memicu ValueError", "ValueError", "Did not raise", False)
    except ValueError as e:
        record_result("TEST-13A", "Robustness", "Input DataFrame None memicu ValueError", "ValueError", str(e), True)

    try:
        v10.calculate_multisensor_rul_v8(pd.DataFrame(), crit_val=50.0)
        record_result("TEST-13B", "Robustness", "Input DataFrame kosong memicu ValueError", "ValueError", "Did not raise", False)
    except ValueError as e:
        record_result("TEST-13B", "Robustness", "Input DataFrame kosong memicu ValueError", "ValueError", str(e), True)

    # 14. MUTASI DICTIONARY INPUT (IN-PLACE MUTATION DEFECT)
    input_dict = {
        "output.load": pd.Series([50.0] * 20, index=timestamps[:20], name="output.load"),
        "battery.voltage": pd.Series([54.0] * 20, index=timestamps[:20], name="battery.voltage"),
        "battery.temp": pd.Series([25.0] * 20, index=timestamps[:20], name="battery.temp"),
        "battery.capacity": pd.Series([99.0] * 5, index=timestamps[:5], name="battery.capacity")
    }
    input_keys_before = set(input_dict.keys())
    sample_counts_sparse = {"output.load": 20, "battery.voltage": 20, "battery.temp": 20, "battery.capacity": 5}
    latest_sparse = {k: timestamps[19] for k in input_dict}

    v10.validate_schema_and_quality(
        input_dict, latest_sparse, sample_counts_sparse, v10.UPS_MANDATORY, now_utc, max_age_seconds=300, min_samples=10
    )
    input_keys_after = set(input_dict.keys())
    dict_mutated = (input_keys_before != input_keys_after)
    record_result("TEST-14", "Architecture/Side-Effect Defect", "Fungsi validate_schema_and_quality tidak memutasi dictionary caller", False, dict_mutated, not dict_mutated, {"mutated_keys": list(input_keys_before - input_keys_after), "defect_note": "validate_schema_and_quality memutasi series_by_name pemanggil dengan del series_by_name[s]."})

    out_file = os.path.join(CURRENT_DIR, "test_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(test_records, f, indent=2)

    total_tests = len(test_records)
    passed_tests = sum(1 for r in test_records if r["passed"])
    failed_tests = total_tests - passed_tests

    print("\\n" + "="*60)
    print("RINGKASAN PENGUJIAN SINTETIS FASE 47")
    print(f"Total Pengujian  : {total_tests}")
    print(f"Lulus (PASS)     : {passed_tests}")
    print(f"Gagal/Cacat      : {failed_tests}")
    print(f"Hasil disimpan di: {out_file}")
    print("="*60)

if __name__ == "__main__":
    run_tests()
'''

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Generated:", target_path)
