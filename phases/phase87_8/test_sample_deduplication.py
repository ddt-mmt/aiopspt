#!/usr/bin/env python3
import unittest
import pandas as pd

class TestSampleDeduplication(unittest.TestCase):
    def test_deduplication(self):
        df = pd.DataFrame([
            {"clock": 1000, "key": "temp", "value": 25.0},
            {"clock": 1000, "key": "temp", "value": 25.0},
            {"clock": 1001, "key": "temp", "value": 25.1},
        ])
        dedup = df.drop_duplicates(subset=["clock", "key"])
        self.assertEqual(len(dedup), 2)

if __name__ == "__main__":
    unittest.main()
