import unittest
import os
import json
import pandas as pd
import numpy as np

STAGING_DIR = "/root/grafan_aiops/shadow_v5"
DATA_DIR = os.path.join(STAGING_DIR, "telemetry_store")
os.makedirs(DATA_DIR, exist_ok=True)

class TestContinuousLearningStaging(unittest.TestCase):
    def test_staging_directories_exist(self):
        self.assertTrue(os.path.exists(STAGING_DIR))
        self.assertTrue(os.path.exists(DATA_DIR))

    def test_continuous_eval_pipeline_module(self):
        eval_script_path = os.path.join(STAGING_DIR, "continuous_eval_pipeline.py")
        self.assertTrue(os.path.exists(eval_script_path))

    def test_collector_module_exists(self):
        collector_path = os.path.join(STAGING_DIR, "continuous_collector.py")
        self.assertTrue(os.path.exists(collector_path))

if __name__ == "__main__":
    unittest.main()
