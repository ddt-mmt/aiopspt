# Laporan Resmi: Phase 47 — Candidate V10 Offline Validation & Safety Review

## 1. Ringkasan Eksekutif
Fase 47 melaksanakan audit logika statis dan pengujian offline terisolasi terhadap kandidat model AIOps V10 (`script_aiops.py.candidate.v10`). Berdasarkan pengujian sintetis ekstensif (23 skenario uji), kandidat V10 berhasil lulus pada uji kualitas dasar (schema validation, data staleness, sampel minimum, pembersihan nilai NaN/Inf, serta penanganan duplikasi timestamp). Namun, audit mendalam dan harness pengujian offline mengungkap 6 cacat logika dan celah batas (edge case defects) yang signifikan pada perhitungan RUL, penentuan status tindakan (`determine_action_status_hardened`), dan mutasi dictionary in-place. 

Keputusan akhir gerbang pengujian adalah **PASS_OFFLINE_TESTS_ONLY**. Kandidat **TIDAK** siap untuk aktivasi produksi atau live integration tanpa perbaikan arsitektural dan penambalan logika. Skrip produksi dan file kandidat asli tetap utuh dan tidak berubah (`SHA256` terverifikasi persis sama).

---

## 2. Scope dan Batas Keselamatan
- **Production Host:** `prox-prod` (`10.28.1.110`) — **TIDAK BERUBAH** (0 perubahan).
- **Staging Host:** `prox-dev` (`10.28.1.100`) — Diakses secara pasif/SSH read-only.
- **Candidate File:** `/root/grafan_aiops/script_aiops.py.candidate.v10` — **TIDAK BERUBAH** (Read-only).
- **Production Script:** `/root/grafan_aiops/script_aiops.py` — **TIDAK BERUBAH** (Read-only).
- **Akses Zabbix API:** **TIDAK ADA** interaksi tulis atau live fetch selama fase ini.

---

## 3. Checksum Sebelum dan Sesudah
- **Kandidat V10 Asli:**
  - `1b3e0a046c6736d397bc2c01667ff913bae5ffb097836937f24946af4aa16bff` (Sebelum & Sesudah: **IDENTIK**)
