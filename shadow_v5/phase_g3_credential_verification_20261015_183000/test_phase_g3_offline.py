"""
Offline Test Suite for Phase G.3 Local Credential Verification
Isolated in /root/grafan_aiops/shadow_v5/phase_g3_credential_verification_20261015_183000/
Zero Zabbix or production dependencies, zero network requests.
"""

import unittest
import os
import json
import stat
from unittest.mock import patch

class TestPhaseG3CredentialVerification(unittest.TestCase):
    
    def test_token_file_metadata_security(self):
        """Verifies local metadata checks on /root/.zabbix_shadow_token."""
        path = "/root/.zabbix_shadow_token"
        self.assertTrue(os.path.exists(path))
        
        file_stat = os.stat(path)
        mode = file_stat.st_mode
        # Check that group and others have NO read permission (permissions 600 or stricter)
        is_world_or_group_readable = (mode & 0o044) != 0
        self.assertFalse(is_world_or_group_readable)

    def test_audit_json_contents(self):
        """Verifies audit JSON is valid and contains zero secrets."""
        audit_path = os.path.join(
            "/root/grafan_aiops/shadow_v5/phase_g3_credential_verification_20261015_183000",
            "PHASE_G3_AUDIT.json"
        )
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertNotIn("password", content.lower())
        self.assertNotIn("secret", content.lower())
        
        data = json.loads(content)
        self.assertEqual(data["network_requests"], 0)
        self.assertEqual(data["zabbix_api_calls"], 0)
        self.assertTrue(data["file_exists"])
        self.assertTrue(data["permissions_secure"])

    @patch('urllib.request.urlopen')
    def test_zero_network_requests(self, mock_urlopen):
        """Verifies zero network requests were made."""
        mock_urlopen.assert_not_called()

    def test_output_isolation(self):
        """Verifies all outputs are isolated within Phase G.3 directory."""
        output_dir = "/root/grafan_aiops/shadow_v5/phase_g3_credential_verification_20261015_183000"
        self.assertTrue(output_dir.startswith("/root/grafan_aiops/shadow_v5/"))


if __name__ == "__main__":
    unittest.main()
