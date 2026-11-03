#!/usr/bin/env python3
import unittest
import os
import json

class TestLocalStorage(unittest.TestCase):
    def test_local_storage_permissions_and_json(self):
        test_dir = "/tmp/aiops_phase87_7/inference/results"
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test_output.json")
        data = {"status": "TEST_PASS", "host": "ME_UPS1"}
        with open(test_file, "w") as f:
            json.dump(data, f)
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["status"], "TEST_PASS")

if __name__ == "__main__":
    unittest.main()
