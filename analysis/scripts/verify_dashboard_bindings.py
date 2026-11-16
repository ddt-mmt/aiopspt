#!/usr/bin/env python3
"""
AIOps — Dashboard binding verifier (READ-ONLY).

Memeriksa bahwa SETIAP target panel di config/aiops_facility_dashboard.json
menunjuk ke item Zabbix yang benar-benar ada, untuk tiap host pada variabel
$ups_host / $pac_host. Sebelum perbaikan (analysis/FINDINGS.md F-4), panel
telemetri mentah menunjuk item yang tidak ada → panel kosong.

Hanya memakai user.login + host.get + item.get (read-only).

Usage:
    ZABBIX_PASS=... python3 analysis/scripts/verify_dashboard_bindings.py
Exit code 0 = semua cocok, 1 = ada yang tidak cocok.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
DASH = REPO / "config" / "aiops_facility_dashboard.json"
API = os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix").rstrip("/") + "/api_jsonrpc.php"
USER = os.getenv("ZABBIX_USER", "admin")
PASS = os.getenv("ZABBIX_PASS", "")

HOSTS = {
    "$ups_host": ["ME_UPS1", "ME_UPS2", "ME_UPS3"],
    "$pac_host": ["ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"],
}


def rpc(auth, method, params):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "auth": auth, "id": 1}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    if not PASS:
        print("ERROR: set ZABBIX_PASS env var.", file=sys.stderr)
        sys.exit(2)
    auth = rpc(None, "user.login", {"username": USER, "password": PASS}).get("result")
    if not auth:
        print("ERROR: login failed.", file=sys.stderr)
        sys.exit(2)

    dash = json.loads(DASH.read_text())
    hostid_cache = {}
    failures = []
    checked = 0

    for panel in dash.get("panels", []):
        for t in panel.get("targets") or []:
            item = t.get("item")
            hostvar = t.get("host")
            if not item or hostvar not in HOSTS:
                continue
            for host in HOSTS[hostvar]:
                if host not in hostid_cache:
                    res = rpc(auth, "host.get", {"output": ["hostid"], "filter": {"host": [host]}})["result"]
                    hostid_cache[host] = res[0]["hostid"] if res else None
                hid = hostid_cache[host]
                if not hid:
                    failures.append(f"{host}: host not found")
                    continue
                matches = rpc(auth, "item.get", {"hostids": hid, "filter": {"name": [item]},
                                                 "output": ["itemid"]})["result"]
                checked += 1
                status = "OK" if len(matches) == 1 else f"BAD({len(matches)})"
                if len(matches) != 1:
                    failures.append(f"{panel.get('title')} | {host} | {item!r} -> {len(matches)} matches")
                print(f"  [{status:7}] {host:8} {item!r}")

    print(f"\nchecked={checked} failures={len(failures)}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("ALL PANEL TARGETS RESOLVE ✔")


if __name__ == "__main__":
    main()
