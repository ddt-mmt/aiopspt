# Evaluasi AIOps untuk Data Center HPC — Metodologi & Hasil Terukur

**Konteks:** proyek AIOps prediktif (UPS/PAC) berbasis Zabbix–Grafana untuk fasilitas HPC.
**Tanggal evaluasi:** 2026-11-16. **Sifat:** read-only untuk produksi; data benchmark bersifat offline.
**Reproduksi:** seluruh angka di dokumen ini dihasilkan oleh skrip di `analysis/benchmark/` dan `analysis/scripts/`; setiap artefak punya JSON/CSV pendamping.

> Dokumen ini menyajikan hasil **terukur** menggantikan klaim yang sebelumnya
> berstatus `NOT_MEASURABLE`. Ia juga **memisahkan tegas** antara model produksi
> di data nyata dan benchmark publik — dua hal yang tidak boleh dicampur.

---

## 0. Ringkasan eksekutif (untuk pembaca cepat)

1. **Temuan akar masalah (integritas data).** Sistem produksi sebelumnya menampilkan
   nilai **sintetik/acak**, bukan telemetri sensor: engine menulis ulang key sensor dengan
   rumus turunan Health Score (F-1) dan memakai `np.random` saat quality gate gagal (F-2).
   Konsekuensinya, klaim "akurasi tidak dapat dipastikan" adalah gejala, bukan sebab.
2. **Perbaikan integritas terverifikasi.** Engine yang diperbaiki menjalankan siklus nyata
   dengan **0 tulisan ke Zabbix** (mode DRY_RUN), menghasilkan **6 nilai Health berbeda &
   deterministik** (bukan uniform), dan **1 abstain jujur** saat data tidak mencukupi
   (`analysis/evidence/staging_dry_run.json`).
3. **Akurasi prognostik kini TERUKUR (benchmark NASA).** Pada sel baterai dengan ground
   truth EOL, ekstrapolasi linear mencapai **MAE ≈ 15 siklus** vs baseline naive ≈ 39 siklus
   (subset kanonik). Ini menjawab "seberapa akurat" dengan angka, bukan klaim.
4. **Deteksi kerusakan kini TERUKUR (benchmark LBNL RTU).** Isolation Forest engine mencapai
   **F1 ≈ 0.46 (recall 0.30)** pada data berlabel; baseline statistik Robust-Z lebih baik
   (**F1 ≈ 0.71, recall 0.56**). Ini bukti bahwa model produksi **belum optimal** dan
   memberi arah perbaikan yang konkret.
5. **Datasets publik kini benar-benar diakuisisi.** Sebelumnya `NOT_ACQUIRED` dengan hash
   payload kosong; sekarang LBNL (305 MB) & NASA (210 MB) terunduh, terverifikasi SHA-256,
   dan siap dipakai (`analysis/benchmark/DATASET_ACQUISITION_MANIFEST.json`).
6. **Toleransi prediksi kini JUJUR (interval terkalibrasi).** Menggunakan **conformal
   prediction**, band 80% benar-benar berisi nilai sebenarnya **86%** dari waktu — sedangkan
   bootstrap naive yang "terlihat presisi" (±9 siklus) hanya mencakup **21%** (band yang
   **berbohong**, analepsi indikator bahan bakar). Engine juga kini mengeluarkan **band TTF**
   (lo–point–hi), bukan angka tunggal.

---

## 0b. Posisi konseptual: prediksi = rentang, bukan titik

Prediksi sisa umur (RUL/TTF) **tidak mungkin 100% pasti** — sama seperti indikator bahan bakar
kendaraan berubah saat menanjak, macet, atau gaya berkendara berubah. Nilai tunggal
("RUL = 50") menyesatkan; yang benar adalah **rentang + tingkat keyakinan**, mis. *"RUL ≈ 50,
band 80%: 35–68"*. Kontribusi metodologis dokumen ini: **mengukur apakah rentang itu jujur**
(calibration) dan **seberapa ketat** (sharpness) — bukan sekadar mempersempit angka.

Dua istilah kunci (standar literatur prognostik):
- **PICP (Prediction Interval Coverage Probability):** fraksi nilai sebenarnya yang jatuh di
  dalam band. Harus ≈ tingkat nominal (mis. band 80% → PICP ≈ 0.80).
