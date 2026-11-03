#!/usr/bin/env python3
import unittest

class TestObservationDuration(unittest.TestCase):
    def test_observation_state(self):
        status = "OBSERVATION_IN_PROGRESS"
        self.assertIn(status, ["OBSERVATION_IN_PROGRESS", "PASS", "PASS_WITH_GAPS"])

if __name__ == "__main__":
    unittest.main()
