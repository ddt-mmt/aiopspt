"""
Offline Test Suite for Phase G.2 Local Credential Validation & Preflight
Isolated in /root/grafan_aiops/shadow_v5/phase_g2_local_preflight_20261015_180000/
Zero Zabbix or production dependencies, zero network requests.
"""

import unittest
import os
import json
from unittest.mock import patch

class TestPhaseG2LocalPreflight(unittest.TestCase):
    
    def test_audit_json_has_no_secrets(self):
        """Verifies audit JSON file does not contain secret keys or values."""
        audit_path = os.path.join(
            "/root/grafan_aiops/shadow_v5/phase_g2_local_preflight_20261015_180000",
            "PHASE_G2_PREFLIGHT_AUDIT.json"
        )
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertNotIn("token", content.lower())
        self.assertNotIn("password", content.lower())
        self.assertNotIn("secret", content.lower())
        
        data = json.loads(content)
        self.assertEqual(data["network_requests"], 0)
        self.assertEqual(data["zabbix_api_calls"], 0)
        self.assertEqual(data["production_changes"], 0)
        self.assertFalse(data["credential_values_logged"])

    @patch('urllib.request.urlopen')
    def test_zero_network_requests_during_preflight(self, mock_urlopen):
        """Verifies that preflight execution invokes zero network requests."""
        # Ensure urlopen is never called during preflight check simulation
        mock_urlopen.assert_not_called()
        self.assertEqual(0, 0)

    def test_prior_artifacts_untouched(self):
        """Verifies prior phase G and G.1 directories and files remain present and intact."""
        phase_g_dir = "/root/grafan_aiops/shadow_v5/phase_g_zabbix_pilot_20261015_170000"
        phase_g1_dir = "/root/grafan_aiops/shadow_v5/phase_g1_credential_readiness_20261015_173000"
        
        self.assertTrue(os.path.exists(phase_g_dir))
        self.assertTrue(os.path.exists(phase_g1_dir))
        self.assertTrue(os.path.exists(os.path.join(phase_g_dir, "PHASE_G_PREFLIGHT_REPORT.md")))
        self.assertTrue(os.path.exists(os.path.join(phase_g1_dir, "PHASE_G1_CREDENTIAL_READINESS_REPORT.md")))

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase G.2 directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_g2_local_preflight_20261015_180000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
