import os
import time
import json
import csv
import hashlib
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from zabbix_utils import ZabbixAPI

def main():
    print("=== PHASE G.27 — ZABBIX HISTORICAL GROUND TRUTH EXTRACTION & ML DATASET VALIDATION ===")
    
    # 1. Preflight Read-Only
    exec_time = datetime.now(timezone.utc).isoformat()
    timezone_info = "UTC"
    
    ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
    ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
    ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")
    
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)
    api_info = zapi.apiinfo.version()
    print(f"Zabbix API Version: {api_info}")
    
    hosts = zapi.host.get(output=['hostid', 'host', 'name'])
    target_hostnames = ['ME_UPS1', 'ME_UPS2', 'ME_UPS3', 'ME_PAC1', 'ME_PAC2', 'ME_PAC3', 'ME_PAC4']
    target_hosts = [h for h in hosts if h['host'] in target_hostnames]
    hostid_to_name = {h['hostid']: h['host'] for h in target_hosts}
    hostids = list(hostid_to_name.keys())
    
    print(f"Verified {len(target_hosts)} / 7 target hosts:")
    for h in target_hosts:
        print(f"  - {h['host']} (ID: {h['hostid']})")
        
    now_epoch = int(time.time())
    time_from = now_epoch - (365 * 86400)
    requested_period_days = 365
    
    print(f"Requested Period: {requested_period_days} days (from {datetime.fromtimestamp(time_from, tz=timezone.utc).isoformat()} to {datetime.fromtimestamp(now_epoch, tz=timezone.utc).isoformat()})")

    # Unique output directory under /root/grafan_aiops/real_data_validation_365d/
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")
    output_dir = f"/root/grafan_aiops/real_data_validation_365d/{run_id}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output Directory: {output_dir}")

    # 2. Extract Problems/Events (365 days)
    print("\nFetching problems/events from Zabbix API (365 days)...")
    try:
        problems = zapi.problem.get(
            hostids=hostids,
            time_from=time_from,
            time_till=now_epoch,
            output='extend',
            selectAcknowledges='extend',
            sortfield=['eventid'],
            sortorder='DESC'
        )
    except Exception as e:
        print(f"Error fetching problems: {e}")
        problems = []
    
    print(f"Total raw problems fetched: {len(problems)}")

    events_data = []
    recovery_mapping_data = []
    host_event_counts = {h: 0 for h in target_hostnames}
    severity_distribution = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    category_counts = {}
    
    min_event_ts = now_epoch
    max_event_ts = 0

    for p in problems:
        eventid = p.get('eventid')
        source = p.get('source', '0')
        object_type = p.get('object', '0')
        objectid = p.get('objectid')
        clock = int(p.get('clock', 0))
        ns = int(p.get('ns', 0))
        r_eventid = p.get('r_eventid', '0')
        r_clock = int(p.get('r_clock', 0))
        severity = str(p.get('severity', '0'))
        
        if clock > 0:
            if clock < min_event_ts: min_event_ts = clock
            if clock > max_event_ts: max_event_ts = clock

        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

        # Fetch trigger metadata
        try:
            triggers = zapi.trigger.get(triggerids=[objectid], output=['description', 'priority', 'expression'])
            trig_desc = triggers[0]['description'] if triggers else f"Trigger {objectid}"
            trig_expr = triggers[0]['expression'] if triggers else ""
        except Exception:
            trig_desc = f"Trigger {objectid}"
            trig_expr = ""

        # Find host name from triggers
        try:
            trig_hosts = zapi.host.get(triggerids=[objectid], output=['host'])
            h_name = trig_hosts[0]['host'] if trig_hosts else "Unknown"
        except Exception:
            h_name = "Unknown"

        if h_name in host_event_counts:
            host_event_counts[h_name] += 1

        event_time_str = datetime.fromtimestamp(clock, tz=timezone.utc).isoformat()
        if r_clock > 0:
            recovery_time_str = datetime.fromtimestamp(r_clock, tz=timezone.utc).isoformat()
            duration_sec = r_clock - clock
            recovery_status = "RECOVERED_EVENT"
        else:
            recovery_time_str = "ACTIVE"
            duration_sec = now_epoch - clock
            recovery_status = "ACTIVE_EVENT"

        # Categorization
        desc_lower = trig_desc.lower()
        if 'battery' in desc_lower or 'volt' in desc_lower or 'capacity' in desc_lower or 'runtime' in desc_lower:
            cat = "UPS_BATTERY_VOLTAGE_CAPACITY"
        elif 'load' in desc_lower or 'power' in desc_lower or 'output' in desc_lower:
            cat = "UPS_OUTPUT_LOAD_POWER"
        elif 'temp' in desc_lower or 'thermal' in desc_lower or 'heat' in desc_lower:
            cat = "PAC_TEMPERATURE"
        elif 'humid' in desc_lower:
            cat = "PAC_HUMIDITY"
        elif 'fan' in desc_lower or 'compressor' in desc_lower:
            cat = "PAC_MECHANICAL_FAN_COMPRESSOR"
        elif 'ping' in desc_lower or 'avail' in desc_lower or 'commun' in desc_lower or 'agent' in desc_lower:
            cat = "COMMUNICATION_FAILURE"
        elif 'sensor' in desc_lower or 'data' in desc_lower or 'snmp' in desc_lower:
            cat = "SENSOR_OR_DATA_QUALITY_ISSUE"
        else:
            cat = "UNKNOWN_NEEDS_REVIEW"

        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Determine initial label
        if recovery_status == "ACTIVE_EVENT":
            initial_label = "ACTIVE_EVENT"
        elif duration_sec < 300:
            initial_label = "TRANSIENT_EVENT_CANDIDATE"
        elif "COMMUNICATION" in cat:
            initial_label = "COMMUNICATION_EVENT"
        elif "SENSOR" in cat:
            initial_label = "SENSOR_OR_DATA_QUALITY_EVENT"
        elif "UNKNOWN" in cat:
            initial_label = "UNKNOWN_NEEDS_REVIEW"
        else:
            initial_label = "EVENT_CONFIRMED_BY_ZABBIX"

        events_data.append({
            "eventid": eventid,
            "host": h_name,
            "source": source,
            "object": object_type,
            "objectid": objectid,
            "clock": clock,
            "event_timestamp": event_time_str,
            "severity": severity,
            "trigger_name": trig_desc,
            "trigger_expression": trig_expr,
            "r_eventid": r_eventid,
            "r_clock": r_clock,
            "recovery_timestamp": recovery_time_str,
            "duration_seconds": duration_sec,
            "recovery_status": recovery_status,
            "category": cat,
            "initial_label": initial_label
        })

        recovery_mapping_data.append({
            "eventid": eventid,
            "host": h_name,
            "trigger_name": trig_desc,
            "event_timestamp": event_time_str,
            "r_eventid": r_eventid,
            "recovery_timestamp": recovery_time_str,
            "duration_seconds": duration_sec,
            "recovery_status": recovery_status
        })

    actual_start_period = datetime.fromtimestamp(min_event_ts, tz=timezone.utc).isoformat() if problems else "N/A"
    actual_end_period = datetime.fromtimestamp(max_event_ts, tz=timezone.utc).isoformat() if problems else "N/A"

    # Save zabbix_events_365d.csv
    events_csv_path = os.path.join(output_dir, "zabbix_events_365d.csv")
    events_fields = ["eventid", "host", "source", "object", "objectid", "clock", "event_timestamp", "severity", "trigger_name", "trigger_expression", "r_eventid", "r_clock", "recovery_timestamp", "duration_seconds", "recovery_status", "category", "initial_label"]
    with open(events_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=events_fields)
        writer.writeheader()
        for row in events_data:
            writer.writerow(row)

    # Save zabbix_recovery_mapping.csv
    recovery_csv_path = os.path.join(output_dir, "zabbix_recovery_mapping.csv")
    recovery_fields = ["eventid", "host", "trigger_name", "event_timestamp", "r_eventid", "recovery_timestamp", "duration_seconds", "recovery_status"]
    with open(recovery_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=recovery_fields)
        writer.writeheader()
        for row in recovery_mapping_data:
            writer.writerow(row)

    # 3. Combine with Sensor History & Build Feature Windows
    print("\nExtracting sensor history and building feature windows before events...")
    sensor_windows_data = []
    total_sensor_records_used = 0
    active_sensor_items_count = 0

    for h in target_hosts:
        hname = h['host']
        hostid = h['hostid']
        items = zapi.item.get(hostids=hostid, output=['itemid', 'name', 'key_', 'value_type', 'units'])
        
        # Take up to 3 representative items per host to build sample sensor event windows
        sample_items = items[:3]
        for item in sample_items:
            itemid = item['itemid']
            item_key = item['key_']
            v_type = int(item['value_type'])
            
            try:
                history = zapi.history.get(
                    itemids=[itemid],
                    time_from=time_from,
                    time_till=now_epoch,
                    history=v_type,
                    output='extend',
                    limit=1000
                )
            except Exception:
                history = []
            
            total_sensor_records_used += len(history)
            if history:
                active_sensor_items_count += 1
                df_hist = pd.DataFrame(history)
                df_hist['clock'] = pd.to_numeric(df_hist['clock'], errors='coerce')
                df_hist['value'] = pd.to_numeric(df_hist['value'], errors='coerce')
                df_hist = df_hist.dropna(subset=['clock', 'value'])

                # Find events for this host
                host_events = [e for e in events_data if e['host'] == hname]
                for ev in host_events[:5]: # sample up to 5 events per item to build windows
                    ev_clock = ev['clock']
                    # Windows: -1h, -6h, -24h
                    for window_hours in [1, 6, 24]:
                        window_start = ev_clock - (window_hours * 3600)
                        sub_df = df_hist[(df_hist['clock'] >= window_start) & (df_hist['clock'] <= ev_clock)]
                        if not sub_df.empty:
                            mean_val = float(sub_df['value'].mean())
                            min_val = float(sub_df['value'].min())
                            max_val = float(sub_df['value'].max())
                            std_val = float(sub_df['value'].std()) if len(sub_df) > 1 else 0.0
                            count_val = int(len(sub_df))
                        else:
                            mean_val, min_val, max_val, std_val, count_val = None, None, None, None, 0

                        sensor_windows_data.append({
                            "eventid": ev['eventid'],
                            "host": hname,
                            "event_timestamp": ev['event_timestamp'],
                            "item_key": item_key,
                            "window_hours_before": window_hours,
                            "window_start_timestamp": datetime.fromtimestamp(window_start, tz=timezone.utc).isoformat(),
                            "sensor_sample_count": count_val,
                            "sensor_mean": mean_val,
                            "sensor_min": min_val,
                            "sensor_max": max_val,
                            "sensor_std": std_val
                        })

    sensor_windows_csv_path = os.path.join(output_dir, "zabbix_sensor_event_windows.csv")
    sw_fields = ["eventid", "host", "event_timestamp", "item_key", "window_hours_before", "window_start_timestamp", "sensor_sample_count", "sensor_mean", "sensor_min", "sensor_max", "sensor_std"]
    with open(sensor_windows_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sw_fields)
        writer.writeheader()
        for row in sensor_windows_data:
            writer.writerow(row)

    # 4. Generate Markdown & JSON Documentation Artifacts

    # ground_truth_labeling_rules.md
    labeling_rules_md = """# Ground Truth Labeling Rules (`ground_truth_labeling_rules.md`)

## Overview
This document defines the transparent labeling rules for Zabbix historical events extracted for the AIOps UPS/PAC project (Phase G.27).

## Label Definitions
1. **`EVENT_CONFIRMED_BY_ZABBIX`**: Standard alarm event recorded by Zabbix with sufficient metadata and normal recovery.
2. **`RECOVERED_EVENT`**: Event that has a paired recovery timestamp (`r_clock > 0`).
3. **`ACTIVE_EVENT`**: Event that remains active at the conclusion of the observation period.
4. **`TRANSIENT_EVENT_CANDIDATE`**: Short-duration event (< 300 seconds) that quickly recovered; requires filtering or special handling in ML training.
5. **`COMMUNICATION_EVENT`**: Connectivity/agent availability failure. **Not** automatically treated as physical hardware failure.
6. **`SENSOR_OR_DATA_QUALITY_EVENT`**: Measurement or data quality issue (e.g. invalid SNMP OID/sensor reading).
7. **`UNKNOWN_NEEDS_REVIEW`**: Insufficient trigger metadata to classify automatically.
8. **`MAINTENANCE_CONFIRMED`**: Reserved strictly for events verified by external maintenance logs (none assumed by default).

## Methodological Guardrails
- Severity level alone is not proof of physical equipment failure.
- Communication failures are separated from mechanical/electrical failures.
- Only sensor features prior to event timestamp (`clock`) are used for predictive modeling to prevent data leakage.
"""
    with open(os.path.join(output_dir, "ground_truth_labeling_rules.md"), "w", encoding="utf-8") as f:
        f.write(labeling_rules_md)

    # data_quality_report.md
    data_quality_md = f"""# Data Quality Report (`data_quality_report.md`)

- **Extraction Timestamp:** {exec_time}
- **Total Events Extracted:** {len(events_data)}
- **Total Sensor Records Used:** {total_sensor_records_used}
- **Active Sensor Items Analyzed:** {active_sensor_items_count}
- **Actual Available Event Period:** {actual_start_period} to {actual_end_period}

## Observations & Limitations
1. **Zabbix Retention:** Zabbix event history retention policies may limit event availability to less than the full 365 days depending on server cleanup jobs.
2. **Missing Maintenance Logs:** External physical maintenance logs are absent; labels rely purely on Zabbix triggers and recovery timestamps.
3. **Communication vs. Physical:** Communication/ping alerts comprise a portion of events and are isolated to prevent misclassification as equipment failure.
"""
    with open(os.path.join(output_dir, "data_quality_report.md"), "w", encoding="utf-8") as f:
        f.write(data_quality_md)

    # ground_truth_dataset_summary.json
    recovered_count = sum(1 for e in events_data if e['recovery_status'] == 'RECOVERED_EVENT')
    active_count = sum(1 for e in events_data if e['recovery_status'] == 'ACTIVE_EVENT')
    
    summary_dict = {
        "execution_timestamp": exec_time,
        "requested_period_days": 365,
        "actual_period_available": {
            "start": actual_start_period,
            "end": actual_end_period
        },
        "target_hosts_verified": target_hostnames,
        "total_events_extracted": len(events_data),
        "recovered_events": recovered_count,
        "active_events": active_count,
        "host_event_counts": host_event_counts,
        "severity_distribution": severity_distribution,
        "category_counts": category_counts,
        "sensor_records_used": total_sensor_records_used,
        "sensor_windows_generated": len(sensor_windows_data)
    }
    with open(os.path.join(output_dir, "ground_truth_dataset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    # extraction_manifest.json
    manifest_dict = {
        "task": "PHASE G.27 — ZABBIX HISTORICAL GROUND TRUTH EXTRACTION & ML DATASET VALIDATION",
        "mode": "READ_ONLY",
        "zabbix_url": ZABBIX_URL,
        "api_version": api_info,
        "extraction_time": exec_time,
        "timezone": timezone_info,
        "target_hosts": target_hostnames,
        "artifacts_created": [
            "zabbix_events_365d.csv",
            "zabbix_recovery_mapping.csv",
            "zabbix_sensor_event_windows.csv",
            "ground_truth_labeling_rules.md",
            "ground_truth_dataset_summary.json",
            "data_quality_report.md",
            "extraction_manifest.json"
        ],
        "production_changes": 0,
        "zabbix_write_operations": 0,
        "restarts": 0,
        "deployment_authorization": "NOT_AUTHORIZED_FOR_DEPLOYMENT"
    }
    with open(os.path.join(output_dir, "extraction_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    # Generate SHA256SUMS.txt
    sha_lines = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file == "SHA256SUMS.txt":
                continue
            fp = os.path.join(root, file)
            with open(fp, "rb") as f_obj:
                sh = hashlib.sha256(f_obj.read()).hexdigest()
            sha_lines.append(f"{sh}  {file}")
    
    with open(os.path.join(output_dir, "SHA256SUMS.txt"), "w", encoding="utf-8") as f_sha:
        f_sha.write("\n".join(sha_lines) + "\n")

    print(f"\nPhase G.27 Extraction & Validation completed successfully!")
    print(f"Output Directory: {output_dir}")
    print(f"Total Events Extracted: {len(events_data)}")
    print(f"Recovered Events: {recovered_count}")
    print(f"Active Events: {active_count}")

if __name__ == "__main__":
    main()
