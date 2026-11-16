# NASA Battery #5 — RUL dengan Interval Prediksi (Tolerance Band)
Generated: 2026-11-16T08:31:26.558152+00:00
Metode band: **split-conformal** (leave-one-battery-out) — lebar band ditentukan
dari seberapa salah model pada data yang ditahan, sehingga coverage-nya sahih.

## Akurasi titik (referensi)
- MAE = 13.661 siklus · RMSE = 22.785 · bias = 5.54

## Kalibrasi band (conformal)

| Nominal | Coverage empiris | Mean width (siklus) | n |
|---|---|---|---|
| 50% | 0.5714 | 18.66 | 14 |
| 80% | 0.8571 | 57.28 | 14 |
| 90% | 0.8571 | 114.69 | 14 |

## Temuan penting (analogi bahan bakar)
Bootstrap naive menghasilkan band SEMPIT (~±5 siklus untuk 80%) TAPI coverage-nya
hanya ~0.21 — yaitu 'indikator bahan bakar yang berbohong': terlihat presisi, tetapi
4 dari 5 kali nilai sebenarnya di LUAR rentang. Conformal memperlebar band sesuai
kesalahan nyata sehingga coverage mendekati nominal. Inilah 'batas toleransi yang
jujur': rentang bisa lebih lebar, tetapi artinya benar.

## Cara membaca
- Coverage empiris ≈ nominal → band JUJUR.
- Width = batas toleransi terukur (bukan klaim '±15%').

## Batasan
- n kecil (puluhan titik) → CI coverage lebar; jangan klaim presisi berlebihan.
- NASA = sel Li-ion lab, bukan baterai UPS produksi. Kalibrasi METODOLOGI.