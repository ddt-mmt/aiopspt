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

# Host IDs from previous research
hosts = {
    "SW-CORE-1": "10683",
    "SW-CORE-2": "10684",
    "RO-CIBINONG-1": "10677",
    "RO-JKT-BRIN-2": "10673",
    "RO-BB-JKT-BRIN": "10674",
    "RO-GW-1": "10681",
    "RO-GW-2": "10682",
    "RO-LIPI": "10685",
    "RO-SERPONG": "10686",
    "RO-CCR-SERPONG": "10687",
    "ME_UPS1": "10688",
    "ME_UPS2": "10697",
    "ME_UPS3": "10701",
    "ME_PAC1": "10689",
    "ME_PAC2": "10690",
    "ME_PAC3": "10696",
    "ME_PAC4": "10698",
    "SRV-KERUING03": "10678",
    "Zabbix-server": "10084",
    "PC-SEMERU01": "10700"
}

# Icon IDs (based on research)
ICONS = {
    "router": "10",  # Crypto-router_(96)
    "switch": "60",  # Network_(96)
    "server": "94",  # Rackmountable_1U_server_2D_(96)
    "ups": "65",     # Network_adapter_(96)
    "pac": "88",     # Rack_42_(96)
    "pc": "70"       # Notebook_(96)
}

elements = []
selementid_counter = 0

# Core Switches (Center)
elements.append({
    "selementid": str(selementid_counter),
    "elements": [{"hostid": hosts["SW-CORE-1"]}],
    "elementtype": 0, # Host
    "iconid_off": ICONS["switch"],
    "x": 400, "y": 300,
    "label": "SW-CORE-1"
})
core1_id = str(selementid_counter)
selementid_counter += 1

elements.append({
    "selementid": str(selementid_counter),
    "elements": [{"hostid": hosts["SW-CORE-2"]}],
    "elementtype": 0,
    "iconid_off": ICONS["switch"],
    "x": 600, "y": 300,
    "label": "SW-CORE-2"
})
core2_id = str(selementid_counter)
selementid_counter += 1

# Routers (Top)
router_list = ["RO-CIBINONG-1", "RO-JKT-BRIN-2", "RO-BB-JKT-BRIN", "RO-GW-1", "RO-GW-2", "RO-LIPI", "RO-SERPONG", "RO-CCR-SERPONG"]
for i, r in enumerate(router_list):
    elements.append({
        "selementid": str(selementid_counter),
        "elements": [{"hostid": hosts[r]}],
        "elementtype": 0,
        "iconid_off": ICONS["router"],
        "x": 100 + (i * 120), "y": 100,
        "label": r
    })
    selementid_counter += 1

# UPS & PAC (Bottom)
peripherals = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]
for i, p in enumerate(peripherals):
    icon = ICONS["ups"] if "UPS" in p else ICONS["pac"]
    elements.append({
        "selementid": str(selementid_counter),
        "elements": [{"hostid": hosts[p]}],
        "elementtype": 0,
        "iconid_off": icon,
        "x": 100 + (i * 120), "y": 500,
        "label": p
    })
    selementid_counter += 1

# Servers & PC (Sides)
others = [("SRV-KERUING03", ICONS["server"], 100, 300), 
          ("Zabbix-server", ICONS["server"], 900, 300),
          ("PC-SEMERU01", ICONS["pc"], 900, 500)]

for name, icon, x, y in others:
    elements.append({
        "selementid": str(selementid_counter),
        "elements": [{"hostid": hosts[name]}],
        "elementtype": 0,
        "iconid_off": icon,
        "x": x, "y": y,
        "label": name
    })
    selementid_counter += 1

# Links (Connect everything to Core 1 and Core 2 for redundancy)
links = []
for i in range(2, selementid_counter):
    links.append({
        "selementid1": str(i),
        "selementid2": core1_id,
        "color": "00FF00" # Green
    })
    links.append({
        "selementid1": str(i),
        "selementid2": core2_id,
        "color": "00FF00"
    })

# Connection between Cores
links.append({
    "selementid1": core1_id,
    "selementid2": core2_id,
    "color": "FF0000", # Red for Core link
    "width": 3
})

map_params = {
    "name": "Network Topology Gemini CLI",
    "width": 1000,
    "height": 700,
    "backgroundid": "0",
    "label_type": 0,
    "selements": elements,
    "links": links
}

result = zabbix_request("map.create", map_params)
print(json.dumps(result, indent=2))
