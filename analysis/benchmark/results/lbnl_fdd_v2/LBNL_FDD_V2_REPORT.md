# LBNL RTU — Fault Detection v2 (scored + threshold-tuned)
Generated: 2026-11-16T08:31:19.486011+00:00

## Ranking quality (threshold-free)

| Detector | ROC-AUC | PR-AUC |
|---|---|---|
| isolation_forest | 0.6212 | 0.9838 |
| robust_z | 0.6878 | 0.9907 |
| residual | 0.6336 | 0.989 |

## Operating points (recall & F1 at target false-alarm-rate)

### isolation_forest

| FAR target | actual FAR | recall | precision | F1 |
|---|---|---|---|---|
| 0.01 | 0.01 | 0.0038 | 0.9485 | 0.0076 |
| 0.05 | 0.05 | 0.035 | 0.9711 | 0.0676 |
| 0.1 | 0.1 | 0.1472 | 0.986 | 0.2562 |

### robust_z

| FAR target | actual FAR | recall | precision | F1 |
|---|---|---|---|---|
| 0.01 | 0.01 | 0.2538 | 0.9992 | 0.4048 |
| 0.05 | 0.05 | 0.273 | 0.9962 | 0.4286 |
| 0.1 | 0.1 | 0.3005 | 0.9931 | 0.4614 |

### residual

| FAR target | actual FAR | recall | precision | F1 |
|---|---|---|---|---|
| 0.01 | 0.01 | 0.2515 | 0.9992 | 0.4018 |
| 0.05 | 0.05 | 0.2755 | 0.9962 | 0.4316 |
| 0.1 | 0.1 | 0.3 | 0.9931 | 0.4608 |


## Window-level detection (60-min window, operator-relevant)

Alarm dinyatakan menyala bila >=5% baris dalam jendela 60 menit ditandai.

| Detector | FAR | recall (window) | precision | F1 |
|---|---|---|---|---|
| isolation_forest | 0.02 | 0.04 | 0.9897 | 0.0769 |
| robust_z | 0.04 | 0.2617 | 0.9968 | 0.4145 |
| residual | 0.06 | 0.2838 | 0.9956 | 0.4416 |

## Cara membaca
- ROC-AUC/PR-AUC = kualitas peringkat detektor tanpa memilih ambang.
- PERINGATAN: PR-AUC tampak tinggi (0.98) karena kelas rusak mayoritas — gunakan
  ROC-AUC / balanced-accuracy / MCC untuk gambaran seimbang.
- Titik operasi = 'batas toleransi' deteksi: pada FAR 5%, berapa fault tertangkap
  (level baris). Deteksi level BARIS memang sulit (ROC-AUC 0.62-0.69).
- Deteksi level JENDELA (lebih relevan operator) lihat tabel di atas.

## Batasan
- RTU != PAC produksi; ini benchmark konsep, jangan pindahkan ambang ke produksi.
- Label di level-file (baris diasumsikan rusak); kondisi transient mungkin salah label.