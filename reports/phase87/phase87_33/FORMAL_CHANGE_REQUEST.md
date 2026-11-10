# FORMAL CHANGE REQUEST: OPTION B PRODUCTION READ-ONLY SHADOW

## Change Identification
- **Change ID:** CR-AIOPS-V12-OPTION-B-001
- **Change Title:** AIOps V12 Production Read-Only Shadow Deployment (Option B)
- **Requested By:** Didit (System Administrator / Project Owner)
- **Date:** November 10, 2026
- **Target Architecture:** Option B (Independent Read-Only Shadow Execution)

## 1. Description of Change
Deploy the AIOps V12 standalone runtime container in staging/shadow mode to consume telemetry data from the production Zabbix server (`http://10.28.1.110/zabbix`) in strict read-only mode. The runtime will execute predictive models (`ME_UPS1-3`, `ME_PAC1-4`), generate shadow prediction outputs, and record anomaly and health scores in isolated log files and shadow storage without writing back to Zabbix or interacting with production V11 (`aiops_predictor_hpc`).

## 2. Business Justification
Enable empirical evaluation of V12 multi-horizon intelligence, device behavioral learning, and RUL degradation estimation against live production data streams without introducing any risk to active monitoring, alerting, or control systems.

## 3. In-Scope Items
- Standalone V12 runtime container deployment in isolated network namespace.
- Read-only API polling of Zabbix metrics.
- Independent anomaly detection, degradation scoring, and shadow prediction generation.
- Isolated log storage and shadow evidence export.

## 4. Out-of-Scope Items (Strictly Prohibited)
- Modification or replacement of production V11 `aiops_predictor_hpc`.
- Writing metrics, events, or derived items back to Zabbix via API or `zabbix_sender`.
- Modification of production Grafana dashboards or data sources.
- Execution of online learning or automatic model promotion.
- Transmission of control commands to UPS or PAC units.

## 5. Risk Assessment & Mitigations
- **Network / API Load:** Minimized via conservative polling intervals (60s).
- **Data Integrity:** Protected by read-only API tokens and network segmentation.
- **Production Interference:** Prevented by complete isolation of V12 runtime storage and lack of write credentials.

## 6. Rollback Plan
Immediate termination of the V12 shadow container process and revocation of read-only API credentials. Production V11 remains untouched and unaffected at all times.
