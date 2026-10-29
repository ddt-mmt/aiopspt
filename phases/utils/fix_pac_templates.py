import os
from zabbix_utils import ZabbixAPI

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "1sampai6")

def main():
    print("Menghubungkan ke Zabbix API untuk mengganti template ME_PAC1 dan ME_PAC2...")
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

    target_hosts = ["ME_PAC1", "ME_PAC2"]
    correct_template_id = "10699" # Template_Carel_TDAV_PAC_Custom
    old_template_id = "10694"     # Template_Schneider_Uniflair_PAC_Custom

    for hname in target_hosts:
        hosts = zapi.host.get(filter={"host": [hname]}, selectParentTemplates=["templateid"], output=["hostid"])
        if not hosts:
            print(f"Host {hname} tidak ditemukan.")
            continue
        
        hostid = hosts[0]["hostid"]
        current_templates = [t["templateid"] for t in hosts[0].get("parentTemplates", [])]
        print(f"Host {hname} current templates: {current_templates}")

        # Replace old template with correct Carel template
        new_templates = [t for t in current_templates if t != old_template_id]
        if correct_template_id not in new_templates:
            new_templates.append(correct_template_id)

        print(f"Updating {hname} (ID: {hostid}) templates to: {new_templates}")
        try:
            zapi.host.update({
                "hostid": hostid,
                "templates": [{"templateid": tid} for tid in new_templates]
            })
            print(f"Berhasil memperbarui template untuk {hname}.")
        except Exception as e:
            print(f"Gagal memperbarui template untuk {hname}: {e}")

    print("Proses pembaruan template selesai.")

if __name__ == "__main__":
    main()
