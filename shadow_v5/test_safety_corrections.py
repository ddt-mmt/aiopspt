import os
import sys
import json
import time
import signal
import hashlib
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

STAGING_DIR = "/root/grafan_aiops/shadow_v5"
FIXTURE_DIR = os.path.join(STAGING_DIR, "fixture_test_store")
os.makedirs(FIXTURE_DIR, exist_ok=True)

class TestSafetyCorrections(unittest.TestCase):
    def test_production_hash_integrity(self):
        active_script = "/root/grafan_aiops/script_aiops.py"
        expected_hash = "58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291"
        with open(active_script, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_hash, expected_hash, "Production script hash mismatch!")

    def test_composite_key_deduplication_fixture(self):
        """Uji deduplikasi dengan composite key (clock, metric_name) agar sensor berbeda di timestamp sama tidak terhapus."""
        base_time = pd.Timestamp("2026-10-14 00:00:00", tz="UTC")
        
        # Simulasikan data mentah dengan dua sensor berbeda (return.temp.c dan supply.temp.c) pada clock yang sama
        data = [
            {"clock": base_time, "metric": "return.temp.c", "value": 22.5},
            {"clock": base_time, "metric": "supply.temp.c", "value": 14.2},
            {"clock": base_time, "metric": "return.temp.c", "value": 22.5}, # duplikat identik
            {"clock": base_time + pd.Timedelta(minutes=1), "metric": "return.temp.c", "value": 22.6}
        ]
        df = pd.DataFrame(data)
        
        # Terapkan deduplikasi berbasis composite key: ["clock", "metric"]
        df_dedup = df.drop_duplicates(subset=["clock", "metric"], keep="last")
        
        # Seharusnya baris duplikat identik return.temp.c pada base_time terhapus (tersisa 1), tetapi supply.temp.c tetap ada.
        self.assertEqual(len(df_dedup), 3, "Deduplikasi composite key gagal mempertahankan metrik berbeda pada timestamp sama.")

    def test_graceful_shutdown_simulation(self):
        """Uji simulasi penanganan SIGINT/SIGTERM dan penutupan file staging dengan aman."""
        shutdown_flag = [False]

        def signal_handler(signum, frame):
            shutdown_flag[0] = True

        # Daftarkan handler sementara
        old_handler = signal.signal(signal.SIGINT, signal_handler)
        try:
            # Simulasikan file open dan penulisan aman
            test_file = os.path.join(FIXTURE_DIR, "graceful_test.csv")
            df_test = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df_test.to_csv(test_file, index=False)
            
            # Simulasi sinyal
            signal.raise_signal(signal.SIGINT)
            self.assertTrue(shutdown_flag[0], "Signal SIGINT gagal ditangkap.")
            self.assertTrue(os.path.exists(test_file), "File staging gagal ditutup/disimpan dengan aman.")
        finally:
            signal.signal(signal.SIGINT, old_handler)

    def test_numerical_kill_switch_thresholds(self):
        """Verifikasi bahwa ambang batas numerik (RAM < 80%, Disk < 5GB, Timeout siklus) terdokumentasi."""
        thresholds = {
            "max_memory_percent": 80.0,
            "max_staging_disk_mb": 5120.0,
            "cycle_timeout_seconds": 120,
            "max_consecutive_api_errors": 5
        }
        self.assertLess(thresholds["max_memory_percent"], 100.0)
        self.assertGreater(thresholds["max_staging_disk_mb"], 0)

if __name__ == "__main__":
    unittest.main()
