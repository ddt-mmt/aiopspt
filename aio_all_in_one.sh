#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

APP_DIR="/root/grafan_aiops"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${APP_DIR}/backup_aio_${TS}"
LOG_FILE="${APP_DIR}/aio_audit_${TS}.log"
REPORT="${APP_DIR}/aio_report_${TS}.txt"

# Audit-only: tidak reboot, tidak stop/recreate container,
# tidak mengubah konfigurasi monitoring atau menghapus data.

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: jalankan sebagai root."
    exit 1
fi

if [[ ! -d "$APP_DIR" ]]; then
    echo "ERROR: direktori proyek tidak ditemukan: $APP_DIR"
    exit 1
fi

mkdir -m 700 -p "$BACKUP_DIR"
touch "$LOG_FILE" "$REPORT"
chmod 600 "$LOG_FILE" "$REPORT"

exec > >(tee -a "$LOG_FILE") 2>&1

section() {
    echo
    echo "============================================================"
    echo "$*"
    echo "============================================================"
}

check_file() {
    local f="$1"
    if [[ -f "$APP_DIR/$f" ]]; then
        echo "[OK] Ditemukan: $f"
        cp -a "$APP_DIR/$f" "$BACKUP_DIR/"
    else
        echo "[WARN] Tidak ditemukan: $f"
    fi
}

section "1. IDENTITAS SERVER"
date -Is
hostname -f 2>/dev/null || hostname
uname -a
id

section "2. BACKUP FILE PROYEK"
for f in     script_aiops.py     docker-compose.yml     Dockerfile     aiops_dashboards.yaml     aiops_facility_dashboard.json     README.md     THESIS_METHODOLOGY.md     cari_id.py
do
    check_file "$f"
done

echo "Backup tersimpan di: $BACKUP_DIR"

section "3. STATUS DOCKER"
if command -v docker >/dev/null 2>&1; then
    docker version --format 'Docker server: {{.Server.Version}}'         2>&1 || true

    echo "--- Container terkait AIOps/Grafana/Zabbix ---"
    docker ps --format         'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'         2>&1 || true

    echo "--- Compose services ---"
    if [[ -f "$APP_DIR/docker-compose.yml" ]]; then
        docker compose -f "$APP_DIR/docker-compose.yml"             config --services 2>&1 || true

        echo "--- Validasi Compose ---"
        docker compose -f "$APP_DIR/docker-compose.yml"             config --quiet 2>&1             && echo "[OK] Sintaks Compose valid"             || echo "[WARN] Compose perlu diperiksa"
    fi
else
    echo "[WARN] Docker tidak ditemukan."
fi

section "4. VALIDASI PYTHON"
if command -v python3 >/dev/null 2>&1; then
    python3 --version

    for f in script_aiops.py cari_id.py; do
        if [[ -f "$APP_DIR/$f" ]]; then
            echo "--- Compile check: $f ---"
            if python3 -m py_compile "$APP_DIR/$f"; then
                echo "[OK] Sintaks Python valid: $f"
            else
                echo "[ERROR] Sintaks Python bermasalah: $f"
            fi
        fi
    done
else
    echo "[ERROR] Python 3 tidak ditemukan."
fi

section "5. AUDIT POLA BERISIKO PADA SCRIPT"
cd "$APP_DIR"

if [[ -f script_aiops.py ]]; then
    python3 - <<'PY'
from pathlib import Path
import re

p = Path("script_aiops.py")
s = p.read_text(errors="replace")
lines = s.splitlines()

checks = [
    (
        "Fallback data acak/simulasi",
        re.compile(
            r"\b(random|randint|randrange|uniform|normalvariate)\b"
            r"|np\.random|numpy\.random|synthetic|simulat",
            re.I
        ),
        "Pastikan data sintetis tidak masuk ke hasil monitoring produksi."
    ),
    (
        "Forward/backward fill",
        re.compile(r"\.(ffill|bfill|fillna)\s*\(|method\s*=\s*['\"](ffill|bfill)", re.I),
        "Periksa apakah data kosong diisi dan menimbulkan nilai semu."
    ),
    (
        "Merge timestamp",
        re.compile(r"\bmerge_asof\b|\bmerge\s*\(|\bjoin\s*\(", re.I),
        "Periksa sinkronisasi waktu dan kemungkinan kehilangan sampel."
    ),
    (
        "Isolation Forest",
        re.compile(r"IsolationForest", re.I),
        "Validasi data input, parameter model, dan false positive."
    ),
    (
        "TTF / Remaining Useful Life",
        re.compile(r"\bTTF\b|time.to.failure|remaining.useful.life", re.I),
        "Periksa satuan, sensor yang digunakan, dan validasi hasil."
    ),
    (
        "Interval polling",
        re.compile(r"\btime\.sleep\s*\(|INTERVAL|POLL_INTERVAL", re.I),
        "Pastikan polling tidak bertumpuk dan sesuai interval target."
    ),
    (
        "Credential literal",
        re.compile(
            r"(?i)(password|passwd|api[_-]?token|secret)"
            r"\s*=\s*['\"][^'\"]{3,}['\"]"
        ),
        "Gunakan environment variable atau secret manager."
    ),
    (
        "Verifikasi TLS dinonaktifkan",
        re.compile(r"verify\s*=\s*False|CERT_NONE", re.I),
        "Periksa keamanan koneksi API."
    ),
]

