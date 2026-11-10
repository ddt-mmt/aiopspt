# AIOps & Monitoring Scripts Inventory

This directory contains consolidated scripts and tools related to the Grafan AIOps project (`grafan_aiops`), previously scattered in the root workspace.

## Directory Structure

- **`audits/`**: Phase audit runner scripts (`run_phase50_audit.py` through `run_phase60_audit.py`, and `run_phase58_review.py`).
- **`builds/`**: Phase 87 build and deployment scripts (`build_phase87_11.py` through `build_phase87_17.py`).
- **`checks/`**: Diagnostic and check scripts (`cek_aiops.sh`, `check_dates.py`, `check_distribution.py`, `check_live_zabbix.py`, `check_recent.py`, `check_return_36.py`, `check_snmp.py`, `check_spike_details.py`, `check_today_all.py`, `check_wib.py`).
- **`generators/`**: Test generation and artifact production scripts (`generate_artifacts.py`, `generate_phase47_test.py`, `generate_v11.py`, `generate_v11_tests.py`).
- **`monitoring/`**: Zabbix alerting, PAC/UPS analytics, dashboard runners, and trigger configuration utilities (`analyze_pac_ups.py`, `create_dashboard.py`, `create_map.py`, `create_map_v2.py`, `create_missing_triggers.py`, `expand_me_monitoring.py`, `fetch_live_history.py`, `run_dashboard.py`, `update_dashboard.py`, `update_pac_monitoring.py`, `zabbix_separate_alerts.py`).
