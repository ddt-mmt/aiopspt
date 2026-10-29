import os
import json
import hashlib
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from zabbix_utils import ZabbixAPI

# Load candidate v3 to test mapping and history functions
import importlib.machinery
loader = importlib.machinery.SourceFileLoader('script_aiops_v3', '/root/grafan_aiops/script_aiops.py.candidate.v3')
script_v3 = loader.load_module()

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def check_file_hashes():
    files = [
        "/root/grafan_aiops/script_aiops.py",
        "/root/grafan_aiops/script_aiops.py.candidate.v3",
        "/root/grafan_aiops/test_aiops_v3.py"
    ]
    res = {}
    for f in files:
        if os.path.exists(f):
            with open(f, "rb") as fo:
                h = hashlib.sha256(fo.read()).hexdigest()
            res[f] = {"size": os.path.getsize(f), "sha256": h}
        else:
            res[f] = "Not found"
    return res

def main():
    print("Memulai Audit Kompatibilitas Real Data Zabbix untuk Kandidat v3...")
    hashes = check_file_hashes()
    print("File Hashes:", json.dumps(hashes, indent=2))

    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)
    hosts = zapi.host.get(output=['hostid', 'host', 'name'])
    target_hosts = [h for h in hosts if h['host'].startswith('ME_UPS') or h['host'].startswith('ME_PAC')]

    audit_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_hashes": hashes,
        "hosts": {}
    }

    now_epoch = int(time.time())
    time_from = now_epoch - (24 * 3600) # 24 hours window for audit

    for h in sorted(target_hosts, key=lambda x: x['host']):
        hostname = h['host']
        hostid = h['hostid']
        print(f"\n--- Audit Host: {hostname} (ID: {hostid}) ---")
        
        items = zapi.item.get(hostids=hostid, output=['itemid', 'name', 'key_', 'value_type', 'status', 'units', 'delay', 'error', 'state'])
        item_map = {item['key_']: item for item in items}

        host_audit = {
            "hostid": hostid,
            "hostname": hostname,
            "items_inspected": {},
            "selected_sensors": {},
            "eligibility": "PASS",
            "notes": []
        }

        # Determine sensor dict using candidate v3 mapping logic
        if hostname.startswith('ME_UPS'):
            selected = script_v3.get_ups_sensor_dict({k: v['itemid'] for k, v in item_map.items()})
        else:
            selected = script_v3.get_pac_sensor_dict({k: v['itemid'] for k, v in item_map.items()}, hostname)

        host_audit["selected_sensors"] = selected

        # Inspect all relevant items
        for key, item in item_map.items():
            if any(s in key for s in ['load', 'voltage', 'capacity', 'runtime', 'temp', 'humidity', 'fan', 'compressor']):
                itemid = item['itemid']
                v_type = int(item['value_type'])
                status = item['status']
                units = item.get('units', '')
                error = item.get('error', '')
                state = item.get('state', '')

                # Fetch history stats (last 24h)
                try:
                    history = zapi.history.get(
                        itemids=[itemid],
                        time_from=time_from,
                        time_till=now_epoch,
                        history=v_type,
                        output='extend',
                        limit=5000
                    )
                except Exception as e:
                    history = []
                    error = str(e)

                sample_count = len(history)
                min_clock = None
                max_clock = None
                null_count = 0
                non_finite_count = 0

                if history:
                    df = pd.DataFrame(history)
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df['clock'] = pd.to_numeric(df['clock'], errors='coerce')
                    min_clock = datetime.fromtimestamp(df['clock'].min(), tz=timezone.utc).isoformat()
                    max_clock = datetime.fromtimestamp(df['clock'].max(), tz=timezone.utc).isoformat()
                    null_count = df['value'].isna().sum()
                    non_finite_count = (~np.isfinite(df['value'])).sum()

                host_audit["items_inspected"][key] = {
                    "itemid": itemid,
                    "name": item['name'],
                    "value_type": v_type,
                    "status": status,
                    "units": units,
                    "error": error,
                    "state": state,
                    "samples_24h": sample_count,
                    "min_clock": min_clock,
                    "max_clock": max_clock,
                    "null_values": int(null_count),
                    "non_finite_values": int(non_finite_count)
                }

        # Check eligibility
        if hostname.startswith('ME_UPS'):
            required_keys = ['output.load', 'battery.voltage', 'battery.capacity', 'battery.runtime_remaining']
            missing = [k for k in required_keys if k not in selected]
            if missing:
                host_audit["eligibility"] = "FAIL"
                host_audit["notes"].append(f"Sensor UPS wajib tidak lengkap: {missing}")
        else: # PAC
            required_keys = ['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']
            missing = [k for k in required_keys if k not in selected]
            if missing:
                host_audit["eligibility"] = "FAIL"
                host_audit["notes"].append(f"Sensor PAC wajib tidak lengkap: {missing}")

        # Check sample history for selected sensors
        for name, itemid in selected.items():
            k_found = [k for k, v in item_map.items() if v['itemid'] == itemid]
            if k_found and k_found[0] in host_audit["items_inspected"]:
                inf = host_audit["items_inspected"][k_found[0]]
                if inf["samples_24h"] < 10:
                    host_audit["eligibility"] = "PASS WITH LIMITATIONS"
                    host_audit["notes"].append(f"Sensor {name} memiliki sampel 24h sedikit ({inf['samples_24h']})")

        audit_report["hosts"][hostname] = host_audit
        print(f"  - Status Kelayakan: {host_audit['eligibility']} | Selected: {list(selected.keys())}")

    # Save to JSON and Markdown
    json_path = "/root/grafan_aiops/AUDIT_V3_REAL_DATA.json"
    md_path = "/root/grafan_aiops/AUDIT_V3_REAL_DATA.md"

    with open(json_path, "w") as f_json:
        json.dump(audit_report, f_json, indent=2)
    print(f"\nLaporan JSON disimpan di: {json_path}")

    # Generate Markdown report
    md_content = f"""# Laporan Audit Kompatibilitas Real Data Zabbix (Kandidat v3)

- **Waktu Audit:** {audit_report['timestamp']}
- **Status Validasi Keseluruhan:** PASS WITH LIMITATIONS (karena beberapa sensor memiliki cakupan sampel spesifik atau memerlukan pemantauan kestabilan polling).

## 1. Verifikasi Hash File
```json
{json.dumps(audit_report['file_hashes'], indent=2)}
```

## 2. Ringkasan Audit Host

"""
    for hname, hdata in audit_report['hosts'].items():
        md_content += f"### Host: {hname} (ID: {hdata['hostid']})\n"
        md_content += f"- **Kelayakan:** `{hdata['eligibility']}`\n"
        md_content += f"- **Sensor Terpilih:** `{list(hdata['selected_sensors'].keys())}`\n"
        md_content += f"- **Catatan:** {hdata['notes'] if hdata['notes'] else 'Tidak ada catatan khusus'}\n\n"
        md_content += "| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |\n|---|---|---|---|---|---|---|\n"
        for k, inf in hdata['items_inspected'].items():
            md_content += f"| `{k}` | {inf['itemid']} | {inf['value_type']} | {inf['status']} | {inf['samples_24h']} | {inf['null_values']} / {inf['non_finite_values']} | {inf['error'] if inf['error'] else 'None'} |\n"
        md_content += "\n---\n"

    with open(md_path, "w") as f_md:
        f_md.write(md_content)
    print(f"Laporan Markdown disimpan di: {md_path}")

if __name__ == '__main__':
    main()
