#!/usr/bin/env python3
"""
AIOps V11 (Hardened) — FIXED build.

Perubahan penting dibanding build sebelumnya (lihat analysis/FINDINGS.md):
  F-1  DILARANG menulis nilai sensor sintetik ke key sensor asli.
       Engine HANYA menulis metrik turunan: *.health.score, *.ttf.hours, *.action.status.
  F-2  DILARANG fallback acak (np.random). Bila quality gate gagal → ABSTAIN:
       tidak mengirim prediksi apa pun (health/ttf/action dilewati) dan mencatat alasan.
  F-7  Key item diselaraskan ke item SNMP yang benar-benar ada (lihat ITEM_KEY_MAP).

Prinsip: bila data tidak memenuhi syarat, lebih baik TIDAK menampilkan apa-apa
daripada menampilkan angka palsu.
"""
import os
import time
import logging
import numpy as np
import pandas as pd
from zabbix_utils import ZabbixAPI, ItemValue, Sender
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aiops_hardened_v11_fixed")

SAFETY_VERSION = "v11-hardened-fixed-1"

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "")
ZABBIX_SERVER_IP = os.getenv("ZABBIX_SERVER_IP", "10.28.1.110")
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "60"))
DAYS_WINDOW = int(os.getenv("DAYS_WINDOW", "30"))

# DRY_RUN=1 → hitung semua, TAPI jangan kirim apa pun ke Zabbix dan jangan
# membuat item. Mode aman untuk shadow/staging: membuktikan mesin bekerja
# pada data nyata tanpa mengubah apa pun di produksi.
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# Ambang staleness default + per-fitur (detik). Diukur dari interval update SNMP:
#   output.load/temp  : ~60s  → 600s aman
#   battery.voltage   : ~180-2700s → perlu ~6 jam
#   battery.capacity  : sparse     → ~12 jam
MIN_SAMPLES = int(os.getenv("MIN_SAMPLES", "10"))
MAX_AGE_DEFAULT = int(os.getenv("MAX_AGE_DEFAULT", "21600"))  # 6 jam
SENSOR_MAX_AGE = {
    'output.load': 600,
    'battery.voltage': 21600,
    'battery.temp': 21600,
    'battery.capacity': 43200,
    'battery.runtime_remaining': 21600,
    'ups.status': 21600,
    'return.temp.c': 600,
    'supply.temp.c': 600,
    'return.humidity.rh': 600,
    'evaporator.fan.speed': 3600,
    'compressor.status': 3600,
}

