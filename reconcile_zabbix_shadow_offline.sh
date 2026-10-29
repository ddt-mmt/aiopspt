#!/usr/bin/env bash
set -uo pipefail
umask 077

ROOT="/root/grafan_aiops"
BASE="$ROOT/shadow_v5"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BASE/outputs/offline_reconciliation_${STAMP}.md"

mkdir -p "$BASE/outputs" || exit 1

{
    echo "# Zabbix Shadow — Offline Evidence Reconciliation"
    echo
    echo "- Generated: $(date -Is)"
    echo "- Mode: OFFLINE ONLY"
    echo "- Network/API calls: NONE"
    echo "- Production/config changes: NONE"
    echo

    echo "## 1. Phase G5/G10 report discovery"
    echo

    find "$BASE" -type f \
      \( -iname '*PHASE_G5*' -o -iname '*G5*REPORT*' \
         -o -iname '*PHASE_G10*' -o -iname '*G10*REPORT*' \) \
      -print 2>/dev/null | sort | while IFS= read -r f; do
        echo "### File: ${f#$ROOT/}"
        stat -c -- '- Size: %s bytes%n- Modified: %y' "$f" 2>/dev/null || true
        sha256sum "$f" 2>/dev/null || true
        echo
        case "$f" in
          *.md|*.txt|*.json)
            # Print only relevant evidence lines; never print credentials.
            grep -Ein \
              'AUTHENTICATED_READ_ONLY_REQUEST_CONFIRMED|HISTORY_PILOT_COLLECTED|SUCCESS|failed|request|item.?id|time.?from|time.?till|limit|max|record|row|history\.get|apiinfo\.version|token|credential|secret|password' \
              "$f" 2>/dev/null |
              sed -E \
                -e 's/((token|password|secret|authorization|api.?key)[^:=]*[:=])[[:space:]]*[^ ,"}]+/\1 [REDACTED]/Ig' \
                -e 's/(Bearer[[:space:]]+)[A-Za-z0-9._~+\/=-]+/\1[REDACTED]/Ig' |
              head -n 100 || true
            echo
            ;;
        esac
    done

    echo "## 2. Phase G10 CSV inventory and quality"
    echo

    python3 - "$BASE" <<'PY'
import csv, hashlib, json, math, sys
from pathlib import Path
from datetime import datetime, timezone

base = Path(sys.argv[1])
folders = sorted(base.glob("phase_g10_history_pilot_*"))

if not folders:
    print("No Phase G10 directory found.")
    raise SystemExit(0)

for folder in folders:
    for path in sorted(folder.glob("*.csv")):
        print(f"### {path.relative_to(base.parent)}")
        data = path.read_bytes()
        print(f"- Size bytes: {len(data)}")
        print(f"- SHA-256: {hashlib.sha256(data).hexdigest()}")

        try:
            with path.open("r", newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                headers = reader.fieldnames or []
                rows = list(reader)
        except Exception as exc:
            print(f"- CSV parse: ERROR ({type(exc).__name__})")
            print()
            continue

        print(f"- Headers: {', '.join(headers) if headers else '(none)'}")
        print(f"- Data rows: {len(rows)}")

        time_cols = [
            c for c in headers
            if any(k in c.lower() for k in ("clock", "time", "timestamp", "date"))
        ]
        value_cols = [
            c for c in headers
            if any(k in c.lower() for k in ("value", "clock", "time", "timestamp", "date"))
        ]

        for col in time_cols:
            vals = [(r.get(col) or "").strip() for r in rows]
            nonempty = [v for v in vals if v]
            duplicates = len(nonempty) - len(set(nonempty))
            print(f"- Time-like column '{col}': empty={len(vals)-len(nonempty)}, duplicate_values={duplicates}")
            if nonempty:
                print(f"  - Lexical min/max: {min(nonempty)} / {max(nonempty)}")

        for col in headers:
            if col in value_cols:
                continue
            vals = [(r.get(col) or "").strip() for r in rows]
            if any(k in col.lower() for k in ("value", "load", "voltage", "temp", "humidity")):
                missing = sum(not v for v in vals)
                nonnumeric = 0
                for v in vals:
                    if not v:
                        continue
                    try:
                        float(v)
                    except (ValueError, OverflowError):
                        nonnumeric += 1
                print(f"- Numeric-like column '{col}': empty={missing}, nonnumeric={nonnumeric}")

        print()

print("Note: CSV statistics do not prove that the source token is currently valid")
print("or that the Zabbix role is restricted to read-only permissions.")
PY

    echo
    echo "## 3. Static pilot script inspection"
    echo
    PILOT="$BASE/phase_g10_history_pilot_20261015_240000/execute_history_pilot.py"

    if [[ -f "$PILOT" ]]; then
        echo "- File: ${PILOT#$ROOT/}"
        stat -c -- '- Size: %s bytes%n- Modified: %y' "$PILOT"
        sha256sum "$PILOT"
        echo
        echo "Relevant static lines (credentials redacted; script NOT executed):"
        grep -Ein \
          'history\.get|itemids|itemid|time_from|time_till|limit|apiinfo\.version|requests\.post|requests\.get|Authorization|Bearer|token|password|url' \
          "$PILOT" 2>/dev/null |
          sed -E \
            -e 's/((token|password|secret|authorization|api.?key)[^:=]*[:=])[[:space:]]*[^ ,"}]+/\1 [REDACTED]/Ig' \
            -e 's/(Bearer[[:space:]]+)[A-Za-z0-9._~+\/=-]+/\1[REDACTED]/Ig' |
          head -n 100 || true
    else
        echo "- Phase G10 execution script not found at expected path."
        echo "- Search manually for execute_history_pilot.py within shadow_v5."
    fi

    echo
    echo "## 4. Conclusions and limitations"
    echo
    echo "- Historical API success: confirm only if the G5/G10 reports or audit files explicitly support it."
    echo "- Current Gemini CLI token/quota: NOT CHECKED by this script."
    echo "- Current Zabbix token status: NOT VERIFIED."
    echo "- Effective Zabbix read-only role: NOT VERIFIED by historical successful reads alone."
    echo "- Current network/API calls: NONE."
    echo "- Data limit: compare observed CSV row counts and the static pilot limit with the current target of at most 100 records per item."
    echo
    echo "## 5. Suggested status"
    echo
    echo "Use OFFLINE_DATA_READY only if CSV parsing, timestamps, required columns, and provenance are adequate."
    echo "Use RECOLLECTION_REQUIRED_MAX_100 if fresh data is needed to meet the 100-record/item target."
} > "$OUT"

chmod 600 "$OUT"

echo "=== OFFLINE RECONCILIATION COMPLETE ==="
echo "Report: $OUT"
echo
echo "Preview:"
sed -n '1,220p' "$OUT"
