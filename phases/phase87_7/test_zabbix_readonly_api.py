#!/usr/bin/env python3
import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from zabbix_readonly_client import ReadOnlyZabbixAPI, READ_ONLY_METHODS_ALLOWLIST, PROHIBITED_METHODS

class TestZabbixReadOnlyAPI(unittest.TestCase):
    def test_allowlist_methods(self):
        for method in READ_ONLY_METHODS_ALLOWLIST:
            self.assertIn(method, READ_ONLY_METHODS_ALLOWLIST)

    def test_prohibited_methods_rejected(self):
        client = ReadOnlyZabbixAPI()
        for method in PROHIBITED_METHODS:
            with self.assertRaises(PermissionError):
                client.call(method, {})

if __name__ == "__main__":
    unittest.main()
