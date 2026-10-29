#!/usr/bin/env python3
"""Phase 45: offline-only Zabbix shadow preflight.
No network requests, no API calls, no config changes, no telemetry retrieval.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/root/grafan_aiops")
SHADOW = ROOT / "shadow_v5"
APPROVAL = SHADOW / "outputs/operator_approval_20261021_062232.json"
CANDIDATE = ROOT / "script_aiops.py.candidate.v10"
EXPECTED_CANDIDATE_SHA256 = (
    "1b3e0a046c6736d397bc2c01667ff913bae5ffb097836937f24946af4aa16bff"
)
EXPECTED_RECORDER_SHA256 = (
    "54653fec20c3467aa5876b145cc3575373038547fc57ef859a5ccce8375e7d58"
)
EXPECTED_APPROVAL_SHA256 = (
    "fb9e31ecf204e01c59b79071af6c5c4757e2594f0260594da147ae315a9f0ddf"
)
RECORDER = SHADOW / "approval_recorder_v43.py"

# Previously documented proposed items. 90706 is conditional and excluded
# unless a separate, explicit mapping confirmation can be found locally.
REQUIRED_ITEMS = {
    "59609": ("ME_UPS1", "output.load[upsHighPrecOutputLoad]", "%"),
    "59604": ("ME_UPS1", "battery.voltage[upsHighPrecBatteryActualVoltage]", "V"),
    "60386": ("ME_PAC1", "return.temp.c", "C"),
    "60387": ("ME_PAC1", "supply.temp.c", "C"),
    "60385": ("ME_PAC1", "return.humidity.rh", "%RH"),
}
CONDITIONAL_ITEM = "90706"
EXCLUDED_ITEM = "59603"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def report(label, status, detail=""):
    print(f"[{status}] {label}" + (f": {detail}" if detail else ""))

def read_approval(path):
    if not path.is_file():
        report("Operator approval file", "BLOCKED", f"not found: {path}")
        return None
    try:
        raw = path.read_bytes()
        obj = json.loads(raw)
    except Exception as e:
        report("Operator approval file", "FAIL", f"unreadable/invalid JSON ({type(e).__name__})")
        return None

    # Match the canonical JSON hash used by the recorder, excluding its hash field.
    hash_field = next(
        (k for k in ("record_sha256", "sha256", "integrity_sha256") if k in obj),
        None,
    )
    if not hash_field:
        report("Approval integrity hash", "NOT VERIFIED", "hash field not recognized")
    else:
        payload = dict(obj)
        stored_hash = str(payload.pop(hash_field))
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        calculated = hashlib.sha256(canonical).hexdigest()
        if calculated == stored_hash and stored_hash == EXPECTED_APPROVAL_SHA256:
            report("Approval integrity hash", "PASS", calculated)
        else:
            report("Approval integrity hash", "FAIL", "hash mismatch")

    # Display only non-secret approval metadata.
    decision = str(obj.get("decision", obj.get("approval", ""))).upper()
    report("Operator decision", "PASS" if decision == "APPROVE" else "BLOCKED",
           decision or "decision field not found")
    report("Operator role", "INFO", str(obj.get("role", "not recorded")))
    report("Approval timestamp", "INFO",
           str(obj.get("timestamp", obj.get("created_at", "not recorded"))))
    return obj

def main():
    print("PHASE 45 — OFFLINE READ-ONLY PREFLIGHT")
    print("Started:", datetime.now(timezone.utc).isoformat())
    print("Mode: local filesystem only; network/API calls disabled")
    print()

    failures = 0
    approval = read_approval(APPROVAL)
    print()

    if RECORDER.is_file():
        actual = sha256(RECORDER)
        status = "PASS" if actual == EXPECTED_RECORDER_SHA256 else "MISMATCH"
        report("Approval recorder SHA-256", status, actual)
        if status != "PASS":
            failures += 1
    else:
        report("Approval recorder", "BLOCKED", "file missing")
        failures += 1

    if CANDIDATE.is_file():
        actual = sha256(CANDIDATE)
        status = "PASS" if actual == EXPECTED_CANDIDATE_SHA256 else "MISMATCH"
        report("V10 candidate SHA-256", status, actual)
        if status != "PASS":
            failures += 1
    else:
        report("V10 candidate", "NOT FOUND",
               f"expected {CANDIDATE}; locate actual path before proceeding")
        failures += 1

    print()
    report("Approved core item list", "INFO",
           ", ".join(REQUIRED_ITEMS.keys()))
    report("Conditional item 90706", "EXCLUDED",
           "include only after mapping is explicitly confirmed")
    report("Item 59603", "EXCLUDED",
           "previously reported disabled / SNMP noSuchName")
    report("History retrieval", "NOT RUN", "no Zabbix API calls made")
    report("Effective API permissions", "NOT VERIFIED",
           "requires authoritative local evidence; credentials are not tested")
    report("Output retention approval", "NOT VERIFIED",
           "operator approval alone does not prove a retention policy was approved")
    report("Network activity", "NONE", "this script contains no network client")

    # Search local text files for mapping references only. Never print file contents
    # that may contain tokens, passwords, or other credentials.
    print()
    evidence_roots = [
        ROOT / "shadow_v5",
        Path("/tmp/aiops_staging_v8"),
    ]
    patterns = {
        "90706": re.compile(r"\b90706\b"),
        "59603": re.compile(r"\b59603\b"),
        "core item IDs": re.compile(r"\b(59609|59604|60386|60387|60385)\b"),
    }
    hits = {k: 0 for k in patterns}
    scanned = 0
    for base in evidence_roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.is_symlink():
                continue
            if p.suffix.lower() not in {".csv", ".md", ".txt", ".json"}:
                continue
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                content = p.read_text(errors="ignore")
            except OSError:
                continue
            scanned += 1
            for name, pattern in patterns.items():
                if pattern.search(content):
                    hits[name] += 1
    report("Local evidence scan", "INFO",
           f"{scanned} text files scanned; file counts only, no contents printed")
    for name, count in hits.items():
        report(f"Evidence references: {name}", "INFO", f"{count} files")

    print()
    if approval is None:
        failures += 1
    if failures:
        report("FINAL STATUS", "BLOCKED",
               f"{failures} critical local checks failed; do not retrieve history")
        return 2

    report("FINAL STATUS", "OFFLINE PREFLIGHT ONLY",
           "not authorization to call Zabbix API or begin telemetry collection")
    return 0

if __name__ == "__main__":
    sys.exit(main())
