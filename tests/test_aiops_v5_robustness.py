import unittest
import pandas as pd
import numpy as np
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_v5', '/root/grafan_aiops/src/candidates/script_aiops.py.candidate.v5')
v5_mod = loader.load_module()

class TestRobustnessV5(unittest.TestCase):

    def test_quality_gating_normal(self):
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': np.linspace(20.0, 25.0, 15),
            'sensor2': np.linspace(50.0, 55.0, 15)
        })
        pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)
        self.assertIsInstance(pred, int)
        self.assertGreaterEqual(health, 0.0)
        self.assertLessEqual(health, 100.0)

    def test_discrete_feature_exclusion_from_slope(self):
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'compressor.status': [1] * 15, # Discrete feature first
            'return.temp.c': np.linspace(20.0, 25.0, 15) # Continuous feature
        })
        pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)
        self.assertIsInstance(health, float)

    def test_non_finite_raises(self):
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': [np.nan] * 15,
            'sensor2': np.linspace(50.0, 55.0, 15)
        })
        with self.assertRaises(ValueError):
            v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)

if __name__ == '__main__':
    unittest.main()
