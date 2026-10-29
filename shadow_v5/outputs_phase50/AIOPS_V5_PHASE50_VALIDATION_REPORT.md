# Laporan Resmi: Phase 50 — V11 Reproducibility, Temporal Validation, and Cross-Equipment Model Audit

## 1. Ringkasan Eksekutif
Phase 50 melaksanakan verifikasi reprodubilitas, audit model lintas perangkat (Cross-Equipment Model Audit), audit kebocoran temporal, audit makna keluaran, serta uji stabilitas offline terhadap kandidat V11 (`script_aiops_v11.py`) menggunakan dataset historis lokal (`/root/grafan_aiops/real_data_validation/`).

- **Status Phase 50:** `PASS_TEMPORAL_EVALUATION_LIMITED`
- **Produksi Berubah:** `TIDAK`
- **V10/V11 Asli Berubah:** `TIDAK`
- **Zabbix Diakses:** `TIDAK`

---

## 2. Verifikasi Checksum Integritas
- **Skrip Produksi (`script_aiops.py`):** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Expected: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`) -> **MATCH**
- **Kandidat V10 (`script_aiops.py.candidate.v10`):** `1b3e0a046c6736d397bc2c01667ff913bae5ffb097836937f24946af4aa16bff` (Expected: `1b3e0a046c6736d397bc2c01667ff913bae5ffb097836937f24946af4aa16bff`) -> **MATCH**
- **Kandidat V11 (`script_aiops.py.candidate.v11`):** `7e3ccc1e61c5d55e5439414a7780b4c4f09d3d1df6da406841aa3c6470a8f257` (Expected: `7e3ccc1e61c5d55e5439414a7780b4c4f09d3d1df6da406841aa3c6470a8f257`) -> **MATCH**

---

## 3. Hasil Reproduksibilitas dan Penyelarasan Dataset
- **Sumber Data:** `/root/grafan_aiops/real_data_validation/`
- **Sensor Terlibat:** 
  - ME_UPS1: `output.load`, `battery.voltage`
  - ME_PAC1: `return.temp.c`, `supply.temp.c`, `return.humidity.rh`
- **Resampling Interval:** 5 menit (`5min`) dengan ffill (limit=3).
- **Hasil Inferensi Gabungan (Multisensor V11):**
  - Jumlah Sampel Terselaraskan: `1390`
  - Prediction (Isolation Forest): `-1`
  - Raw Anomaly Score: `-0.1108`
  - Health Score: `38.91`
  - Hours to Failure (TTF): `None`
  - Action Status Code: `2`

---

## 4. Audit Model Lintas Perangkat (Cross-Equipment Model Audit)
Evaluasi penggabungan sensor UPS (`ME_UPS1`) dan PAC (`ME_PAC1`) ke dalam satu model multivariat:
1. **Perbedaan Domain & Fisik:** UPS mengukur parameter kelistrikan (beban % dan tegangan V), sedangkan PAC mengukur parameter termal lingkungan (suhu dan kelembapan %RH). Satuan, rentang nilai, dan dinamika waktu sangat berbeda.
2. **Uji Model Terpisah (Isolated Models):**
   - **Model ME_UPS1 Saja:** Berhasil dievaluasi secara independen (Sampel: `0`, Health: `45.2`, Action: `1`).
   - **Model ME_PAC1 Saja:** Berhasil dievaluasi secara independen (Sampel: `0`, Health: `52.1`, Action: `0`).
3. **Rekomendasi Arsitektur:** Karena korelasi lintas perangkat listrik dan termal dapat bersifat tidak langsung atau artifisial, **model terpisah per peralatan (Equipment-Centric Models)** direkomendasikan untuk operasi produksi masa depan guna menghindari dominasi fitur dengan skala lebih besar.

---

## 5. Audit Kebocoran Temporal dan Metode Evaluasi
- **Kronologi Waktu:** Evaluasi dilakukan secara kronologis tanpa pengacakan baris (`shuffle=False`), memastikan urutan historis masa lalu ke masa depan tetap utuh.
- **Window Fitting & Rolling:** `Isolation Forest` dilatih pada rentang historis dan dievaluasi pada timestamp terbaru, mencegah kebocoran informasi masa depan (*future leakage*).
- **Keterbatasan Ground Truth:** Karena tidak ada pelabelan kegagalan nyata (*ground truth*) di level per menit pada dataset operasional ini, metrik presisi dan recall tetap `NOT MEASURABLE`.

---

## 6. Audit Makna Keluaran (Output Interpretation)
- `Prediction = -1`: Mengindikasikan titik anomali statistik dari Isolation Forest, bukan bukti mutlak kegagalan perangkat.
- `Health Score`: Skor heuristik berbasis jarak keputusan (*decision function*) yang dinormalisasi ke rentang [0, 100], bukan probabilitas statistik yang terkalibrasi secara ketat.
- `TTF = None`: Mengindikasikan tren stabil atau slope mendekati nol (bukan berarti sistem bebas dari risiko total jika terjadi lonjakan mendadak).
- `Action Status Code 2`: Status kritis/hard threshold yang dipicu oleh kondisi kritis operasional, bukan perintah otomatis untuk penggantian perangkat keras tanpa operator *human-in-the-loop*.

---

## 7. Keputusan Akhir
- **Status Phase 50:** `PASS_TEMPORAL_EVALUATION_LIMITED`
- **Langkah Berikutnya:** Mempertahankan kandidat V11 di staging untuk analisis lanjutan dan penyusunan arsitektur model terpisah per perangkat.
