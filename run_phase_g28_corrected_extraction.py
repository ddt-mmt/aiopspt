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
    print("=== PHASE G.28 — CORRECTED ZABBIX 365-DAY EVENT EXTRACTION (USING event.get) ===")
    
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
    
    now_epoch = int(time.time())
    time_from = now_epoch - (365 * 86400)
    
    output_dir = "/root/grafan_aiops/real_data_validation_365d/run_g28_corrected"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Fetching 365-day events using event.get...")
    all_events = []
    
    # Query in 30-day chunks to ensure completeness without hitting pagination limits
    one_day = 86400
    thirty_days = 30 * one_day
    
    for i in range(13):
        t_till = now_epoch - (i * thirty_days)
        t_from = t_till - thirty_days
        if t_from < time_from:
            t_from = time_from
            
        try:
            chunk = zapi.event.get(
                hostids=hostids,
                source=0,
                object=0,
                time_from=t_from,
                time_till=t_till,
                output=['eventid', 'source', 'object', 'objectid', 'clock', 'ns', 'r_eventid', 'value', 'acknowledged', 'severity'],
                sortfield=['clock'],
                sortorder='DESC'
            )
            all_events.extend(chunk)
        except Exception as e:
            print(f"Error fetching chunk {i}: {e}")
            
    print(f"Total raw events fetched across chunks: {len(all_events)}")
    
    # Deduplicate by eventid
    seen = set()
    unique_events = []
    for ev in all_events:
        eid = ev['eventid']
        if eid not in seen:
            seen.add(eid)
            unique_events.append(ev)
            
    print(f"Total unique events: {len(unique_events)}")

    # Fetch recovery event timestamps for r_eventids
    r_eventids = list(set([ev['r_eventid'] for ev in unique_events if ev.get('r_eventid') and ev['r_eventid'] != '0']))
    r_event_clock_map = {}
    
    # Batch fetch recovery events if any
    if r_eventids:
        # fetch in batches of 500
        for b in range(0, len(r_eventids), 500):
            batch = r_eventids[b:b+500]
            try:
                revs = zapi.event.get(
                    eventids=batch,
                    output=['eventid', 'clock']
                )
                for rev in revs:
                    r_event_clock_map[rev['eventid']] = int(rev['clock'])
            except Exception as e:
                print(f"Error fetching recovery events batch: {e}")

    events_data = []
    recovery_mapping_data = []
    host_event_counts = {h: 0 for h in target_hostnames}
    severity_distribution = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    category_counts = {}
    
    min_event_ts = now_epoch
    max_event_ts = 0

    # Cache trigger info
    trigger_cache = {}

    for ev in unique_events:
        eventid = ev['eventid']
        source = ev.get('source', '0')
        object_type = ev.get('object', '0')
        objectid = ev.get('objectid')
        clock = int(ev.get('clock', 0))
        value = ev.get('value', '1') # 1 = problem, 0 = recovery
        r_eventid = ev.get('r_eventid', '0')
        severity = str(ev.get('severity', '0'))
        
        if clock > 0:
            if clock < min_event_ts: min_event_ts = clock
            if clock > max_event_ts: max_event_ts = clock

        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

        # Fetch trigger metadata with cache
        if objectid not in trigger_cache:
            try:
                trigs = zapi.trigger.get(triggerids=[objectid], output=['description', 'priority', 'expression'])
                trig_desc = trigs[0]['description'] if trigs else f"Trigger {objectid}"
                trig_expr = trigs[0]['expression'] if trigs else ""
                
                trig_hosts = zapi.host.get(triggerids=[objectid], output=['host'])
                h_name = trig_hosts[0]['host'] if trig_hosts else "Unknown"
            except Exception:
                trig_desc = f"Trigger {objectid}"
                trig_expr = ""
                h_name = "Unknown"
            trigger_cache[objectid] = (trig_desc, trig_expr, h_name)
        else:
            trig_desc, trig_expr, h_name = trigger_cache[objectid]

        if h_name in host_event_counts:
            host_event_counts[h_name] += 1

        event_time_str = datetime.fromtimestamp(clock, tz=timezone.utc).isoformat()
        
        r_clock = r_event_clock_map.get(r_eventid, 0)
        if r_clock > 0:
            recovery_time_str = datetime.fromtimestamp(r_clock, tz=timezone.utc).isoformat()
            duration_sec = r_clock - clock
            recovery_status = "RECOVERED_EVENT"
        elif r_eventid != '0':
            recovery_time_str = "RECOVERED_EXTERNAL_CLOCK"
            duration_sec = 0
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

        if recovery_status == "ACTIVE_EVENT":
            initial_label = "ACTIVE_EVENT"
        elif duration_sec > 0 and duration_sec < 300:
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

    actual_start_period = datetime.fromtimestamp(min_event_ts, tz=timezone.utc).isoformat() if unique_events else "N/A"
    actual_end_period = datetime.fromtimestamp(max_event_ts, tz=timezone.utc).isoformat() if unique_events else "N/A"

    # Save CSVs
    events_csv_path = os.path.join(output_dir, "zabbix_events_365d.csv")
    events_fields = ["eventid", "host", "source", "object", "objectid", "clock", "event_timestamp", "severity", "trigger_name", "trigger_expression", "r_eventid", "r_clock", "recovery_timestamp", "duration_seconds", "recovery_status", "category", "initial_label"]
    with open(events_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=events_fields)
        writer.writeheader()
        for row in events_data:
            writer.writerow(row)

    recovery_csv_path = os.path.join(output_dir, "zabbix_recovery_mapping.csv")
    recovery_fields = ["eventid", "host", "trigger_name", "event_timestamp", "r_eventid", "recovery_timestamp", "duration_seconds", "recovery_status"]
    with open(recovery_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=recovery_fields)
        writer.writeheader()
        for row in recovery_mapping_data:
            writer.writerow(row)

    # Summaries & Manifest
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
        "category_counts": category_counts
    }
    with open(os.path.join(output_dir, "ground_truth_dataset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    print(f"Corrected extraction completed! Total events extracted: {len(events_data)}")
    print(f"Recovered: {recovered_count}, Active: {active_count}")
    print(f"Saved to: {output_dir}")

if __name__ == "__main__":
    main()
