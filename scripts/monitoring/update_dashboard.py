import requests
import json

URL = "http://localhost/zabbix/api_jsonrpc.php"
TOKEN = "fbd0dfe9685382cc9bc37582192515151a76f0adc206bedc69e83ee62940ff8f"

def zabbix_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": TOKEN,
        "id": 1
    }
    response = requests.post(URL, json=payload)
    return response.json()

# New Sysmap ID
sysmapid = "3"
dashboardid = "404"

dashboard_params = {
    "dashboardid": dashboardid,
    "pages": [
        {
            "widgets": [
                {
                    "type": "map",
                    "name": "Network Topology Full Width",
                    "x": 0,
                    "y": 0,
                    "width": 24, # Full width in Zabbix grid
                    "height": 20,
                    "fields": [
                        {
                            "type": 8,
                            "name": "sysmapid",
                            "value": sysmapid
                        }
                    ]
                }
            ]
        }
    ]
}

result = zabbix_request("dashboard.update", dashboard_params)
print(json.dumps(result, indent=2))