- **MPIW (Mean Prediction Interval Width):** lebar rata-rata band. Semakin sempit semakin
  tajam — **asalkan PICP terjaga**. Band sempit dengan PICP rendah = kebohongan.

## 1. Pertanyaan penelitian & posisi kontribusi

- **RQ1 (integritas):** apakah keluaran sistem mewakili telemetri sensor sebenarnya?
- **RQ2 (prognostik):** seberapa akurat estimasi RUL/TTF terhadap ground truth nyata?
- **RQ3 (deteksi):** seberapa baik deteksi anomali menemukan kerusakan berlabel?
- **RQ4 (toleransi):** seberapa jujur dan ketat rentang prediksi (interval) yang dilaporkan?

Kontribusi metodologis: kerangka evaluasi **leakage-aware** + **manifest akuisisi ber-hash**
+ **pemisahan domain** (referensi publik ≠ telemetri operasional) yang dapat direproduksi.

---

## 2. Metodologi

### 2.1 Pemisahan domain data (kebijakan)
| Sumber | Peran | Dicek ke produksi? |
|---|---|---|
| Telemetri Zabbix (UPS/PAC) | Operasional; input engine | Ya (read-only) |
| NASA PCoE Battery #5 | Benchmark prognostik RUL | **Tidak** |
| LBNL RTU FDD | Benchmark deteksi kerusakan | **Tidak** |

Pelanggaran prinsip ini (mencampur benchmark ke jalur produksi tanpa pemetaan fitur &
anti-leakage) **dihindari** — sesuai kebijakan proyek.

### 2.2 Akuisisi & integritas dataset
Setiap dataset dinyatakan `ACQUIRED_VERIFIED` hanya bila: URL resmi + tanggal + path lokal +
ukuran byte non-nol + SHA-256 arsip + uji integritas zip + hitung artefak. Detail:

| Dataset | Ukuran arsip | SHA-256 (potong) | Artefak |
|---|---|---|---|
| NASA Battery #5 | 209,708,670 B | `82302a7d…` | 34 `.mat` (B0005–B0056) |
| LBNL RTU | 305,603,469 B | `9de1dc2e…` | 81 CSV (Simulated/ORNL/Field) |

### 2.3 Protokol benchmark RUL (NASA) — *leakage-aware*
- EOL didefinisikan 70% kapasitas rated 2.0 Ah → **1.4 Ah** (ambang literatur).
- Titik prediksi pada fraksi umur 0.5/0.6/0.7/0.8; model **hanya dilatih dari siklus yang
  sudah teramati** (≤ titik prediksi); siklus masa depan tidak pernah dipakai.
- Filter validitas: sel harus **mulai sehat** (kapasitas awal > EOL) dan **mencapai EOL**.
  Sel protokol "randomized" yang mulai sudah terdegradasi dikeluarkan (jika tidak, EOL
  menyulut di siklus 0 dan merusak metrik).
- Model dibandingkan: naive (RUL=0), linear, sqrt, exp.

### 2.4 Protokol benchmark deteksi (LBNL) — *supervised*
- Train **hanya** pada baseline sehat (50% pertama). Uji pada sisa baseline (label SEHAT)
  dan 24 file fault (label RUSAK).
- Metrik level-baris: precision, recall, F1, false-alarm-rate, confusion matrix.
- Detektor: Isolation Forest (engine) vs Robust-Z (baseline statistik).

### 2.5 Verifikasi staging (integritas keluaran)
Siklus engine dijalankan `DRY_RUN=1` terhadap Zabbix produksi (read-only). Diukur: jumlah
tulisan (harus 0), jumlah nilai Health berbeda (bukti tidak uniform-acak), jumlah abstain.

---

## 3. Hasil

### 3.1 Integritas keluaran (RQ1) — terverifikasi
Sumber: `analysis/evidence/staging_dry_run.json`

| Metrik | Nilai | Interpretasi |
|---|---|---|
| Tulisan ke Zabbix (DRY_RUN) | **0** | tidak ada mutasi saat verifikasi |
| Nilai Health berbeda antar-host | **6 dari 6** | deterministik, bukan uniform acak |
| Host abstain (data tak cukup) | **1** (ME_PAC4) | abstain jujur, bukan angka karangan |

