# Phase G.38 — Production Transition & Change Plan

## Overview
This document outlines the formal transition and change plan for moving the validated AIOps anomaly detection pipeline from staging to production, subject to formal authorization and review.

---

## 1. Components to Add vs. Unchanged Production Components
- **Components to Add (in a separate production-safe container/service):**
  - Production-hardened detector execution wrapper (read-only Zabbix API consumer).
  - Dedicated staging/production database or metrics schema for anomaly logs.
  - Isolated Grafana dashboard import (`staging_facility_dashboard.json` adapted with production datasource UIDs).
- **Unchanged Production Components:**
  - Existing Zabbix server, Zabbix database, Telegraf, InfluxDB, and proxy containers.
  - Production `script_aiops.py` and `aiops_predictor_hpc` container (left untouched).
  - Network routing, firewall rules, and DNS configurations.

---

## 2. Data Flow Architecture
1. **Read-Only Telemetry Ingestion:** Scheduled cron or lightweight worker queries historical/recent telemetry from Zabbix API via read-only token.
2. **Offline/Near-Real-Time Analysis:** `staging_detector.py` logic processes metrics in isolated memory space.
3. **Storage & Visualization:** Results written exclusively to dedicated anomaly log tables/files, visualized via Grafana staging/production dashboards without modifying Zabbix triggers or item history.

---

## 3. Resource, Permissions, Datasource, and Network Requirements
- **Permissions:** Read-only API access to Zabbix history; read-only access to source CSV exports.
- **Datasources:** Dedicated PostgreSQL or JSON datasource for Grafana anomaly panels.
- **Network:** Zero inbound firewall changes; outbound read-only HTTPS to Zabbix API.

---

## 4. Risks and Service Impact
- **Service Impact:** Zero downtime risk as execution is asynchronous and read-only.
- **Alert Fatigue Risk:** Mitigated by strict Robust Z-score thresholds (3.5) and clear operator disclaimers separating statistical anomalies from physical hardware faults.

---

## 5. Implementation, Verification, and Rollback Steps
1. **Implementation:** Deploy containerized anomaly worker with read-only credentials.
2. **Verification:** Run dry-run validation script comparing output checksums against staging baselines.
3. **Rollback:** Stop worker container and drop dedicated anomaly schema/tables. Production service remains 100% operational.

---

## 6. Acceptance Criteria & Monitoring
- 100% test pass rate on telemetry parsing and anomaly detection.
- Zero errors in production container logs.
- Continuous monitoring of detector execution times and memory usage.

---

## 7. Approval Gate
- **Status:** `NOT_AUTHORIZED` until formal review and sign-off by operations leadership.
