import os
import sys
import json
import time
import hashlib
import signal
import pandas as pd
import numpy as np
import importlib.machinery
from datetime import datetime, timezone

STAGING_DIR = "/root/grafan_aiops/shadow_v5"
DATA_DIR = os.path.join(STAGING_DIR, "telemetry_store")
os.makedirs(DATA_DIR, exist_ok=True)

CANDIDATE_V5 = "/root/grafan_aiops/script_aiops.py.candidate.v5"

class StagingContinuousCollector:
    def __init__(self, interval_seconds=60, max_retries=3, max_cycle_duration_seconds=120, request_timeout=10):
        self.interval_seconds = interval_seconds
        self.max_retries = max_retries
        self.max_cycle_duration_seconds = max_cycle_duration_seconds
        self.request_timeout = request_timeout
        self.shutdown_requested = False
        
        self.loader = importlib.machinery.SourceFileLoader('script_v5_collector', CANDIDATE_V5)
        self.v5_mod = self.loader.load_module()

        # Register graceful shutdown handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def log(self, msg):
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] [COLLECTOR] {msg}")

    def _handle_signal(self, signum, frame):
        self.log(f"Menerima sinyal shutdown ({signum}). Menghentikan koleksi secara terkoordinasi...")
        self.shutdown_requested = True

    def fetch_live_telemetry_readonly(self):
        """Mengambil telemetri aktual dari Zabbix secara ketat read-only tanpa mutasi dengan timeout eksplisit."""
        from zabbix_utils import ZabbixAPI
        zabbix_url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
        zabbix_user = os.getenv("ZABBIX_USER", "admin")
        zabbix_pass = os.getenv("ZABBIX_PASS", "1sampai6")

        retries = 0
        while retries < self.max_retries and not self.shutdown_requested:
            try:
                zapi = ZabbixAPI(url=zabbix_url, user=zabbix_user, password=zabbix_pass, timeout=self.request_timeout)
                all_hosts = zapi.host.get(output=['hostid', 'host', 'name'])
                ups_hosts = [h for h in all_hosts if h['host'].startswith('ME_UPS')]
                pac_hosts = [h for h in all_hosts if h['host'].startswith('ME_PAC')]
                return zapi, ups_hosts, pac_hosts
            except Exception as e:
                retries += 1
                self.log(f"Koneksi Zabbix gagal (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(2 * retries)
        raise ConnectionError("Gagal terhubung ke Zabbix API setelah max retries atau shutdown diminta.")

    def run_collection_cycle(self):
        if self.shutdown_requested:
            self.log("Shutdown diminta sebelum siklus dimulai. Membatalkan.")
            return {"status": "SHUTDOWN", "results_count": 0}

        cycle_start_time = time.monotonic()
        self.log("Memulai siklus pengumpulan telemetri read-only (dengan deadline & timeout eksplisit)...")
        try:
            zapi, ups_hosts, pac_hosts = self.fetch_live_telemetry_readonly()
        except Exception as e:
            self.log(f"Collector Error: {e}")
            return {"status": "ERROR", "error": str(e)}

        cycle_timestamp = datetime.now(timezone.utc).isoformat()
        results = []

        all_hosts = ups_hosts + pac_hosts
        for host_obj in all_hosts:
            if self.shutdown_requested:
                self.log("Shutdown diminta di tengah siklus. Menghentikan pemrosesan host tersisa.")
                break

            if time.monotonic() - cycle_start_time > self.max_cycle_duration_seconds:
                self.log(f"Cycle timeout deadline ({self.max_cycle_duration_seconds}s) terlampaui. Menghentikan siklus.")
                results.append({
                    "timestamp": cycle_timestamp,
                    "status": "CYCLE_TIMEOUT_ABORT",
                    "error": "Exceeded max cycle duration"
                })
                break

            hostid = host_obj['hostid']
            hostname = host_obj['host']

            try:
                items = zapi.item.get(hostids=hostid, output=['itemid', 'key_'])
                item_map = {item['key_']: item['itemid'] for item in items}

                if hostname.startswith("ME_UPS"):
                    sensor_dict = self.v5_mod.get_ups_sensor_dict(item_map)
                    crit_val = 95.0
                else:
                    sensor_dict = self.v5_mod.get_pac_sensor_dict(item_map, hostname)
                    crit_val = 35.0

                if not sensor_dict:
                    continue

                df_history, quality_status, quality_msg = self.v5_mod.get_sensor_history_v5(zapi, sensor_dict, days=30)

                if df_history is None or quality_status != "NORMAL":
                    results.append({
                        "timestamp": cycle_timestamp,
                        "host": hostname,
                        "status": "ABSTAIN",
                        "quality_status": quality_status,
                        "quality_message": quality_msg,
                        "health_score": 50.0,
                        "ttf_hours": None
                    })
                    continue

                pred, health, ttf, conf = self.v5_mod.calculate_multisensor_rul_v5(df_history, crit_val=crit_val)
                action = self.v5_mod.determine_action_status(health, ttf)

                results.append({
                    "timestamp": cycle_timestamp,
                    "host": hostname,
                    "status": "SUCCESS",
                    "quality_status": "NORMAL",
                    "quality_message": "OK",
                    "health_score": float(health),
                    "ttf_hours": float(ttf) if ttf is not None else None,
                    "confidence": float(conf) if conf is not None else 0.0,
                    "action_status": int(action),
                    "samples_count": len(df_history)
                })

                # Simpan sampel mentah/fitur secara terisolasi ke staging CSV/Parquet (Append-Only)
                host_csv = os.path.join(DATA_DIR, f"{hostname}_telemetry.csv")
                df_history['host'] = hostname
                df_history['collected_at'] = cycle_timestamp
                if os.path.exists(host_csv):
                    df_history.to_csv(host_csv, mode='a', header=False, index=False)
                else:
                    df_history.to_csv(host_csv, index=False)

            except Exception as host_err:
                self.log(f"Error memproses host {hostname}: {host_err}")
                results.append({
                    "timestamp": cycle_timestamp,
                    "host": hostname,
                    "status": "ERROR",
                    "error": str(host_err)
                })

        summary_path = os.path.join(STAGING_DIR, f"collector_run_{int(time.time())}.json")
        with open(summary_path, "w") as f:
            json.dump({"timestamp": cycle_timestamp, "results": results}, f, indent=2)

        self.log(f"Siklus selesai. Hasil disimpan ke {summary_path}")
        return {"status": "SUCCESS", "results_count": len(results)}

if __name__ == "__main__":
    collector = StagingContinuousCollector()
    res = collector.run_collection_cycle()
    print(json.dumps(res, indent=2))