Rincian Health (satu siklus nyata): UPS1 62.22 · UPS2 67.60 · UPS3 71.20 ·
PAC1 58.57 · PAC2 57.36 · PAC3 62.50 · PAC4 UNAVAILABLE.

> Bandingkan dengan perilaku lama: Health berayun acak (stdev 4–6, nilai berbeda tiap
> siklus tanpa dasar). Sekarang berbeda **antar-host** namun stabil **per-host**.

### 3.2 Akurasi prognostik RUL (RQ2) — TERUKUR
Sumber: `analysis/benchmark/results/nasa_rul/`. Sel valid yang mencapai EOL: **10** dari 33.

**Subset kanonik (B0005/B0006/B0007/B0018 — sel standar literatur), unit = siklus:**

| Model | MAE | RMSE | bias | median | p90 |
|---|---|---|---|---|---|
| naive (RUL=0) | 38.67 | 40.73 | −38.67 | 38.50 | 53.60 |
| **linear** | **14.99** | 24.50 | +7.41 | 10.00 | 28.20 |
| exp | 26.98 | 40.40 | +24.59 | 16.55 | 51.45 |
| sqrt | 103.66 | 158.86 | +103.66 | 68.61 | 190.28 |

**Seluruh sel valid (n=15 prediksi):** linear MAE 13.22 · RMSE 22.09.

**Interpretasi:** ekstrapolasi linear mengalahkan baseline naive secara berarti
(MAE 15 vs 39 siklus; ~62% lebih kecil), tetapi **bias positif** (cenderung over-estimasi
RUL / optimistis) dan **p90 ≈ 28 siklus** menunjukkan ekor error yang besar. Model
`sqrt` justru buruk untuk protokol ini. **Tidak ada klaim akurasi absolut sebagai "±X%":
yang dilaporkan adalah distribusi error terukur.**

> Konversi ke waktu bergantung laju siklus; NASA memakai siklus cepat. Karena itu metrik
> dinyatakan dalam **siklus** agar jujur, bukan "jam" yang bisa menyesatkan.

### 3.3 Deteksi kerusakan (RQ3) — TERUKUR
Sumber: `analysis/benchmark/results/lbnl_fdd/`. Train pada baseline sehat; uji pada
held-out baseline + 24 file fault (150k+ baris).

| Detektor | precision | recall | F1 | false-alarm-rate |
|---|---|---|---|---|
| **Isolation Forest (engine)** | 0.988 | **0.301** | 0.461 | 0.179 |
| Robust-Z baseline | 0.990 | **0.559** | **0.715** | 0.263 |

**Interpretasi:** Isolation Forest sangat **spesifik** (precision 0.99) tapi **tidak
sensitif** (recall 0.30) — ia hanya menandai ~30% baris rusak. Baseline statistik sederhana
menangkap fault lebih banyak. Ini temuan penting tesis: **kontaminasi 0.05 membuat model
"pelit" menandai anomali**, dan mendeteksi fault bertipe halus (mis. undercharge ringan,
deteksi ~0.12) sangat lemah. Arah perbaikan: kalibrasi ambang per-fault, fitur residual
terhadap baseline, atau model supervised.

**Deteksi per-fault (Isolation Forest) — contoh:**
| Fault | ISO flag-rate |
|---|---|
| suctionpipe09bar | 1.000 |
| evapfouling50 | 0.848 |
| condfouling50 | 0.319 |
| undercharge10 | 0.116 |

Fault berat mudah terdeteksi; fault halus (undercharge/overcharge ringan) hampir tidak.

**v2 — evaluasi berbasis SKOR + pemilihan titik operasi** (`results/lbnl_fdd_v2/`).
v1 memakai satu ambang tetap; v2 mengevaluasi skor kontinu sehingga operator memilih
trade-off false-alarm vs recall.

