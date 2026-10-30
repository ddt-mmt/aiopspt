#!/usr/bin/env python3
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import sys
sys.path.append('/root/grafan_aiops/src')
from script_aiops_v12_candidate import AIOpsV12Engine

class TestAIOpsV12Engine(unittest.TestCase):
    def setUp(self):
        self.engine = AIOpsV12Engine()

    def test_insufficient_data(self):
        df = pd.DataFrame({'load': [50.0] * 5})
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res['data_quality'], 'INSUFFICIENT_DATA')
        self.assertEqual(res['health_score'], 'UNAVAILABLE')
        self.assertEqual(res['ttf_hours'], 'NOT_ESTIMABLE')

    def test_nan_data(self):
        df = pd.DataFrame({'load': [50.0] * 15})
        df.loc[5, 'load'] = np.nan
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res['data_quality'], 'DEGRADED_DATA')
        self.assertEqual(res['health_score'], 'UNAVAILABLE')

    def test_normal_telemetry(self):
        np.random.seed(42)
        df = pd.DataFrame({
            'load': np.random.normal(50, 2, 20),
            'voltage': np.random.normal(52, 0.5, 20),
            'temp': np.random.normal(28, 1, 20)
        })
        res = self.engine.evaluate_telemetry("ME_UPS1", df)
        self.assertEqual(res['data_quality'], 'NORMAL')
        self.assertIsInstance(res['health_score'], float)
        self.assertIn(res['policy_recommendation'], ['NORMAL_MONITORING', 'PREVENTIVE_MAINTENANCE_REVIEW'])
        self.assertNotEqual(res['ttf_hours'], 8760)

if __name__ == '__main__':
    unittest.main()
