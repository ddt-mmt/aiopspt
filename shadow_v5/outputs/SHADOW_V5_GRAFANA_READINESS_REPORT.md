# AIOps Shadow v5 — Grafana Integration & Alert Readiness Report

## 1. Temuan Metodologi Split
- **Implementasi Aktual (`shadow_runner.py`):** Berdasarkan audit kode read-only, split kronologis membagi dataset urut waktu menjadi **70% training** dan **30% test/evaluation** (`n_train = int(n * 0.7)`), tanpa memisahkan *validation set* terpisah.
- **Dampak & Mitigasi:** Tidak ada pencampuran data masa depan ke masa lalu (`.sort_index()` diterapkan sebelum pemotongan). Seluruh fiting parameter model Isolation Forest v5 dan scaling hanya dilakukan pada training slice.

## 2. Kontrak Data Aktual (`shadow_v5_metrics.csv` & `shadow_v5_results.json`)
- `host`: Identifier host string (`ME_UPS1` s.d. `ME_PAC4`).
- `total_samples`: Total sampel time-series setelah resample 1 jam.
- `train_samples`: Jumlah sampel training (70%).
- `eval_samples`: Jumlah sampel evaluasi/test (30%).
- `status`: Status eksekusi (`SUCCESS` / `ERROR`).
- `shadow_health_score`: Indeks anomali multivariat ternormalisasi (0-100). **Bukan probabilitas kesehatan.**
- `shadow_ttf_hours`: Estimasi heuristik linier *slope* TTF. **Bukan RUL terverifikasi.**
- `data_quality_status`: Status gating kualitas (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`).

## 3. Dashboard Staging (`shadow_v5_dashboard_staging.json`)
- Berhasil dibuat di direktori staging terisolasi tanpa menyentuh dashboard produksi.
- Memuat 6 panel utama: Health Score, TTF, Data Quality Status, Runner Status, Anomaly Counts, dan Anomaly Reasons.

## 4. Rancangan Shadow Alerting (Kandidat Eksperimen)
- **Persistent Anomalies:** Pemicu alert hanya aktif jika Health Score $< 70$ selama minimal 3 siklus berturut-turut untuk mencegah *alert storms* dari fluktuasi sesaat.
- **Data Quality Gating:** Alert otomatis ditahan (*abstain*) jika status data bernilai `DEGRADED_DATA` atau `INSUFFICIENT_DATA`.
- **Status Notifikasi:** Belum diaktifkan ke produksi (murni offline staging).

## 5. Hasil Uji Offline
- Validasi struktur JSON dashboard staging: **PASS**.
- Validasi kontrak data: **PASS**.
- Uji eksekusi offline runner staging: **PASS**.

## 6. Verifikasi Integritas Produksi (Sebelum & Sesudah)
- **Hash SHA-256 `script_aiops.py`:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Identik, tidak ada perubahan).
- **Zabbix Writes:** 0.
- **Container Restarts:** 0.

## 7. Daftar Kendala
- Kurangnya *ground-truth failure labels* membatasi validasi metrik klasifikasi supervisi (*Precision, Recall*).

## 8. Status Akhir Readiness
- **STATUS: READY WITH WARNINGS**
- Keterangan: Komponen staging, dashboard JSON, dan alert design telah tervalidasi secara offline dan aman, namun notifikasi produksi tetap ditahan hingga data insiden nyata tersedia.
