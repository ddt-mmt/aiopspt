import os
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Memperbarui OID di Template_Schneider_Uniflair_PAC_Custom (ID 10694)...")
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

    template_id = "10694"
    correct_oids = {
        "return.temp.c": ".1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1.10",
        "supply.temp.c": ".1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1.12",
        "return.humidity.rh": ".1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1.18",
        "evaporator.fan.speed": ".1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1.1"
    }

    items = zapi.item.get(hostids=template_id, output=["itemid", "key_", "snmp_oid"])
    for it in items:
        key = it["key_"]
        if key in correct_oids:
            itemid = it["itemid"]
            new_oid = correct_oids[key]
            print(f"Updating template item {key} (ID: {itemid}) to OID: {new_oid}")
            zapi.item.update({
                "itemid": itemid,
                "snmp_oid": new_oid
            })
            print(f"Berhasil memperbarui {key} di template.")

    print("Pembaruan OID template selesai.")

if __name__ == "__main__":
    main()