# ---------------------------------------------------------------------------
# Feature lists (logical names). Algoritma memakai nama logis ini sebagai kolom
# DataFrame; pemetaan ke key Zabbix sebenarnya ada di ITEM_KEY_MAP di bawah.
#
# CATATAN DATA (diverifikasi 2026-11-16 atas 30 hari ME_UPS1):
#   output.load[...]                n≈38709  (real, kontinu)
#   battery.voltage[...]            n≈3329   (real, kontinu)
#   battery.runtime_remaining[...]  n≈4955   (real, kontinu)
#   battery.capacity[...]           n≈376    (real, sparse)
#   output.status[...]              n≈122    (real, diskrit)
#   battery.temperature[SNMP]       n=0      (TIDAK ADA DATA)
# Karena itu battery.temp TIDAK boleh mandatory (akan memaksa abstain permanen);
# ia dipindah ke optional, dan mandatory UPS = sinyal yang benar-benar ada.
# ---------------------------------------------------------------------------
UPS_MANDATORY = [
    'output.load',
    'battery.voltage'
]
UPS_OPTIONAL = [
    'battery.temp',
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

# ---------------------------------------------------------------------------
# F-7: pemetaan nama logis -> key item Zabbix nyata.
# Sebelumnya engine memakai key polos ('output.load', 'battery.capacity', ...)
# yang berupa item TRAPPER kosong / hasil tulisan sintetik engine sendiri,
# sehingga quality gate selalu gagal. Di sini diarahkan ke item SNMP fisik.
# ---------------------------------------------------------------------------
ITEM_KEY_MAP = {
    'output.load': 'output.load[upsHighPrecOutputLoad]',
    'battery.voltage': 'battery.voltage[upsHighPrecBatteryActualVoltage]',
    'battery.temp': 'battery.temperature[upsHighPrecBatteryTemperature]',
    'battery.capacity': 'battery.capacity[upsHighPrecBatteryCapacity]',
    'battery.runtime_remaining': 'battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]',
    'ups.status': 'output.status[upsBasicOutputStatus]',
    'return.temp.c': 'return.temp.c',
    'supply.temp.c': 'supply.temp.c',
    'return.humidity.rh': 'return.humidity.rh',
    'evaporator.fan.speed': 'evaporator.fan.speed',
    'compressor.status': 'compressor.1.status',
}

SENSOR_CONFIG = {
    'battery.temp': {'direction': 'up', 'crit_high': 40.0, 'crit_low': None},
    'battery.voltage': {'direction': 'down', 'crit_high': None, 'crit_low': 44.0},
    'output.load': {'direction': 'up', 'crit_high': 95.0, 'crit_low': None},
    'return.temp.c': {'direction': 'up', 'crit_high': 35.0, 'crit_low': None},
    'supply.temp.c': {'direction': 'up', 'crit_high': 26.0, 'crit_low': None},
    'return.humidity.rh': {'direction': 'up', 'crit_high': 80.0, 'crit_low': 20.0}
}


def ensure_item_exists(zapi, host_id, item_name, key_name, value_type=0):
    """Membuat item TXT/derived bila belum ada. HANYA untuk metrik turunan AIOps."""
    if DRY_RUN:
        return
    items = zapi.item.get(hostids=host_id, filter={'key_': [key_name]}, output=['itemid'])
    if not items:
        try:
            zapi.item.create({
                'name': item_name,
                'key_': key_name,
                'hostid': host_id,
                'type': 2,          # Zabbix trapper
                'value_type': value_type,
                'interfaceid': 0,
                'delay': '0'
            })
            logger.info(f"Item '{item_name}' ({key_name}) berhasil dibuat di host ID {host_id}.")
        except Exception as e:
            logger.error(f"Gagal membuat item {key_name} di host {host_id}: {e}")


def _resolve_sensor_itemids(zapi, host_id, logical_names):
    """Petakan nama logis -> itemid berdasarkan ITEM_KEY_MAP (fallback: key polos)."""
    items = zapi.item.get(hostids=host_id, output=['itemid', 'key_'])
    key_to_id = {item['key_']: item['itemid'] for item in items}
    resolved = {}
    missing = []
    for name in logical_names:
        real_key = ITEM_KEY_MAP.get(name, name)
        itemid = key_to_id.get(real_key)
        if itemid is None and real_key != name:
            # fallback ke key polos hanya bila item SNMP memang tidak ada
            itemid = key_to_id.get(name)
        if itemid:
            resolved[name] = itemid
        else:
            missing.append(f"{name}->{real_key}")
    if missing:
        logger.info(f"Item sensor tidak ditemukan (akan dianggap sparse/abstain): {missing}")
    return resolved


def get_sensor_history_and_metadata(zapi, item_ids_dict, days=30):
    series_dict = {}
    latest_dict = {}
    sample_counts = {}
    time_till = int(datetime.now(timezone.utc).timestamp())
    time_from = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())

    for name, item_id in item_ids_dict.items():
        if not item_id:
            continue
        item_info = zapi.item.get(itemids=[item_id], output=["value_type"])
        if not item_info:
            continue
        v_type = int(item_info[0]['value_type'])

        history = zapi.history.get(
            itemids=[item_id],
            time_from=time_from,
            time_till=time_till,
            history=v_type,
            output='extend'
        )
        if not history:
            sample_counts[name] = 0
            latest_dict[name] = None
            continue

        df = pd.DataFrame(history)
        if not df.empty and 'value' in df.columns:
            try:
                df['value'] = df['value'].astype(float)
                df['clock'] = pd.to_datetime(df['clock'].astype(int), unit='s', utc=True)
                # FIX: beri nama seri = nama logis. Tanpa ini semua kolom bernama
                # 'value' dan pd.concat(axis=1) menghasilkan kolom duplikat,
                # sehingga df[col] mengembalikan DataFrame (bukan Series) → TypeError.
                series_dict[name] = df.set_index('clock')['value'].rename(name)
                sample_counts[name] = len(df)
                latest_dict[name] = df['clock'].max()
            except Exception as e:
                logger.warning(f"Error parsing history for {name}: {e}")
                sample_counts[name] = 0
                latest_dict[name] = None
        else:
            sample_counts[name] = 0
            latest_dict[name] = None

    return series_dict, latest_dict, sample_counts


