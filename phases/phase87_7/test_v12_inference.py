#!/usr/bin/env python3
import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
try:
    from source.v12_snapshot.script_aiops_v12_candidate import AIOpsV12Engine
except ModuleNotFoundError:
    from src.script_aiops_v12_candidate import AIOpsV12Engine

class TestV12Inference(unittest.TestCase):
    def setUp(self):
        self.engine = AIOpsV12Engine()

    def test_insufficient_data(self):
        df = pd.DataFrame({"temp": [25.0, 25.5]})
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res["data_quality"], "INSUFFICIENT_DATA")
        self.assertEqual(res["health_score"], "UNAVAILABLE")

    def test_degraded_data_nan(self):
        data = {"temp": [25.0 + i for i in range(15)]}
        data["temp"][5] = np.nan
        df = pd.DataFrame(data)
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res["data_quality"], "DEGRADED_DATA")

    def test_valid_data(self):
        np.random.seed(42)
        df = pd.DataFrame({
            "temp": np.random.normal(25.0, 0.5, 20),
            "voltage": np.random.normal(54.0, 0.2, 20)
        })
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res["data_quality"], "NORMAL")
        self.assertIsInstance(res["health_score"], float)
        self.assertIn(res["anomaly_label"], ["NORMAL", "ANOMALY"])

if __name__ == "__main__":
    unittest.main()
