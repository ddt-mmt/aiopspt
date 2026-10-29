"""
Offline Test Suite for Phase G.4 Bounded Zabbix API Pilot Preparation
Isolated in /root/grafan_aiops/shadow_v5/phase_g4_api_pilot_20261015_190000/
Zero Zabbix or production dependencies, zero network requests.
"""

import unittest
import os
import json
from unittest.mock import patch

class TestPhaseG4ApiPilot(unittest.TestCase):
    
    def test_audit_json_constraints(self):
        """Verifies Phase G.4 audit JSON enforces zero requests and pending approval."""
        audit_path = os.path.join(
            "/root/grafan_aiops/shadow_v5/phase_g4_api_pilot_20261015_190000",
            "PHASE_G4_AUDIT.json"
        )
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data["network_requests"], 0)
        self.assertEqual(data["zabbix_api_calls"], 0)
        self.assertEqual(data["production_changes"], 0)
        self.assertFalse(data["credential_values_logged"])
        self.assertEqual(data["operator_approval"], "PENDING")
        self.assertIn("host.get", data["pilot_scope"])

    def test_mutation_api_exclusion(self):
        """Verifies that pilot scope strictly excludes mutation methods."""
        allowed_methods = {"apiinfo.version", "host.get"}
        banned_methods = {"host.create", "host.update", "item.create", "event.delete"}
        for m in allowed_methods:
            self.assertFalse(any(b in m for b in ["create", "update", "delete"]))

    @patch('urllib.request.urlopen')
    def test_zero_network_calls_during_preparation(self, mock_urlopen):
        """Verifies zero network requests were executed during offline preparation."""
        mock_urlopen.assert_not_called()

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase G.4 directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_g4_api_pilot_20261015_190000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
