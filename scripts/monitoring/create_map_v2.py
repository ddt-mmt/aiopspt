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

# Delete existing map first
zabbix_request("map.delete", ["2"])

# Hosts with SNMP enabled (based on API check)
snmp_hosts = [
    {"hostid": "10677", "name": "RO-CIBINONG-1", "type": "router"},
    {"hostid": "10688", "name": "ME_UPS1", "type": "ups"},
    {"hostid": "10689", "name": "ME_PAC1", "type": "pac"},
    {"hostid": "10690", "name": "ME_PAC2", "type": "pac"},
    {"hostid": "10696", "name": "ME_PAC3", "type": "pac"},
    {"hostid": "10697", "name": "ME_UPS2", "type": "ups"},
    {"hostid": "10698", "name": "ME_PAC4", "type": "pac"},
    {"hostid": "10701", "name": "ME_UPS3", "type": "ups"}
]

# Core switches are essential for topology logic (adding them back even if not in the direct SNMP list, or assume they are the hubs)
# For this specific request, I will only use the 8 SNMP hosts found.
# I'll place the Router as the top center, and others in a wider arc.

ICONS = {
    "router": "10",
    "ups": "65",
    "pac": "88"
}

elements = []
width = 1920
height = 900 # Adjusted for 1080 dashboard view

# Place Router at top center
elements.append({
    "selementid": "0",
    "elements": [{"hostid": "10677"}],
    "elementtype": 0,
    "iconid_off": ICONS["router"],
    "x": width // 2, "y": 150,
    "label": "RO-CIBINONG-1"
})

# Place others in a wide line
other_hosts = [h for h in snmp_hosts if h["hostid"] != "10677"]
spacing = width // (len(other_hosts) + 1)

for i, h in enumerate(other_hosts):
    elements.append({
        "selementid": str(i + 1),
        "elements": [{"hostid": h["hostid"]}],
        "elementtype": 0,
        "iconid_off": ICONS[h["type"]],
        "x": spacing * (i + 1), "y": 500,
        "label": h["name"]
    })

# Connect everything to the Router
links = []
for i in range(1, len(elements)):
    links.append({
        "selementid1": "0",
        "selementid2": str(i),
        "color": "00FF00",
        "width": 2
    })

map_params = {
    "name": "Network Topology Gemini CLI",
    "width": width,
    "height": height,
    "backgroundid": "0",
    "label_type": 0,
    "selements": elements,
    "links": links
}

result = zabbix_request("map.create", map_params)
print(json.dumps(result, indent=2))
