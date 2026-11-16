# NASA Battery #5 — RUL Benchmark Results
Generated: 2026-11-16T08:18:00.085167+00:00
EOL threshold: 1.4 Ah (70% of 2.0 Ah rated)
Predict at life fractions: [0.5, 0.6, 0.7, 0.8]
Leakage control: model trained only on cycles <= prediction point; future cycles never used

Batteries valid for RUL (started healthy and reached EOL): 10 / 33

## Metrics — ALL valid cells (unit: discharge cycles)

| Model | n | MAE | RMSE | bias | median | p90 | max |
|---|---|---|---|---|---|---|---|
| naive | 15 | 32.0 | 36.509 | -32.0 | 33.0 | 52.4 | 62.0 |
| linear | 15 | 13.223 | 22.088 | 4.698 | 7.09 | 24.014 | 74.02 |
| sqrt | 15 | 84.113 | 142.115 | 81.744 | 54.0 | 160.786 | 470.5 |
| exp | 15 | 22.741 | 36.228 | 18.516 | 13.63 | 43.436 | 117.3 |

## Metrics — CANONICAL subset (B0005/B0006/B0007/B0018, literature-standard cells)

| Model | n | MAE | RMSE | bias | median | p90 | max |
|---|---|---|---|---|---|---|---|
| naive | 12 | 38.667 | 40.727 | -38.667 | 38.5 | 53.6 | 62.0 |
| linear | 12 | 14.993 | 24.501 | 7.408 | 10.0 | 28.196 | 74.02 |
| sqrt | 12 | 103.661 | 158.862 | 103.661 | 68.61 | 190.279 | 470.5 |
| exp | 12 | 26.978 | 40.399 | 24.594 | 16.55 | 51.449 | 117.3 |

## Catatan interpretasi
- Angka MAE/RMSE di atas adalah error jumlah SIKLUS, bukan hari. Konversi ke waktu
  bergantung pada pola pemakaian; NASA menguji dengan banyak siklus cepat.
- 'naive' adalah baseline bawah (selalu menebak RUL=0); model berguna harus jauh lebih baik.
- Hasil ini TIDAK boleh diklaim sebagai akurasi UPS produksi: kimia/sel/kondisi berbeda.
  Ini benchmark metodologi prognostik, bukan replika baterai UPS data center.