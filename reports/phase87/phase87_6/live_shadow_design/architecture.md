# Future Staging Live-Shadow Design — Phase 87.6

## 1. Overview
This document specifies the architecture for running a read-only live-shadow test of V12 against staging Zabbix telemetry without affecting production or raw sensor measurements.

## 2. Core Principles
- **Read-Only Access:** V12 polls staging Zabbix API using dedicated read-only credentials stored outside Git.
- **Derived Metric Isolation:** Any predicted health scores or anomaly indices are written exclusively to isolated staging custom metric items (`aiops.v12.health_score`), never touching raw sensor items.
- **Freshness Validation:** Stale or missing telemetry triggers graceful degradation warnings rather than fabricated synthetic fallbacks.
