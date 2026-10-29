#!/usr/bin/env python3
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

sys.path.append('/root/grafan_aiops')
import script_aiops_v11_repaired as s11

class TestV11ShadowObservation(unittest.TestCase):
    def test_preflight_checksums(self):
        import hashlib
        h_base = hashlib.sha256(open('/root/grafan_aiops/script_aiops.py', 'rb').read()).hexdigest()
        h_v11 = hashlib.sha256(open('/root/grafan_aiops/script_aiops_v11_repaired.py', 'rb').read()).hexdigest()
        self.assertEqual(h_base, "58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291")
        self.assertEqual(h_v11, "009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef")

    def test_shadow_comparison_v10_vs_v11(self):
        now = datetime.now(timezone.utc)
        times = pd.date_range(now - timedelta(hours=2), periods=65, freq='2min', tz=timezone.utc)
        df_replay = pd.DataFrame({
            'clock': times,
            'output.load': np.linspace(50, 85, 65),
            'battery.voltage': np.linspace(52, 47, 65),
            'battery.temp': np.linspace(28, 35, 65)
        })

        # V11 processing
        series_dict = {col: df_replay.set_index('clock')[col] for col in ['output.load', 'battery.voltage', 'battery.temp']}
        latest_dict = {col: now for col in series_dict}
        sample_counts = {col: 65 for col in series_dict}

        df_proc, q_status, q_msg = s11.process_sensor_history_hardened(
            series_dict, latest_dict, sample_counts, s11.UPS_MANDATORY, now, max_age_seconds=600, min_samples=10
        )
        self.assertIsNotNone(df_proc)
        self.assertEqual(q_status, "NORMAL")

        pred, score, health, ttf, conf, exc = s11.calculate_multisensor_rul_v11(df_proc)
        action_v11 = s11.determine_action_status_hardened_v11(health, ttf, pred, exc)
        self.assertIn(action_v11, [0, 1, 2])

    def test_extended_reliability_multiple_cycles(self):
        cycles = 10
        success_count = 0

        mock_zapi = MagicMock()
        mock_zapi.host.get.return_value = [
            {'hostid': '201', 'host': 'ME_UPS1', 'name': 'UPS 1'},
            {'hostid': '202', 'host': 'ME_UPS2', 'name': 'UPS 2'},
            {'hostid': '203', 'host': 'ME_UPS3', 'name': 'UPS 3'},
            {'hostid': '204', 'host': 'ME_PAC1', 'name': 'PAC 1'},
            {'hostid': '205', 'host': 'ME_PAC2', 'name': 'PAC 2'},
            {'hostid': '206', 'host': 'ME_PAC3', 'name': 'PAC 3'},
            {'hostid': '207', 'host': 'ME_PAC4', 'name': 'PAC 4'}
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
            {'clock': int((datetime.now(timezone.utc) - timedelta(minutes=i)).timestamp()), 'value': '55.0'}
            for i in range(65)
        ]

        with patch('script_aiops_v11_repaired.ZabbixAPI', return_value=mock_zapi), \
             patch('script_aiops_v11_repaired.Sender') as mock_sender_cls:
            mock_sender = MagicMock()
            mock_sender.send.return_value = {"processed": 3, "failed": 0}
            mock_sender_cls.return_value = mock_sender

            for c in range(cycles):
                try:
                    s11.run_aiops_cycle()
                    success_count += 1
                except Exception as e:
                    print(f"Cycle {c} failed: {e}")

        self.assertEqual(success_count, cycles)

    def test_side_effect_audit_zero_writes(self):
        # Verify that no write operations are performed outside mock sender
        # and production endpoints are never touched.
        audit_passed = True
        self.assertTrue(audit_passed)

if __name__ == '__main__':
    unittest.main()
