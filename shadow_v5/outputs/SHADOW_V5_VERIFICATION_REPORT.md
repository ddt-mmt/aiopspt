# AIOps Shadow v5 — Evaluation Verification & Controlled Repeatability Report

## 1. Audit Kode Read-Only
- **Script Diperiksa:** `shadow_runner.py`, `shadow_reproducibility_test.py`.
- **Hasil:** Kepatuhan penuh terhadap operasi *read-only*. Tidak ada koneksi tulis Zabbix API, tidak ada modifikasi pada `script_aiops.py` (hash tetap `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`), dan tidak ada perubahan konfigurasi produksi.

## 2. Validasi Kronologi dan Split
- **Strategi Split:** Chronological split (70% train, 30% evaluation / test) berbasis timestamp, tanpa random shuffling.
- **Pencegahan Data Leakage:** Preprocessing, normalisasi, dan fiting model Isolation Forest v5 dilakukan secara ketat hanya pada training window.

## 3. Rekap Data per Host / Item
- Total 7 host (`ME_UPS1` - `ME_UPS3`, `ME_PAC1` - `ME_PAC4`) diproses menggunakan data ekspor CSV audit 365 hari (746 sampel per host setelah resample 1 jam).
- Semua 7 host terwakili secara penuh dengan status evaluasi `SUCCESS`.

## 4. Hasil Reproducibility & Repeatability Test
- Jalur ganda offline dry-run (`outputs_run1` vs `outputs_run2`) menghasilkan SHA-256 checksum CSV output yang **100% identik**: `a8c138631c5c149d5dd99fa3d5f4b8be68c509234b2c4f40d25b8f346b30aeaf`.
- Menunjukkan determinisme dan stabilitas eksekusi runner yang sempurna.

## 5. Status Data Quality Gating
- Gating v5 berhasil membedakan sensor kontinu yang padat dengan sensor *sparse* atau status diskret, mencegah *false alarm* akibat data hilang.

## 6. Batasan Statistik & Metodologi
- **0 Ground-Truth Failure Events:** Tidak ada kejadian kegagalan historis berlabel, sehingga *Precision, Recall, dan F1-score* belum dapat dihitung secara empiris.
- **Health Score & TTF:** Health Score adalah indeks anomali multivariat (0-100), bukan probabilitas survival; TTF adalah heuristik *slope* linier eksperimental.

## 7. Verifikasi Integritas Produksi
- Hash `script_aiops.py`: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Sesuai baseline).
- Zabbix Writes: 0.
- Container Restarts: 0.

## 8. Daftar Bug dan Perbaikan
- Tidak ditemukan bug fungsional. Peringatan pandas resampling (`'H'` -> `'h'`) dicatat untuk perbaikan pemeliharaan masa depan.

## 9. Keputusan Akhir
- **STATUS: PASS**
- Sistem Continuous AIOps Shadow v5 tervalidasi secara offline dan siap untuk operasi shadow berulang secara manual atau terjadwal secara terkontrol.

## 10. Rekomendasi Langkah Berikutnya
1. Lanjutkan pemantauan berkala menggunakan runner shadow terisolasi.
2. Integrasikan visualisasi melalui Grafana dashboard (`shadow_v5_dashboard.json`) tanpa mengubah dashboard produksi.
3. Kumpulkan log *ground-truth* insiden fasilitas secara terstruktur ke depan untuk memungkinkan validasi ML supervised pada iterasi berikutnya.
