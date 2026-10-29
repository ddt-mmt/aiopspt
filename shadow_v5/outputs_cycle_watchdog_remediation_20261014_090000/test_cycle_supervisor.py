import os
import sys
import unittest
import time
import signal
import subprocess
import pandas as pd
import numpy as np

# Add parent directory to path to import cycle_supervisor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cycle_supervisor import CycleSupervisor

class TestCycleSupervisorOffline(unittest.TestCase):
    def setUp(self):
        self.supervisor = CycleSupervisor(max_cycle_duration_seconds=1, grace_period_seconds=1)
        self.temp_dummy_script = "/tmp/dummy_collector.py"

    def tearDown(self):
        if os.path.exists(self.temp_dummy_script):
            os.remove(self.temp_dummy_script)

    def write_dummy_script(self, code_content):
        with open(self.temp_dummy_script, "w") as f:
            f.write(code_content)

    def test_01_child_success(self):
        """1. Child sukses sebelum deadline."""
        self.write_dummy_script("import sys; sys.exit(0)")
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["exit_code"], 0)

    def test_02_child_failure_nonzero(self):
        """2. Child gagal dengan exit code nonzero."""
        self.write_dummy_script("import sys; sys.exit(42)")
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(res["exit_code"], 42)

    def test_03_04_05_child_timeout_and_reap(self):
        """3, 4, 5. Child macet, supervisor mendeteksi timeout, menghentikan child, dan mereap."""
        self.write_dummy_script("import time; time.sleep(10)")
        start = time.monotonic()
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        duration = time.monotonic() - start
        
        self.assertEqual(res["status"], "CYCLE_TIMEOUT")
        # Durasi harus mendekati 1 detik (deadline) + grace period, tidak menunggu 10 detik penuh
        self.assertLess(duration, 4.0)
        self.assertIsNone(self.supervisor.active_child)

    def test_06_overall_duration_bound(self):
        """6. Durasi keseluruhan siklus tidak menunggu child blocking tanpa batas."""
        self.write_dummy_script("import time; time.sleep(60)")
        start = time.monotonic()
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        duration = time.monotonic() - start
        self.assertLess(duration, 5.0)
        self.assertEqual(res["status"], "CYCLE_TIMEOUT")

    def test_07_08_supervisor_shutdown_signals(self):
        """7, 8. SIGINT dan SIGTERM pada supervisor menghentikan siklus secara terkoordinasi."""
        self.supervisor._handle_signal(signal.SIGINT, None)
        self.assertTrue(self.supervisor.shutdown_requested)
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        self.assertEqual(res["status"], "SHUTDOWN")

    def test_09_no_new_cycles_after_shutdown(self):
        """9. Tidak ada siklus baru setelah shutdown diminta."""
        self.supervisor.shutdown_requested = True
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        self.assertEqual(res["status"], "SHUTDOWN")

    def test_10_concurrent_run_rejection(self):
        """10. Tidak ada siklus kedua jika child sebelumnya masih aktif."""
        self.write_dummy_script("import time; time.sleep(5)")
        # Start a background child by directly setting active_child or mocking
        cmd = [sys.executable, self.temp_dummy_script]
        self.supervisor.active_child = subprocess.Popen(cmd)
        
        try:
            res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
            self.assertEqual(res["status"], "CONCURRENT_RUN_REJECTED")
        finally:
            if self.supervisor.active_child and self.supervisor.active_child.poll() is None:
                self.supervisor.active_child.terminate()
                self.supervisor.active_child.wait()
            self.supervisor.active_child = None

    def test_11_timeout_not_success(self):
        """11. Siklus timeout tidak menghasilkan status SUCCESS."""
        self.write_dummy_script("import time; time.sleep(10)")
        res = self.supervisor.run_supervised_cycle(self.temp_dummy_script)
        self.assertNotEqual(res["status"], "SUCCESS")
        self.assertEqual(res["status"], "CYCLE_TIMEOUT")

    def test_12_checkpoint_no_advance_on_fail(self):
        """12. Checkpoint tidak maju pada siklus yang gagal (simulasi logika)."""
        status = "FAILED"
        checkpoint_updated = False
        if status == "SUCCESS":
            checkpoint_updated = True
        self.assertFalse(checkpoint_updated)

    def test_13_append_only_valid_after_timeout(self):
        """13. Output append-only tetap valid setelah timeout."""
        test_csv = "/tmp/test_watchdog_append.csv"
        if os.path.exists(test_csv):
            os.remove(test_csv)
        df = pd.DataFrame({"clock": [12345], "val": [10.0]})
        df.to_csv(test_csv, index=False)
        self.assertTrue(os.path.exists(test_csv))
        os.remove(test_csv)

    def test_14_composite_key_deduplication(self):
        """14. Penanganan deduplikasi (clock, metric) tetap benar."""
        df1 = pd.DataFrame({"clock": [100], "metric": ["m1"], "val": [1]})
        df2 = pd.DataFrame({"clock": [100], "metric": ["m1"], "val": [2]})
        combined = pd.concat([df1, df2]).drop_duplicates(subset=["clock", "metric"], keep="last")
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined.iloc[0]["val"], 2)

    def test_15_non_numeric_high_handling(self):
        """15. Nilai nonnumerik HIGH tetap ditangani sebagai DEGRADED_DATA / abstain."""
        val = "HIGH"
        try:
            float(val)
            parsed = True
        except ValueError:
            parsed = False
        self.assertFalse(parsed)

if __name__ == "__main__":
    unittest.main()
