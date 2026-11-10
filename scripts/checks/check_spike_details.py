import os
from datetime import datetime
from zabbix_utils import ZabbixAPI
import pandas as pd

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

zapi = ZabbixAPI(url=url)
zapi.login(user=user, password=password)

hosts = zapi.host.get(output=["hostid", "host"], filter={"host": ["ME_PAC1", "ME_PAC2"]})
start_of_day = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

for h in hosts:
    items = zapi.item.get(hostids=h['hostid'], output=["itemid", "key_", "value_type"], filter={"key_": ["return.temp.c", "supply.temp.c"]})
    for item in items:
        history = zapi.history.get({
            "output": "extend",
            "history": int(item['value_type']),
            "itemids": item['itemid'],
            "time_from": start_of_day,
            "sortfield": "clock",
            "sortorder": "ASC",
            "limit": 2000
        })
        if history:
            df = pd.DataFrame(history)
            df['clock'] = pd.to_datetime(df['clock'].astype(int), unit='s')
            df['value'] = df['value'].astype(float)
            highs = df[df['value'] > 28]
            if not highs.empty:
                print(f"\n--- {h['host']} {item['key_']} high values (>28) ---")
                print(highs[['clock', 'value']])
