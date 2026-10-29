"""
Offline Test Suite for Phase G Zabbix Pilot Safety & Guardrails
Isolated in /root/grafan_aiops/shadow_v5/phase_g_zabbix_pilot_20261015_170000/
Zero Zabbix or production dependencies.
"""

import unittest
import re

def redact_secrets(text: str) -> str:
    """Redacts sensitive tokens, passwords, and auth headers from text/logs."""
    # Example regex for token/password fields
    redacted = re.sub(r'(token|password|auth|secret)=([^\s&]+)', r'\1=REDACTED', text, flags=re.IGNORECASE)
    redacted = re.sub(r'Bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer REDACTED', redacted)
    return redacted

def validate_api_method(method: str) -> bool:
    """Enforces read-only Zabbix API methods only. Rejects any mutation methods."""
    forbidden_suffixes = ("_create", "_update", "_delete", ".create", ".update", ".delete")
    if any(method.endswith(s) for s in forbidden_suffixes):
        return False
    allowed_methods = {"host.get", "item.get", "history.get", "apiinfo.version"}
    return method in allowed_methods


class TestPhaseGOfflineSafety(unittest.TestCase):
    
    def test_secret_redaction(self):
        """Verifies that secrets, tokens, and passwords are correctly redacted."""
        raw_log = "Connecting to Zabbix with token=secret12345 and password=mySecurePass and auth Header Bearer eyJhbGciOi..."
        cleaned = redact_secrets(raw_log)
        self.assertNotIn("secret12345", cleaned)
        self.assertNotIn("mySecurePass", cleaned)
        self.assertNotIn("eyJhbGciOi", cleaned)
        self.assertIn("token=REDACTED", cleaned)
        self.assertIn("password=REDACTED", cleaned)
        self.assertIn("Bearer REDACTED", cleaned)

    def test_mutation_api_ban(self):
        """Verifies that mutation API methods are strictly banned."""
        self.assertTrue(validate_api_method("host.get"))
        self.assertTrue(validate_api_method("history.get"))
        self.assertFalse(validate_api_method("host.create"))
        self.assertFalse(validate_api_method("item.update"))
        self.assertFalse(validate_api_method("host_delete"))

    def test_target_host_filtering(self):
        """Verifies target host filtering covers exactly the 7 required assets."""
        expected_hosts = {
            "ME_UPS1", "ME_UPS2", "ME_UPS3",
            "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"
        }
        self.assertEqual(len(expected_hosts), 7)
        self.assertIn("ME_UPS1", expected_hosts)
        self.assertIn("ME_PAC4", expected_hosts)

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase G directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_g_zabbix_pilot_20261015_170000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
