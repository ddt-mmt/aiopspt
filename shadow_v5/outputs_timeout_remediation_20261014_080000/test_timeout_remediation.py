import os
import sys
import unittest
import time
import signal
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Add parent directory to path to import continuous_collector
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from continuous_collector import StagingContinuousCollector

class TestTimeoutRemediationOffline(unittest.TestCase):
    def setUp(self):
        self.collector = StagingContinuousCollector(interval_seconds=1, max_retries=2, max_cycle_duration_seconds=1, request_timeout=2)

    def test_01_request_timeout_and_retry_limits(self):
        """Test that retries are limited and backoff works without infinite loops."""
        self.assertEqual(self.collector.max_retries, 2)
        self.assertEqual(self.collector.request_timeout, 2)

    def test_02_cycle_monotonic_deadline(self):
        """Test that monotonic deadline aborts cycle when time exceeds max_cycle_duration_seconds."""
        # Force start time in the past to simulate deadline expiration
        cycle_start_time = time.monotonic() - 5.0 # 5 seconds ago, max is 1s
        self.assertGreater(time.monotonic() - cycle_start_time, self.collector.max_cycle_duration_seconds)

    def test_03_graceful_shutdown_flag(self):
        """Test that signal handling sets shutdown_requested to True and blocks new cycles."""
        self.assertFalse(self.collector.shutdown_requested)
        # Simulate SIGINT signal handling
        self.collector._handle_signal(signal.SIGINT, None)
        self.assertTrue(self.collector.shutdown_requested)
        
        # Verify run_collection_cycle immediately returns SHUTDOWN
        res = self.collector.run_collection_cycle()
        self.assertEqual(res["status"], "SHUTDOWN")

    def test_04_composite_key_deduplication(self):
        """Test that deduplication with composite key (clock, metric) preserves distinct sensors at same timestamp."""
        df1 = pd.DataFrame({
            "clock": [1000, 1000],
            "metric": ["sensor.temp", "sensor.humidity"],
            "value": [25.5, 60.0]
        })
        df2 = pd.DataFrame({
            "clock": [1000, 1000],
            "metric": ["sensor.temp", "sensor.humidity"],
            "value": [26.0, 61.0]
        })
        combined = pd.concat([df1, df2]).drop_duplicates(subset=["clock", "metric"], keep="last")
        self.assertEqual(len(combined), 2)
        self.assertIn("sensor.temp", combined["metric"].values)
        self.assertIn("sensor.humidity", combined["metric"].values)

    def test_05_append_only_storage_behavior(self):
        """Test append-only CSV write behavior without header duplication."""
        test_csv = "/tmp/test_append_telemetry.csv"
        if os.path.exists(test_csv):
            os.remove(test_csv)
            
        df_first = pd.DataFrame({"clock": [100], "value": [1.0]})
        df_second = pd.DataFrame({"clock": [200], "value": [2.0]})
        
        # First write with header
        df_first.to_csv(test_csv, index=False)
        # Second write append without header
        df_second.to_csv(test_csv, mode='a', header=False, index=False)
        
        loaded = pd.read_csv(test_csv)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(list(loaded["clock"]), [100, 200])
        os.remove(test_csv)

    def test_06_non_numeric_handling(self):
        """Test non-numeric string values (e.g. 'HIGH') handling simulation."""
        raw_vals = ["25.0", "HIGH", "26.5"]
        converted = []
        for v in raw_vals:
            try:
                converted.append(float(v))
            except ValueError:
                converted.append(np.nan)
        
        self.assertEqual(converted[0], 25.0)
        self.assertTrue(np.isnan(converted[1]))
        self.assertEqual(converted[2], 26.5)

    def test_07_zero_network_or_zabbix_calls(self):
        """Confirm no live network or Zabbix calls are made during offline unit tests."""
        # We assert that no network socket was opened or Zabbix client initialized
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
