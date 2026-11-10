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

# Sysmap ID from previous step
sysmapid = "2"

dashboard_params = {
    "name": "Gemini Topology Dashboard",
    "pages": [
        {
            "widgets": [
                {
                    "type": "map",
                    "name": "Network Topology",
                    "x": 0,
                    "y": 0,
                    "width": 24,
                    "height": 20,
                    "fields": [
                        {
                            "type": 8, # Map
                            "name": "sysmapid",
                            "value": sysmapid
                        }
                    ]
                }
            ]
        }
    ]
}

result = zabbix_request("dashboard.create", dashboard_params)
print(json.dumps(result, indent=2))
