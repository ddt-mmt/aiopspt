import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sys
import importlib.machinery

# Load candidate v3
loader = importlib.machinery.SourceFileLoader('script_aiops_v3', '/root/grafan_aiops/script_aiops.py.candidate.v3')
script_v3 = loader.load_module()

class TestAIOpsSafetyIsolated(unittest.TestCase):

    def setUp(self):
        # Mock Zabbix API and Sender to ensure zero network writes
        self.mock_zapi = MagicMock()
        self.mock_sender = MagicMock()

    @patch('script_aiops_v3.ZabbixAPI')
    @patch('script_aiops_v3.Sender')
    def test_run_aiops_cycle_missing_sensors_no_synthetic(self, mock_sender_cls, mock_zapi_cls):
        """Pastikan sensor hilang/stale tidak menghasilkan nilai sintetis dan tidak mengirim trapper."""
        mock_zapi = mock_zapi_cls.return_value
        mock_sender = mock_sender_cls.return_value

        # Mock host discovery
        mock_zapi.host.get.return_value = [
            {'hostid': '10688', 'host': 'ME_UPS1', 'name': 'ME_UPS1'}
        ]
        # Mock item get to return empty or incomplete sensors
        mock_zapi.item.get.return_value = []

        # Run cycle
        script_v3.run_aiops_cycle()

        # Verify sender.send was NOT called because prediction was skipped
        mock_sender.send.assert_not_called()

    def test_calculate_multisensor_rul_non_finite_raises(self):
        """Pastikan nilai non-finite memicu ValueError tanpa fallback acak."""
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=25)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': [np.nan] * 15,
            'sensor2': np.linspace(50.0, 55.0, 15)
        })
        with self.assertRaises(ValueError):
            script_v3.calculate_multisensor_rul(df, crit_val=95.0)

    def test_determine_action_status_ttf_none(self):
        """Verifikasi semantik TTF=None dan health scores."""
        # Normal health, TTF=None -> Action 0 (Normal)
        self.assertEqual(script_v3.determine_action_status(85.0, None), 0)
        # Low health -> Action 1 or 2 regardless of TTF
        self.assertEqual(script_v3.determine_action_status(50.0, None), 1)
        self.assertEqual(script_v3.determine_action_status(30.0, None), 2)
        # Critical TTF <= 24 -> Action 2
        self.assertEqual(script_v3.determine_action_status(80.0, 12.0), 2)

    def test_get_sensor_history_stale_raises(self):
        """Pastikan sensor stale memicu ValueError."""
        # Mock zapi history returning very old timestamps
        mock_zapi = MagicMock()
        mock_zapi.item.get.return_value = [{'value_type': '0'}]
        old_epoch = int(pd.Timestamp.now(tz="UTC").timestamp()) - 100000
        mock_zapi.history.get.return_value = [
            {'clock': str(old_epoch), 'value': '50.0'}
        ]
        
        with self.assertRaises(ValueError) as ctx:
            script_v3.get_sensor_history(mock_zapi, {'load': '123'}, days=1)
        self.assertIn("stale", str(ctx.exception).lower())

if __name__ == '__main__':
    unittest.main()
