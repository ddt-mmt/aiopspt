import unittest
import pandas as pd
import numpy as np
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_v5_ext', '/root/grafan_aiops/script_aiops.py.candidate.v5')
v5_mod = loader.load_module()

class TestAIOpsV5ExtendedRobustness(unittest.TestCase):

    def test_nan_inf_rejection(self):
        """Uji penolakan nilai NaN atau Inf tanpa fallback sintetis."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': [np.nan] * 15,
            'sensor2': np.linspace(10.0, 20.0, 15)
        })
        with self.assertRaises(ValueError):
            v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)

    def test_insufficient_samples_rejection(self):
        """Uji penolakan sampel kurang dari batas minimum (10)."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=5)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(5)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': np.linspace(10.0, 15.0, 5),
            'sensor2': np.linspace(20.0, 25.0, 5)
        })
        with self.assertRaises(ValueError):
            v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)

    def test_ttf_abstain_on_stable_trend(self):
        """Uji bahwa TTF mengembalikan None (abstain) pada tren stabil atau datar."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(20)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': [22.0] * 20, # Flatline / stable trend
            'sensor2': [50.0] * 20
        })
        pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)
        self.assertIsNone(ttf)
        self.assertEqual(conf, "MEDIUM")

    def test_discrete_compressor_handling(self):
        """Uji bahwa status kompresor diskret 0/1 tidak merusak regresi slope."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(20)]
        df = pd.DataFrame({
            'clock': times,
            'compressor.status': [1] * 20,
            'return.temp.c': np.linspace(20.0, 25.0, 20)
        })
        pred, health, ttf, conf = v5_mod.calculate_multisensor_rul_v5(df, crit_val=35.0)
        self.assertIsInstance(health, float)

if __name__ == '__main__':
    unittest.main()
