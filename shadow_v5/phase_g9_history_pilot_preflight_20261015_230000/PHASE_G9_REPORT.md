# Phase G.9 Minimal History Pilot Preflight Report

## 1. Metadata
- **Preflight Timestamp:** 2026-10-15T04:03:55.295939
- **Staging Directory:** `/root/grafan_aiops/shadow_v5/phase_g9_history_pilot_preflight_20261015_230000`
- **Input Source:** `/root/grafan_aiops/shadow_v5/phase_g8_candidate_validation_20261015_220000/PHASE_G8_VALIDATED_CANDIDATES.csv`
- **Selected Candidates Count:** 2
- **Final Status:** `HISTORY_PILOT_PREFLIGHT_READY`

## 2. Selected Pilot Candidates

### Candidate 1
- **Host ID:** `10688`
- **Item ID:** `59604`
- **Name:** `Battery voltage`
- **Key:** `battery.voltage[upsHighPrecBatteryActualVoltage]`
- **Units:** `V`
- **Value Type:** `0 (Numeric Float)`
- **Selection Rationale:** PRIORITY numerical sensor relevant for operational anomaly detection with validated metadata.

### Candidate 2
- **Host ID:** `10688`
- **Item ID:** `59607`
- **Name:** `Input voltage`
- **Key:** `input.voltage[upsHighPrecInputLineVoltage]`
- **Units:** `V`
- **Value Type:** `0 (Numeric Float)`
- **Selection Rationale:** PRIORITY numerical sensor relevant for operational anomaly detection with validated metadata.


## 3. Pilot Execution Parameters
- **API Method:** `history.get`
- **Time Window:** Max 60 minutes
- **Max Points Per Item:** 500
- **History Type:** Numeric float (value_type 0)

## 4. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