for title, pattern, advice in checks:
    hits = [
        (i, line.strip()[:220])
        for i, line in enumerate(lines, 1)
        if pattern.search(line)
    ]
    print(f"\n[{title}]")
    if hits:
        for n, line in hits[:15]:
            print(f"  Baris {n}: {line}")
        print(f"  Tindakan: {advice}")
    else:
        print("  Tidak ditemukan pola yang cocok.")

print("\nCatatan: hasil di atas adalah indikator audit, bukan bukti pasti bug.")
PY
else
    echo "[WARN] script_aiops.py tidak ditemukan."
fi

section "6. AUDIT HOST DAN SENSOR"
if [[ -f script_aiops.py ]]; then
    grep -nEi         'ME_UPS|ME_PAC|zabbix|sensor|history.get|item.get|lastvalue|clock|timestamp'         script_aiops.py 2>/dev/null || true
fi

section "7. AUDIT KONFIGURASI DAN RAHASIA"
for f in docker-compose.yml Dockerfile aiops_dashboards.yaml; do
    if [[ -f "$f" ]]; then
        echo "--- $f ---"
        grep -nEi             'environment:|env_file:|password|token|secret|zabbix|grafana|volume:|restart:|healthcheck:'             "$f" 2>/dev/null             | sed -E                 's/(PASSWORD|PASSWD|TOKEN|SECRET)([=:][[:space:]]*).*/\1\2[REDACTED]/I'             || true
    fi
done

section "8. VALIDASI DASHBOARD JSON"
if command -v python3 >/dev/null 2>&1; then
    for f in aiops_facility_dashboard.json; do
        if [[ -f "$f" ]]; then
            if python3 -m json.tool "$f" >/dev/null; then
                echo "[OK] JSON valid: $f"
            else
                echo "[ERROR] JSON tidak valid: $f"
            fi
        fi
    done
fi

section "9. PEMERIKSAAN LOG TERAKHIR"
if command -v docker >/dev/null 2>&1; then
    while IFS= read -r cname; do
        [[ -n "$cname" ]] || continue
        echo "--- $cname ---"
        docker logs --tail 80 "$cname" 2>&1             | grep -Ei                 'error|exception|traceback|failed|timeout|unauthorized|denied|warning'             | tail -n 30 || true
    done < <(
        docker ps --format '{{.Names}}'             | grep -Ei 'aiops|grafana|zabbix|prometheus' || true
    )
fi

section "10. BUAT LAPORAN"
{
    echo "AIOps Audit Report"
    echo "Tanggal: $(date -Is)"
    echo "Host: $(hostname -f 2>/dev/null || hostname)"
    echo "Project: $APP_DIR"
    echo "Backup: $BACKUP_DIR"
    echo "Log: $LOG_FILE"
    echo
    echo "Prioritas pemeriksaan:"
    echo "1. Hentikan penggunaan fallback acak sebagai data produksi."
    echo "2. Tandai data sensor yang hilang; hindari imputasi diam-diam."
    echo "3. Selaraskan timestamp antar sensor secara eksplisit."
    echo "4. Hitung TTF per sensor yang relevan dan validasi satuannya."
    echo "5. Pindahkan credential dari source code ke environment/secret."
    echo "6. Uji model anomaly detection dengan data historis berlabel."
    echo "7. Validasi dashboard dan provisioning sebelum deployment."
    echo
    echo "Script ini tidak mengubah konfigurasi atau merestart service."
} | tee "$REPORT"

section "SELESAI"
echo "Backup : $BACKUP_DIR"
echo "Log    : $LOG_FILE"
echo "Laporan: $REPORT"
echo
echo "Tidak ada reboot, stop container, atau penghapusan data."
