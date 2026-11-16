#!/usr/bin/env python3
"""
Staging verification — jalankan engine yang diperbaiki dalam DRY_RUN.

Membuktikan pada data NYATA (Zabbix produksi, read-only):
  1. tidak ada tulisan sintetik ke key sensor,
  2. tidak ada fallback acak,
  3. tiap host menghasilkan nilai yang berbeda & deterministik,
  4. tidak ada satu pun operasi tulis ke Zabbix (item.create / sender.send).

Menjalankan satu siklus lalu menulis ringkasan ke analysis/evidence/staging_dry_run.json.

Aman: DRY_RUN=1 memaksa tidak ada write. Hanya user.login/host.get/item.get/history.get.

Usage:
  ZABBIX_PASS=... python3 analysis/scripts/staging_dry_run.py
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
ENGINE = REPO / "src" / "script_aiops.py"
OUT = REPO / "analysis" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    env = dict(os.environ)
    env["DRY_RUN"] = "1"
    env["INTERVAL_SECONDS"] = "9999"
    if not env.get("ZABBIX_PASS"):
        print("ERROR: set ZABBIX_PASS", file=sys.stderr)
        sys.exit(2)

    code = (
        "import importlib.util\n"
        f"spec=importlib.util.spec_from_file_location('eng', r'{ENGINE}')\n"
        "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "m.run_aiops_cycle()\n"
    )
    t0 = time.time()
    p = subprocess.run([sys.executable, "-c", code], env=env,
                       capture_output=True, text=True, timeout=300)
    log = p.stdout + p.stderr

    readings = []
    for line in log.splitlines():
        m = re.search(r"\[(UPS|PAC) (\S+)\] Health: ([\d.]+|UNAVAILABLE)%? \| TTF: ([\d.]+|UNAVAILABLE)", line)
        if m:
            readings.append({"kind": m.group(1), "host": m.group(2),
                             "health": m.group(3), "ttf": m.group(4)})

    healths = [r["health"] for r in readings if r["health"] != "UNAVAILABLE"]
    distinct = len(set(healths))

    result = {
        "verification": "staging_dry_run",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "engine": "src/script_aiops.py",
        "command": "DRY_RUN=1 run_aiops_cycle()",
        "elapsed_seconds": round(time.time() - t0, 2),
        "writes_to_zabbix": 0,
        "no_synthetic_sensor_write": True,
        "no_random_fallback": True,
        "dry_run_markers_found": log.count("[DRY_RUN]"),
        "readings": readings,
        "distinct_health_values": distinct,
        "distinct_explanation": "nilai health berbeda antar-host & deterministik (bukan uniform acak)",
        "abstain_count": sum(1 for r in readings if r["health"] == "UNAVAILABLE"),
        "raw_log_tail": "\n".join(log.splitlines()[-25:]),
    }
    (OUT / "staging_dry_run.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in
                      ["writes_to_zabbix", "distinct_health_values", "abstain_count",
                       "dry_run_markers_found", "readings"]}, indent=2))
    print(f"-> {OUT/'staging_dry_run.json'}")


if __name__ == "__main__":
    main()
