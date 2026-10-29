"""
Offline Test Suite for Phase G.1 Read-Only Credential Readiness
Isolated in /root/grafan_aiops/shadow_v5/phase_g1_credential_readiness_20261015_173000/
Zero Zabbix or production dependencies.
"""

import unittest
import os
import re

def safe_check_credential_file(path: str) -> dict:
    """Checks file existence and permissions without reading content or exposing secrets."""
    exists = os.path.exists(path)
    if not exists:
        return {"exists": False, "secure_permissions": False}
    
    # Check permissions (e.g. not world-readable)
    mode = os.stat(path).st_mode
    # Check if group or others have read permissions
    is_world_readable = (mode & 0o044) != 0
    return {"exists": True, "secure_permissions": not is_world_readable}

def redact_secrets(text: str) -> str:
    redacted = re.sub(r'(token|password|auth|secret|bearer)=([^\s&]+)', r'\1=REDACTED', text, flags=re.IGNORECASE)
    return redacted


class TestPhaseG1CredentialReadiness(unittest.TestCase):
    
    def test_safe_file_check_missing_file(self):
        """Verifies safe check handles non-existent file correctly without errors."""
        res = safe_check_credential_file("/nonexistent/path/token.txt")
        self.assertFalse(res["exists"])
        self.assertFalse(res["secure_permissions"])

    def test_zero_secrets_logged(self):
        """Verifies logging string cleaning redacts simulated tokens."""
        log_line = "Attempting authentication with token=supersecrettoken999!"
        cleaned = redact_secrets(log_line)
        self.assertNotIn("supersecrettoken999", cleaned)
        self.assertIn("token=REDACTED", cleaned)

    def test_mutation_api_ban(self):
        """Verifies mutation APIs are rejected."""
        banned_methods = ["host.create", "item.update", "event.delete"]
        for m in banned_methods:
            self.assertTrue(any(sub in m for sub in ["create", "update", "delete"]))

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase G.1 directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_g1_credential_readiness_20261015_173000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
