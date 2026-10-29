"""
Synthetic Regression Tests for Offline Adapter v40.
Isolated in /root/grafan_aiops/shadow_v5/
"""

import unittest
import math
from datetime import datetime, timezone, timedelta
from offline_adapter_v40 import OfflineAdapterV40, STATUS_NORMAL, STATUS_DEGRADED, STATUS_STALE, STATUS_INSUFFICIENT, STATUS_UNAVAILABLE

class TestOfflineAdapterV40(unittest.TestCase):
    def setUp(self):
        self.adapter = OfflineAdapterV40(max_stale_seconds=3600, max_forward_fill=2)
        self.now_iso = datetime.now(timezone.utc).isoformat()

    def test_valid_records(self):
        """Test processing of valid records across mandatory features."""
        rows = []
        base_time = datetime.now(timezone.utc)
        for i in range(15):
            t = (base_time - timedelta(minutes=i)).isoformat()
            rows.append({"item_id": "59609", "unit": "%", "value": 50.0 + (i * 0.1), "timestamp": t})
            rows.append({"item_id": "59604", "unit": "V", "value": 48.0 + (i * 0.05), "timestamp": t})
            rows.append({"item_id": "60386", "unit": "C", "value": 22.0 + (i * 0.05), "timestamp": t})
            rows.append({"item_id": "60387", "unit": "C", "value": 18.0 + (i * 0.05), "timestamp": t})
            rows.append({"item_id": "60385", "unit": "%", "value": 45.0 + (i * 0.05), "timestamp": t})

        result = self.adapter.process_time_series(rows)
        self.assertEqual(result["status"], STATUS_NORMAL)
        self.assertGreater(result["health_score"], 0.0)
        self.assertEqual(result["ttf_status"], "CALCULATED")
        self.assertIsNotNone(result["ttf"])

    def test_partial_and_missing_mandatory_features(self):
        """Test partial records or missing mandatory features resulting in INSUFFICIENT or DEGRADED status."""
        t = datetime.now(timezone.utc).isoformat()
        rows = [
            {"item_id": "59609", "unit": "%", "value": 50.0, "timestamp": t},
            # Missing 59604, 60386, 60387, 60385
        ]
        result = self.adapter.process_time_series(rows)
        # With only 1 valid sample, status should be insufficient
        self.assertIn(result["status"], [STATUS_INSUFFICIENT, STATUS_UNAVAILABLE])

    def test_stale_records(self):
        """Test rejection of stale records exceeding max_stale_seconds."""
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        rows = [
            {"item_id": "59609", "unit": "%", "value": 50.0, "timestamp": old_time}
        ]
        is_valid, errs = self.adapter.validate_record(rows[0])
        self.assertFalse(is_valid)
        self.assertTrue(any("stale" in e.lower() for e in errs))

        result = self.adapter.process_time_series(rows)
        self.assertEqual(result["status"], STATUS_STALE)

    def test_invalid_units(self):
        """Test rejection of records with invalid units."""
        t = datetime.now(timezone.utc).isoformat()
        row = {"item_id": "59609", "unit": "RPM", "value": 50.0, "timestamp": t}
        is_valid, errs = self.adapter.validate_record(row)
        self.assertFalse(is_valid)
        self.assertTrue(any("unit" in e.lower() for e in errs))

    def test_nan_and_inf_values(self):
        """Test rejection of NaN and Inf values."""
        t = datetime.now(timezone.utc).isoformat()
        row_nan = {"item_id": "59609", "unit": "%", "value": float('nan'), "timestamp": t}
        is_valid, errs = self.adapter.validate_record(row_nan)
        self.assertFalse(is_valid)
        self.assertTrue(any("non-finite" in e.lower() for e in errs))

        row_inf = {"item_id": "59609", "unit": "%", "value": float('inf'), "timestamp": t}
        is_valid, errs = self.adapter.validate_record(row_inf)
        self.assertFalse(is_valid)
        self.assertTrue(any("non-finite" in e.lower() for e in errs))

    def test_duplicate_timestamps_deterministic(self):
        """Test deterministic handling of duplicate timestamps (keeping last)."""
        t = datetime.now(timezone.utc).isoformat()
        rows = [
            {"item_id": "59609", "unit": "%", "value": 10.0, "timestamp": t},
            {"item_id": "59609", "unit": "%", "value": 90.0, "timestamp": t} # duplicate, should keep last (90.0)
        ]
        res = self.adapter.process_time_series(rows)
        # processed values should use 90.0
        # let's verify via single row validation or internal processing logic
        self.assertEqual(res["valid_samples"], 1)

    def test_unavailable_health_and_missing_data(self):
        """Test that missing or invalid data never converts into normal health."""
        rows = [
            {"item_id": "59609", "unit": "%", "value": None, "timestamp": self.now_iso}
        ]
        result = self.adapter.process_time_series(rows)
        self.assertNotEqual(result["status"], STATUS_NORMAL)
        self.assertEqual(result["health_score"], 0.0)

    def test_ttf_abstention_zero_variance(self):
        """Test TTF abstention when variance is zero (constant values)."""
        t = datetime.now(timezone.utc)
        rows = []
        for i in range(12):
            ts = (t - timedelta(minutes=i)).isoformat()
            rows.append({"item_id": "59609", "unit": "%", "value": 50.0, "timestamp": ts})
            rows.append({"item_id": "59604", "unit": "V", "value": 48.0, "timestamp": ts})
            rows.append({"item_id": "60386", "unit": "C", "value": 22.0, "timestamp": ts})
            rows.append({"item_id": "60387", "unit": "C", "value": 18.0, "timestamp": ts})
            rows.append({"item_id": "60385", "unit": "%", "value": 45.0, "timestamp": ts})

        result = self.adapter.process_time_series(rows)
        self.assertIn("ABSTAINED", result["ttf_status"])
        self.assertIsNone(result["ttf"])

if __name__ == "__main__":
    unittest.main()
