# Catatan Perubahan Produksi — 2026-11-16

**Host:** `prox-prod` (10.28.1.110)
**Pelaksana:** pemilik sistem (operator), dengan bantuan Claude Code
**Status akhir:** ✅ DEPLOYED & VERIFIED

---

## 0. Otorisasi (override eksplisit)

Governance repo (`docs/PROJECT_CURRENT_STATUS.md`) mencatat:

> `Production Change Authorization: NOT_GRANTED`
> `Deployment Eligibility: INELIGIBLE_PENDING_APPROVAL`

**Pemilik sistem secara eksplisit menginstruksikan deploy ke produksi** ("naikan ke
produksi aja, agar saya bisa lihat hasilnya langsung"), sehingga gate otorisasi
di-override atas keputusan pemilik. Kelengkapan approval stakeholder formal
(Tahap Phase 87) **tidak** diklaim lengkap oleh catatan ini; ini keputusan operasional
pemilik untuk melihat hasil perbaikan secara langsung.

Ruang lingkup perubahan **terbatas** pada dua komponen AIOps (engine + dashboard);
tidak menyentuh Zabbix server, jaringan, atau layanan lain.

---

## 1. Backup & rollback (dibuat SEBELUM perubahan)

Direktori: `analysis/deployment/backup_20261116/`

| Artefak | Nilai |
|---|---|
| Dashboard Grafana (sebelum) | `grafana_dashboard_before.json` (21,346 B, sha256 `b568e48e…`) |
| Engine (sebelum) | `script_aiops_before.py` (18,881 B, sha256 `009090d5…`, md5 `19d0c956…`) |
| Image lama | `grafan_aiops-aiops_engine:latest` = `9140b4883654` |
| Image rollback (anchor) | **`grafan_aiops-aiops_engine:pre-fix-rollback`** (tag permanen) |

**Rollback engine:**
```bash
cd /root/grafan_aiops
docker compose down
docker tag grafan_aiops-aiops_engine:pre-fix-rollback grafan_aiops-aiops_engine:latest
docker compose up -d
```
**Rollback dashboard:**
```bash
docker cp analysis/deployment/backup_20261116/grafana_dashboard_before.json \
  grafana:/etc/grafana/provisioning/dashboards/aiops_facility_dashboard.json
```

---

## 2. Perubahan yang diterapkan

### 2.1 Dashboard Grafana
- Copy `config/aiops_facility_dashboard.json` (v6) → container `grafana` provisioning path.
- Efek: panel telemetri mentah kini menunjuk item nyata (42/42 target resolve);
  deskripsi jujur (bukan probabilitas / belum terkalibrasi / heuristik).
- Grafana auto-reload provisioning tiap 10s; **verifikasi in-container: version 6**.

### 2.2 Engine `aiops_predictor_hpc`
- File root `docker-compose.yml` **dipulihkan** (hilang saat cleanup root) agar
  redeploy deterministik; isinya disamakan dengan config container yang berjalan.
- Image di-rebuild dari `config/Dockerfile` (yang menyalin `src/script_aiops.py`),
  container di-**recreate** (`docker compose up -d --build`).
- Engine kini: **tanpa synthetic write, tanpa `np.random`**, key SNMP benar, mode
  `DRY_RUN`, dan **band TTF** (`*.ttf.low/high.hours`).
- md5 terpasang: **`a8dc1520…`** (= md5 repo, terverifikasi).

---

## 3. Dua perbaikan tuning yang ditemukan SAAT deploy live

Deploy live mengungkap dua masalah yang tidak terlihat saat pengujian offline:

### F-7c — toleransi "data masa depan" terlalu ketat
- Gejala: **semua LCD PAC ABSTAIN** tiap siklus —
  `FUTURE_DATA … {'return.temp.c': 14, ...}` (14–15 s di depan jam engine).
- Sebab: skew NTP normal ~15s, sedangkan toleransi hanya 10s.
- Perbaikan: `FUTURE_TOLERANCE_SECONDS` default **300s** (menyerap skew, tetap menolak
  data yang benar-benar jauh di masa depan).

### F-8 — band item menampilkan 0 yang menyesatkan
- Gejala: PAC `*.ttf.low/high.hours` menampilkan **0** (band "n/a" tidak dikirim,
  item baru default 0) → terbaca seolah "ganti sekarang".
- Perbaikan: band **selalu dikirim**; `-1` = sentinel "tidak dapat diestimasi"
  (jelas, bukan 0 yang ambigu).

---

## 4. Verifikasi pasca-deploy

Capture: `analysis/deployment/post_deploy_values.txt` (2026-11-16T08:45:39Z)

| host | health | ttf | ttf_lo | ttf_hi | action | age(s) |
|---|---|---|---|---|---|---|
| ME_UPS1 | 64.19 | 8760 | 8760 | 8760 | 1 | 96 |
| ME_UPS2 | 65.19 | 8760 | 8760 | 8760 | 1 | 91 |
| ME_UPS3 | 68.48 | 8760 | 8760 | 8760 | 1 | 84 |
| ME_PAC1 | 56.56 | 8760 | **-1** | **-1** | 1 | 79 |
| ME_PAC2 | 56.32 | 8760 | -1 | -1 | 1 | 75 |
| ME_PAC3 | 62.76 | 8760 | -1 | -1 | 1 | 70 |
| ME_PAC4 | 49.36 | 8760 | -1 | -1 | 1 | 66 |

**Cek keberhasilan:**
- [x] Ketujuh host melaporkan nilai (tidak ada ABSTAIN permanen)
- [x] Nilai Health berbeda antar-host & stabil per-host (bukan acak)
- [x] Nilai realistik: Health 49–68%; `action=1` (MAINTENANCE) sesuai ambang <70%
- [x] Band: UPS `8760–8760h`; PAC `-1` (tidak dapat diestimasi) — jujur, tanpa mengarang
- [x] Grafana dashboard version 6
- [x] md5 engine terpasang = md5 repo (`a8dc1520…`)
- [x] Deployed file tidak memuat `np.random.uniform` / `sim_load` / `sim_temp` (0 match)

**Yang MASIH belum valid (jujur):**
- `*.ttf.hours` masih 8760 untuk semua host → **tidak ada tren degradasi terdeteksi**
  dalam jendela amatan; TTF belum informatif. Butuh horizon/data lebih panjang atau
  model prognostik yang lebih baik (lihat `THESIS_EVALUATION.md`).
- Akurasi TTF/RUL terhadap kegagalan perangkat produksi tetap `NOT_MEASURABLE`
  (tanpa ground truth insiden).

---

## 5. Tindak lanjut wajib (P0 keamanan — BELUM dilakukan)

- [ ] **Rotasi password Zabbix** `admin` (masih <REDACTED-ZABBIX-PASSWORD>, ter-hardcode di ≥15 file ter-track).
- [ ] **Revoke GitHub PAT** yang tertanam di `git remote` origin.
- [ ] Pindahkan kredensial ke env/secret manager.

Langkah ini sengaja tidak dilakukan otomatis oleh asisten (butuh keputusan & akses
pemilik); dicatat di sini sebagai utang keamanan yang harus segera ditutup.
