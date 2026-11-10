#!/usr/bin/env python3
target_path = "/tmp/aiops_staging_v8/shadow_v11/script_aiops.py.candidate.v11"
code = '''#!/usr/bin/env python3
import os
import time
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aiops_hardened_v11")

UPS_MANDATORY = [
    'output.load',
    'battery.voltage',
    'battery.temp'
]
UPS_OPTIONAL = [
    'battery.capacity',
    'battery.runtime_remaining',
    'ups.status'
]

PAC_MANDATORY = [
    'return.temp.c',
    'supply.temp.c',
    'return.humidity.rh'
]
PAC_OPTIONAL = [
    'evaporator.fan.speed',
    'compressor.status'
]

SENSOR_CONFIG = {
    'battery.temp': {'direction': 'up', 'crit_high': 40.0, 'crit_low': None},
    'battery.voltage': {'direction': 'down', 'crit_high': None, 'crit_low': 44.0},
    'output.load': {'direction': 'up', 'crit_high': 95.0, 'crit_low': None},
    'return.temp.c': {'direction': 'up', 'crit_high': 35.0, 'crit_low': None},
    'supply.temp.c': {'direction': 'up', 'crit_high': 26.0, 'crit_low': None},
    'return.humidity.rh': {'direction': 'up', 'crit_high': 80.0, 'crit_low': 20.0}
}

def validate_schema_and_quality(series_by_name, latest_by_name, sample_counts, mandatory_features, now_utc, max_age_seconds=300, min_samples=10, future_tolerance_seconds=10):
    if series_by_name is not None:
        series_by_name = dict(series_by_name)
    else:
        return "INSUFFICIENT_DATA", "series_by_name is None"

    missing_mandatory = [f for f in mandatory_features if f not in series_by_name]
    if missing_mandatory:
        return "INSUFFICIENT_DATA", f"Fitur wajib hilang: {missing_mandatory}"

    stale = {}
    future_stamps = {}
    
    for name, stamp in latest_by_name.items():
        if stamp is None or pd.isna(stamp):
            return "INSUFFICIENT_DATA", f"Timestamp NaT/None untuk sensor {name}"
        
        if stamp.tzinfo is None and now_utc.tzinfo is not None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        elif stamp.tzinfo is not None and now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        diff_seconds = (now_utc - stamp).total_seconds()
        
        if diff_seconds < -future_tolerance_seconds:
            future_stamps[name] = int(-diff_seconds)
        elif diff_seconds > max_age_seconds:
            stale[name] = int(diff_seconds)

    if future_stamps:
        return "FUTURE_DATA", f"Timestamp di masa depan terdeteksi (hard gate aktif): {future_stamps}"

    if stale:
        return "STALE_DATA", f"Sensor stale terdeteksi (hard gate aktif): {stale}"

    sparse_sensors = [name for name, count in sample_counts.items() if count < min_samples]
    for s in sparse_sensors:
        if s in mandatory_features:
            return "INSUFFICIENT_DATA", f"Fitur wajib terlalu sparse: {s}"
        elif s in series_by_name:
            logger.info(f"Dropping sparse optional sensor from local copy: {s}")
            del series_by_name[s]

    if not series_by_name:
        return "INSUFFICIENT_DATA", "Tidak ada sensor tersisa yang memenuhi syarat"

    return "NORMAL", "Quality gate passed"

def process_sensor_history_hardened(series_by_name, latest_by_name, sample_counts, mandatory_features, now_utc, max_age_seconds=300, min_samples=10):
    if series_by_name is not None:
        working_series = dict(series_by_name)
    else:
        return None, "INSUFFICIENT_DATA", "series_by_name is None"

    q_status, q_msg = validate_schema_and_quality(
        working_series, latest_by_name, sample_counts, mandatory_features, now_utc, max_age_seconds, min_samples
    )
    if q_status in ("INSUFFICIENT_DATA", "STALE_DATA", "FUTURE_DATA"):
        return None, q_status, q_msg

    sparse_sensors = [name for name, count in sample_counts.items() if count < min_samples]
    for s in sparse_sensors:
        if s not in mandatory_features and s in working_series:
            del working_series[s]

    merged = pd.concat(working_series.values(), axis=1).sort_index()
    
    null_counts_before = merged.isnull().sum().to_dict()
    merged = merged.ffill(limit=2)
    null_counts_after = merged.isnull().sum().to_dict()
    
    imputed_counts = {k: null_counts_before[k] - null_counts_after[k] for k in null_counts_before}
    if sum(imputed_counts.values()) > 0:
        logger.info(f"Forward-fill audit log (limit=2 applied): {imputed_counts}")

    merged = merged.dropna()
    if len(merged) < min_samples:
        return None, "INSUFFICIENT_DATA", f"Sampel selaras tidak cukup setelah alignment: {len(merged)}; minimal {min_samples}"

    if sum(imputed_counts.values()) > 0:
        final_status = "DEGRADED_DATA"
    elif q_status == "NORMAL":
        final_status = "NORMAL"
    else:
        final_status = "LOW_CONFIDENCE"

    merged = merged.reset_index()
    merged = merged.rename(columns={merged.columns[0]: "clock"})
    return merged, final_status, "Data diproses dan divalidasi dengan sukses"

def calculate_multisensor_rul_v11(df_multisensor, sensor_configs=None):
    if df_multisensor is None or df_multisensor.empty:
        raise ValueError("DataFrame multisenor kosong atau None")

    feature_cols = [c for c in df_multisensor.columns if c != "clock"]
    if not feature_cols:
        raise ValueError("Kolom sensor tidak tersedia")

    df = df_multisensor.copy()
    df["clock"] = pd.to_datetime(df["clock"], utc=True, errors="coerce")
    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = (
        df.replace([np.inf, -np.inf], np.nan)
          .dropna(subset=["clock"] + feature_cols)
          .sort_values("clock")
          .drop_duplicates(subset=["clock"], keep="last")
    )

    if len(df) < 10:
        raise ValueError(f"Sampel valid tidak cukup untuk inferensi: {len(df)}")

    X = df[feature_cols].to_numpy(dtype=float)
    if not np.isfinite(X).all():
        raise ValueError("Data sensor mengandung nilai non-finite (NaN/Inf)")

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    latest_val = X[-1].reshape(1, -1)
    prediction = int(model.predict(latest_val)[0])
    raw_anomaly_score = float(model.decision_function(latest_val)[0])
    
    health_score = round(max(0.0, min(100.0, (raw_anomaly_score + 0.5) * 100)), 2)

    configs = sensor_configs or SENSOR_CONFIG
    continuous_candidates = [c for c in feature_cols if not ('status' in str(c).lower() or 'state' in str(c).lower())]
    primary_col = continuous_candidates[0] if continuous_candidates else feature_cols[0]

    primary = df[primary_col].rolling(window=60, min_periods=1).mean()
    times = (df["clock"] - df["clock"].iloc[0]).dt.total_seconds().to_numpy() / 3600.0

    if len(np.unique(times)) < 2:
        raise ValueError("Timestamp unik tidak cukup untuk menghitung tren slope")

    slope = float(np.polyfit(times, primary.to_numpy(), 1)[0])
    current_val = float(primary.iloc[-1])

    config = configs.get(primary_col, {})
    direction = config.get('direction', 'up')
    crit_high = config.get('crit_high', None)
    crit_low = config.get('crit_low', None)

    hours_to_failure = None
    exceeded_critical = False

    if direction == 'up':
        if crit_high is not None:
            if current_val >= crit_high:
                exceeded_critical = True
                hours_to_failure = 0.0
            elif slope > 1e-5:
                raw_ttf = (crit_high - current_val) / slope
                hours_to_failure = max(0.0, min(8760.0, float(raw_ttf)))
    elif direction == 'down':
        if crit_low is not None:
            if current_val <= crit_low:
                exceeded_critical = True
                hours_to_failure = 0.0
            elif slope < -1e-5:
                raw_ttf = (current_val - crit_low) / abs(slope)
                hours_to_failure = max(0.0, min(8760.0, float(raw_ttf)))

    confidence = "HIGH" if len(df) >= 60 else "MEDIUM"
    return prediction, raw_anomaly_score, health_score, hours_to_failure, confidence, exceeded_critical

def determine_action_status_hardened_v11(health, ttf, prediction, exceeded_critical):
    if health is None:
        return -1
    
    if exceeded_critical or (ttf is not None and ttf <= 24) or (health < 40):
        return 2
    elif prediction == -1 or health < 70 or (ttf is not None and ttf <= 720):
        return 1
    else:
        return 0
'''

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)
print(f"Candidate V11 written successfully to {target_path}")
