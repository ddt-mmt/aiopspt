import os
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)
    hosts = zapi.host.get(output=['hostid', 'host', 'name'])
    target_hosts = [h for h in hosts if h['host'].startswith('ME_UPS') or h['host'].startswith('ME_PAC')]
    
    for h in target_hosts:
        print(f"\n=== Host: {h['host']} (ID: {h['hostid']}, Name: {h['name']}) ===")
        items = zapi.item.get(hostids=h['hostid'], output=['itemid', 'name', 'key_', 'value_type', 'status'])
        for item in items:
            print(f"  - [{item['itemid']}] {item['key_']} | Name: {item['name']} | Type: {item['value_type']} | Status: {item['status']}")

if __name__ == '__main__':
    main()
