# Zabbix Read-Only Collection Plan — Phase F

## 1. Principles & Safety Mandates
- **Read-Only API Calls Exclusively:** Only `host.get`, `item.get`, and `history.get` operations are permitted.
- **Zero Mutation:** No mutation APIs (`*._create`, `*._update`, `*._delete`) or Zabbix Sender are allowed.
- **No Credentials Storage:** API tokens and credentials must be injected via environment variables at runtime and never persisted to disk or logs.
- **Production Impact Protection:** All historical pulls must use strict batching, rate-limiting, and off-peak scheduling to prevent any performance degradation on the Zabbix database or production container.

## 2. Request Parameters & Constraints
- **Time Ranges (`time_from`, `time_till`):** Maximum pull windows of 24 hours per request batch to prevent memory pressure.
- **Object Limits:** Paginated response limits (e.g., `limit: 1000`) for item and history queries.
- **Retries & Backoff:** Exponential backoff with jitter on network timeouts.
- **Redaction:** Automatic regex-based redaction of any sensitive strings in logs or debug output.
