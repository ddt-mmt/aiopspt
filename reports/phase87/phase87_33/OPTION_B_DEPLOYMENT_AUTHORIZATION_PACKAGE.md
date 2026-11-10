# OPTION B DEPLOYMENT AUTHORIZATION PACKAGE

## A. Change Description
- **Title:** Option B Production Read-Only Shadow Deployment
- **Change Owner:** Didit (System Administrator)
- **Technical Lead:** AIOps Engineering Team
- **Scope:** Standalone V12 runtime consuming Zabbix telemetry in read-only shadow mode.

## B. Technical Architecture
- Isolated container deployment (`aiops_v12_shadow`).
- Read-only API polling via HTTP (`http://10.28.1.110/zabbix`).
- Local model execution for `ME_UPS1-3` and `ME_PAC1-4`.
- Independent logging to `/root/grafan_aiops/logs/shadow/`.

## C. Risk & Impact Assessment
- **Production V11:** Unaffected.
- **Zabbix Production:** Read-only access; zero write operations.
- **Grafana Production:** Unchanged.
- **Security:** Governed by network segmentation and security exception request.

## D. Implementation Plan Draft
1. Build standalone V12 runtime container image.
2. Configure read-only API endpoint and token via secure env variables.
3. Start container in shadow observation mode.
4. Monitor telemetry ingestion health.

## E. Validation Plan
- Verify API responsiveness and metric freshness (60s interval).
- Validate anomaly score calculations against baseline test fixtures.
- Ensure zero outbound write requests to Zabbix.

## F. Rollback Plan
- Stop and remove shadow container: `docker stop aiops_v12_shadow`.
- Revoke read-only API token.
- Confirm production V11 continues uninterrupted.

## G. Monitoring & Support
- Monitored via local log inspection and shadow dashboard views.
- Escalation path: AIOps Engineering Team -> System Administrator.
