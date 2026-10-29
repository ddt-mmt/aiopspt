import os
import time
import json
import csv
from datetime import datetime, timezone, timedelta
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Memulai Audit Ground Truth Zabbix (Problems/Events 30 hari terakhir)...")
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

    # Get target hosts
    hosts = zapi.host.get(output=['hostid', 'host', 'name'])
    target_hostnames = ['ME_UPS1', 'ME_UPS2', 'ME_UPS3', 'ME_PAC1', 'ME_PAC2', 'ME_PAC3', 'ME_PAC4']
    target_hosts = [h for h in hosts if h['host'] in target_hostnames]
    hostid_to_name = {h['hostid']: h['host'] for h in target_hosts}
    hostids = list(hostid_to_name.keys())

    print(f"Ditemukan {len(target_hosts)} host target dari 7 yang dicari.")

    # Time range: 30 days ago to now
    now_epoch = int(time.time())
    time_from = now_epoch - (30 * 86400)

    events_data = []
    host_event_counts = {h['host']: 0 for h in target_hosts}
    categories_count = {}

    try:
        # Fetch problems using problem.get API
        problems = zapi.problem.get(
            hostids=hostids,
            time_from=time_from,
            time_till=now_epoch,
            output='extend',
            selectAcknowledges='extend',
            sortfield=['eventid'],
            sortorder='DESC'
        )
        print(f"Total problems fetched: {len(problems)}")

        for p in problems:
            # Get trigger details to know host and trigger name
            triggerid = p.get('objectid')
            # Fetch trigger info
            triggers = zapi.trigger.get(triggerids=[triggerid], output=['description', 'priority', 'expression'])
            trig_desc = triggers[0]['description'] if triggers else f"Trigger {triggerid}"
            priority = triggers[0]['priority'] if triggers else '0'

            # Find host name from triggers or problem objects
            # Alternatively get hosts via trigger
            trig_hosts = zapi.host.get(triggerids=[triggerid], output=['host'])
            h_name = trig_hosts[0]['host'] if trig_hosts else "Unknown"

            if h_name in host_event_counts:
                host_event_counts[h_name] += 1

            clock = int(p.get('clock', 0))
            r_clock = int(p.get('r_clock', 0))
            event_time = datetime.fromtimestamp(clock, tz=timezone.utc).isoformat()
            recovery_time = datetime.fromtimestamp(r_clock, tz=timezone.utc).isoformat() if r_clock > 0 else "Unresolved"
            recovery_status = "Recovered" if r_clock > 0 else "Active"

            # Categorize alarm based on description keywords
            desc_lower = trig_desc.lower()
            if 'temp' in desc_lower or 'thermal' in desc_lower or 'heat' in desc_lower:
                cat = "Temperature"
            elif 'battery' in desc_lower or 'volt' in desc_lower or 'power' in desc_lower or 'load' in desc_lower:
                cat = "Power/Battery"
            elif 'fan' in desc_lower or 'compressor' in desc_lower:
                cat = "Mechanical/PAC"
            elif 'ping' in desc_lower or 'avail' in desc_lower or 'commun' in desc_lower:
                cat = "Connectivity/Availability"
            else:
                cat = "Other"

            categories_count[cat] = categories_count.get(cat, 0) + 1

            events_data.append({
                "host": h_name,
                "event_id": p.get('eventid'),
                "event_time": event_time,
                "recovery_time": recovery_time,
                "trigger_name": trig_desc,
                "severity": priority,
                "recovery_status": recovery_status,
                "event_category": cat,
                "confirmation_status": "unverified"
            })

    except Exception as e:
        print(f"Error querying Zabbix problems: {e}")

    # Save CSV
    csv_path = "/root/grafan_aiops/zabbix_ground_truth_30d.csv"
    csv_fields = ["host", "event_id", "event_time", "recovery_time", "trigger_name", "severity", "recovery_status", "event_category", "confirmation_status"]
    with open(csv_path, "w", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=csv_fields)
        writer.writeheader()
        for row in events_data:
            writer.writerow(row)
    print(f"CSV tersimpan di: {csv_path} ({len(events_data)} baris)")

    # Save Markdown Report
    md_path = "/root/grafan_aiops/AUDIT_ZABBIX_GROUND_TRUTH.md"
    recovered_count = sum(1 for e in events_data if e["recovery_status"] == "Recovered")
    active_count = len(events_data) - recovered_count

    md_content = f"""# Laporan Audit Ground Truth Zabbix (Problems/Events 30 Hari Terakhir)

- **Waktu Audit:** {datetime.now(timezone.utc).isoformat()}
- **Metode Akses:** Zabbix API (`problem.get`, `trigger.get`, `host.get`) dengan autentikasi read-only.
- **Rentang Waktu:** 30 hari terakhir (~{datetime.fromtimestamp(time_from, tz=timezone.utc).strftime('%Y-%m-%d')} s.d. sekarang).
- **Host Diperiksa:** {target_hostnames}

---

## 1. Ringkasan Hasil Event
- **Total Event Ditemukan:** {len(events_data)}
- **Event dengan Pemulihan (Recovered):** {recovered_count}
- **Event Aktif (Unresolved):** {active_count}

## 2. Jumlah Event per Host
"""
    for hname, cnt in host_event_counts.items():
        md_content += f"- **{hname}:** {cnt} event\n"

    md_content += "\n## 3. Kategori Alarm\n"
    for cat, cnt in categories_count.items():
        md_content += f"- **{cat}:** {cnt} event\n"

    md_content += """
---

## 4. Keterbatasan Retensi & Akses
- API Zabbix mengembalikan data historis sesuai dengan periode retensi trigger/problem yang dikonfigurasi di Zabbix server.
- Seluruh status konfirmasi diatur ke `unverified` karena belum ada cross-check operasional/tiket pemeliharaan fisik secara langsung.

## 5. Kesimpulan Kesiapan Dataset
- **Apakah data cukup untuk membangun dataset evaluasi offline?** 
  Jika event alarm tercatat dalam jumlah yang memadai, data ini dapat digunakan sebagai titik referensi (*weak labels* / alarm markers) untuk mengevaluasi anomali. Namun, untuk validasi RUL (*Remaining Useful Life*) yang presisi, tetap diperlukan catatan pemeliharaan (*maintenance logs*).

## 6. Langkah Selanjutnya
- Gunakan file `zabbix_ground_truth_30d.csv` sebagai referensi waktu terjadinya alarm saat menganalisis skor anomali model AIOps.
"""

    with open(md_path, "w") as f_md:
        f_md.write(md_content)
    print(f"Laporan Markdown tersimpan di: {md_path}")

if __name__ == '__main__':
    main()
