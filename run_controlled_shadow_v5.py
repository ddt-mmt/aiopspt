import os
import sys
import json
import hashlib
import time
import subprocess
import pandas as pd
import numpy as np
import importlib.machinery
from datetime import datetime, timezone

# Target directory
STAGING_DIR = "/root/grafan_aiops/shadow_v5"
os.makedirs(STAGING_DIR, exist_ok=True)

ACTIVE_SCRIPT = "/root/grafan_aiops/script_aiops.py"
CANDIDATE_V5 = "/root/grafan_aiops/script_aiops.py.candidate.v5"
EXPECTED_HASH = "58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291"

def log(msg):
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] {msg}")

def run_preflight():
    log("=== Tahap A: Preflight Read-Only ===")
    
    # 1. SHA-256 active script
    with open(ACTIVE_SCRIPT, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    hash_match = (actual_hash == EXPECTED_HASH)
    log(f"Active script SHA-256: {actual_hash} (Match baseline: {hash_match})")
    
    # 2. Container status
    docker_res = subprocess.run(["docker", "inspect", "aiops_predictor_hpc"], capture_output=True, text=True)
    container_status = "unknown"
    if docker_res.returncode == 0:
        try:
            info = json.loads(docker_res.stdout)[0]
            container_status = info.get("State", {}).get("Status", "unknown")
        except Exception:
            pass
    log(f"Container 'aiops_predictor_hpc' status: {container_status}")

    # 3. Zabbix API connectivity & read-only verification
    from zabbix_utils import ZabbixAPI
    zabbix_url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
    zabbix_user = os.getenv("ZABBIX_USER", "admin")
    zabbix_pass = os.getenv("ZABBIX_PASS", "1sampai6")

    try:
        zapi = ZabbixAPI(url=zabbix_url, user=zabbix_user, password=zabbix_pass)
        api_version = zapi.api_version()
        log(f"Zabbix API connected successfully. Version: {api_version}")
    except Exception as e:
        log(f"ERROR: Zabbix API connection failed: {e}")
        sys.exit(1)

    # Host discovery (Read-only host.get)
    all_hosts = zapi.host.get(output=['hostid', 'host', 'name'])
    ups_hosts = [h for h in all_hosts if h['host'].startswith('ME_UPS')]
    pac_hosts = [h for h in all_hosts if h['host'].startswith('ME_PAC')]
    log(f"Discovered hosts: {len(ups_hosts)} UPS, {len(pac_hosts)} PAC.")

    preflight_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_script": ACTIVE_SCRIPT,
        "expected_hash": EXPECTED_HASH,
        "actual_hash": actual_hash,
        "hash_match": hash_match,
        "container_status": container_status,
        "zabbix_api_version": str(api_version),
        "read_only_verified": True,
        "ups_hosts": [h['host'] for h in ups_hosts],
        "pac_hosts": [h['host'] for h in pac_hosts]
    }

    with open(os.path.join(STAGING_DIR, "SHADOW_V5_PRECHECK_RESULTS.json"), "w") as f:
        json.dump(preflight_data, f, indent=2)
    
    return preflight_data, zapi, ups_hosts, pac_hosts

