# AIOps Shadow v5 — Official Public Dataset Expansion Report

## Executive Summary
This report documents the inventory, controlled acquisition design, canonical schema adapters, and offline test validation for the **AIOps Shadow v5 Official Public Dataset Expansion**. All activities and artifacts are strictly isolated within `/root/grafan_aiops/shadow_v5/`. Zero Zabbix queries, database writes, or production alterations were performed.

## 1. Dataset Catalog & Inventory (Stage A)
Four primary official repositories were inventoried and cataloged in `PUBLIC_DATASET_CATALOG.md`:
1. **LBNL Fault Detection and Diagnostics (LBNL FDD):** HVAC/AHU/Chiller anomaly detection (`https://faultdetection.lbl.gov/data/`).
2. **NASA Prognostics Center of Excellence (PCoE) — Li-ion Battery:** UPS and battery health/RUL prognosis (`https://www.nasa.gov/.../pcoe/pcoe-data-set-repository/`).
3. **NASA Health Monitoring and Prognostics for Computer Servers:** Server telemetry and component health (`https://data.nasa.gov/...`).
4. **ASHRAE Data Repository:** Building energy and thermal benchmarks (`https://data.ashrae.org/`).

*Note:* All unknown or unverified attributes (exact file sizes, checksums prior to live download, license strings) are explicitly marked as `NOT VERIFIED` in accordance with safety directives.

## 2. Controlled Acquisition & Provenance (Stage B)
- **Script:** `run_public_dataset_acquisition.py`
- **Manifest:** `PUBLIC_DATASET_ACQUISITION_MANIFEST.json`
- **Security Controls:**
  - Domain allowlisting (`faultdetection.lbl.gov`, `nasa.gov`, `ashrae.org`).
  - HTTPS-only transport enforcement.
  - SHA-256 integrity calculation and manifest recording.
  - Temporary staging and path traversal prevention.

## 3. Canonical Data Schema & Adapters (Stage C)
- **Module:** `dataset_adapters.py`
- **Mandatory Fields:** `source_id`, `dataset_id`, `asset_type`, `asset_id`, `timestamp`, `metric_name`, `value`, `unit`, `quality_status`, `label`, `label_source`, `split`, `provenance`.
- **Quality Statuses Supported:** `normal`, `faulted`, `anomaly_unlabeled`, `missing`, `stale`, `nonnumeric`, `invalid`.
- **Separation:** Raw data and transformed canonical records are cleanly separated.

## 4. Offline Benchmark & Test Results (Stage D)
- **Test Suite:** `test_public_dataset_expansion.py`
- **Execution Results:**
  - `test_domain_allowlist`: PASSED (Correctly permits official domains, blocks malicious/external domains).
  - `test_canonical_schema_validation`: PASSED (Validates schema compliance and quality statuses).
  - `test_manifest_generation`: PASSED (Produces compliant acquisition manifests).
  - `test_path_traversal_prevention`: PASSED (Protects archive extraction against path traversal).

## 5. Transfer Limitations & Risks
- Public laboratory or simulation datasets may have different operating profiles, sensor distributions, and control loop dynamics compared to live enterprise data center infrastructure (Zabbix telemetry).
- Public dataset metrics serve as robust offline algorithmic testbeds for anomaly detection and RUL estimation, but do not replace production validation.

## Final Decision
**READY FOR OFFLINE BENCHMARK**
