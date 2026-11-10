import os
from zabbix_utils import ZabbixAPI

url = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
user = os.getenv("ZABBIX_USER", "admin")
password = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Connecting to Zabbix API...")
    zapi = ZabbixAPI(url=url)
    zapi.login(user=user, password=password)
    print("Successfully connected.")

    target_hosts = ["ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4", "ME_UPS1", "ME_UPS2", "ME_UPS3"]
    hosts = zapi.host.get(output=["hostid", "host"], filter={"host": target_hosts})

    for h in hosts:
        hostid = h['hostid']
        hostname = h['host']
        print(f"\nProcessing Host: {hostname} (ID: {hostid})")

        is_pac = "PAC" in hostname

        if is_pac:
            trig_name = f"{hostname}: PAC Filter Maintenance Required"
            expression = f"last(/{hostname}/pac.maintenance.filter.status)=1"
        else:
            trig_name = f"{hostname}: UPS Battery Maintenance Required"
            expression = f"last(/{hostname}/ups.maintenance.battery.status)=1"

        existing_triggers = zapi.trigger.get(hostids=hostid, filter={"description": [trig_name]}, output=["triggerid"])
        if not existing_triggers:
            try:
                zapi.trigger.create({
                    'description': trig_name,
                    'expression': expression,
                    'priority': 3, # Average severity
                    'status': 0 # Enabled
                })
                print(f"  -> Created trigger '{trig_name}' successfully.")
            except Exception as e:
                print(f"  -> Failed to create trigger: {e}")
        else:
            print(f"  -> Trigger '{trig_name}' already exists.")

if __name__ == "__main__":
    main()
