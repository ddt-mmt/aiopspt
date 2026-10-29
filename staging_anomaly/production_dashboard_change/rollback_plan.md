# Rollback Plan for Production Dashboard Change

## Overview
This rollback plan details the steps to remove or revert the newly added AIOps dashboard (`aiops-ups-pac-anomaly-new`) without affecting any existing production dashboards, datasources, or services.

---

## 1. Rollback Steps
1. **Remove Dashboard JSON / Provisioning File:** If provisioned via file, remove the dashboard JSON file from the provisioning directory.
2. **Remove via API / DB (if imported):** If imported via Grafana API or database, delete dashboard by UID `aiops-ups-pac-anomaly-new`.
3. **Verify Existing Dashboards:** Confirm that existing dashboards (`_60EMioWz`, `aiops-facility-hpc`, `adsdvvn`) and existing datasources (`dfzsjpsghmgw0f`, `dfzvifoy1efpcb`) remain 100% untouched and operational.

---

## 2. Safety & Impact
- **Service Restarts:** 0 restarts required.
- **Downtime Risk:** None.
- **Zabbix / InfluxDB Impact:** None.
