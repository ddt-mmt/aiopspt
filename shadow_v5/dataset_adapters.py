"""
Canonical Data Schema & Adapters for AIOps Shadow v5 Public Dataset Expansion.
Isolated in /root/grafan_aiops/shadow_v5/
Zero Zabbix or production dependencies.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

CANONICAL_SCHEMA_FIELDS = [
    "source_id",
    "dataset_id",
    "asset_type",
    "asset_id",
    "timestamp",
    "metric_name",
    "value",
    "unit",
    "quality_status",
    "label",
    "label_source",
    "split",
    "provenance"
]

VALID_QUALITY_STATUSES = {
    "normal",
    "faulted",
    "anomaly_unlabeled",
    "missing",
    "stale",
    "nonnumeric",
    "invalid"
}

def validate_canonical_record(record: Dict[str, Any]) -> List[str]:
    """Validates a record against the canonical schema and rules."""
    errors = []
    for field in CANONICAL_SCHEMA_FIELDS:
        if field not in record:
            errors.append(f"Missing mandatory field: {field}")
            
    q_status = record.get("quality_status")
    if q_status not in VALID_QUALITY_STATUSES:
        errors.append(f"Invalid quality_status '{q_status}'. Must be one of {VALID_QUALITY_STATUSES}")
        
    value = record.get("value")
    if q_status in ["normal", "faulted", "anomaly_unlabeled"]:
        if value is None:
            errors.append("Value cannot be None for valid data points")
        elif not isinstance(value, (int, float)):
            errors.append(f"Value must be numeric for valid data points, got {type(value)}")
            
    return errors


class BaseDatasetAdapter:
    """Base class for public dataset canonical adapters."""
    def __init__(self, dataset_id: str, source_id: str, asset_type: str):
        self.dataset_id = dataset_id
        self.source_id = source_id
        self.asset_type = asset_type

    def adapt_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement adapt_row")


class SimulatedPublicFixtureAdapter(BaseDatasetAdapter):
    """Adapter for offline testing and fixture generation without external network calls."""
    def adapt_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "source_id": self.source_id,
            "dataset_id": self.dataset_id,
            "asset_type": self.asset_type,
            "asset_id": raw_row.get("asset_id", "fixture_asset_01"),
            "timestamp": raw_row.get("timestamp", datetime.utcnow().isoformat()),
            "metric_name": raw_row.get("metric_name", "temperature_c"),
            "value": raw_row.get("value", 25.0),
            "unit": raw_row.get("unit", "C"),
            "quality_status": raw_row.get("quality_status", "normal"),
            "label": raw_row.get("label", 0),
            "label_source": raw_row.get("label_source", "ground_truth_fixture"),
            "split": raw_row.get("split", "train"),
            "provenance": raw_row.get("provenance", "fixture_generated")
        }
        return record
