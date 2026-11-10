import os
import time
from datetime import datetime, timedelta
from zabbix_utils import ZabbixAPI
import pandas as pd

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

try:
    zapi = ZabbixAPI(url=url)
    zapi.login(user=user, password=password)
    print("Connected to Zabbix API.")
    
    hosts = zapi.host.get(output=["hostid", "host"], filter={"host": ["ME_PAC1", "ME_PAC2"]})
    host_map = {h['hostid']: h['host'] for h in hosts}
    
    time_from = int((datetime.now() - timedelta(days=5)).timestamp())
    
    all_data = []
    for h_id, h_name in host_map.items():
        items = zapi.item.get(hostids=h_id, output=["itemid", "name", "key_", "value_type"], filter={"key_": ["return.temp.c", "supply.temp.c"]})
        for item in items:
            history = zapi.history.get({
                "output": "extend",
                "history": int(item['value_type']),
                "itemids": item['itemid'],
                "time_from": time_from,
                "sortfield": "clock",
                "sortorder": "ASC",
                "limit": 5000
            })
            for h_record in history:
                all_data.append({
                    "host": h_name,
                    "key": item['key_'],
                    "timestamp": datetime.fromtimestamp(int(h_record['clock'])),
                    "value": float(h_record['value'])
                })
                
    if all_data:
        df = pd.DataFrame(all_data)
        print("\n=== LIVE 5-DAY HISTORY SUMMARY ===")
        print(df.groupby(['host', 'key'])['value'].agg(['count', 'min', 'max', 'mean']))
        
        returns = df[df['key'] == 'return.temp.c']
        print("\nReturn temp records > 30°C:")
        high_returns = returns[returns['value'] > 30]
        if len(high_returns) > 0:
            print(high_returns.sort_values('timestamp', ascending=False).head(20))
        else:
            print("No return temp > 30°C found in last 5 days history query.")
            
        df.to_csv("live_5d_history.csv", index=False)
    else:
        print("No history data retrieved.")
        
except Exception as e:
    print("Error querying Zabbix history:", e)
