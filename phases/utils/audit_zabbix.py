import os
from zabbix_utils import ZabbixAPI

ZABBIX_URL = "http://10.28.1.110/zabbix"
ZABBIX_USER = "admin"
ZABBIX_PASS = "1sampai6"

def main():
    try:
        zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)
        hosts = zapi.host.get(filter={'host': ['ME_PAC4']}, output=['hostid', 'host', 'name'])
        if not hosts:
            print("Host ME_PAC4 tidak ditemukan di Zabbix.")
            return
        
        host = hosts[0]
        hostid = host['hostid']
        print(f"Host: {host['host']} (ID: {hostid}, Name: {host['name']})")

        items = zapi.item.get(hostids=hostid, output='extend')
        print(f"\nDitemukan {len(items)} item untuk {host['host']}:")
        for item in items:
            print(f"- ID: {item.get('itemid')} | Name: {item.get('name')} | Key: {item.get('key_')} | OID: {item.get('snmp_oid')} | Preprocessing: {item.get('preprocessing')}")

        # Get latest history for items
        print("\nNilai History Terbaru:")
        for item in items:
            try:
                history = zapi.history.get(itemids=[item['itemid']], limit=3, sortfield='clock', sortorder='DESC')
                print(f"  Item {item.get('key_')} (ID {item.get('itemid')}):")
                if history:
                    for h in history:
                        print(f"    Clock: {h['clock']} | Value: {h['value']}")
                else:
                    print("    Tidak ada data history.")
            except Exception as e:
                print(f"    Gagal ambil history: {e}")

    except Exception as e:
        print(f"Error querying Zabbix: {e}")

if __name__ == '__main__':
    main()
