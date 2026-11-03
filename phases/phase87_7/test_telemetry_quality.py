#!/usr/bin/env python3
import unittest
import pandas as pd
import numpy as np

class TestTelemetryQuality(unittest.TestCase):
    def test_missing_data_classification(self):
        df = None
        is_insufficient = df is None or len(df) < 10
        self.assertTrue(is_insufficient)

    def test_nan_detection(self):
        df = pd.DataFrame({"temp": [25.0, np.nan, 26.0]})
        has_nan = df.isin([np.nan, np.inf, -np.inf]).any().any()
        self.assertTrue(has_nan)

if __name__ == "__main__":
    unittest.main()
