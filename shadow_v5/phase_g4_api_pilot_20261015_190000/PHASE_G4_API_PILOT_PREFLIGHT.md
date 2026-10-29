# Phase G4 API Pilot Preflight — AIOps Shadow v5

## 1. Metadata
- **Preparation Timestamp:** 2026-10-15T19:00:00Z
- **Staging Directory:** `/root/grafan_aiops/shadow_v5/phase_g4_api_pilot_20261015_190000/`
- **Credential Path:** `/root/.zabbix_shadow_token` (Verified permissions `600`, owner `root`).

## 2. Endpoint & Authentication Configuration
- **Endpoint URL:** `http://10.28.1.110/zabbix/api_jsonrpc.php` (Discovered from project history and configuration references).
- **Authentication Method:** JSON-RPC Bearer Token (`Authorization: Bearer <token>`) or `auth` parameter per Zabbix API specs.
- **Zabbix Version:** Enterprise Zabbix 6.x / 7.x JSON-RPC interface.

## 3. Bounded Pilot Scope
- **Request 1:** `apiinfo.version` (Connectivity & auth test).
- **Request 2:** `host.get` restricted to 7 target assets (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`, `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`) with output limited to host ID and host name.
- **Excluded Operations:** No `item.get`, `history.get`, `trend.get`, or any mutation operations (`*._create`, `*._update`, `*._delete`).
- **Request Limits:** Max 1 batch request, strict timeout (10s), zero automatic retries on failure.

## 4. Safety & Risk Controls
- Zero modification to Zabbix database, configuration, alerts, or dashboards.
- Zero credential logging or token display in console or reports.
- Strict isolation in Phase G.4 staging directory.

## 5. Status
**READY_FOR_OPERATOR_APPROVAL**