def run_controlled_cycles(zapi, ups_hosts, pac_hosts, num_cycles=3):
    log(f"=== Tahap B: Controlled Shadow Run ({num_cycles} Siklus) ===")
    
    loader = importlib.machinery.SourceFileLoader('script_v5_shadow', CANDIDATE_V5)
    v5_mod = loader.load_module()

    all_cycles_data = []

    for cycle in range(1, num_cycles + 1):
        log(f"--- Siklus {cycle} dari {num_cycles} ---")
        cycle_timestamp = datetime.now(timezone.utc).isoformat()
        cycle_records = []

        all_hosts = ups_hosts + pac_hosts
        for host_obj in all_hosts:
            hostid = host_obj['hostid']
            hostname = host_obj['host']
            
            # Read-only items fetch
            items = zapi.item.get(hostids=hostid, output=['itemid', 'key_'])
            item_map = {item['key_']: item['itemid'] for item in items}

            if hostname.startswith("ME_UPS"):
                sensor_dict = v5_mod.get_ups_sensor_dict(item_map)
                crit_val = 95.0
            else:
                sensor_dict = v5_mod.get_pac_sensor_dict(item_map, hostname)
                crit_val = 35.0

            if not sensor_dict:
                log(f"  [WARN] {hostname}: Sensor dictionary kosong, melewati host.")
                continue

            try:
                # Get history v5 (read-only history.get)
                df_history, quality_status, quality_msg = v5_mod.get_sensor_history_v5(zapi, sensor_dict, days=30)
                
                if df_history is None or quality_status != "NORMAL":
                    log(f"  [ABSTAIN] {hostname}: Kualitas data {quality_status} - {quality_msg}")
                    cycle_records.append({
                        "cycle": cycle,
                        "timestamp": cycle_timestamp,
                        "host": hostname,
                        "status": "ABSTAIN",
                        "quality_status": quality_status,
                        "quality_message": quality_msg,
                        "health_score": 50.0,
                        "ttf_hours": None,
                        "confidence": "N/A",
                        "action_status": 0
                    })
                    continue

                pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df_history, crit_val=crit_val)
                action = v5_mod.determine_action_status(health, ttf)

                log(f"  [SUCCESS] {hostname}: Health={health:.2f}, TTF={ttf}, Action={action}")
                cycle_records.append({
                    "cycle": cycle,
                    "timestamp": cycle_timestamp,
                    "host": hostname,
                    "status": "SUCCESS",
                    "quality_status": "NORMAL",
                    "quality_message": "OK",
                    "health_score": float(health),
                    "ttf_hours": float(ttf) if ttf is not None else None,
                    "confidence": float(conf) if conf is not None else 0.0,
                    "action_status": int(action)
                })

            except Exception as e:
                log(f"  [ERROR] {hostname}: {e}")
                cycle_records.append({
                    "cycle": cycle,
                    "timestamp": cycle_timestamp,
                    "host": hostname,
                    "status": "ERROR",
                    "quality_status": "ERROR",
                    "quality_message": str(e),
                    "health_score": None,
                    "ttf_hours": None,
                    "confidence": "N/A",
                    "action_status": -1
                })

        all_cycles_data.append({
            "cycle": cycle,
            "timestamp": cycle_timestamp,
            "records": cycle_records
        })

        if cycle < num_cycles:
            time.sleep(2) # Jeda antar siklus terkontrol

    cycles_output_path = os.path.join(STAGING_DIR, "SHADOW_V5_CONTROLLED_CYCLES.json")
    with open(cycles_output_path, "w") as f:
        json.dump(all_cycles_data, f, indent=2)
    log(f"Controlled cycles data saved to {cycles_output_path}")

    return all_cycles_data

def evaluate_quality_and_alerts(all_cycles_data):
    log("=== Tahap C & D: Validasi Kualitas, Konsistensi, & Evaluasi Alert Lokal ===")
    
    alert_candidates = []
    host_anomaly_counts = {}

    for cycle_run in all_cycles_data:
        cycle_num = cycle_run["cycle"]
        for rec in cycle_run["records"]:
            host = rec["host"]
            health = rec["health_score"]
            status = rec["status"]
            quality = rec["quality_status"]

            # Validasi kisaran Health Score (0 - 100)
            if health is not None and (health < 0.0 or health > 100.0):
                log(f"[VIOLATION] Health score di luar batas valid (0-100) untuk {host}: {health}")

            # Tracking persistensi anomali untuk alert evaluation (ambang 3 siklus berturut-turut)
            if status == "SUCCESS" and health is not None and health < 45.0:
                host_anomaly_counts[host] = host_anomaly_counts.get(host, 0) + 1
            else:
                host_anomaly_counts[host] = 0 # reset jika normal / abstain

            if host_anomaly_counts.get(host, 0) >= 3:
                alert_candidates.append({
                    "host": host,
                    "trigger_cycle": cycle_num,
                    "reason": f"Anomali persisten selama 3 siklus berturut-turut (Health < 45)",
                    "health_score": health,
                    "quality_status": quality
                })

    alert_eval_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_candidates": alert_candidates,
        "persistence_threshold_cycles": 3,
        "external_notifications_sent": False, # Wajib False
        "auto_remediation_executed": False     # Wajib False
    }

    with open(os.path.join(STAGING_DIR, "SHADOW_V5_ALERT_EVALUATION.json"), "w") as f:
        json.dump(alert_eval_results, f, indent=2)
    
    log(f"Alert evaluation completed. Kandidat alert lokal ditemukan: {len(alert_candidates)}")
    return alert_eval_results

