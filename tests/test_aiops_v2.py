import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sys
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('script_aiops_v2', '/root/grafan_aiops/src/candidates/script_aiops.py.candidate.v2')
script_v2 = loader.load_module()

class TestAIOpsCandidateV2(unittest.TestCase):

    def test_get_ups_sensor_dict(self):
        item_map = {
            'output.load[upsHighPrecOutputLoad]': '101',
            'battery.voltage[upsHighPrecBatteryActualVoltage]': '102',
            'battery.temperature[upsHighPrecBatteryTemperature]': '103', # Should be excluded
            'battery.capacity[upsHighPrecBatteryCapacity]': '104'
        }
        sensor_dict = script_v2.get_ups_sensor_dict(item_map)
        self.assertIn('output.load', sensor_dict)
        self.assertIn('battery.voltage', sensor_dict)
        self.assertIn('battery.capacity', sensor_dict)
        self.assertNotIn('battery.temperature', sensor_dict)

    def test_get_pac_sensor_dict(self):
        item_map_pac1 = {
            'return.temp.c': '201',
            'supply.temp.c': '202',
            'return.humidity.rh': '203',
            'evaporator.fan.speed': '204',
            'compressor.1.status': '205',
            'aiops.compressor.status': '206' # Should be ignored as input
        }
        sd = script_v2.get_pac_sensor_dict(item_map_pac1, 'ME_PAC1')
        self.assertIn('return.temp.c', sd)
        self.assertIn('compressor.status', sd)
        self.assertEqual(sd['compressor.status'], '205')

        item_map_pac4 = {
            'return.temp.c': '301',
            'supply.temp.c': '302',
            'return.humidity.rh': '303',
            'evaporator.fan.speed': '304',
            'compressor.status': '305'
        }
        sd4 = script_v2.get_pac_sensor_dict(item_map_pac4, 'ME_PAC4')
        self.assertIn('compressor.status', sd4)
        self.assertEqual(sd4['compressor.status'], '305')

    def test_determine_action_status(self):
        self.assertEqual(script_v2.determine_action_status(80.0, 1000.0), 0)
        self.assertEqual(script_v2.determine_action_status(50.0, 500.0), 1)
        self.assertEqual(script_v2.determine_action_status(30.0, 10.0), 2)

    def test_calculate_multisensor_rul_valid(self):
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': np.linspace(20.0, 25.0, 15),
            'sensor2': np.linspace(50.0, 55.0, 15)
        })
        pred, health, ttf = script_v2.calculate_multisensor_rul(df, crit_val=35.0)
        self.assertIsInstance(pred, int)
        self.assertGreaterEqual(health, 0.0)
        self.assertLessEqual(health, 100.0)
        self.assertGreater(ttf, 0.0)

    def test_calculate_multisensor_rul_non_finite(self):
        base_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20)
        times = [base_time + pd.Timedelta(minutes=i) for i in range(15)]
        df = pd.DataFrame({
            'clock': times,
            'sensor1': np.linspace(20.0, 25.0, 15),
            'sensor2': [np.nan] * 15
        })
        with self.assertRaises(ValueError):
            script_v2.calculate_multisensor_rul(df, crit_val=35.0)

if __name__ == '__main__':
    unittest.main()
