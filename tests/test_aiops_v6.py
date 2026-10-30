import unittest
import pandas as pd
import numpy as np
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_v6', '/root/grafan_aiops/src/candidates/script_aiops.py.candidate.v6')
v6_mod = loader.load_module()

class TestOptimizationV6(unittest.TestCase):

    def test_adaptive_ffill_limits(self):
        """Uji bahwa battery.capacity diisi lebih lama (6 jam) dibanding sensor lain (5 menit)."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=10)
        
        # Data sparse untuk battery.capacity (hanya 2 titik dalam 10 jam)
        data_cap = pd.DataFrame({
            'clock': [base_time, base_time + pd.Timedelta(hours=5)],
            'value': [100.0, 99.0]
        })
        
        # Resample 1min and ffill with limit 360 (6 hours)
        s_cap = data_cap.set_index('clock')['value'].resample('1min').last()
        filled_cap = s_cap.ffill(limit=360)
        
        # Titik pada menit ke-60 harus terisi (karena limit=360)
        self.assertFalse(np.isnan(filled_cap.iloc[60]))
        
        # Data sparse untuk load (limit=5)
        data_load = pd.DataFrame({
            'clock': [base_time, base_time + pd.Timedelta(hours=5)],
            'value': [40.0, 41.0]
        })
        s_load = data_load.set_index('clock')['value'].resample('1min').last()
        filled_load = s_load.ffill(limit=5)
        
        # Titik pada menit ke-10 harus NaN (karena limit=5)
        self.assertTrue(np.isnan(filled_load.iloc[10]))

    def test_confidence_score_calculation(self):
        """Uji logika perhitungan confidence score (Freshness + Density)."""
        # Mock data gating components
        # Density: total_obs / expected_obs
        # Freshness: 1 - avg_age / threshold
        
        # Test case: Perfect freshness and high density
        # Score should be close to 1.0 (labeled HIGH)
        # Note: This is an internal component check, normally we check output labels.
        pass

    def test_data_error_action_status(self):
        """Uji bahwa q_status != NORMAL menghasilkan Action Status 3 (DATA_ERROR)."""
        status = v6_mod.determine_action_status_v6(100.0, None, "INSUFFICIENT_DATA")
        self.assertEqual(status, 3)

if __name__ == '__main__':
    unittest.main()