| Detektor | ROC-AUC | recall @ FAR 5% | F1 @ FAR 5% |
|---|---|---|---|
| Isolation Forest (engine) | 0.621 | 0.035 | 0.068 |
| Robust-Z | 0.688 | 0.273 | 0.429 |
| Residual-to-baseline | 0.634 | 0.276 | 0.432 |

**Peringatan metrik penting:** PR-AUC yang tampak tinggi (0.98) adalah **artefak
ketidakseimbangan kelas** (baris rusak justru mayoritas pada set uji gabungan), bukan
kualitas deteksi. Untuk gambaran seimbang gunakan **ROC-AUC / balanced-accuracy / MCC** —
dan di sana terlihat deteksi level-baris memang **sulit** (ROC-AUC 0.62–0.69).

**Deteksi level-JENDELA (relevan operator; FAR dikontrol dari jendela sehat):**

| Detektor | recall (window 60 mnt) | F1 | FAR |
|---|---|---|---|
| Isolation Forest (engine) | 0.040 | 0.077 | 0.02 |
| Robust-Z | 0.262 | 0.415 | 0.04 |
| Residual-to-baseline | 0.284 | 0.442 | 0.06 |

**Kesimpulan deteksi:** pada kontrol false-alarm yang jujur, ketiga detektor unsupervised
**lemah**, dan Isolation Forest engine adalah yang terlemah. Baseline statistik sederhana
(Robust-Z / residual) lebih baik. Ini temuan negatif yang valid dan penting untuk tesis:
*pendekatan unsupervised generik tidak cukup untuk FDD halus* — arah lanjutan: fitur
residual per-parameter, model supervised, atau residual terhadap baseline musiman.

### 3.4 Toleransi prediksi — Interval Terkalibrasi (RQ baru, inti analogi bahan bakar)
Sumber: `analysis/benchmark/results/nasa_rul_intervals/`.
Prediksi titik memakai median residual-bootstrap; band dibangun dengan **split-conformal**
(leave-one-battery-out) sehingga lebar ditentukan dari kesalahan model pada data yang ditahan.

| Metode band | Nominal | **Coverage empiris (PICP)** | Mean width (MPIW, siklus) |
|---|---|---|---|
| Bootstrap naive | 80% | **0.21** ❌ | 9.2 |
| **Conformal** | 50% | 0.57 | 18.7 |
| **Conformal** | 80% | **0.86** ✅ | 57.3 |
| **Conformal** | 90% | 0.86 | 114.7 |

**Interpretasi (inti tesis):** bootstrap naive menghasilkan band **sempit tapi bohong** —
mengklaim 80% namun hanya 21% benar (nilai sebenarnya di luar rentang 4 dari 5 kali).
Conformal **memperlebar** band (80% → ~57 siklus) sehingga coverage ≈ nominal: inilah
"batas toleransi sejujur mungkin". **Band yang lebar tetapi benar > band sempit yang salah.**

**Di engine produksi:** fungsi `compute_ttf_band_for_df` kini mengeluarkan band TTF
(`ups.ttf.low/high.hours`, `pac.ttf.low/high.hours`). Pada data nyata saat ini, band
melaporkan `8760–8760h` bila tidak terdeteksi tren degradasi (bukan mengarang lebar),
dan `n/a` bila tak dapat diekstrapolasi. Contoh keluaran nyata (DRY_RUN):
`UPS ME_UPS1 … TTF: 8760.0h | Band(80%): 8760.0-8760.0h`.

---

## 4. Batasan (wajib dinyatakan — integritas ilmiah)

1. **Domain benchmark ≠ produksi.** NASA = sel Li-ion lab; LBNL = RTU HVAC. UPS/PAC data
   center berbeda (kimia, beban, kondisi). Angka ini **bukan** akurasi perangkat produksi —
   melainkan **kemampuan metodologi** pada data ber-ground-truth.
2. **Ground truth produksi tetap kosong.** Tanpa catatan kegagalan UPS/PAC nyata, akurasi
   TTF/RUL di produksi tetap **tidak dapat diukur secara langsung**; benchmark ini adalah
   **proksi metodologis**, bukan validasi lapangan.
3. **TTF produksi sering jenuh 8760h** (tidak ada tren degradasi terdeteksi dalam jendela),
   sehingga belum informatif — perlu model ber-interval & horizon yang sesuai.
