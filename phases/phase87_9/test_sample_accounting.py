#!/usr/bin/env python3
import unittest
import pandas as pd

class TestSampleAccounting(unittest.TestCase):
    def test_sample_uniqueness(self):
        df = pd.DataFrame([
            {"host": "ME_UPS1", "clock": 1000, "key": "temp", "value": 25.0},
            {"host": "ME_UPS1", "clock": 1000, "key": "temp", "value": 25.0},
        ])
        unique = df.drop_duplicates(subset=["host", "clock", "key"])
        self.assertEqual(len(unique), 1)

if __name__ == "__main__":
    unittest.main()
