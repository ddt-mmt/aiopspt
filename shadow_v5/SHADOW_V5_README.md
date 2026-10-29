# Continuous AIOps Shadow Operation (v5)

## Overview
This directory contains the staging implementation for **Continuous AIOps Shadow Operation v5**, operating strictly in read-only mode using historical Zabbix audit data without mutating production environments, modifying production scripts (`script_aiops.py`), or writing to Zabbix API.

## Directory Structure
- `shadow_runner.py`: Python script executing read-only shadow evaluation and temporal splitting.
- `shadow_v5_dashboard.json`: Grafana dashboard template for shadow telemetry.
- `outputs/`: Generated JSON and CSV shadow execution reports.

## Safety & Compliance
- **Production Script Hash:** Verified as `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (unchanged).
- **Zabbix Writes:** 0
- **Production Changes:** None.

## How to Run Dry-Run / Manual Cycle
```bash
python3 /root/grafan_aiops/shadow_v5/shadow_runner.py
```
