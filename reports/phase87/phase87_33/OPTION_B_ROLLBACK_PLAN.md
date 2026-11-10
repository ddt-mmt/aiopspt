# OPTION B ROLLBACK PLAN

## Rollback Triggers
- Any unexpected write traffic detected towards Zabbix.
- Resource contention affecting production host performance.
- Persistent runtime exceptions in V12 shadow container.

## Rollback Execution Steps
1. Stop the shadow container immediately:
   ```bash
   docker stop aiops_v12_shadow
   docker rm aiops_v12_shadow
   ```
2. Revoke read-only Zabbix API token in Zabbix administration panel.
3. Archive shadow logs for forensic analysis.
4. Verify production V11 `aiops_predictor_hpc` is operating normally without interruption.
