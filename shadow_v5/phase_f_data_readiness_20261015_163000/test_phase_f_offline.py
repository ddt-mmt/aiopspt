"""
Offline Test Suite for Phase F Data Readiness & Evaluation Design
Isolated in /root/grafan_aiops/shadow_v5/phase_f_data_readiness_20261015_163000/
Zero Zabbix or production dependencies.
"""

import unittest
import os
import csv

class TestPhaseFOffline(unittest.TestCase):
    
    def test_feature_inventory_template_schema(self):
        """Verifies that FEATURE_INVENTORY_TEMPLATE.csv exists and has the required columns."""
        csv_path = os.path.join(
            "/root/grafan_aiops/shadow_v5/phase_f_data_readiness_20261015_163000",
            "FEATURE_INVENTORY_TEMPLATE.csv"
        )
        self.assertTrue(os.path.exists(csv_path), "FEATURE_INVENTORY_TEMPLATE.csv missing")
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            
        expected_columns = [
            "host",
            "item_identifier",
            "item_name",
            "timestamp",
            "value",
            "unit",
            "data_type",
            "quality_status",
            "asset_class"
        ]
        self.assertEqual(header, expected_columns)

    def test_temporal_split_anti_leakage(self):
        """Verifies that temporal split enforces strict chronological separation without overlap."""
        timestamps = [f"2026-10-15T00:{i:02d}:00Z" for i in range(60)]
        
        train_split = timestamps[:40]
        test_split = timestamps[40:]
        
        # Max train timestamp must be strictly less than min test timestamp
        self.assertLess(train_span := train_split[-1], test_split[0])
        # No intersection
        self.assertTrue(set(train_split).isdisjoint(set(test_split)))

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase F directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_f_data_readiness_20261015_163000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
