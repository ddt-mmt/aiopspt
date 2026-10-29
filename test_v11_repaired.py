#!/usr/bin/env python3
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

sys.path.append('/root/grafan_aiops')
import script_aiops_v11_repaired as s

class TestV11Repaired(unittest.TestCase):
    def test_quality_gate_normal(self):
        now = datetime.now(timezone.utc)
        series = {
            'output.load': pd.Series([50.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.voltage': pd.Series([52.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.temp': pd.Series([28.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc))
        }
        latest = {
            'output.load': now,
            'battery.voltage': now,
            'battery.temp': now
        }
        counts = {'output.load': 15, 'battery.voltage': 15, 'battery.temp': 15}
        status, msg = s.validate_schema_and_quality(series, latest, counts, s.UPS_MANDATORY, now)
        self.assertEqual(status, "NORMAL")

    def test_quality_gate_stale(self):
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(seconds=600)
        series = {
            'output.load': pd.Series([50.0]*15, index=pd.date_range(old_time - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.voltage': pd.Series([52.0]*15, index=pd.date_range(old_time - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.temp': pd.Series([28.0]*15, index=pd.date_range(old_time - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc))
        }
        latest = {
            'output.load': old_time,
            'battery.voltage': old_time,
            'battery.temp': old_time
        }
        counts = {'output.load': 15, 'battery.voltage': 15, 'battery.temp': 15}
        status, msg = s.validate_schema_and_quality(series, latest, counts, s.UPS_MANDATORY, now)
        self.assertEqual(status, "STALE_DATA")

    def test_rul_calculation(self):
        now = datetime.now(timezone.utc)
        times = pd.date_range(now - timedelta(hours=2), periods=65, freq='2min', tz=timezone.utc)
        df = pd.DataFrame({
            'clock': times,
            'output.load': [98.0]*65,
            'battery.voltage': [43.0]*65,
            'battery.temp': [42.0]*65
        })
        pred, score, health, ttf, conf, exc = s.calculate_multisensor_rul_v11(df)
        action = s.determine_action_status_hardened_v11(health, ttf, pred, exc)
        self.assertIn(action, [0, 1, 2])
        self.assertTrue(exc)

if __name__ == '__main__':
    unittest.main()
