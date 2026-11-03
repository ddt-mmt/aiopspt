#!/usr/bin/env python3
import unittest

class TestObservationAccounting(unittest.TestCase):
    def test_host_count(self):
        hosts = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]
        self.assertEqual(len(hosts), 7)

if __name__ == "__main__":
    unittest.main()
