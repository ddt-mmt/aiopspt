#!/usr/bin/env bash
set -u
umask 077

APP="/root/grafan_aiops"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="/root/aiops_diagnostic_${TS}"

mkdir -p "$OUT"
chmod 700 "$OUT"

exec > >(tee -a "$OUT/diagnostic.log") 2>&1

echo "================================================"
echo " AIOPS ALL-IN-ONE DIAGNOSTIC"
echo " Waktu : $(date -Is)"
echo " Host  : $(hostname)"
echo " Output: $OUT"
echo "================================================"

echo
echo "=== 1. IDENTITAS DAN FILESYSTEM ==="
id
pwd
df -h /root
findmnt -T /root 2>/dev/null || true

echo
echo "=== 2. DIREKTORI PROYEK ==="
if [[ -d "$APP" ]]; then
    ls -lah "$APP"
else
    echo "PERINGATAN: $APP tidak ditemukan."
fi

echo
echo "=== 3. BACKUP FILE PROYEK ==="
if [[ -d "$APP" ]]; then
    BACKUP="$OUT/grafan_aiops_backup.tar.gz"

    if tar -czf "$BACKUP"         --exclude='__pycache__'         -C /root grafan_aiops; then
        chmod 600 "$BACKUP"
        echo "Backup berhasil: $BACKUP"
        ls -lh "$BACKUP"
    else
        echo "PERINGATAN: backup tidak berhasil sempurna."
    fi
fi

echo
echo "=== 4. VALIDASI PYTHON ==="
if command -v python3 >/dev/null 2>&1; then
    python3 --version
    for f in script_aiops.py cari_id.py; do
        if [[ -f "$APP/$f" ]]; then
            if python3 -m py_compile "$APP/$f"; then
                echo "[OK] Sintaks Python: $f"
            else
                echo "[ERROR] Sintaks Python: $f"
            fi
        else
            echo "[WARN] File tidak ditemukan: $f"
        fi
    done
else
    echo "[WARN] Python 3 tidak tersedia."
fi

echo
echo "=== 5. VALIDASI JSON DASHBOARD ==="
if [[ -f "$APP/aiops_facility_dashboard.json" ]]; then
    if python3 -m json.tool         "$APP/aiops_facility_dashboard.json" >/dev/null; then
        echo "[OK] JSON dashboard valid."
    else
        echo "[ERROR] JSON dashboard tidak valid."
    fi
else
    echo "[WARN] File JSON dashboard tidak ditemukan."
fi

echo
echo "=== 6. VALIDASI DOCKER COMPOSE ==="
if command -v docker >/dev/null 2>&1; then
    docker ps --format       'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true

    if [[ -f "$APP/docker-compose.yml" ]]; then
        docker compose -f "$APP/docker-compose.yml"             config --quiet             && echo "[OK] Compose valid."             || echo "[WARN] Compose perlu diperiksa."
    else
        echo "[WARN] docker-compose.yml tidak ditemukan."
    fi
else
    echo "[WARN] Docker tidak tersedia."
fi

echo
echo "=== 7. PROSES AIOPS ==="
pgrep -af '[s]cript_aiops.py' || true

echo
echo "=== 8. SYSTEMD DAN CRON ==="
systemctl list-units --type=service --all --no-pager 2>/dev/null     | grep -Ei 'aiops|grafana|prometheus' || true

grep -RniE 'script_aiops.py|grafan_aiops'     /etc/cron.d /etc/crontab /var/spool/cron 2>/dev/null     || true

echo
echo "=== 9. LOKASI FILE PROYEK ==="
find /root /home /opt /srv     -type f \(       -name 'script_aiops.py' -o       -name 'aio_all_in_one.sh' -o       -name 'aiops_facility_dashboard.json'     \) -print 2>/dev/null || true

echo
echo "================================================"
echo " SELESAI"
echo " Laporan: $OUT/diagnostic.log"
echo " Backup : $OUT/grafan_aiops_backup.tar.gz"
echo " Tidak ada container dihentikan."
echo " Tidak ada service direstart."
echo " Tidak ada file proyek yang dihapus."
echo "================================================"
