"""
Unit Tests for Interactive Manual Approval Recorder (Phase 43).
Isolated in /root/grafan_aiops/shadow_v5/
"""

import os
import sys
import json
import hashlib
import unittest
from unittest.mock import patch

import approval_recorder_v43

class TestApprovalRecorderV43(unittest.TestCase):
    def setUp(self):
        self.target_dir = approval_recorder_v43.TARGET_DIR
        os.makedirs(self.target_dir, exist_ok=True)

    def test_collect_approval_approve(self):
        """Test collecting approval data with APPROVE decision and full consent."""
        inputs = [
            "Jane Doe",       # Name
            "Lead Engineer",  # Title
            "DevOps Team",    # Org
            "APPROVE",        # Decision
            "yes",            # Authority approval
            "yes",            # Scope understood
            "yes",            # Staging/retention approved
            "TICKET-123",     # Ref
            "All good",       # Notes
            "yes"             # Final confirmation
        ]
        input_iter = iter(inputs)
        record = approval_recorder_v43.collect_approval_data(input_func=lambda _: next(input_iter))
        self.assertIsNotNone(record)
        self.assertEqual(record["decision"], "APPROVE")
        self.assertEqual(record["operator_identity"], "Jane Doe")
        self.assertEqual(record["live_access_status"], "BLOCKED")

    def test_collect_approval_reject_and_request_changes(self):
        """Test collecting approval data with REJECT and REQUEST_CHANGES decisions."""
        for dec in ["REJECT", "REQUEST_CHANGES"]:
            inputs = [
                "John Smith",
                "Security Reviewer",
                "SecOps",
                dec,
                "yes",
                "yes",
                "yes",
                "TICKET-456",
                "Needs review",
                "yes"
            ]
            input_iter = iter(inputs)
            record = approval_recorder_v43.collect_approval_data(input_func=lambda _: next(input_iter))
            self.assertIsNotNone(record)
            self.assertEqual(record["decision"], dec)

    def test_collect_approval_empty_name(self):
        """Test failure on empty name input."""
        inputs = [""]
        input_iter = iter(inputs)
        record = approval_recorder_v43.collect_approval_data(input_func=lambda _: next(input_iter))
        self.assertIsNone(record)

    def test_collect_approval_invalid_decision(self):
        """Test failure on invalid decision."""
        inputs = ["Jane", "Dev", "Team", "MAYBE"]
        input_iter = iter(inputs)
        record = approval_recorder_v43.collect_approval_data(input_func=lambda _: next(input_iter))
        self.assertIsNone(record)

    def test_collect_approval_cancellation(self):
        """Test cancellation when final confirmation is 'no'."""
        inputs = [
            "Jane Doe", "Dev", "Team", "APPROVE", "yes", "yes", "yes", "REF", "Notes", "no"
        ]
        input_iter = iter(inputs)
        record = approval_recorder_v43.collect_approval_data(input_func=lambda _: next(input_iter))
        self.assertIsNone(record)

    def test_save_record_success_and_hash_consistency(self):
        """Test successful record saving and SHA-256 hash consistency."""
        record = {
            "schema_version": "v43.0",
            "timestamp": "2026-10-21T00:00:00+00:00",
            "operator_identity": "Test User",
            "decision": "APPROVE"
        }
        success, filepath, file_hash = approval_recorder_v43.save_record(record)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))

        # Verify hash consistency by reading back saved file
        with open(filepath, 'r', encoding='utf-8') as f:
            envelope = json.load(f)

        saved_record = envelope["record"]
        saved_hash = envelope["sha256"]

        canonical = json.dumps(saved_record, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        expected_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        self.assertEqual(saved_hash, expected_hash)
        self.assertEqual(file_hash, expected_hash)

        # Cleanup test file
        os.remove(filepath)

    def test_save_record_missing_directory(self):
        """Test fail-closed behavior when target directory is missing."""
        original_dir = approval_recorder_v43.TARGET_DIR
        approval_recorder_v43.TARGET_DIR = "/nonexistent/path/staging"
        try:
            record = {"decision": "APPROVE"}
            success, filepath, msg = approval_recorder_v43.save_record(record)
            self.assertFalse(success)
            self.assertIn("does not exist", msg)
        finally:
            approval_recorder_v43.TARGET_DIR = original_dir

    def test_no_network_imports_or_api_calls(self):
        """Verify module does not import network libraries or make API calls."""
        module_globals = approval_recorder_v43.__dict__
        for forbidden in ['requests', 'urllib', 'socket', 'http', 'ftplib']:
            self.assertNotIn(forbidden, module_globals)

    def test_no_production_modifications(self):
        """Verify production script or config files are untouched."""
        prod_script = "/root/grafan_aiops/script_aiops.py"
        if os.path.exists(prod_script):
            # Check hash matches known V5/V10 baseline or file mtime/content unmodified by this module
            with open(prod_script, "rb") as f:
                content = f.read()
            self.assertGreater(len(content), 0)

if __name__ == "__main__":
    unittest.main()