- **Skrip Produksi (`script_aiops.py`):**
  - `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Sebelum & Sesudah: **IDENTIK**)

---

## 4. Temuan Audit per Fungsi (Tahap B)

### A. `validate_schema_and_quality()`
- **Kelebihan:** Pemeriksaan fitur wajib (`UPS_MANDATORY`, `PAC_MANDATORY`) dan ambang batas kedaluwarsa data (`max_age_seconds=300`) berfungsi dengan baik.
- **Cacat Arsitektural:** Fungsi ini melakukan mutasi in-place terhadap diksioner `series_by_name` pemanggil ketika menghapus sensor opsional yang sparse (`del series_by_name[s]`), yang melanggar prinsip immutabilitas argumen input.

### B. `process_sensor_history_hardened()`
- **Kelebihan:** Menggabungkan data secara bersih, menerapkan forward-fill (`limit=2`), dan mencatat log audit imputasi.
- **Catatan:** Bergantung penuh pada validitas timestamp awal dan rentang sampel selaras.

### C. `calculate_multisensor_rul_v8()`
- **Kelebihan:** Menggunakan `IsolationForest(contamination=0.05)` dengan pembersihan nilai NaN/Inf dan duplikasi timestamp.
- **Cacat Logika (RUL):**
  1. Perhitungan slope hanya mendukung sensor dengan kenaikan nilai menuju batas atas (`slope > 1e-5 and current_val < crit_val`). Sensor degradasi batas bawah (seperti `battery.voltage` yang menurun menuju ambang kritis 44V) menghasilkan `TTF = None` karena slope bernilai negatif.
  2. Ketika nilai sensor sudah melampaui batas kritis (`current_val >= crit_val`), `ttf` dikembalikan sebagai `None`, sehingga gagal membedakan antara "kondisi stabil normal" dan "kondisi sudah mengalami kegagalan total".

### D. `determine_action_status_hardened()`
- **Cacat Logika:** 
  1. Mengabaikan keluaran prediksi biner IsolationForest (`prediction` bernilai `-1` untuk anomali) secara langsung karena tanda fungsi hanya menerima `(health, ttf)`.
  2. Blind spot: Ketika `ttf = None` (misalnya akibat sensor sudah melampaui batas kritis tetapi model anomali menghasilkan skor kesehatan `>= 70`), status tindakan dikembalikan sebagai `0` (NORMAL), yang merupakan risiko keselamatan serius (false negative).

---

## 5. Daftar Pengujian dan Hasil Harness Sintetis (23 Skenario)

| Test ID | Kategori | Deskripsi Pengujian | Ekspektasi | Aktual | Status |
|---|---|---|---|---|---|
| TEST-01 | Quality Gate | Data valid dengan sampel cukup (>=10) | PASS | NORMAL, 65 rows | **PASS** |
| TEST-01B| Pipeline | Inferensi RUL & status pada data valid | Action in [0,1,2] | Action=0, Health=100.0 | **PASS** |
| TEST-02 | Quality Gate | Fitur wajib hilang (fail-closed) | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **PASS** |
| TEST-03 | Quality Gate | Data stale (>300s) (fail-closed) | STALE_DATA | STALE_DATA | **PASS** |
| TEST-04 | Quality Gate | Sampel kurang dari minimum (<10) | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **PASS** |
| TEST-05 | Cleaning | Timestamp invalid dan NaT | ValueError / Drop | ValueErrorhandled | **PASS** |
| TEST-05B| Security | Deteksi timestamp di masa depan | BLOCKED | Lolos sebagai NORMAL | **DEFECT** |
| TEST-06 | Cleaning | Nilai NaN dan Infinity | Handled/Cleaned | Cleaned successfully | **PASS** |
| TEST-07 | Cleaning | Duplikasi timestamp (`drop_duplicates`) | Deduplicated | Deduplicated safely | **PASS** |
| TEST-08A| RUL | Slope positif mendekati crit_val | TTF > 0 | TTF = 28.5 jam | **PASS** |
| TEST-08B| RUL | Slope nol (konstan) | TTF is None | TTF = None | **PASS** |
| TEST-08C| RUL Defect | Sensor degradasi menurun (voltage drop) | TTF calculated | TTF = None (Slope<0) | **DEFECT** |
| TEST-08D| RUL Defect | Sensor melewati ambang kritis | TTF=0 or Critical | TTF = None | **DEFECT** |
| TEST-09A| Action | Health=80, TTF=None | Status 0 (Normal) | Status 0 | **PASS** |
| TEST-09B| Action | Health=30, TTF=None | Status 2 (Critical) | Status 2 | **PASS** |
| TEST-09C| Action Edge | TTF=None karena lewat batas, health>70 | Warning/Critical | Status 0 (Blind spot) | **DEFECT** |
| TEST-10 | Action | Health is None | Status -1 (Unavailable) | Status -1 | **PASS** |
| TEST-11A| Anomaly | Deteksi outlier ekstrem IsolationForest | prediction = -1 | prediction = -1 | **PASS** |
| TEST-11B| Action Defect| Memanfaatkan prediksi biner anomali | Consumes pred | Ignored in signature | **DEFECT** |
| TEST-12 | Alignment | Penyelarasan timestamp interleaved | Valid merged df | Merged with ffill | **PASS** |
| TEST-13A| Robustness | Input DataFrame None | ValueError | ValueError raised | **PASS** |
| TEST-13B| Robustness | Input DataFrame kosong | ValueError | ValueError raised | **PASS** |
| TEST-14 | Side-Effect | Mutasi dictionary input caller | No mutation | Dict mutated (del) | **DEFECT** |

- **Total Pengujian:** 23
- **Lulus (PASS):** 17
- **Gagal / Cacat (DEFECT):** 6

---

## 6. Kecukupan Data Historis (Pilot G10)
Analisis terhadap direktori `/root/grafan_aiops/shadow_v5/phase_g10_history_pilot_20261015_240000/` menunjukkan:
- `PHASE_G10_BATTERY_VOLTAGE.csv`: Hanya memiliki **1 sampel** (point count = 1), rentang timestamp tunggal (`1792034604`). Tidak cukup untuk inferensi multi-sensor atau perhitungan slope.
- `PHASE_G10_INPUT_VOLTAGE.csv`: Memiliki **47 sampel** dengan rentang timestamp unik.
- **Kesimpulan Kecukupan:** Data historis pilot G10 **TIDAK MENCUKUPI** untuk pengujian model multivariat V10 secara penuh, karena kurangnya sinkronisasi multi-fitur dengan rentang waktu yang memadai.

---

## 7. Metrik yang `NOT MEASURABLE`
Karena ketiadaan label kegagalan nyata (ground truth maintenance/failure labels) pada dataset historis pilot:
- **Precision, Recall, False-Positive Rate:** `NOT MEASURABLE`
- **Lead Time to Failure Accuracy:** `NOT MEASURABLE`
- **RUL Error Magnitude:** `NOT MEASURABLE`

---

## 8. Cacat Logika dan Rekomendasi Perbaikan
1. **Perbaikan Slope RUL:** Perluas `calculate_multisensor_rul_v8` untuk mendukung sensor batas bawah (seperti tegangan baterai) dengan mendeteksi kemiringan negatif terhadap ambang bawah (`crit_low`).
2. **Penanganan Over-Threshold:** Jika `current_val >= crit_val`, set `hours_to_failure = 0.0` alih-alih `None` agar status tindakan segera mengaktifkan tingkat darurat (`CRITICAL`).
3. **Integrasi Prediksi Biner:** Sertakan `prediction == -1` dari IsolationForest secara eksplisit ke dalam `determine_action_status_hardened`.
4. **Immutabilitas Input:** Hindari mutasi in-place pada `validate_schema_and_quality` dengan melakukan penyalinan dictionary (`dict(series_by_name)`).
5. **Validasi Timestamp Masa Depan:** Tambahkan pemeriksaan agar timestamp yang melebihi waktu aktual (`now_utc`) ditolak atau ditandai sebagai anomali data.

---

## 9. Batasan Hasil Offline
Hasil pengujian ini sepenuhnya bersifat sintetis dan offline. Model Isolation Forest dilatih dan diuji pada data buatan atau data pilot terbatas tanpa label keandalan operasional aktual. Pengujian ini tidak menjamin performa model di lingkungan produksi yang sesungguhnya.

---

## 10. Keputusan Akhir dan Langkah Lanjutan yang Aman
- **Keputusan Akhir:** `PASS_OFFLINE_TESTS_ONLY`
- **Apakah Produksi Berubah:** `TIDAK`
- **Apakah Kandidat Asli Berubah:** `TIDAK`
- **Apakah Ada Akses Zabbix:** `TIDAK` (pada fase ini)
- **Langkah Selanjutnya yang Paling Aman:** 
  1. Mempertahankan kandidat V10 dalam status read-only/offline.
  2. Mengembangkan patch terpisah di direktori staging untuk mengatasi 6 cacat logika yang ditemukan.
  3. Menunggu pengumpulan ground truth historis yang memadai sebelum pertimbangan aktivasi lanjutan.
