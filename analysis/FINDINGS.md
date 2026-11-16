# FINDINGS — Register Temuan AIOps

Semua temuan berbasis bukti read-only pada 2026-11-16. Severity: 🔴 kritis, 🟠 tinggi, 🟡 info.

---

## F-1 🔴 Runtime menulis nilai sensor SINTETIK ke key asli
**Lokasi:** `src/script_aiops.py:345-357` (UPS), `:405-421` (PAC).
**Bukti:** `analysis/evidence/data_volume_compare.json` — `output.load`(trapper) last 69.8 vs `output.load[upsHighPrecOutputLoad]`(SNMP) last 48.9; `battery.voltage` 52.7 vs 215.9.
**Dampak:** Dashboard menampilkan beban/tegangan/temperatur buatan yang menyesatkan; sensor asli tidak terwakili.
**Perbaikan:** Hentikan penulisan key sensor dari engine; hanya kirim metrik turunan.

---

## F-2 🔴 Health Score acak saat quality gate gagal
**Lokasi:** `src/script_aiops.py:334,341,394,401` → `np.random.uniform(65.0,85.0)`.
**Bukti:** Distribusi 30d stdev 4.04–6.55, min 33–39 (tidak wajar untuk health fisik); gate gagal tiap siklus (log).
**Dampak:** Status kebijakan (MAINTENANCE) hampir permanen tanpa dasar; angka tak dapat dipercaya.
**Perbaikan:** Ganti dengan abstain (`UNAVAILABLE`). V12 candidate sudah benar → deploy.

---

## F-3 🟠 TTF konstan 8760 jam (tidak informatif)
**Lokasi:** `src/script_aiops.py:257-275` (clamp `min(8760,…)`) + jalur fallback.
**Bukti:** `ups.ttf.hours`/`pac.ttf.hours` = 8760 di semua host (history & inventory).
**Dampak:** Prediksi sisa umur tak bermakna; panel TTF selalu di ujung skala.
**Perbaikan:** Perbaiki input (F-4/F-7) lalu validasi slope; berikan interval, bukan titik.

---

## F-4 🟠 Panel dashboard menunjuk item yang tidak ada
**Lokasi:** `config/aiops_facility_dashboard.json`.
**Bukti:** Query by `name` `ups.output.load`/`ups.battery.temp`/`ups.battery.voltage` dan `return.temp.c`/`supply.temp.c`/`return.humidity.rh` → `NO MATCH` via `item.get`. Nama item asli: `UPS output.load`, `UPS battery.temp`, dsb.
**Dampak:** Panel telemetri mentah kosong; kesan sistem "belum jalan".
**Perbaikan:** Query by `key_` atau perbaiki nama; verifikasi tiap target lewat API.

---

## F-5 🔴 Kredensial hardcoded & ter-push ke GitHub
**Lokasi:** ≥15 file ter-track: `config/docker-compose.yml:14`, `phases/legacy/backup_aio_.../cari_id.py:5`, `phases/utils/audit_zabbix.py:6`, `phases/scripts/run_*.py`, `aio_audit_20261012_092412.log:111,163`, dll.
**Bukti:** `git grep -nE '<REDACTED-ZABBIX-PASSWORD>|ghp_' HEAD`.
**Tambahan:** `git remote` menyimpan PAT `ghp_…` pada URL origin (bocor).
**Perbaikan:** Rotasi password Zabbix + revoke PAT; pindahkan ke env/secret manager; purge dari history bila perlu.

---

## F-6 🟡 Dokumentasi proyek sudah jujur soal batas akurasi
**Lokasi:** `docs/ML_WORKFLOW_AND_ACCURACY.md` §5, `docs/VALIDATION_LIMITATIONS.md`, `README.md` §3/§8.
**Isi:** TTF/RUL `NOT_MEASURABLE`; `contamination=0.05` ≠ akurasi 95%; Health Score `NOT_CALIBRATED`; target ±15%/±20% adalah *design target*, bukan toleransi teruji.
**Dampak:** Positif — tidak ada klaim akurasi palsu tertulis. Ketidakpastian user konsisten dengan sumber.
**Perbaikan:** Pertahankan; jangan promosikan target desain jadi klaim SLA.

---

## F-7 🟠 Fitur wajib sering kosong/stale → gate gagal terus
**Lokasi:** `src/script_aiops.py:21-40` (mandatory lists) + `ensure_item_exists`.
**Bukti:** log `Timestamp NaT/None untuk sensor battery.capacity` (UPS) & `compressor.status` (PAC); `Sampel selaras tidak cukup … 0`.
**Catatan:** Data asli sebenarnya ada (`battery.capacity[upsHighPrecBatteryCapacity]`=100, `compressor.1.status`=1) — key salah.
**Perbaikan:** Selaraskan key mandatory dengan item SNMP yang benar.

---

## Ketergantungan antar-temuan
`F-5` (keamanan) independen — tangani duluan.
`F-7` → menyebabkan `F-2` → menyebabkan `F-1` (nilai sintetik) → memperkuat `F-3`.
`F-4` membuat gejala makin tak terlihat.
Perbaiki urut: **F-5 → F-2 → F-1 → F-7 → F-4 → F-3 → (validasi akurasi)**.
