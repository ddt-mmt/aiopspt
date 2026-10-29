# Laporan Validasi Robustness v5 (`ROBUSTNESS_V5_VALIDATION.md`)

- **Tanggal Laporan:** 12 Oktober 2026
- **Target Proyek:** `/root/grafan_aiops` (`prox-prod`)
- **Status Validasi:** **PASS WITH RESTRICTIONS (READY FOR CONTROLLED SHADOW TESTING)**

---

## 1. Ringkasan Eksekutif
Kandidat engine v5 (`script_aiops.py.candidate.v5`) dirancang dan diuji secara ketat untuk meningkatkan ketahanan (*robustness*) terhadap data hilang, *sensor stuck*, *stale data*, dan mencegah bias dari fitur diskret (seperti status kompresor 0/1). Seluruh pengujian dijalankan secara offline dan terisolasi tanpa efek samping terhadap sistem produksi.

## 2. Peningkatan Utama pada v5
1. **Data Quality Gating:** Membedakan status `NORMAL`, `DEGRADED_DATA`, dan `INSUFFICIENT_DATA` secara eksplisit, serta mengabaikan sensor *sparse* seperti `battery.capacity` alih-alih melakukan *forward-fill* ekstrem.
2. **Pemisahan Fitur Diskret:** Variabel status kompresor diskret (0/1) dikeluarkan dari perhitungan regresi linier slope TTF, namun tetap dipertahankan dalam IsolationForest untuk deteksi anomali multivariat.
3. **Indikator Confidence / Uncertainty:** Menambahkan tingkat keyakinan (*confidence level*) pada output evaluasi model berdasarkan ukuran sampel.

## 3. Hasil Pengujian Offline
Unit test dan evaluasi offline dijalankan dan berhasil lulus (`PASS`). Hash SHA-256 active source tetap konsisten dan kontainer produksi berjalan normal.
