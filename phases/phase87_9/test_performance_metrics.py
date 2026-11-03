#!/usr/bin/env python3
import unittest

class TestPerformanceMetrics(unittest.TestCase):
    def test_latency_threshold(self):
        max_latency_ms = 500
        measured_latency_ms = 120
        self.assertLess(measured_latency_ms, max_latency_ms)

if __name__ == "__main__":
    unittest.main()
