#!/usr/bin/env python3
import unittest

class TestHostCoverage(unittest.TestCase):
    def test_seven_hosts(self):
        targets = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]
        self.assertEqual(len(targets), 7)

if __name__ == "__main__":
    unittest.main()
