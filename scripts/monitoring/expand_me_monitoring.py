import os
from datetime import datetime
from zabbix_utils import ZabbixAPI, Sender, ItemValue

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")
zabbix_server_ip = os.getenv("ZABBIX_SERVER_IP", "10.28.1.110")

def main():
    print("Connecting to Zabbix API...")
    zapi = ZabbixAPI(url=url)
    zapi.login(user=user, password=password)
    print("Successfully connected.")

    target_hosts = ["ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4", "ME_UPS1", "ME_UPS2", "ME_UPS3"]
    hosts = zapi.host.get(output=["hostid", "host"], filter={"host": target_hosts})
    
    print(f"Found {len(hosts)} matching hosts in Zabbix.")

    for h in hosts:
        hostid = h['hostid']
        hostname = h['host']
        print(f"\nProcessing Host: {hostname} (ID: {hostid})")
        
        # Determine item key based on host type
        if "PAC" in hostname:
            key_name = "pac.maintenance.filter.status"
            item_name = "PAC Filter Maintenance Status"
        else:
            key_name = "ups.maintenance.battery.status"
            item_name = "UPS Battery Maintenance Status"
            
        # Ensure item exists
        items = zapi.item.get(hostids=hostid, filter={"key_": [key_name]}, output=["itemid"])
        if not items:
            try:
                zapi.item.create({
                    'name': item_name,
                    'key_': key_name,
                    'hostid': hostid,
                    'type': 2, # Zabbix trapper
                    'value_type': 3, # Numeric unsigned
                    'interfaceid': 0,
                    'delay': '0'
                })
                print(f"  -> Created trapper item '{key_name}' successfully.")
            except Exception as e:
                print(f"  -> Failed to create item {key_name}: {e}")
        else:
            print(f"  -> Item '{key_name}' already exists.")

        # Push test/baseline value (0 = Normal/OK) using ItemValue
        try:
            sender = Sender(server=zabbix_server_ip, port=10051)
            packet = [ItemValue(host=hostname, key=key_name, value=0)]
            res = sender.send(packet)
            print(f"  -> Zabbix sender result for {hostname}: {res}")
        except Exception as e:
            print(f"  -> Failed to send test data via sender: {e}")

if __name__ == "__main__":
    main()
