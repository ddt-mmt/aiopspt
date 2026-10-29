# V10 Offline Data Readiness

- Network/API calls: NONE
- Token access: NONE
- Production modifications: NONE

## Historical CSV inventory

### PHASE_G10_BATTERY_VOLTAGE.csv
- SHA-256: `efa12ccc3bde1db32da8d45c24b7a5abb2fcfbebca31a3419f8ed5978d8dd5d5`
- Columns: `itemid, clock, value, ns`
- Data rows: 1
- Valid numeric records: 1
- Invalid records: 0
- Schema check: PASS
- CSV structural check: PASS

### PHASE_G10_INPUT_VOLTAGE.csv
- SHA-256: `fc55b3e82a0b3d9d364eb2867ecdc2be32df13451cb2ee43836bda7e90fe785a`
- Columns: `itemid, clock, value, ns`
- Data rows: 47
- Valid numeric records: 47
- Invalid records: 0
- Schema check: PASS
- CSV structural check: PASS

## Candidate V10

- Candidate: FOUND
- SHA-256: `1b3e0a046c6736d397bc2c01667ff913bae5ffb097836937f24946af4aa16bff`
- Size: 5810 bytes
- Execution: NOT RUN

## Decision

- CSV structural readiness: PASS
- Model compatibility: NOT VERIFIED
- Detection accuracy: NOT MEASURABLE from CSV structure alone
- Operational/live readiness: NOT VERIFIED
- Read-only role enforcement: NOT VERIFIED

This report checks file structure only. It does not prove that the model can safely consume these measurements.
