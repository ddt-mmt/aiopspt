# Ground Truth Labeling Rules (`ground_truth_labeling_rules.md`)

## Overview
This document defines the transparent labeling rules for Zabbix historical events extracted for the AIOps UPS/PAC project (Phase G.27).

## Label Definitions
1. **`EVENT_CONFIRMED_BY_ZABBIX`**: Standard alarm event recorded by Zabbix with sufficient metadata and normal recovery.
2. **`RECOVERED_EVENT`**: Event that has a paired recovery timestamp (`r_clock > 0`).
3. **`ACTIVE_EVENT`**: Event that remains active at the conclusion of the observation period.
4. **`TRANSIENT_EVENT_CANDIDATE`**: Short-duration event (< 300 seconds) that quickly recovered; requires filtering or special handling in ML training.
5. **`COMMUNICATION_EVENT`**: Connectivity/agent availability failure. **Not** automatically treated as physical hardware failure.
6. **`SENSOR_OR_DATA_QUALITY_EVENT`**: Measurement or data quality issue (e.g. invalid SNMP OID/sensor reading).
7. **`UNKNOWN_NEEDS_REVIEW`**: Insufficient trigger metadata to classify automatically.
8. **`MAINTENANCE_CONFIRMED`**: Reserved strictly for events verified by external maintenance logs (none assumed by default).

## Methodological Guardrails
- Severity level alone is not proof of physical equipment failure.
- Communication failures are separated from mechanical/electrical failures.
- Only sensor features prior to event timestamp (`clock`) are used for predictive modeling to prevent data leakage.
