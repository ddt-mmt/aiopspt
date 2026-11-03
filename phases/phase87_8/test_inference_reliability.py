#!/usr/bin/env python3
import unittest
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../aiops_phase87_7/source/v12_snapshot")))
try:
    from script_aiops_v12_candidate import AIOpsV12Engine
except ModuleNotFoundError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../grafan_aiops/src")))
    from script_aiops_v12_candidate import AIOpsV12Engine

class TestInferenceReliability(unittest.TestCase):
    def test_engine_robustness(self):
        engine = AIOpsV12Engine()
        res = engine.evaluate_telemetry("ME_UPS1", pd.DataFrame())
        self.assertEqual(res["data_quality"], "INSUFFICIENT_DATA")
        self.assertEqual(res["health_score"], "UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
