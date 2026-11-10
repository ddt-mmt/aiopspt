import os
from zabbix_utils import ZabbixAPI

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

try:
    zapi = ZabbixAPI(url=url)
    zapi.login(user=user, password=password)
    print("Successfully connected to Zabbix API at", url)
    
    hosts = zapi.host.get(output=["hostid", "host", "name"], filter={"host": ["ME_PAC1", "ME_PAC2", "ME_UPS1"]})
    for h in hosts:
        print(f"\nHost: {h['host']} (ID: {h['hostid']})")
        items = zapi.item.get(hostids=h['hostid'], output=["itemid", "name", "key_", "lastvalue", "lastclock"])
        for item in items:
            print(f"  - [{item['itemid']}] {item['name']} ({item['key_']}) = {item['lastvalue']}")
            
except Exception as e:
    print("Zabbix API connection failed:", e)
