#!/usr/bin/env python3
import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../aiops_phase87_7/scripts")))
try:
    from zabbix_readonly_client import ReadOnlyZabbixAPI, PROHIBITED_METHODS
except ModuleNotFoundError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../phase87_7")))
    from zabbix_readonly_client import ReadOnlyZabbixAPI, PROHIBITED_METHODS

class TestNoWritePolicy(unittest.TestCase):
    def test_prohibited_methods(self):
        client = ReadOnlyZabbixAPI()
        for method in PROHIBITED_METHODS:
            with self.assertRaises(PermissionError):
                client.call(method, {})

if __name__ == "__main__":
    unittest.main()
