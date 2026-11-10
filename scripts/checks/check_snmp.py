import requests
import json

TOKEN = "db1e2392b9af390a9af93cde1842b47b782f5cba1ab6c68ba319efa4a1c55c50"
URL = "http://localhost/zabbix/api_jsonrpc.php"

def zabbix_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": TOKEN,
        "id": 1
    }
    response = requests.post(URL, json=payload)
    return response.json().get("result")

# Get hosts in SWITCH group
hosts = zabbix_request("host.get", {
    "groupids": ["32"],
    "output": ["hostid", "host", "name"],
    "selectInterfaces": ["ip", "available", "error", "type"]
})

print(f"{'Hostname':<20} | {'IP':<15} | {'Status (SNMP)':<15} | {'Error'}")
print("-" * 75)

for host in hosts:
    # Interface type 2 is SNMP
    snmp_int = next((i for i in host["interfaces"] if i["type"] == "2"), None)
    
    if snmp_int:
        status_map = {"0": "Unknown", "1": "Available", "2": "Unavailable"}
        status = status_map.get(snmp_int["available"], "Unknown")
        error = snmp_int["error"]
        print(f"{host['name']:<20} | {snmp_int['ip']:<15} | {status:<15} | {error}")
    else:
        print(f"{host['name']:<20} | {'N/A':<15} | {'No SNMP Int':<15} |")
