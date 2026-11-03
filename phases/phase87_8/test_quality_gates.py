#!/usr/bin/env python3
import unittest
import numpy as np
import pandas as pd

class TestQualityGates(unittest.TestCase):
    def test_quality_gate_checks(self):
        df_valid = pd.DataFrame({"a": range(15)})
        self.assertFalse(df_valid.isin([np.nan, np.inf]).any().any())

        df_nan = pd.DataFrame({"a": [1, 2, np.nan]})
        self.assertTrue(df_nan.isin([np.nan, np.inf]).any().any())

if __name__ == "__main__":
    unittest.main()
