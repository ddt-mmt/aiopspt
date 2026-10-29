#!/usr/bin/env python3
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

sys.path.append('/root/grafan_aiops')
import script_aiops_v11_repaired as s

class TestV11ShadowExtended(unittest.TestCase):
    def test_checksum_verification(self):
        import hashlib
        with open('/root/grafan_aiops/script_aiops_v11_repaired.py', 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(h, "009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef")

    def test_quality_gate_future_data(self):
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(seconds=600)
        series = {
            'output.load': pd.Series([50.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.voltage': pd.Series([52.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)),
            'battery.temp': pd.Series([28.0]*15, index=pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc))
        }
        latest = {
            'output.load': future_time,
            'battery.voltage': future_time,
            'battery.temp': future_time
        }
        counts = {'output.load': 15, 'battery.voltage': 15, 'battery.temp': 15}
        status, msg = s.validate_schema_and_quality(series, latest, counts, s.UPS_MANDATORY, now)
        self.assertEqual(status, "FUTURE_DATA")

    def test_quality_gate_insufficient_data(self):
        now = datetime.now(timezone.utc)
        series = {
            'output.load': pd.Series([50.0]*5, index=pd.date_range(now - timedelta(minutes=5), periods=5, freq='1min', tz=timezone.utc)),
            'battery.voltage': pd.Series([52.0]*5, index=pd.date_range(now - timedelta(minutes=5), periods=5, freq='1min', tz=timezone.utc)),
            'battery.temp': pd.Series([28.0]*5, index=pd.date_range(now - timedelta(minutes=5), periods=5, freq='1min', tz=timezone.utc))
        }
        latest = {'output.load': now, 'battery.voltage': now, 'battery.temp': now}
        counts = {'output.load': 5, 'battery.voltage': 5, 'battery.temp': 5}
        df, status, msg = s.process_sensor_history_hardened(series, latest, counts, s.UPS_MANDATORY, now, min_samples=10)
        self.assertIsNone(df)
        self.assertEqual(status, "INSUFFICIENT_DATA")

    def test_process_sensor_history_degraded_imputation(self):
        now = datetime.now(timezone.utc)
        times = pd.date_range(now - timedelta(minutes=15), periods=15, freq='1min', tz=timezone.utc)
        load_s = pd.Series([50.0]*15, index=times)
        load_s.iloc[5] = np.nan
        series = {
            'output.load': load_s,
            'battery.voltage': pd.Series([52.0]*15, index=times),
            'battery.temp': pd.Series([28.0]*15, index=times)
        }
        latest = {'output.load': now, 'battery.voltage': now, 'battery.temp': now}
        counts = {'output.load': 15, 'battery.voltage': 15, 'battery.temp': 15}
        df, status, msg = s.process_sensor_history_hardened(series, latest, counts, s.UPS_MANDATORY, now, min_samples=10)
        self.assertIsNotNone(df)
        self.assertEqual(status, "DEGRADED_DATA")

    def test_daemon_cycle_resilience_with_mock(self):
        mock_zapi = MagicMock()
        mock_zapi.host.get.return_value = [
            {'hostid': '101', 'host': 'ME_UPS1', 'name': 'UPS 1'},
            {'hostid': '102', 'host': 'ME_PAC1', 'name': 'PAC 1'}
        ]
        def mock_item_get(**kwargs):
            if 'filter' in kwargs:
                return []
            if 'output' in kwargs and kwargs['output'] == ['value_type']:
                return [{'value_type': '0'}]
            return [
                {'itemid': '1', 'key_': 'output.load', 'value_type': '0'},
                {'itemid': '2', 'key_': 'battery.voltage', 'value_type': '0'},
                {'itemid': '3', 'key_': 'battery.temp', 'value_type': '0'},
                {'itemid': '4', 'key_': 'return.temp.c', 'value_type': '0'},
                {'itemid': '5', 'key_': 'supply.temp.c', 'value_type': '0'},
                {'itemid': '6', 'key_': 'return.humidity.rh', 'value_type': '0'}
            ]
        mock_zapi.item.get.side_effect = mock_item_get
        mock_zapi.history.get.return_value = [
            {'clock': int((datetime.now(timezone.utc) - timedelta(minutes=i)).timestamp()), 'value': '50.0'}
            for i in range(65)
        ]

        with patch('script_aiops_v11_repaired.ZabbixAPI', return_value=mock_zapi), \
             patch('script_aiops_v11_repaired.Sender') as mock_sender_cls:
            mock_sender = MagicMock()
            mock_sender.send.return_value = {"processed": 3, "failed": 0}
            mock_sender_cls.return_value = mock_sender

            try:
                s.run_aiops_cycle()
                success = True
            except Exception as e:
                print(f"Daemon cycle exception: {e}")
                success = False

            self.assertTrue(success)
            mock_sender.send.assert_called()

    def test_daemon_exception_handling_resilience(self):
        with patch('script_aiops_v11_repaired.ZabbixAPI', side_effect=Exception("Connection refused mock")):
            try:
                s.run_aiops_cycle()
                resilient = True
            except Exception:
                resilient = False
            self.assertTrue(resilient)

if __name__ == '__main__':
    unittest.main()