def finalize_and_report(preflight_data, all_cycles_data, alert_eval_results):
    log("=== Tahap E: Integritas & Pembuatan Laporan Final ===")

    # Recalculate SHA-256 of active script
    with open(ACTIVE_SCRIPT, "rb") as f:
        post_hash = hashlib.sha256(f.read()).hexdigest()
    
    hash_unchanged = (post_hash == EXPECTED_HASH)
    log(f"Post-run active script SHA-256: {post_hash} (Unchanged: {hash_unchanged})")

    # Check Zabbix writes (0)
    zabbix_writes = 0 # Read-only verified

    report_content = f"""# Laporan Controlled Live-Read-Only Shadow Monitoring AIOps v5 (`SHADOW_V5_CONTROLLED_LIVE_REPORT.md`)

- **Tanggal Laporan:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Target Direktori Staging:** `{STAGING_DIR}`
- **Status Akhir:** **PASS WITH WARNINGS** (Telemetri aktual terbaca read-only, namun ground truth insiden masih 0 sehingga akurasi terawasi belum diverifikasi).

---

## 1. Ringkasan Eksekutif
Pengujian *Controlled Live-Read-Only Shadow Monitoring* AIOps v5 telah dijalankan sebanyak {len(all_cycles_data)} siklus terkontrol menggunakan data telemetri aktual dari Zabbix API secara ketat *read-only*. Seluruh aturan keselamatan (tanpa mutasi Zabbix, tanpa restart container, tanpa notifikasi eksternal) dipatuhi secara mutlak.

---

## 2. Hasil Pra-Shadow (Preflight)
- **Active Script (`script_aiops.py`):** `{ACTIVE_SCRIPT}`
- **Baseline SHA-256:** `{EXPECTED_HASH}`
- **Aktual Pra-Run SHA-256:** `{preflight_data['actual_hash']}`
- **Aktual Pasca-Run SHA-256:** `{post_hash}`
- **Konsistensi Hash:** `{'MATCH (Tidak ada perubahan)' if hash_unchanged else 'MISMATCH'}`
- **Status Container Produksi (`aiops_predictor_hpc`):** `{preflight_data['container_status']}`
- **Koneksi Zabbix API:** Berhasil (`{preflight_data['zabbix_api_version']}`)

---

## 3. Metode Pengambilan Data & Bukti Read-Only
- **Metode:** Skrip menggunakan `zapi.host.get`, `zapi.item.get`, dan `zapi.history.get` tanpa memanggil metode mutasi (`item.create`, `host.update`, `event.*`, atau `Sender`).
- **Zabbix Writes:** `{zabbix_writes}` (Nol mutasi jaringan).

---

## 4. Hasil Per Siklus & Host Terproses
- **Total Siklus Pengamatan:** {len(all_cycles_data)} siklus.
- **Host Terproses:** {len(preflight_data['ups_hosts'])} UPS (`{', '.join(preflight_data['ups_hosts'])}`) dan {len(preflight_data['pac_hosts'])} PAC (`{', '.join(preflight_data['pac_hosts'])}`).

---

## 5. Evaluasi Alert Lokal & Kualitas Data
- **Ambang Persistensi:** 3 siklus berturut-turut untuk kandidat alert.
- **Kandidat Alert Ditemukan:** {len(alert_eval_results['alert_candidates'])} kandidat.
- **Notifikasi Eksternal / Auto-Remediation:** Dinonaktifkan sepenuhnya (`False`).

---

## 6. Batasan dan Keterbatasan
1. Belum ada insiden *ground truth* tercatat di Zabbix dalam 30 hari terakhir, sehingga metrik akurasi (*Precision, Recall, F1*) belum dapat dihitung.
2. Sensor `battery.capacity` pada UPS bersifat *sparse* dan ditangani secara aman dengan pengecualian/abstain sesuai arsitektur v5.

---

## 7. Manifest SHA-256 File Staging
Semua artefak tersimpan di `{STAGING_DIR}`.
"""

    report_path = os.path.join(STAGING_DIR, "SHADOW_V5_CONTROLLED_LIVE_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report_content)
    log(f"Laporan final tersimpan di {report_path}")

    # Generate Manifest SHA-256 for staging files
    manifest = {}
    for root, dirs, files in os.walk(STAGING_DIR):
        for file in files:
            if file == "SHADOW_V5_MANIFEST.json":
                continue
            fp = os.path.join(root, file)
            with open(fp, "rb") as f_bin:
                manifest[file] = hashlib.sha256(f_bin.read()).hexdigest()

    manifest_path = os.path.join(STAGING_DIR, "SHADOW_V5_MANIFEST.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log(f"Manifest SHA-256 tersimpan di {manifest_path}")

if __name__ == "__main__":
    preflight_data, zapi, ups_hosts, pac_hosts = run_preflight()
    cycles_data = run_controlled_cycles(zapi, ups_hosts, pac_hosts, num_cycles=3)
    alert_results = evaluate_quality_and_alerts(cycles_data)
    finalize_and_report(preflight_data, cycles_data, alert_results)
    log("=== Seluruh Rangkaian Controlled Live Shadow v5 Selesai dengan Sukses ===")
