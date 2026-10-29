import os
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Menghubungkan ke Zabbix API untuk memperbaiki OID ME_PAC1 dan ME_PAC2...")
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

    target_hosts = ["ME_PAC1", "ME_PAC2"]
    oid_mapping = {
        "return.temp.c": ".1.3.6.1.4.1.9839.2.1.2.1.0",
        "supply.temp.c": ".1.3.6.1.4.1.9839.2.1.2.10.0",
        "return.humidity.rh": ".1.3.6.1.4.1.9839.2.1.2.6.0"
    }

    for hname in target_hosts:
        hosts = zapi.host.get(filter={"host": [hname]}, output=["hostid"])
        if not hosts:
            print(f"Host {hname} tidak ditemukan.")
            continue
        
        hostid = hosts[0]["hostid"]
        items = zapi.item.get(hostids=hostid, output=["itemid", "key_", "snmp_oid"])
        
        for item in items:
            key = item["key_"]
            if key in oid_mapping:
                itemid = item["itemid"]
                current_oid = item["snmp_oid"]
                new_oid = oid_mapping[key]
                if current_oid != new_oid:
                    print(f"Memperbarui {hname} -> Key: {key} (ID: {itemid}) | OID lama: {current_oid} => OID baru: {new_oid}")
                    zapi.item.update({
                        "itemid": itemid,
                        "snmp_oid": new_oid
                    })
                    print(f"Berhasil memperbarui {key} pada {hname}.")
                else:
                    print(f"Item {key} pada {hname} sudah menggunakan OID yang benar: {current_oid}")

    print("Perbaikan OID selesai.")

if __name__ == "__main__":
    main()
