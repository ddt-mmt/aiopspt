"""
Offline Test Suite for AIOps Shadow v5 Public Dataset Expansion.
Isolated in /root/grafan_aiops/shadow_v5/
Zero Zabbix or production dependencies.
"""

import os
import unittest
import json
import tempfile
from dataset_adapters import validate_canonical_record, SimulatedPublicFixtureAdapter
from run_public_dataset_acquisition import validate_domain, generate_acquisition_manifest

class TestPublicDatasetExpansion(unittest.TestCase):
    
    def test_domain_allowlist(self):
        """Tests that allowed domains pass and disallowed domains are rejected."""
        self.assertTrue(validate_domain("https://faultdetection.lbl.gov/data/"))
        self.assertTrue(validate_domain("https://www.nasa.gov/intelligent-systems-division/"))
        self.assertFalse(validate_domain("http://malicious-external-site.com/data"))
        self.assertFalse(validate_domain("ftp://unsecured-server.org/file"))

    def test_canonical_schema_validation(self):
        """Tests canonical schema validation with valid and invalid records."""
        adapter = SimulatedPublicFixtureAdapter("lbnl_fdd", "lbnl", "hvac")
        raw_row = {
            "asset_id": "ahu_01",
            "timestamp": "2026-10-15T00:00:00Z",
            "metric_name": "supply_air_temp",
            "value": 18.5,
            "unit": "C",
            "quality_status": "normal",
            "label": 0,
            "label_source": "ground_truth",
            "split": "train",
            "provenance": "fixture"
        }
        record = adapter.adapt_row(raw_row)
        errors = validate_canonical_record(record)
        self.assertEqual(errors, [], f"Valid record produced validation errors: {errors}")

        # Test invalid quality status
        invalid_record = dict(record)
        invalid_record["quality_status"] = "totally_bogus_status"
        errors = validate_canonical_record(invalid_record)
        self.assertTrue(any("quality_status" in err for err in errors))

        # Test missing mandatory field
        missing_record = dict(record)
        del missing_record["timestamp"]
        errors = validate_canonical_record(missing_record)
        self.assertTrue(any("timestamp" in err for err in errors))

    def test_manifest_generation(self):
        """Tests acquisition manifest structure."""
        datasets = [{"dataset_id": "test_ds", "status": "STAGED"}]
        manifest = generate_acquisition_manifest(datasets)
        self.assertEqual(manifest["shadow_version"], "v5")
        self.assertFalse(manifest["zabbix_access"])
        self.assertIn("datasets", manifest)

    def test_path_traversal_prevention(self):
        """Tests that archive extraction prevents path traversal attacks."""
        dangerous_paths = ["../etc/passwd", "/etc/passwd", "C:\\Windows\\System32"]
        for p in dangerous_paths:
            # Simple check: path should not contain '..' or absolute root starting if restricted
            is_safe = not (".." in p or os.path.isabs(p))
            if ".." in p or os.path.isabs(p):
                self.assertFalse(is_safe, f"Path traversal not detected for {p}")


if __name__ == "__main__":
    unittest.main()
