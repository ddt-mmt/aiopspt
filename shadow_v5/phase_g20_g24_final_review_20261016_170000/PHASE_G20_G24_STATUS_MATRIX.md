# Phase G.20–G.24 Status Matrix

| Stage & Activity | Reported Status | Available Evidence | Required Evidence / Gaps | Risks / Dependencies | Next Approval Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **G.20.1: Host Identity & Endpoint (`10.28.1.110`)** | `[x]` Reported Complete | Read-only socket/network inspections | Final operator confirmation of IP mapping | IP changes could invalidate SAN | Design & IP Sign-off |
| **G.20.2: AIOps Service & Owner Identification** | `[ ]` Pending | Container inventory logs (`aiops_predictor_hpc`, `zabbix_server`) | Formal ownership documentation | Service overlap or port collision | Operator Confirmation |
| **G.20.3: Listener & Reverse Proxy Inventory** | `[ ]` Pending | Read-only netstat/ss/docker ps logs | Active Nginx reverse proxy mapping | Unmanaged port bindings | Inventory Verification |
| **G.21.1: CA Key Storage & Access** | `[x]` Reported Complete | Security architecture guidelines | Secure offline key storage setup | Unauthorized key access | Admin Key Provisioning |
| **G.21.2: Crypto Algorithms & Lifecycle** | `[ ]` Pending | Standard cryptographic best practices | Specific validity period & cipher suites | Weak crypto parameters | Policy Approval |
| **G.21.3: Trust Anchor Distribution** | `[ ]` Pending | Conceptual distribution model | Client trust store deployment plan | Untrusted certificate warnings | Distribution Sign-off |
| **G.22.1: SAN & Identity Review** | `[ ]` Pending | Target endpoint IP `10.28.1.110` identified | Exact SAN list verification | SAN mismatch on IP connection | SAN Approval |
| **G.22.2: Certificate Issuance Approval** | `[x]` Reported Complete | Operator-reported approval status | Formal signed authorization record | Premature execution risk | Issuance Sign-off |
| **G.22.3: Backup & Recovery Procedures** | `[ ]` Pending | Standard backup policies | CA backup & key recovery verification | Permanent CA loss | Backup Verification |
| **G.23.1: Port 443 HTTPS Configuration** | `[x]` Reported Complete | Stored proxy template (`/root/nginx.conf.proxy`) | Active configuration staging | Port conflict on 443 | Config Staging Approval |
| **G.23.2: Deployment Method & Schedule** | `[ ]` Pending | Additive deployment strategy | Change window calendar | Production disruption risk | Schedule Approval |
| **G.23.3: Rollback & Abort Criteria** | `[x]` Reported Complete | Rollback plan documentation | Tested rollback drill verification | Failed rollback recovery | Rollback Sign-off |
| **G.24.1: Token-Free HTTPS Validation** | `[x]` Reported Complete | Test methodology planned | Execution log and curl output | False positive verification | Post-Deployment Test Sign-off |
| **G.24.2: Existing Service Verification** | `[x]` Reported Complete | Service port inventory | Live health check confirmation | Monitoring outage | Service Health Sign-off |
| **G.24.3: Final Audit Logging** | `[x]` Reported Complete | Audit JSON and phase reports | Independent security review | Incomplete audit trail | Final Audit Sign-off |
