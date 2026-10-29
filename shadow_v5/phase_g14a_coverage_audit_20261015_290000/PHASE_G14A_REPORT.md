# Phase G.14A Offline Coverage Audit Report

## 1. Metadata
- **Audit Timestamp:** 2026-10-15T05:19:41.571136
- **Staging Directory:** `/root/grafan_aiops/shadow_v5/phase_g14a_coverage_audit_20261015_290000`
- **Final Status:** `COVERAGE_AUDIT_COMPLETED`

## 2. Host Coverage Analysis
- **Finding:** Phase G.14 execution plan currently targets only host `10688` (`ME_UPS1`). The remaining 6 facility assets (`ME_UPS2`, `ME_UPS3`, `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`) are unrepresented in the immediate 24-hour expansion plan.
- **Per-Host Item Breakdown:**

- **ME_UPS1 (Host ID 10688):** Total Items = 48, Priority Numeric Items = 23

- **ME_PAC1 (Host ID 10689):** Total Items = 43, Priority Numeric Items = 6

- **ME_PAC2 (Host ID 10690):** Total Items = 17, Priority Numeric Items = 6

- **ME_PAC3 (Host ID 10696):** Total Items = 15, Priority Numeric Items = 6

- **ME_PAC4 (Host ID 10698):** Total Items = 15, Priority Numeric Items = 6

- **ME_UPS2 (Host ID 10697):** Total Items = 54, Priority Numeric Items = 27

- **ME_UPS3 (Host ID 10701):** Total Items = 48, Priority Numeric Items = 24


## 3. Volume, Pagination, & Truncation Risks
- Items polling at 30s or 1m intervals generate ~1,440 to ~2,880 points per 24 hours.
- The 1,000 points/request batch limit requires the designed 3-batch pagination cap to prevent silent data truncation.

## 4. PAC Candidates & Transport Security
- **PAC Candidates:** Present in Phase G.6/G.8 source metadata (e.g., return/supply temperature, compressor status, fan speed), but not yet activated in active history pull plans.
- **Transport Security:** Unencrypted HTTP transport risk (`TRANSPORT_HTTP_RISK`) remains unmitigated by TLS. Private network segmentation is assumed but requires formal operator acknowledgment.

## 5. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
- Model Training: `False`
- Automatic Remediation: `False`
