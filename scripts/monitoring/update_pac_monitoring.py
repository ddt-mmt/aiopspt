import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from zabbix_utils import ZabbixAPI

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Connecting to Zabbix API...")
    zapi = ZabbixAPI(url=url)
    zapi.login(user=user, password=password)
    print("Successfully connected.")

    hosts = zapi.host.get(output=["hostid", "host"], filter={"host": ["ME_PAC1", "ME_PAC2"]})
    
    for h in hosts:
        hostid = h['hostid']
        hostname = h['host']
        print(f"\nProcessing Host: {hostname} (ID: {hostid})")
        
        # 1. Ensure maintenance/filter status item exists (Trapper item, efficient update interval 300s)
        key_name = "pac.maintenance.filter.status"
        item_name = "PAC Filter Maintenance Status"
        
        items = zapi.item.get(hostids=hostid, filter={"key_": [key_name]}, output=["itemid"])
        if not items:
            try:
                zapi.item.create({
                    'name': item_name,
                    'key_': key_name,
                    'hostid': hostid,
                    'type': 2, # Zabbix trapper
                    'value_type': 3, # Numeric unsigned (0=OK, 1=Maintenance/Filter Warning)
                    'interfaceid': 0,
                    'delay': '0'
                })
                print(f"  -> Created trapper item '{key_name}' successfully.")
            except Exception as e:
                print(f"  -> Failed to create item {key_name}: {e}")
        else:
            print(f"  -> Item '{key_name}' already exists (ID: {items[0]['itemid']}).")

        # 2. Query recent history with correct UTC -> WIB timezone conversion
        target_items = zapi.item.get(hostids=hostid, filter={"key_": ["return.temp.c", key_name]}, output=["itemid", "key_"])
        time_from = int((datetime.now() - timedelta(days=5)).timestamp())
        
        for item in target_items:
            history = zapi.history.get({
                "output": "extend",
                "history": 0,
                "itemids": item['itemid'],
                "time_from": time_from,
                "limit": 1000,
                "sortfield": "clock",
                "sortorder": "ASC"
            })
            if history:
                df = pd.DataFrame(history)
                # Correct timezone handling: UTC to WIB (UTC+7)
                df['utc_time'] = pd.to_datetime(df['clock'].astype(int), unit='s', utc=True)
                df['wib_time'] = df['utc_time'].dt.tz_convert('Asia/Jakarta')
                df['value'] = df['value'].astype(float)
                
                max_val = df['value'].max()
                print(f"  - Key '{item['key_']}': records={len(df)}, max={max_val}")
                
                # Check for high values (>33°C for temp)
                if 'return.temp.c' in item['key_']:
                    highs = df[df['value'] > 33]
                    if not highs.empty:
                        print(f"    Found {len(highs)} instances above 33°C (WIB):")
                        for _, row in highs.tail(3).iterrows():
                            print(f"      [{row['wib_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}] Value: {row['value']}°C")

if __name__ == "__main__":
    main()
