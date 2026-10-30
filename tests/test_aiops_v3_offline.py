import unittest
from unittest.mock import patch
import sys
import importlib.machinery

# Load evaluate_aiops_v3_offline module
loader = importlib.machinery.SourceFileLoader('eval_offline', '/root/grafan_aiops/phases/utils/evaluate_aiops_v3_offline.py')
eval_mod = loader.load_module()

class TestAIOpsOfflineEvaluation(unittest.TestCase):

    @patch('script_aiops_v3.ZabbixAPI')
    @patch('script_aiops_v3.Sender')
    def test_offline_evaluation_runs_without_network(self, mock_sender_cls, mock_zapi_cls):
        """Pastikan evaluasi offline berjalan sukses tanpa memanggil API Zabbix atau Sender."""
        res = eval_mod.run_offline_evaluation()
        self.assertIn("hosts_evaluated", res)
        # Verify ZabbixAPI and Sender were never called
        mock_zapi_cls.assert_not_called()
        mock_sender_cls.assert_not_called()

        # Check all hosts successfully evaluated
        for hname, hdata in res.get("hosts", {}).items():
            self.assertEqual(hdata["status"], "SUCCESS")

if __name__ == '__main__':
    unittest.main()
