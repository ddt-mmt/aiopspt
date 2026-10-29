# Grafana Dashboard Format Investigation Report

## Executive Summary
This report presents the read-only investigation into the Grafana dashboard format mismatch and Go unmarshal error (`DashboardSpec.spec.annotations of type []v2.DashboardAnnotationQueryKind`) on Grafana v13.2.3.

- **Status Decision:** **`CANDIDATE_VERIFIED_NOT_IMPORTED`** (Read-only investigation complete; zero production changes made).
- **Safety Compliance:** Production changes = 0, Service restarts = 0, Zabbix writes = 0, Direct SQL modifications = 0.

---

## 1. Dashboard Format Analysis & Unified Storage Architecture
- **Grafana v13.2.3 Architecture:** Grafana v13 uses **Unified Storage**, where dashboards are persisted in SQLite/PostgreSQL (`grafana.db` `resource` table) as Kubernetes-style custom resource documents (`kind: Dashboard`, `apiVersion: dashboard.grafana.app/v2`, `metadata`, and `spec`).
- **Root Cause of Unmarshal Error:** 
  When Grafana's importer or API processes a dashboard JSON file, it unmarshals it into a Go struct (`DashboardSpec`). 
  - If the JSON has `annotations` as a legacy dictionary object (`{ "list": [...] }`) at the root or mapped into `spec.annotations`, Go's JSON decoder throws:
    `json: cannot unmarshal object into Go struct field DashboardSpec.spec.annotations of type []v2.DashboardAnnotationQueryKind`.
  - Grafana v2 struct strictly requires `spec.annotations` to be a JSON array (`[]v2.DashboardAnnotationQueryKind`).

---

## 2. Comparison with Production Dashboards (`aiops-facility-hpc`)
Inspection of existing production dashboards stored in `grafana.db` (`aiops-facility-hpc`, `_60EMioWz`, `adsdvvn`) confirms:
1. **API Version:** `dashboard.grafana.app/v2`
2. **Top-Level Structure:** `kind`, `apiVersion`, `metadata`, `spec`, `status`.
3. **Annotations Structure (`spec.annotations`):** Stored as a JSON array (`[]`) containing `AnnotationQuery` objects:
   ```json
   "annotations": [
     {
       "kind": "AnnotationQuery",
       "spec": { ... }
     }
   ]
   ```

---

## 3. Recommendation for Dashboard Import & Format
Based on empirical inspection of Grafana v13.2.3 internal resource schemas:
- **Option B (Dashboard v2 Resource Format):** For native compatibility with Grafana v13 unified storage and API import routes, dashboards should adhere to the Dashboard v2 Custom Resource format (`kind: Dashboard`, `apiVersion: dashboard.grafana.app/v2`, `metadata`, `spec`), ensuring `spec.annotations` is formatted as an array `[]v2.DashboardAnnotationQueryKind`.
- Alternatively, when using legacy dashboard import endpoints, root-level `annotations` must be correctly formatted as an array if mapped to `spec.annotations`.

---

## 4. Next Steps & Safety Confirmation
- No production changes, container restarts, or direct database edits were performed.
- The investigation is complete, and the format requirements for Grafana v13 unified storage have been formally established.
