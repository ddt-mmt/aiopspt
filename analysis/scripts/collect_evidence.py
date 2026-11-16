#!/usr/bin/env python3
"""
AIOps Analysis — Evidence Collector (READ-ONLY).

Menarik bukti langsung dari Zabbix API (read-only: user.login, host.get,
item.get, history.get) dan menuliskannya ke analysis/evidence/ sebagai
artefak JSON/TXT yang dapat di-commit dan diaudit ulang.

TIDAK melakukan write apa pun ke Zabbix (tidak ada item.create / sender.send).
Kredensial diambil dari environment variable, dengan fallback HANYA untuk
memudahkan reproduksi lokal oleh pemilik sistem.

Usage:
    ZABBIX_URL=http://10.28.1.110/zabbix \
    ZABBIX_USER=admin ZABBIX_PASS=... \
    python3 analysis/scripts/collect_evidence.py
"""
import json
import os
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
ZABBIX_USER = os.getenv("ZABBIX_USER", "admin")
ZABBIX_PASS = os.getenv("ZABBIX_PASS", "")

API = ZABBIX_URL.rstrip("/") + "/api_jsonrpc.php"
OUT = Path(__file__).resolve().parent.parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

HOSTS = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]


def rpc(auth, method, params):
    body = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "auth": auth, "id": 1}
    ).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=40))


def main():
    if not ZABBIX_PASS:
        print("ERROR: set ZABBIX_PASS env var.", file=sys.stderr)
        sys.exit(2)

    login = rpc(None, "user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
    auth = login.get("result")
    if not auth:
        print(f"ERROR: login failed: {login}", file=sys.stderr)
        sys.exit(2)

    # 1. Item inventory per host (name, key, type, lastvalue, lastclock).
    inventory = {}
    hostids = {}
    for host in HOSTS:
        res = rpc(auth, "host.get", {"output": ["hostid"], "filter": {"host": [host]}})["result"]
        if not res:
            inventory[host] = {"error": "host not found"}
            continue
        hid = res[0]["hostid"]
        hostids[host] = hid
        items = rpc(
            auth,
            "item.get",
            {"hostids": hid, "output": ["itemid", "key_", "name", "type", "value_type", "lastvalue", "lastclock"]},
        )["result"]
        inventory[host] = {"hostid": hid, "item_count": len(items), "items": items}
        print(f"  {host}: {len(items)} items")

    (OUT / "zabbix_item_inventory.json").write_text(json.dumps(inventory, indent=2))

    # 2. Provenance map: synthetic (trapper) keys vs real (SNMP) keys for the
    #    fault-prone subsystems (power load, battery voltage/temp, temps).
    prov_keys = [
        "output.load", "battery.temp", "battery.voltage",
        "ups.output.load", "ups.battery.temp", "ups.battery.voltage",
        "output.load[upsHighPrecOutputLoad]",
        "battery.voltage[upsHighPrecBatteryActualVoltage]",
        "return.temp.c", "supply.temp.c", "return.humidity.rh",
        "ups.health.score", "ups.ttf.hours", "ups.action.status",
        "pac.health.score", "pac.ttf.hours", "pac.action.status",
    ]
    provenance = {}
    for host, hid in hostids.items():
        rows = []
        for key in prov_keys:
            it = rpc(auth, "item.get", {"hostids": hid, "filter": {"key_": [key]},
                                        "output": ["itemid", "key_", "name", "type", "lastvalue"]})["result"]
            for x in it:
                rows.append(x)
        provenance[host] = rows
    (OUT / "provenance_map.json").write_text(json.dumps(provenance, indent=2))

    # 3. 30-day data-volume + range comparison: synthetic trapper vs real SNMP,
    #    plus health-score distribution (random-fallback detection).
    now = int(time.time())
    frm = now - 30 * 86400
    compare = {}
    for host in ["ME_UPS1", "ME_PAC1"]:
        hid = hostids.get(host)
        if not hid:
            continue
        compare[host] = {}
        for key in ["output.load", "output.load[upsHighPrecOutputLoad]",
                    "battery.voltage", "battery.voltage[upsHighPrecBatteryActualVoltage]",
                    "return.temp.c", "return.humidity.rh",
                    "ups.health.score", "pac.health.score", "ups.ttf.hours", "pac.ttf.hours"]:
            it = rpc(auth, "item.get", {"hostids": hid, "filter": {"key_": [key]},
                                        "output": ["itemid", "value_type"]})["result"]
            if not it:
                compare[host][key] = {"status": "ITEM_MISSING"}
                continue
            vt = int(it[0]["value_type"])
            hist = rpc(auth, "history.get", {
                "itemids": [it[0]["itemid"]],
                "history": 3 if vt == 3 else vt,
                "time_from": frm, "time_till": now,
                "output": ["clock", "value"], "limit": 5000,
            })["result"]
            vals = [float(x["value"]) for x in hist if x["value"] not in ("", "-")]
            entry = {"status": "OK", "n": len(hist)}
            if vals:
                entry.update({
                    "min": round(min(vals), 3), "max": round(max(vals), 3),
                    "mean": round(statistics.mean(vals), 3),
                    "stdev": round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0,
                    "last": vals[0] if hist else None,
                })
            compare[host][key] = entry
        print(f"  compared {host}")
    (OUT / "data_volume_compare.json").write_text(json.dumps(compare, indent=2))

    # 4. Human-readable evidence summary.
    lines = [
        "AIOps Analysis — Evidence Summary (read-only capture)",
        f"captured_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"zabbix_api: {API}",
        "",
        "== 30-day data-volume / range comparison ==",
    ]
    for host, keys in compare.items():
        lines.append(f"\n--- {host} ---")
        for key, e in keys.items():
            lines.append(f"  {key:52} {e}")
    (OUT / "data_volume_compare.txt").write_text("\n".join(lines))

    print(f"\nEvidence written to {OUT}")


if __name__ == "__main__":
    main()
