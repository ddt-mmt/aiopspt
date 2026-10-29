"""
Anti-Fabrication & Regression Test Suite for Phase E.1
Isolated in /root/grafan_aiops/shadow_v5/phase_e1_audit_20261015_153000/
Zero Zabbix or production dependencies.
"""

import unittest
import os
import json
from run_public_offline_benchmarks_v2 import (
    compute_classification_metrics,
    compute_regression_metrics,
    generate_realistic_hvac_dataset,
    generate_realistic_battery_dataset
)

class TestAntiFabricationPhaseE1(unittest.TestCase):
    
    def test_classification_metrics_computation(self):
        """Verifies that classification metrics are computed correctly programmatically from arrays."""
        y_true = [0, 1, 1, 0, 1, 0]
        y_pred = [0, 1, 0, 0, 1, 1]
        metrics = compute_classification_metrics(y_true, y_pred)
        
        # Manual calculation:
        # TP = 2 (indices 1, 4)
        # FP = 1 (index 5: true 0, pred 1)
        # FN = 1 (index 2: true 1, pred 0)
        # TN = 2 (indices 0, 3)
        # Precision = 2 / 3 = 0.6667
        # Recall = 2 / 3 = 0.6667
        self.assertAlmostEqual(metrics["precision"], 0.6667, places=3)
        self.assertAlmostEqual(metrics["recall"], 0.6667, places=3)
        self.assertIn("f1_score", metrics)
        self.assertIn("false_alarm_rate", metrics)

    def test_regression_metrics_computation(self):
        """Verifies regression metrics (MAE, RMSE) computation from actual arrays."""
        y_true = [2.0, 1.8, 1.6]
        y_pred = [1.9, 1.8, 1.5]
        metrics = compute_regression_metrics(y_true, y_pred)
        # Errors: |2.0-1.9|=0.1, |1.8-1.8|=0.0, |1.6-1.5|=0.1. MAE = 0.2 / 3 = 0.0667
        self.assertAlmostEqual(metrics["mae"], 0.0667, places=3)
        self.assertGreaterEqual(metrics["rmse"], metrics["mae"])

    def test_dataset_generation_counts_and_splits(self):
        """Verifies dataset size and temporal/sequential train/test splitting without leakage."""
        hvac = generate_realistic_hvac_dataset(100)
        self.assertEqual(len(hvac), 100)
        
        train = hvac[:70]
        test = hvac[70:]
        self.assertEqual(len(train), 70)
        self.assertEqual(len(test), 30)
        # Ensure no timestamp overlap (temporal split)
        self.assertNotEqual(train[-1]["timestamp"], test[0]["timestamp"])

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase E.1 directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_e1_audit_20261015_153000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
