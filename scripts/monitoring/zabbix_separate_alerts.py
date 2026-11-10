#!/usr/bin/env python3
"""
Script untuk memisahkan alert notifikasi Zabbix antara perangkat
MikroTik CCR2216 dan CCR1072.

Langkah-langkah:
1. Buat 2 host group baru: ROUTER-CCR2216 dan ROUTER-CCR1072
2. Assign host yang sesuai ke group barunya (tanpa menghapus dari group lama)
3. Buat 2 action baru dengan notifikasi Telegram terpisah
4. Update action "Alert Telegram - Network" (ID 12) agar exclude group baru
"""

import requests
import json
import sys

URL = "http://localhost/zabbix/api_jsonrpc.php"
TOKEN = "edafd17c4ba07c238181df59519d2f320cc59b91f79235eb0a229758f37d76cc"

# Target user ID for notifications (admin - userid 4)
TARGET_USERID = "4"
# Telegram media type ID
TELEGRAM_MEDIATYPEID = "65"

def zabbix_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": TOKEN,
        "id": 1
    }
    response = requests.post(URL, json=payload)
    result = response.json()
    if "error" in result:
        print(f"ERROR [{method}]: {json.dumps(result['error'], indent=2)}")
        return None
    return result.get("result")

def main():
    print("=" * 70)
    print("ZABBIX ALERT SEPARATION: CCR2216 vs CCR1072")
    print("=" * 70)

    # =========================================================
    # STEP 1: Buat host group baru
    # =========================================================
    print("\n[STEP 1] Membuat host group baru...")

    # Cek apakah group sudah ada
    existing_groups = zabbix_request("hostgroup.get", {
        "output": ["groupid", "name"],
        "filter": {"name": ["ROUTER-CCR2216", "ROUTER-CCR1072"]}
    })

    existing_names = {g["name"]: g["groupid"] for g in (existing_groups or [])}

    ccr2216_groupid = existing_names.get("ROUTER-CCR2216")
    ccr1072_groupid = existing_names.get("ROUTER-CCR1072")

    if not ccr2216_groupid:
        result = zabbix_request("hostgroup.create", {"name": "ROUTER-CCR2216"})
        if result:
            ccr2216_groupid = result["groupids"][0]
            print(f"  ✅ Group 'ROUTER-CCR2216' dibuat (ID: {ccr2216_groupid})")
        else:
            print("  ❌ Gagal membuat group ROUTER-CCR2216")
            sys.exit(1)
    else:
        print(f"  ℹ️  Group 'ROUTER-CCR2216' sudah ada (ID: {ccr2216_groupid})")

    if not ccr1072_groupid:
        result = zabbix_request("hostgroup.create", {"name": "ROUTER-CCR1072"})
        if result:
            ccr1072_groupid = result["groupids"][0]
            print(f"  ✅ Group 'ROUTER-CCR1072' dibuat (ID: {ccr1072_groupid})")
        else:
            print("  ❌ Gagal membuat group ROUTER-CCR1072")
            sys.exit(1)
    else:
        print(f"  ℹ️  Group 'ROUTER-CCR1072' sudah ada (ID: {ccr1072_groupid})")

    # =========================================================
    # STEP 2: Identifikasi dan assign host ke group baru
    # =========================================================
    print("\n[STEP 2] Mengassign host ke group yang sesuai...")

    # Ambil semua host di group ROUTER (24) dan Network-router (23)
    all_router_hosts = zabbix_request("host.get", {
        "output": ["hostid", "host", "name"],
        "selectGroups": ["groupid", "name"],
        "groupids": ["23", "24"]
    })

    ccr2216_hosts = []
    ccr1072_hosts = []

    for host in (all_router_hosts or []):
        hostname = host["host"].upper()
        if "CCR2216" in hostname or "2216" in hostname:
            ccr2216_hosts.append(host)
        elif "CCR1072" in hostname or "1072" in hostname:
            ccr1072_hosts.append(host)

    print(f"\n  Perangkat CCR2216 yang ditemukan ({len(ccr2216_hosts)}):")
    for h in ccr2216_hosts:
        print(f"    - {h['name']} (ID: {h['hostid']})")

    print(f"\n  Perangkat CCR1072 yang ditemukan ({len(ccr1072_hosts)}):")
    for h in ccr1072_hosts:
        print(f"    - {h['name']} (ID: {h['hostid']})")

    # Assign CCR2216 hosts ke group baru (tambahkan, jangan hapus dari group lama)
    for host in ccr2216_hosts:
        current_groups = [{"groupid": g["groupid"]} for g in host["groups"]]
        # Tambahkan group baru jika belum ada
        if not any(g["groupid"] == ccr2216_groupid for g in current_groups):
            current_groups.append({"groupid": ccr2216_groupid})
            result = zabbix_request("host.update", {
                "hostid": host["hostid"],
                "groups": current_groups
            })
            if result:
                print(f"  ✅ {host['name']} ditambahkan ke group ROUTER-CCR2216")
            else:
                print(f"  ❌ Gagal update {host['name']}")
        else:
            print(f"  ℹ️  {host['name']} sudah di group ROUTER-CCR2216")

    # Assign CCR1072 hosts ke group baru
    for host in ccr1072_hosts:
        current_groups = [{"groupid": g["groupid"]} for g in host["groups"]]
        if not any(g["groupid"] == ccr1072_groupid for g in current_groups):
            current_groups.append({"groupid": ccr1072_groupid})
            result = zabbix_request("host.update", {
                "hostid": host["hostid"],
                "groups": current_groups
            })
            if result:
                print(f"  ✅ {host['name']} ditambahkan ke group ROUTER-CCR1072")
            else:
                print(f"  ❌ Gagal update {host['name']}")
        else:
            print(f"  ℹ️  {host['name']} sudah di group ROUTER-CCR1072")

    # =========================================================
    # STEP 3: Buat action terpisah untuk CCR2216
    # =========================================================
    print("\n[STEP 3] Membuat action 'Alert Telegram - CCR2216'...")

    # Cek apakah action sudah ada
    existing_actions = zabbix_request("action.get", {
        "output": ["actionid", "name"],
        "filter": {"name": ["Alert Telegram - CCR2216", "Alert Telegram - CCR1072"]}
    })
    existing_action_names = {a["name"]: a["actionid"] for a in (existing_actions or [])}

    if "Alert Telegram - CCR2216" not in existing_action_names:
        result = zabbix_request("action.create", {
            "name": "Alert Telegram - CCR2216",
            "eventsource": 0,
            "status": 0,
            "esc_period": "1h",
            "filter": {
                "evaltype": 0,  # AND/OR
                "conditions": [
                    {
                        "conditiontype": 0,  # Host group
                        "operator": 0,       # equals
                        "value": ccr2216_groupid
                    }
                ]
            },
            "operations": [
                {
                    "operationtype": 0,  # send message
                    "esc_period": "0",
                    "esc_step_from": 1,
                    "esc_step_to": 1,
                    "opmessage": {
                        "default_msg": 0,
                        "subject": "🚨 CCR2216 Problem: {EVENT.NAME}",
                        "message": (
                            "<b>🔴 [CCR2216 PROBLEM]</b>\r\n\r\n"
                            "<b>Device:</b> {HOST.NAME}\r\n"
                            "<b>IP:</b> {HOST.IP}\r\n"
                            "<b>Status:</b> PROBLEM\r\n"
                            "<b>Severity:</b> {EVENT.SEVERITY}\r\n"
                            "<b>Time:</b> {EVENT.TIME} {EVENT.DATE}\r\n"
                            "<b>Problem:</b> {EVENT.NAME}\r\n"
                            "<b>Last Value:</b> {ITEM.LASTVALUE}\r\n\r\n"
                            "<b>PESAN: TOLONG LAKUKAN CEK PADA PERANGKAT CCR2216 TERKAIT.</b>"
                        ),
                        "mediatypeid": TELEGRAM_MEDIATYPEID
                    },
                    "opmessage_usr": [
                        {"userid": TARGET_USERID}
                    ]
                }
            ],
            "recovery_operations": [
                {
                    "operationtype": 0,
                    "opmessage": {
                        "default_msg": 0,
                        "subject": "✅ CCR2216 Resolved: {EVENT.NAME}",
                        "message": (
                            "<b>🟢 [CCR2216 RESOLVED]</b>\r\n\r\n"
                            "<b>Device:</b> {HOST.NAME}\r\n"
                            "<b>IP:</b> {HOST.IP}\r\n"
                            "<b>Status:</b> RESOLVED\r\n"
                            "<b>Severity:</b> {EVENT.SEVERITY}\r\n"
                            "<b>Recovery Time:</b> {EVENT.RECOVERY.TIME} {EVENT.RECOVERY.DATE}\r\n"
                            "<b>Problem:</b> {EVENT.NAME}\r\n"
                            "<b>Duration:</b> {EVENT.DURATION}\r\n\r\n"
                            "<b>PESAN: PERANGKAT CCR2216 SUDAH NORMAL KEMBALI.</b>"
                        ),
                        "mediatypeid": TELEGRAM_MEDIATYPEID
                    },
                    "opmessage_usr": [
                        {"userid": TARGET_USERID}
                    ]
                }
            ]
        })
        if result:
            print(f"  ✅ Action 'Alert Telegram - CCR2216' dibuat (ID: {result['actionids'][0]})")
        else:
            print("  ❌ Gagal membuat action CCR2216")
    else:
        print(f"  ℹ️  Action 'Alert Telegram - CCR2216' sudah ada (ID: {existing_action_names['Alert Telegram - CCR2216']})")

    # =========================================================
    # STEP 4: Buat action terpisah untuk CCR1072
    # =========================================================
    print("\n[STEP 4] Membuat action 'Alert Telegram - CCR1072'...")

    if "Alert Telegram - CCR1072" not in existing_action_names:
        result = zabbix_request("action.create", {
            "name": "Alert Telegram - CCR1072",
            "eventsource": 0,
            "status": 0,
            "esc_period": "1h",
            "filter": {
                "evaltype": 0,
                "conditions": [
                    {
                        "conditiontype": 0,
                        "operator": 0,
                        "value": ccr1072_groupid
                    }
                ]
            },
            "operations": [
                {
                    "operationtype": 0,
                    "esc_period": "0",
                    "esc_step_from": 1,
                    "esc_step_to": 1,
                    "opmessage": {
                        "default_msg": 0,
                        "subject": "🚨 CCR1072 Problem: {EVENT.NAME}",
                        "message": (
                            "<b>🔴 [CCR1072 PROBLEM]</b>\r\n\r\n"
                            "<b>Device:</b> {HOST.NAME}\r\n"
                            "<b>IP:</b> {HOST.IP}\r\n"
                            "<b>Status:</b> PROBLEM\r\n"
                            "<b>Severity:</b> {EVENT.SEVERITY}\r\n"
                            "<b>Time:</b> {EVENT.TIME} {EVENT.DATE}\r\n"
                            "<b>Problem:</b> {EVENT.NAME}\r\n"
                            "<b>Last Value:</b> {ITEM.LASTVALUE}\r\n\r\n"
                            "<b>PESAN: TOLONG LAKUKAN CEK PADA PERANGKAT CCR1072 TERKAIT.</b>"
                        ),
                        "mediatypeid": TELEGRAM_MEDIATYPEID
                    },
                    "opmessage_usr": [
                        {"userid": TARGET_USERID}
                    ]
                }
            ],
            "recovery_operations": [
                {
                    "operationtype": 0,
                    "opmessage": {
                        "default_msg": 0,
                        "subject": "✅ CCR1072 Resolved: {EVENT.NAME}",
                        "message": (
                            "<b>🟢 [CCR1072 RESOLVED]</b>\r\n\r\n"
                            "<b>Device:</b> {HOST.NAME}\r\n"
                            "<b>IP:</b> {HOST.IP}\r\n"
                            "<b>Status:</b> RESOLVED\r\n"
                            "<b>Severity:</b> {EVENT.SEVERITY}\r\n"
                            "<b>Recovery Time:</b> {EVENT.RECOVERY.TIME} {EVENT.RECOVERY.DATE}\r\n"
                            "<b>Problem:</b> {EVENT.NAME}\r\n"
                            "<b>Duration:</b> {EVENT.DURATION}\r\n\r\n"
                            "<b>PESAN: PERANGKAT CCR1072 SUDAH NORMAL KEMBALI.</b>"
                        ),
                        "mediatypeid": TELEGRAM_MEDIATYPEID
                    },
                    "opmessage_usr": [
                        {"userid": TARGET_USERID}
                    ]
                }
            ]
        })
        if result:
            print(f"  ✅ Action 'Alert Telegram - CCR1072' dibuat (ID: {result['actionids'][0]})")
        else:
            print("  ❌ Gagal membuat action CCR1072")
    else:
        print(f"  ℹ️  Action 'Alert Telegram - CCR1072' sudah ada (ID: {existing_action_names['Alert Telegram - CCR1072']})")

    # =========================================================
    # STEP 5: Update action "Alert Telegram - Network" (ID 12)
    # agar exclude group CCR2216 dan CCR1072 baru
    # =========================================================
    print("\n[STEP 5] Mengupdate action 'Alert Telegram - Network' agar exclude CCR2216 & CCR1072...")

    # Ambil kondisi filter yang sudah ada di action 12
    action_12 = zabbix_request("action.get", {
        "output": ["actionid"],
        "selectFilter": "extend",
        "actionids": ["12"]
    })

    if action_12:
        current_filter = action_12[0]["filter"]
        current_conditions = current_filter.get("conditions", [])

        # Tambahkan condition exclude untuk group baru
        # conditiontype 0 = host group, operator 1 = does not equal
        new_conditions = list(current_conditions)

        # Cek apakah sudah ada condition exclude untuk group ini
        existing_exclude_values = {
            c["value"] for c in current_conditions
            if c["conditiontype"] == "0" and c["operator"] == "1"
        }

        added = False
        if ccr2216_groupid not in existing_exclude_values:
            new_conditions.append({
                "conditiontype": "0",
                "operator": "1",  # does not equal
                "value": ccr2216_groupid
            })
            added = True

        if ccr1072_groupid not in existing_exclude_values:
            new_conditions.append({
                "conditiontype": "0",
                "operator": "1",  # does not equal
                "value": ccr1072_groupid
            })
            added = True

        if added:
            # Update filter: gunakan custom expression
            # A or B = Network-router OR ROUTER (tetap sama)
            # AND C AND D = NOT CCR2216 AND NOT CCR1072 (baru)
            result = zabbix_request("action.update", {
                "actionid": "12",
                "filter": {
                    "evaltype": 3,  # custom expression
                    "formula": "(A or B) and C and D",
                    "conditions": [
                        {
                            "conditiontype": "0",
                            "operator": "0",  # equals
                            "value": "23",    # Network-router
                            "formulaid": "A"
                        },
                        {
                            "conditiontype": "0",
                            "operator": "0",  # equals
                            "value": "24",    # ROUTER
                            "formulaid": "B"
                        },
                        {
                            "conditiontype": "0",
                            "operator": "1",  # not equals
                            "value": ccr2216_groupid,
                            "formulaid": "C"
                        },
                        {
                            "conditiontype": "0",
                            "operator": "1",  # not equals
                            "value": ccr1072_groupid,
                            "formulaid": "D"
                        }
                    ]
                }
            })
            if result:
                print("  ✅ Action 'Alert Telegram - Network' berhasil diupdate")
                print("     Filter: (Network-router OR ROUTER) AND NOT CCR2216 AND NOT CCR1072")
            else:
                print("  ❌ Gagal update action Network")
        else:
            print("  ℹ️  Action sudah memiliki exclude condition untuk kedua group")

    # =========================================================
    # STEP 6: Verifikasi
    # =========================================================
    print("\n" + "=" * 70)
    print("VERIFIKASI KONFIGURASI")
    print("=" * 70)

    # Verifikasi host groups
    print("\n📋 Host Groups Baru:")
    groups = zabbix_request("hostgroup.get", {
        "output": ["groupid", "name"],
        "filter": {"name": ["ROUTER-CCR2216", "ROUTER-CCR1072"]}
    })
    for g in (groups or []):
        hosts = zabbix_request("host.get", {
            "output": ["hostid", "name", "status"],
            "groupids": [g["groupid"]]
        })
        print(f"\n  Group: {g['name']} (ID: {g['groupid']})")
        for h in (hosts or []):
            status = "✅ Enabled" if h["status"] == "0" else "⏸️  Disabled"
            print(f"    - {h['name']} [{status}]")

    # Verifikasi actions
    print("\n📋 Actions Aktif (Trigger):")
    actions = zabbix_request("action.get", {
        "output": ["actionid", "name", "status"],
        "filter": {"eventsource": 0}
    })
    for a in (actions or []):
        status = "✅ Enabled" if a["status"] == "0" else "❌ Disabled"
        print(f"  [{status}] {a['name']} (ID: {a['actionid']})")

    print("\n" + "=" * 70)
    print("SELESAI! Alert CCR2216 dan CCR1072 sudah dipisah.")
    print("=" * 70)
    print("""
RINGKASAN PERUBAHAN:
1. ✅ Host group 'ROUTER-CCR2216' dibuat untuk perangkat MikroTik CCR2216
2. ✅ Host group 'ROUTER-CCR1072' dibuat untuk perangkat MikroTik CCR1072
3. ✅ Action 'Alert Telegram - CCR2216' dibuat dengan notifikasi khusus
4. ✅ Action 'Alert Telegram - CCR1072' dibuat dengan notifikasi khusus
5. ✅ Action 'Alert Telegram - Network' diupdate agar exclude CCR2216 & CCR1072

NOTIFIKASI TELEGRAM:
- CCR2216 → Subject: "🚨 CCR2216 Problem: ..."  /  "✅ CCR2216 Resolved: ..."
- CCR1072 → Subject: "🚨 CCR1072 Problem: ..."  /  "✅ CCR1072 Resolved: ..."
- Network lain → Subject: "🚨 Network Problem: ..." (tetap sama)
""")

if __name__ == "__main__":
    main()
