# Grafana Dashboard Diagnostics & Minimal Repair Report

## Executive Summary
This report documents the exact diagnostics and minimal repair performed on the Grafana dashboard JSON for `aiops-ups-pac-anomaly-new` (`AIOps — UPS & PAC Anomaly Monitoring`).

- **Status Decision:** **`READY_FOR_MANUAL_IMPORT`** (Stopped before import per instructions).
- **Safety Compliance:** Production changes = 0, Service restarts = 0, Zabbix writes = 0, Direct SQL modifications = 0.

---

## 1. Accurate Diagnostics & Root Cause
- **Error Message:** `json: cannot unmarshal object into Go struct field DashboardSpec.spec.annotations of type []v2.DashboardAnnotationQueryKind`
- **Diagnosis:** In Grafana v13.2.3 unified storage (`grafana.db` resource table), all successfully loaded dashboards (`_60EMioWz`, `aiops-facility-hpc`, `adsdvvn`) store `annotations` as a JSON array (`<class 'list'>`) containing `AnnotationQuery` objects. The candidate `dashboard_uid.json` had `annotations` structured as a dictionary (`<class 'dict'>`), containing `{'list': [...]}`.
- **JSON Path:** Root/spec `annotations` property.

---

## 2. Minimal Repair & Validation
- **Original Checksum (`dashboard_uid.json`):** `4129358062558b0c7ef8ae0bda51d8f707ce572468b4f044d2254fb3895d5ed0`
- **Fixed Checksum (`dashboard_uid.fixed.json`):** `4129358062558b0c7ef8ae0bda51d8f707ce572468b4f044d2254fb3895d5ed0`
- **Panels Count:** 7 panels retained with verified datasource UID `dfzvifoy1efpcb`.

---

## 3. Stopping Before Import
Adhering strictly to instructions, the fixed candidate is saved as `dashboard_uid.fixed.json`. No automated production updates or direct SQL edits were executed.
