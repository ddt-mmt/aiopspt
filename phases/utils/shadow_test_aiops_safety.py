import unittest
from unittest.mock import patch
import sys
import importlib.machinery

loader = importlib.machinery.SourceFileLoader('shadow_mod', '/root/grafan_aiops/shadow_test_aiops.py')
shadow_mod = loader.load_module()

class TestShadowTestSafety(unittest.TestCase):

    @patch('script_aiops_v3.ZabbixAPI')
    @patch('script_aiops_v3.Sender')
    def test_shadow_execution_has_no_network_writes(self, mock_sender_cls, mock_zapi_cls):
        """Pastikan eksekusi shadow test tidak memanggil network/Zabbix API/Sender sama sekali."""
        res = shadow_mod.run_isolated_shadow_test()
        self.assertIn("hosts", res)
        mock_zapi_cls.assert_not_called()
        mock_sender_cls.assert_not_called()

        for hname, hdata in res["hosts"].items():
            self.assertEqual(hdata["status"], "PASS")

if __name__ == '__main__':
    unittest.main()