4. **Health Score belum dikalibrasi** (bukan probabilitas).
5. **Recall deteksi rendah (0.30)** → false-negative tinggi; jangan jadikan satu-satunya
   alarm operasional.
6. Kualitas data produksi: `battery.temperature` (SNMP) nol data; `return.humidity.rh`
   terbaca ~5xx–6xx (skala/unit item salah).

---

## 5. Kesimpulan

- **RQ1:** ✅ sistem dapat dipastikan menampilkan data nyata (0 tulisan, nilai deterministik,
  abstain saat data kurang) — setelah perbaikan integritas.
- **RQ2:** ✅ akurasi prognostik **terukur**: linear MAE ≈ 15 siklus (kanonik) vs naive ≈ 39;
  bias positif & ekor error besar → model masih sederhana tapi lebih baik dari baseline.
- **RQ3:** ✅ deteksi **terukur**: pada kontrol false-alarm jujur, ROC-AUC 0.62–0.69
  (deteksi level-baris sulit), recall window 0.04–0.28. Engine Isolation Forest
  **terlemah**; baseline statistik lebih baik → arah perbaikan jelas.
- **RQ4 (baru — toleransi):** ✅ interval prediksi **terkalibrasi**: conformal 80% → PICP 0.86
  (jujur), sedangkan bootstrap naive → PICP 0.21 (bohong). Engine kini mengeluarkan band
  TTF, bukan angka tunggal.

**Pesan tesis (tiga lapis):**
1. **Integritas data dulu, baru akurasi.** Sistem yang mengarang angka membuat "akurasi"
   tak bermakna (lihat F-1/F-2).
2. **Prediksi yang benar = rentang yang jujur, bukan angka sempit.** Band sempit yang salah
   (PICP 0.21) lebih buruk daripada band lebar yang benar (PICP 0.86) — persis indikator
   bahan bakar yang tidak berbohong.
3. **Metrik seimbang wajib.** PR-AUC tinggi bisa menipu akibat ketidakseimbangan kelas;
   laporkan ROC-AUC/MCC/coverage agar tidak menyesatkan.

---

## 6. Reproduksi (perintah lengkap)

```bash
# 0. Uji keamanan engine (offline)
python3 tests/test_aiops_safety.py

# 1. Akuisisi & manifest dataset (butuh internet) — lihat manifest untuk hash
#    (arsip ~500 MB; data lokal, tidak di-commit)

# 2. Benchmark RUL (NASA)
python3 analysis/benchmark/run_nasa_rul_benchmark.py   # -> results/nasa_rul/

# 3. Benchmark deteksi (LBNL) — v1 (ambang tunggal) & v2 (skor + titik operasi)
python3 analysis/benchmark/run_lbnl_fdd_benchmark.py       # -> results/lbnl_fdd/
python3 analysis/benchmark/run_lbnl_detector_v2.py         # -> results/lbnl_fdd_v2/

# 3b. Interval prediksi RUL (tolerance band, conformal)
python3 analysis/benchmark/run_rul_intervals.py            # -> results/nasa_rul_intervals/

# 4. Verifikasi staging (read-only, DRY_RUN)
ZABBIX_PASS=... python3 analysis/scripts/staging_dry_run.py

# 5. Verifikasi binding dashboard (read-only)
ZABBIX_PASS=... python3 analysis/scripts/verify_dashboard_bindings.py
```

## 7. Peta artefak
| Klaim | Artefak pendukung |
|---|---|
| Integritas keluaran | `evidence/staging_dry_run.json` |
| Akurasi RUL | `benchmark/results/nasa_rul/{metrics.json,predictions.csv,REPORT.md}` |
| Interval RUL (tolerance band) | `benchmark/results/nasa_rul_intervals/{rul_intervals.json,per_point.csv,REPORT.md}` |
| Deteksi kerusakan (v1 & v2) | `benchmark/results/lbnl_fdd*/{metrics.json,REPORT.md}` |
| Akuisisi data | `benchmark/DATASET_ACQUISITION_MANIFEST.json` |
| Akar masalah (sebelum) | `README.md`, `FINDINGS.md`, `evidence/data_volume_compare.json` |
