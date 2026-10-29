import os
from datetime import datetime, timezone, timedelta
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)
    
    item_ids = {
        "return.temp.c": 60723,
        "supply.temp.c": 60725,
        "return.humidity.rh": 60727,
        "compressor.status": 60734
    }

    print("=== 1. Detail Item Zabbix ===")
    for name, itemid in item_ids.items():
        items = zapi.item.get(itemids=[itemid], output=['itemid', 'name', 'key_', 'value_type', 'history', 'trends', 'delay', 'status'])
        if items:
            it = items[0]
            print(f"Item: {it['name']} (Key: {it['key_']}, ID: {it['itemid']})")
            print(f"  - value_type: {it['value_type']} (0: float, 3: unsigned int, 1: char, 2: log, 4: text)")
            print(f"  - history storage: {it['history']}")
            print(f"  - status: {it['status']} (0: enabled, 1: disabled)")

    print("\n=== 2. Query History 24 Jam Terakhir (Menggunakan value_type yang sesuai) ===")
    time_till = int(datetime.now(timezone.utc).timestamp())
    time_from = time_till - (24 * 3600)
    print(f"Time range (UTC): {datetime.fromtimestamp(time_from, tz=timezone.utc)} s.d. {datetime.fromtimestamp(time_till, tz=timezone.utc)}")
    print(f"Time range (Unix): {time_from} s.d. {time_till}")

    for name, itemid in item_ids.items():
        items = zapi.item.get(itemids=[itemid], output=['value_type'])
        if not items:
            continue
        v_type = int(items[0]['value_type'])
        
        # Try fetching history with correct history type table
        try:
            history = zapi.history.get(
                itemids=[itemid],
                time_from=time_from,
                time_till=time_till,
                history=v_type,
                output='extend',
                sortfield='clock',
                sortorder='DESC',
                limit=5
            )
            print(f"\nItem {name} (ID {itemid}, value_type={v_type}): Ditemukan {len(history)} record (menampilkan max 5 terbaru):")
            for h in history:
                dt_wib = datetime.fromtimestamp(int(h['clock']), tz=timezone(timedelta(hours=7)))
                print(f"  - Clock: {h['clock']} ({dt_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB) | Value: {h['value']}")
        except Exception as e:
            print(f"\nItem {name} (ID {itemid}): Error query history type {v_type}: {e}")
            # Try history=0 as fallback
            try:
                history = zapi.history.get(
                    itemids=[itemid],
                    time_from=time_from,
                    time_till=time_till,
                    history=0,
                    output='extend',
                    sortfield='clock',
                    sortorder='DESC',
                    limit=5
                )
                print(f"  Fallback history=0: Ditemukan {len(history)} record")
                for h in history:
                    dt_wib = datetime.fromtimestamp(int(h['clock']), tz=timezone(timedelta(hours=7)))
                    print(f"    - Clock: {h['clock']} ({dt_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB) | Value: {h['value']}")
            except Exception as e2:
                print(f"  Fallback history=0 juga error: {e2}")

    print("\n=== 3. Query Khusus Supply.temp.c (ID 60725) pada 12 Okt 2026 02:24 - 02:53 WIB ===")
    # 12 Okt 2026 02:24 WIB = 11 Okt 2026 19:24 UTC
    # 12 Okt 2026 02:53 WIB = 11 Okt 2026 19:53 UTC
    # Let's also check if the date in user's prompt is 2026-10-12 02:24 WIB.
    dt_start_wib = datetime(2026, 10, 12, 2, 24, tzinfo=timezone(timedelta(hours=7)))
    dt_end_wib = datetime(2026, 10, 12, 2, 53, tzinfo=timezone(timedelta(hours=7)))
    t_from = int(dt_start_wib.timestamp())
    t_till = int(dt_end_wib.timestamp())
    print(f"Target window WIB: {dt_start_wib} s.d. {dt_end_wib}")
    print(f"Target window Unix: {t_from} s.d. {t_till}")

    try:
        hist_supply = zapi.history.get(
            itemids=[60725],
            time_from=t_from,
            time_till=t_till,
            history=0,
            output='extend',
            sortfield='clock',
            sortorder='ASC'
        )
        print(f"Hasil query supply.temp.c pada window tersebut: {len(hist_supply)} record.")
        for h in hist_supply:
            dt_wib = datetime.fromtimestamp(int(h['clock']), tz=timezone(timedelta(hours=7)))
            print(f"  - Clock: {h['clock']} ({dt_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB) | Value: {h['value']}")
    except Exception as e:
        print(f"Error query khusus supply.temp.c: {e}")

    # Also check a wider window around that time (e.g. 24 hours around Oct 12)
    print("\n=== 4. Cek History Lebih Luas untuk supply.temp.c (ID 60725) ===")
    try:
        t_from_wide = t_from - 3600 * 12
        t_till_wide = t_till + 3600 * 12
        hist_wide = zapi.history.get(
            itemids=[60725],
            time_from=t_from_wide,
            time_till=t_till_wide,
            history=0,
            output='extend',
            sortfield='clock',
            sortorder='DESC',
            limit=20
        )
        print(f"Ditemukan {len(hist_wide)} record dalam rentang ±12 jam dari target:")
        for h in hist_wide:
            dt_wib = datetime.fromtimestamp(int(h['clock']), tz=timezone(timedelta(hours=7)))
            print(f"  - Clock: {h['clock']} ({dt_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB) | Value: {h['value']}")
    except Exception as e:
        print(f"Error query wide supply.temp.c: {e}")

if __name__ == '__main__':
    main()