def validate_schema_and_quality(series_by_name, latest_by_name, sample_counts, mandatory_features,
                                now_utc, max_age_seconds=3600, min_samples=10, future_tolerance_seconds=10,
                                per_feature_max_age=None):
    """Gerbang kualitas data.

    FIX (F-7b): staleness kini PER-FITUR dan default 3600s (bukan 300s).
    Item SNMP UPS (mis. battery.voltage) terbukti ter-update tiap ~180-2700s,
    sehingga ambang 300s menghasilkan STALE_DATA palsu dan memaksa abstain terus.
    Aturan:
      - fitur MANDATORY yang stale/masa-depan → hard gate (STALE_DATA/FUTURE_DATA)
      - fitur OPTIONAL yang stale → dibuang dari working set (seperti sparse),
        tidak menggagalkan seluruh analisa.
    """
    if series_by_name is not None:
        series_by_name = dict(series_by_name)
    else:
        return "INSUFFICIENT_DATA", "series_by_name is None"

    missing_mandatory = [f for f in mandatory_features if f not in series_by_name or sample_counts.get(f, 0) == 0]
    if missing_mandatory:
        return "INSUFFICIENT_DATA", f"Fitur wajib hilang atau kosong: {missing_mandatory}"

    per_feature_max_age = per_feature_max_age or {}
    stale_mandatory = {}
    stale_optional = {}
    future_stamps = {}

    for name, stamp in latest_by_name.items():
        if stamp is None or pd.isna(stamp):
            # foldnaNone pada fitur wajib = data tidak memadai; pada optional = drop.
            if name in mandatory_features:
                return "INSUFFICIENT_DATA", f"Timestamp NaT/None untuk sensor wajib {name}"
            stale_optional[name] = -1
            continue

        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        diff_seconds = (now_utc - stamp).total_seconds()
        limit = per_feature_max_age.get(name, max_age_seconds)

        if diff_seconds < -future_tolerance_seconds:
            future_stamps[name] = int(-diff_seconds)
        elif diff_seconds > limit:
            if name in mandatory_features:
                stale_mandatory[name] = int(diff_seconds)
            else:
                stale_optional[name] = int(diff_seconds)

    if future_stamps:
        return "FUTURE_DATA", f"Timestamp di masa depan terdeteksi (hard gate aktif): {future_stamps}"

    if stale_mandatory:
        return "STALE_DATA", f"Sensor wajib stale (hard gate aktif): {stale_mandatory}"

    for s in stale_optional:
        if s in series_by_name:
            logger.info(f"Dropping stale optional sensor from local copy: {s} (age={stale_optional[s]}s)")
            del series_by_name[s]

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


