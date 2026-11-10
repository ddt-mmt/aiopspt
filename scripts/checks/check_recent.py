import os
from datetime import datetime, timedelta
from zabbix_utils import ZabbixAPI
import pandas as pd

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

zapi = ZabbixAPI(url=url)
zapi.login(user=user, password=password)

hosts = zapi.host.get(output=["hostid", "host"], filter={"host": ["ME_PAC1", "ME_PAC2"]})
time_from = int((datetime.now() - timedelta(days=5)).timestamp())

for h in hosts:
    items = zapi.item.get(hostids=h['hostid'], output=["itemid", "key_", "value_type"], filter={"key_": ["return.temp.c"]})
    for item in items:
        history = zapi.history.get({
            "output": "extend",
            "history": int(item['value_type']),
            "itemids": item['itemid'],
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 100
        })
        print(f"\n--- Latest 100 return temp for {h['host']} ---")
        df = pd.DataFrame(history)
        if not df.empty:
            df['clock'] = pd.to_datetime(df['clock'].astype(int), unit='s')
            df['value'] = df['value'].astype(float)
            print(df[['clock', 'value']].head(20))
            print("Max in last 100 records:", df['value'].max())
        else:
            print("No history.")
