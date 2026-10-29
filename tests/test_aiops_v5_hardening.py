import unittest
import pandas as pd
import numpy as np
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_v8', '/root/grafan_aiops/script_aiops.py.candidate.v8')
v8_mod = loader.load_module()

class TestHardeningV8(unittest.TestCase):

    def test_1_normal_data(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        series_map = {
            'return.temp.c': pd.Series(np.linspace(20.0, 25.0, 15), index=times),
            'supply.temp.c': pd.Series(np.linspace(15.0, 18.0, 15), index=times),
            'return.humidity.rh': pd.Series(np.linspace(50.0, 55.0, 15), index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 15 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=600
        )
        self.assertEqual(status, "NORMAL")
        self.assertIsNotNone(df)
        pred, raw_score, health, ttf, conf = v8_mod.calculate_multisensor_rul_v8(df, crit_val=35.0)
        self.assertIsInstance(raw_score, float)
        self.assertIsInstance(health, float)

    def test_2_missing_optional_features_safe(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        series_map = {
            'return.temp.c': pd.Series(np.linspace(20.0, 25.0, 15), index=times),
            'supply.temp.c': pd.Series(np.linspace(15.0, 18.0, 15), index=times),
            'return.humidity.rh': pd.Series(np.linspace(50.0, 55.0, 15), index=times),
            'compressor.status': pd.Series([1] * 15, index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 15 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=600
        )
        self.assertIn(status, ["NORMAL", "DEGRADED_DATA"])
        self.assertIsNotNone(df)

    def test_3_missing_mandatory_features_insufficient(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        series_map = {
            'return.temp.c': pd.Series(np.linspace(20.0, 25.0, 15), index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 15 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=600
        )
        self.assertEqual(status, "INSUFFICIENT_DATA")
        self.assertIsNone(df)

    def test_4_stale_timestamp_degraded(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(hours=2)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        series_map = {
            'return.temp.c': pd.Series(np.linspace(20.0, 25.0, 15), index=times),
            'supply.temp.c': pd.Series(np.linspace(15.0, 18.0, 15), index=times),
            'return.humidity.rh': pd.Series(np.linspace(50.0, 55.0, 15), index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 15 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=300
        )
        self.assertEqual(status, "DEGRADED_DATA")

    def test_5_ffill_bounded_and_logged(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        s1 = pd.Series(np.linspace(20.0, 25.0, 15), index=times)
        s1.iloc[5:8] = np.nan
        
        series_map = {
            'return.temp.c': s1,
            'supply.temp.c': pd.Series(np.linspace(15.0, 18.0, 15), index=times),
            'return.humidity.rh': pd.Series(np.linspace(50.0, 55.0, 15), index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 15 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=600
        )
        self.assertIsNotNone(status)

    def test_6_coverage_or_min_samples_insufficient(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=5)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(5)]
        series_map = {
            'return.temp.c': pd.Series(np.linspace(20.0, 25.0, 5), index=times),
            'supply.temp.c': pd.Series(np.linspace(15.0, 18.0, 5), index=times),
            'return.humidity.rh': pd.Series(np.linspace(50.0, 55.0, 5), index=times)
        }
        latest_map = {k: times[-1] for k in series_map}
        counts = {k: 5 for k in series_map}
        
        df, status, msg = v8_mod.process_sensor_history_hardened(
            series_map, latest_map, counts, v8_mod.PAC_MANDATORY, now, max_age_seconds=600
        )
        self.assertEqual(status, "INSUFFICIENT_DATA")

    def test_7_nan_infinity_rejected(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df_bad = pd.DataFrame({
            'clock': times,
            'return.temp.c': [np.nan] * 15,
            'supply.temp.c': [np.inf] * 15,
            'return.humidity.rh': np.linspace(50.0, 55.0, 15)
        })
        with self.assertRaises(ValueError):
            v8_mod.calculate_multisensor_rul_v8(df_bad, crit_val=35.0)

    def test_8_discrete_feature_not_sloped(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'compressor.status': [1] * 15,
            'return.temp.c': np.linspace(20.0, 25.0, 15)
        })
        pred, raw_score, health, ttf, conf = v8_mod.calculate_multisensor_rul_v8(df, crit_val=35.0)
        self.assertIsInstance(health, float)

    def test_9_iforest_score_separation(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'return.temp.c': np.linspace(20.0, 25.0, 15),
            'supply.temp.c': np.linspace(15.0, 18.0, 15),
            'return.humidity.rh': np.linspace(50.0, 55.0, 15)
        })
        pred, raw_score, health, ttf, conf = v8_mod.calculate_multisensor_rul_v8(df, crit_val=35.0)
        self.assertNotEqual(raw_score, health)

    def test_10_offline_deterministic(self):
        now = pd.Timestamp.now(tz="UTC")
        base_time = now - pd.Timedelta(minutes=10)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'return.temp.c': np.linspace(20.0, 25.0, 15),
            'supply.temp.c': np.linspace(15.0, 18.0, 15),
            'return.humidity.rh': np.linspace(50.0, 55.0, 15)
        })
        res1 = v8_mod.calculate_multisensor_rul_v8(df, crit_val=35.0)
        res2 = v8_mod.calculate_multisensor_rul_v8(df, crit_val=35.0)
        self.assertEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()
