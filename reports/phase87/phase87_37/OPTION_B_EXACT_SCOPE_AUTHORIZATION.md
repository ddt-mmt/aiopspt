# OPTION B EXACT SCOPE AUTHORIZATION

## 1. Authorized Scope
`OPTION_B_PRODUCTION_READ_ONLY_SHADOW`

### Permitted Activities
- Independent V12 read-only shadow operation.
- Read-only telemetry polling within approved allowlist (`ME_UPS1-3`, `ME_PAC1-4`).
- Independent V12 computation, anomaly scoring, and health evaluation.
- Isolated shadow output logging.

### Prohibited Activities
- Production V11 modification or replacement.
- Zabbix write operations or derived item creation (`zabbix_sender`).
- Production Grafana dashboard modification.
- Production database writes.
- Online model promotion or actuation.
- Physical equipment control.
