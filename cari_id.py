from zabbix_utils import ZabbixAPI

ZABBIX_URL = "http://10.28.1.110/zabbix"
ZABBIX_USER = "admin"
ZABBIX_PASS = "1sampai6"

def main():
    print("Membangun koneksi ke API...")
    zapi = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASS)

    print("Menarik daftar Item ID dari Host 10689...\n")
    # Mengambil daftar ID dan Nama Item khusus untuk host tersebut
    items = zapi.item.get(
        hostids="10689",
        output=["itemid", "name"]
    )

    # Mencetak hasilnya ke layar terminal
    for item in items:
        print(f"ID: {item['itemid']}  --->  {item['name']}")

if __name__ == "__main__":
    main()