def process_sensor_history_hardened(series_by_name, latest_by_name, sample_counts, mandatory_features,
                                    now_utc, max_age_seconds=3600, min_samples=10,
                                    per_feature_max_age=None, resample_seconds=60, ffill_limit=5):
    """Selaraskan seri multi-sensor ke kisi waktu bersama, lalu validasi.

    FIX (langkah alignment): sensor UPS/PAC punya stempel waktu yang berbeda,
    sehingga pd.concat + dropna() nyaris selalu menghasilkan 0 baris (clock
    tidak pernah persis sama). Solusinya: resample tiap seri ke kisi 60 detik
    (mean) lebih dulu, baru forward-fill terbatas, baru dropna. Ini membuat
    "sampel selaras" benar-benar ada tanpa mengarang data (batas ffill dihitung
    dalam menit, dan sel yang lebih lama dari batas tetap dibuang).
    """
    if series_by_name is not None:
        working_series = dict(series_by_name)
    else:
        return None, "INSUFFICIENT_DATA", "series_by_name is None"

    q_status, q_msg = validate_schema_and_quality(
        working_series, latest_by_name, sample_counts, mandatory_features, now_utc,
        max_age_seconds, min_samples, per_feature_max_age=per_feature_max_age
    )
    if q_status in ("INSUFFICIENT_DATA", "STALE_DATA", "FUTURE_DATA"):
        return None, q_status, q_msg

    sparse_sensors = [name for name, count in sample_counts.items() if count < min_samples]
    for s in sparse_sensors:
        if s not in mandatory_features and s in working_series:
            del working_series[s]

    # --- Selaraskan ke kisi waktu bersama (bukan memaksakan stempel identik) ---
    resampled = []
    for name, ser in working_series.items():
        if not isinstance(ser, pd.Series):
            continue
        ser = pd.to_numeric(ser, errors="coerce")
        ser = ser[~ser.index.duplicated(keep="last")].sort_index()
        r = ser.resample(f"{int(resample_seconds)}s").mean()
        r.name = name
        resampled.append(r)

    if not resampled:
        return None, "INSUFFICIENT_DATA", "Tidak ada seri valid untuk diselaraskan"

    merged = pd.concat(resampled, axis=1).sort_index()

    # ffill PER-KOLOM, dibatasi budget staleness masing-masing sensor.
    # Sensor cepat (output.load, ~60s) hanya boleh ffill sedikit; sensor lambat
    # (battery.voltage, ~180-2700s) butuh jendela lebih lebar. Batas tetap
    # terbatas (dihitung dari per_feature_max_age / resample_seconds), sehingga
    # tidak ada data yang "dikarang" melewati ambang staleness fitur tsb.
    null_counts_before = merged.isnull().sum().to_dict()
    per_feature_max_age = per_feature_max_age or {}
    for col in merged.columns:
        budget_seconds = per_feature_max_age.get(col, max_age_seconds)
        col_limit = max(1, int(budget_seconds // max(1, resample_seconds)))
        merged[col] = merged[col].ffill(limit=col_limit)
    null_counts_after = merged.isnull().sum().to_dict()

    imputed_counts = {k: int(null_counts_before[k] - null_counts_after[k]) for k in null_counts_before}
    if sum(imputed_counts.values()) > 0:
        logger.info(f"Forward-fill audit log (per-feature budget, grid={resample_seconds}s): {imputed_counts}")

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
        slope = 0.0
    else:
        slope = float(np.polyfit(times, primary.to_numpy(), 1)[0])
    current_val = float(primary.iloc[-1])

    config = configs.get(primary_col, {})
    direction = config.get('direction', 'up')
    crit_high = config.get('crit_high', None)
    crit_low = config.get('crit_low', None)

    hours_to_failure = 8760.0
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


def run_aiops_cycle():
    try:
        logger.info(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] "
                    f"Menghubungkan ke Zabbix API ({SAFETY_VERSION} — no synthetic, no random)...")
        zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

        all_hosts = zapi.host.get(output=['hostid', 'host', 'name'])
        ups_hosts = [h for h in all_hosts if h['host'].startswith('ME_UPS')]
        pac_hosts = [h for h in all_hosts if h['host'].startswith('ME_PAC')]

        logger.info(f"Ditemukan {len(ups_hosts)} UPS dan {len(pac_hosts)} PAC.")
        action_labels = {0: "NORMAL (Aman)", 1: "MAINTENANCE (Preventif)", 2: "REPLACE (Segera Ganti!)", -1: "ABSTAIN (Data Tidak Cukup)"}
        sender = Sender(server=ZABBIX_SERVER_IP, port=10051)
        now_utc = datetime.now(timezone.utc)

        # ---- UPS ----
        for ups in ups_hosts:
            hostid = ups['hostid']
            hostname = ups['host']
            logger.info(f"--- Menganalisis UPS: {hostname} (ID: {hostid}) ---")

            # Hanya buat item METRIK TURUNAN; jangan pernah membuat item sensor.
            ensure_item_exists(zapi, hostid, 'UPS Health Score AIOps', 'ups.health.score', 0)
            ensure_item_exists(zapi, hostid, 'UPS Time-to-Failure (Hours)', 'ups.ttf.hours', 0)
            ensure_item_exists(zapi, hostid, 'UPS Policy Action Status', 'ups.action.status', 3)

            sensor_dict = _resolve_sensor_itemids(zapi, hostid, UPS_MANDATORY + UPS_OPTIONAL)

            health = None
            ttf = None
            action = -1
            try:
                if sensor_dict:
                    series_dict, latest_dict, sample_counts = get_sensor_history_and_metadata(zapi, sensor_dict, days=DAYS_WINDOW)
                    df_ups, q_status, q_msg = process_sensor_history_hardened(
                        series_dict, latest_dict, sample_counts, UPS_MANDATORY, now_utc,
                        max_age_seconds=MAX_AGE_DEFAULT, min_samples=MIN_SAMPLES,
                        per_feature_max_age=SENSOR_MAX_AGE
                    )
                    if df_ups is not None:
                        pred, raw_score, health, ttf, conf, exc_crit = calculate_multisensor_rul_v11(df_ups)
                        action = determine_action_status_hardened_v11(health, ttf, pred, exc_crit)
                    else:
                        logger.warning(f"UPS {hostname} ABSTAIN: {q_status} - {q_msg}")
                else:
                    logger.warning(f"UPS {hostname} ABSTAIN: tidak ada item sensor yang cocok.")
            except Exception as e:
                logger.error(f"Error menganalisis UPS {hostname}: {e} → ABSTAIN")

            if health is None:
                # F-2: TIDAK ada fallback acak. Tidak mengirim prediksi palsu.
                logger.info(f"⚡ [UPS {hostname}] Health: UNAVAILABLE | TTF: UNAVAILABLE | Aksi: {action_labels[-1]} (tidak ada push)")
                continue

            logger.info(f"⚡ [UPS {hostname}] Health: {health}% | TTF: {ttf}h | Aksi: {action_labels.get(action, 'UNKNOWN')}")

            # F-1: HANYA metrik turunan. Tidak menulis output.load/battery.* sensor.
            packet = [
                ItemValue(hostname, 'ups.health.score', health),
                ItemValue(hostname, 'ups.ttf.hours', ttf),
                ItemValue(hostname, 'ups.action.status', action),
            ]
            if DRY_RUN:
                logger.info(f"[DRY_RUN] UPS {hostname} — tidak mengirim (health={health}, ttf={ttf}, action={action})")
                continue
            try:
                res = sender.send(packet)
                logger.info(f"Status Pengiriman UPS {hostname}: {res}")
            except Exception as se:
                logger.warning(f"Gagal mengirim sender packet untuk UPS {hostname}: {se}")

        # ---- PAC ----
        for pac in pac_hosts:
            hostid = pac['hostid']
            hostname = pac['host']
            logger.info(f"--- Menganalisis PAC: {hostname} (ID: {hostid}) ---")

            ensure_item_exists(zapi, hostid, 'PAC Health Score AIOps', 'pac.health.score', 0)
            ensure_item_exists(zapi, hostid, 'PAC Time-to-Failure (Hours)', 'pac.ttf.hours', 0)
            ensure_item_exists(zapi, hostid, 'PAC Policy Action Status', 'pac.action.status', 3)

            sensor_dict = _resolve_sensor_itemids(zapi, hostid, PAC_MANDATORY + PAC_OPTIONAL)

            health = None
            ttf = None
            action = -1
            try:
                if sensor_dict:
                    series_dict, latest_dict, sample_counts = get_sensor_history_and_metadata(zapi, sensor_dict, days=DAYS_WINDOW)
                    df_pac, q_status, q_msg = process_sensor_history_hardened(
                        series_dict, latest_dict, sample_counts, PAC_MANDATORY, now_utc,
                        max_age_seconds=MAX_AGE_DEFAULT, min_samples=MIN_SAMPLES,
                        per_feature_max_age=SENSOR_MAX_AGE
                    )
                    if df_pac is not None:
                        pred, raw_score, health, ttf, conf, exc_crit = calculate_multisensor_rul_v11(df_pac)
                        action = determine_action_status_hardened_v11(health, ttf, pred, exc_crit)
                    else:
                        logger.warning(f"PAC {hostname} ABSTAIN: {q_status} - {q_msg}")
                else:
                    logger.warning(f"PAC {hostname} ABSTAIN: tidak ada item sensor yang cocok.")
            except Exception as e:
                logger.error(f"Error menganalisis PAC {hostname}: {e} → ABSTAIN")

            if health is None:
                logger.info(f"❄️ [PAC {hostname}] Health: UNAVAILABLE | TTF: UNAVAILABLE | Aksi: {action_labels[-1]} (tidak ada push)")
                continue

            logger.info(f"❄️ [PAC {hostname}] Health: {health}% | TTF: {ttf}h | Aksi: {action_labels.get(action, 'UNKNOWN')}")

            # F-1: HANYA metrik turunan. Tidak menulis return.temp.c/compressor.status sensor.
            packet = [
                ItemValue(hostname, 'pac.health.score', health),
                ItemValue(hostname, 'pac.ttf.hours', ttf),
                ItemValue(hostname, 'pac.action.status', action),
            ]
            if DRY_RUN:
                logger.info(f"[DRY_RUN] PAC {hostname} — tidak mengirim (health={health}, ttf={ttf}, action={action})")
                continue
            try:
                res = sender.send(packet)
                logger.info(f"Status Pengiriman PAC {hostname}: {res}")
            except Exception as se:
                logger.warning(f"Gagal mengirim sender packet untuk PAC {hostname}: {se}")

        logger.info("Siklus Analisis V11 (fixed) Multi-Device Selesai.\n")

    except Exception as e:
        logger.error(f"Error dalam eksekusi AIOps V11 Cycle: {e}\n")


def main():
    logger.info(f"Memulai AIOps {SAFETY_VERSION} Predictive Engine Daemon (Interval: {INTERVAL_SECONDS} detik)...")
    while True:
        run_aiops_cycle()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
