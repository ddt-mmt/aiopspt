# DEPLOYMENT RUNBOOK — menerapkan perbaikan AIOps dengan aman

Dokumen ini menjelaskan **cara men-deploy** hasil perbaikan (engine + dashboard)
ke lingkungan yang benar, dengan memperhatikan **governance** yang sudah ada.

## Status governance saat ini (dari docs/PROJECT_CURRENT_STATUS.md)
- `Production Change Authorization: NOT_GRANTED`
- `Production Deployment Executed: NO`
- `Deployment Eligibility: INELIGIBLE_PENDING_APPROVAL`

➡️ **Karena itu perbaikan ini TIDAK otomatis diterapkan ke produksi.** Semua
perubahan hanya berupa file di repo + skrip verifikasi read-only.

---

## Apa yang berubah dan di mana efek-nya

| Perubahan | File | Efek langsung di produksi? |
|-----------|------|----------------------------|
| Engine: no synthetic write, no random fallback, key SNMP benar, abstain | `src/script_aiops.py` | **Tidak** — container masih menjalankan image lama. Perlu rebuild+redeploy. |
| Dashboard: panel telemetri mentah diarahkan ke item SNMP nyata | `config/aiops_facility_dashboard.json` | **Tidak** — Grafana membaca file di dalam container (provisioned), bukan dari repo host. Perlu salin ke container. |
| Test keamanan | `tests/test_aiops_safety.py` | Tidak (uji saja) |
| Bukti & analisa | `analysis/**` | Tidak |

> ⚠️ Grafana memuat dashboard dari **dalam container** di
> `/etc/grafana/provisioning/dashboards/aiops_facility_dashboard.json`
> (auto-reload tiap 10s). File itu **bukan** bind-mount dari host, jadi
> mengubah file di repo **tidak** mengubah yang tampil sampai disalin ke container.

---

## Jalur rekomendasi: STAGING dulu (`prox-dev`)

Ikuti pola Phase 87 yang sudah ada (shadow → validasi → gate otorisasi).

### 1. Uji offline (aman, 0 dampak)
```bash
python3 tests/test_aiops_safety.py           # harus OK (8 tes)
python3 -m py_compile src/script_aiops.py    # harus compile
```

### 2. Tinjau diff
```bash
git diff src/script_aiops.py
git diff config/aiops_facility_dashboard.json
```

### 3. Bangun image engine baru (staging)
```bash
docker build -f config/Dockerfile -t grafan_aiops-aiops_engine:fixed .
```
Jalankan di staging dengan env `ZABBIX_PASS` yang **baru** (setelah rotasi),
mode `DRY_RUN` bila tersedia. Amati log: harus muncul `UNAVAILABLE`/`ABSTAIN`
dan **tidak ada** angka acak.

### 4. Terapkan dashboard di staging
```bash
# SALIN ke container Grafana STAGING (bukan produksi)
docker cp config/aiops_facility_dashboard.json <grafana-staging>:/etc/grafana/provisioning/dashboards/aiops_facility_dashboard.json
```

### 5. Verifikasi (read-only, dapat diulang)
```bash
ZABBIX_PASS=... python3 analysis/scripts/verify_dashboard_bindings.py   # harus exit 0
docker logs <aiops-staging> 2>&1 | tail -40
```

### 6. Baru setelah lolos: minta otorisasi & promosikan ke produksi
- Kumpulkan bukti (log, verifikasi) ke `analysis/evidence/`.
- Ikuti gate otorisasi Phase 87 (`production_change_authorization`).
- Jangan menyalin ke Grafana/container produksi sebelum `Production Change Authorization: GRANTED`.

---

## Rollback

```bash
# Engine
git checkout -- src/script_aiops.py     # atau: /bin/cp src/script_aiops_v11_repaired.py src/script_aiops.py
# Dashboard
git checkout -- config/aiops_facility_dashboard.json
# Di container: pulihkan dari backup file dashboard sebelumnya
```

> `src/script_aiops_v11_repaired.py` adalah salinan **byte-identical** dari
> engine lama (md5 `19d0c956...`) dan dapat dipakai untuk rollback cepat.

---

## Dua langkah LISAN yang wajib sebelum redeploy engine

1. **Rotasi kredensial** (F-5): password Zabbix admin + revoke GitHub PAT.
   Setelah itu engine harus membaca `ZABBIX_PASS` dari env, bukan default.
2. **Pastikan `ZABBIX_PASS` tidak lagi punya default literal** di kode
   (saat ini sudah dikosongkan menjadi `os.getenv("ZABBIX_PASS", "")`).
