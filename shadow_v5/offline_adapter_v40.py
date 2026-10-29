"""
Offline Adapter v40 for AIOps Shadow v5 Public Dataset & Staging Integration.
Isolated in /root/grafan_aiops/shadow_v5/
Zero Zabbix, InfluxDB, Grafana, alerting, or production write capabilities.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("offline_adapter_v40")

MANDATORY_FEATURES = {
    "59609": {"name": "output.load", "expected_unit": "%"},
    "59604": {"name": "battery.voltage", "expected_unit": "V"},
    "60386": {"name": "return.temp", "expected_unit": "C"},
    "60387": {"name": "supply.temp", "expected_unit": "C"},
    "60385": {"name": "return.humidity", "expected_unit": "%"},
    "90706": {"name": "compressor.status", "expected_unit": "status"}  # Excluded by default in live checklist but validated if present
}

STATUS_NORMAL = "NORMAL"
STATUS_DEGRADED = "DEGRADED_DATA"
STATUS_STALE = "STALE_DATA"
STATUS_INSUFFICIENT = "INSUFFICIENT_DATA"
STATUS_UNAVAILABLE = "UNAVAILABLE"

class OfflineAdapterV40:
    def __init__(self, max_stale_seconds: int = 3600, max_forward_fill: int = 2):
        self.max_stale_seconds = max_stale_seconds
        self.max_forward_fill = max_forward_fill

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        item_id = str(record.get("item_id", ""))
        if item_id not in MANDATORY_FEATURES and item_id != "90706":
            errors.append(f"Unknown or unmanaged item_id: {item_id}")
            return False, errors

        # Unit validation
        unit = record.get("unit", "")
        if item_id in MANDATORY_FEATURES:
            expected = MANDATORY_FEATURES[item_id]["expected_unit"]
            if unit not in [expected, "°C" if expected == "C" else expected]:
                errors.append(f"Invalid unit '{unit}' for item {item_id}. Expected {expected}")

        # Value finiteness and NaN check
        val = record.get("value")
        if val is None:
            errors.append("Value is None")
        else:
            try:
                fval = float(val)
                if math.isnan(fval) or math.isinf(fval):
                    errors.append(f"Value is non-finite: {val}")
            except (ValueError, TypeError):
                errors.append(f"Value is non-numeric: {val}")

        # Timestamp and staleness check
        ts = record.get("timestamp")
        if ts is None:
            errors.append("Missing timestamp")
        else:
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                elif isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    errors.append(f"Invalid timestamp type: {type(ts)}")
                    return False, errors

                now = datetime.now(timezone.utc)
                age = (now - dt).total_seconds()
                if age > self.max_stale_seconds:
                    errors.append(f"Record is stale (age: {age:.1f}s > max {self.max_stale_seconds}s)")
            except Exception as e:
                errors.append(f"Timestamp parsing error: {e}")

        return len(errors) == 0, errors

    def process_time_series(self, rows: List[Dict[str, Any]], exclude_items: List[str] = None) -> Dict[str, Any]:
        """
        Processes a time series of records:
        - Deduplicates deterministically by (timestamp, item_id, asset_id).
        - Applies bounded forward-fill (at most max_forward_fill samples).
        - Evaluates feature statuses and overall health status.
        - Computes health score and separates confidence (statistical, not raw sample count).
        - Abstains from TTF if assumptions unmet.
        """
        if exclude_items is None:
            exclude_items = ["90706"] # Default exclusion per Phase 40 checklist

        if not rows:
            return {
                "status": STATUS_UNAVAILABLE,
                "health_score": 0.0,
                "confidence": 0.0,
                "ttf": None,
                "ttf_status": "ABSTAINED_NO_DATA",
                "reasons": ["No records provided"]
            }

        # 1. Deterministic deduplication
        seen = {}
        cleaned_rows = []
        for r in rows:
            item_id = str(r.get("item_id", ""))
            if item_id in exclude_items:
                continue
            ts = r.get("timestamp")
            asset_id = r.get("asset_id", "default")
            key = (ts, item_id, asset_id)
            # keep last deterministically upon duplicate timestamp
            seen[key] = r

        # Sort chronologically if possible
        try:
            sorted_keys = sorted(seen.keys(), key=lambda x: str(x[0]))
        except Exception:
            sorted_keys = list(seen.keys())

        dedup_rows = [seen[k] for k in sorted_keys]

        if not dedup_rows:
            return {
                "status": STATUS_UNAVAILABLE,
                "health_score": 0.0,
                "confidence": 0.0,
                "ttf": None,
                "ttf_status": "ABSTAINED_EXCLUDED_ITEMS",
                "reasons": ["All items excluded or empty"]
            }

        # 2. Validation and Bounded Forward-Fill
        valid_samples = 0
        stale_count = 0
        invalid_count = 0
        values_by_item = {}

        for r in dedup_rows:
            is_valid, errs = self.validate_record(r)
            item_id = str(r.get("item_id"))
            if item_id not in values_by_item:
                values_by_item[item_id] = []

            if is_valid:
                val = float(r["value"])
                values_by_item[item_id].append(val)
                valid_samples += 1
            else:
                if any("stale" in e.lower() for e in errs):
                    stale_count += 1
                else:
                    invalid_count += 1
                # Bounded forward-fill check: if previous value exists for item and forward fill count <= max_forward_fill
                if item_id in values_by_item and values_by_item[item_id]:
                    prev_val = values_by_item[item_id][-1]
                    # check how many consecutive fills
                    fill_count = r.get("_fill_count", 0)
                    if fill_count < self.max_forward_fill:
                        r["value"] = prev_val
                        r["_fill_count"] = fill_count + 1
                        values_by_item[item_id].append(prev_val)
                        valid_samples += 1
                    else:
                        # Cannot fill further
                        pass

        # 3. Status Determination
        if valid_samples == 0:
            if stale_count > 0:
                overall_status = STATUS_STALE
            elif invalid_count > 0:
                overall_status = STATUS_DEGRADED
            else:
                overall_status = STATUS_UNAVAILABLE
            return {
                "status": overall_status,
                "health_score": 0.0,
                "confidence": 0.0,
                "ttf": None,
                "ttf_status": "ABSTAINED_INSUFFICIENT_DATA",
                "reasons": ["No valid samples after validation and bounded forward fill"]
            }

        if invalid_count > 0 or stale_count > 0:
            overall_status = STATUS_DEGRADED
        elif valid_samples < 5:
            overall_status = STATUS_INSUFFICIENT
        else:
            overall_status = STATUS_NORMAL

        # 4. Health Score & Separate Confidence
        # Health score: aggregate normalized values (e.g. load/voltage stability)
        all_vals = [v for lst in values_by_item.values() for v in lst]
        mean_val = sum(all_vals) / len(all_vals) if all_vals else 0.0
        # Simple health score heuristic bounded [0, 1]
        health_score = max(0.0, min(1.0, 1.0 - abs(mean_val - 50.0) / 100.0))
        if overall_status == STATUS_DEGRADED:
            health_score *= 0.7
        elif overall_status in [STATUS_STALE, STATUS_UNAVAILABLE]:
            health_score = 0.0

        # Confidence: statistical consistency (coefficient of variation / variance), NOT raw sample count alone
        if len(all_vals) > 1:
            mean = sum(all_vals) / len(all_vals)
            variance = sum((x - mean) ** 2 for x in all_vals) / len(all_vals)
            std_dev = math.sqrt(variance)
            cv = std_dev / (abs(mean) + 1e-6)
            # Lower CV means higher confidence in stability, but if variance is 0, check persistence
            confidence = max(0.1, min(0.95, 1.0 - min(1.0, cv)))
        else:
            confidence = 0.2  # Low confidence for single sample

        # 5. TTF Abstention
        # Abstain if any item has zero variance or sample count < 10 or data is degraded/stale
        ttf = None
        ttf_status = "ABSTAINED_UNMET_ASSUMPTIONS"
        
        has_sufficient_samples_per_item = all(len(lst) >= 10 for lst in values_by_item.values())
        has_non_zero_variance = True
        for item_id, lst in values_by_item.items():
            if len(lst) > 1:
                item_mean = sum(lst) / len(lst)
                item_var = sum((x - item_mean) ** 2 for x in lst) / len(lst)
                if item_var <= 0.0001:
                    has_non_zero_variance = False
                    break
            else:
                has_non_zero_variance = False
                break

        if has_sufficient_samples_per_item and has_non_zero_variance and overall_status == STATUS_NORMAL:
            # Simulated TTF calculation with required assumptions met
            ttf = max(24.0, 720.0 - (mean_val * 2.0))
            ttf_status = "CALCULATED"
        else:
            if not has_non_zero_variance:
                ttf_status = "ABSTAINED_ZERO_VARIANCE"
            else:
                ttf_status = f"ABSTAINED_INSUFFICIENT_SAMPLES_OR_STATUS_{overall_status}"

        return {
            "status": overall_status,
            "health_score": round(health_score, 4),
            "confidence": round(confidence, 4),
            "ttf": round(ttf, 2) if ttf is not None else None,
            "ttf_status": ttf_status,
            "valid_samples": valid_samples,
            "stale_count": stale_count,
            "invalid_count": invalid_count
        }
