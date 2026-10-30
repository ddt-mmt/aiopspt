# AIOps Machine Learning Workflow, Pipeline Flow & Accuracy Tolerances

Dokumen ini menjelaskan alur historis V11 dan persyaratan validasi kandidat V12. Konfigurasi algoritma, target desain, bukti akuisisi dataset, hasil benchmark, dan akurasi terukur dibedakan secara eksplisit. V12 tetap kandidat staging sampai melewati promotion gate.

---

## 1. Spesifikasi Teknis Pengambilan Data dari Zabbix (`Zabbix API Extraction & Query Specification`)

Engine AIOps V11 berinteraksi secara aktif dengan Zabbix Server menggunakan **Zabbix JSON-RPC API** dan utilitas lokal **`zabbix_sender`**. Berikut adalah rincian teknis bagaimana data diambil, difilter, dan disiapkan untuk diolah oleh mesin learning:

### A. Metode API Zabbix yang Digunakan
1. **`host.get`:**
   - **Tujuan:** Menemukan dan memetakan host fasilitas HPC yang terdaftar secara otomatis berdasarkan kelompok perangkat (*host groups*) UPS dan PAC.
   - **Filter:** Berdasarkan penamaan konvensi host production (`ME_UPS1`, `ME_UPS2`, `ME_PAC1`, `ME_PAC2`, dll.).
2. **`item.get`:**
   - **Tujuan:** Mengambil ID item Zabbix unik (*itemid*) berdasarkan *key* sensor fisik aktual (misalnya `upsHighPrecBatteryActualVoltage`, `return.temp.c`, dll.).
   - **Parameter Kunci (*Item Keys*):**
     - UPS: `upsHighPrecBatteryActualVoltage`, `upsHighPrecBatteryCapacity`, `upsHighPrecOutputLoad`, `upsAdvBatteryRunTimeRemaining`.
     - PAC: `return.temp.c`, `supply.temp.c`, `return.humidity.rh`, `evaporator.fan.speed`, `compressor.status`.
3. **`history.get`:**
   - **Tujuan:** Menarik data deret waktu (*time-series history*) dari *itemid* yang telah dipetakan dalam rentang waktu (*time window*) tertentu (default: 24 jam terakhir hingga histori agregasi 365 hari untuk pelatihan offline).
   - **Parameter Kueri:**
     - `history`: Tipe data numerik float (`0`).
     - `time_from` & `time_till`: Batas jendela waktu kueri riwayat.
     - `sortfield`: `clock` (diurutkan secara kronologis menaik).

### B. Alur Ekstraksi Data Kueri ke Model ML
```ascii
[ Zabbix Server API ] 
         │ (JSON-RPC: history.get)
         ▼
[ Raw Time-Series JSON ] 
         │ (Timestamp `clock` & Value `value`)
         ▼
[ Pandas DataFrame Conversion ] 
         │ (Sorting & Missing Value Masking)
         ▼
[ ML Preprocessing & Quality Gating ]
```

---

## 2. Sumber Data dan Provenansi (*Data Sources & Provenance*)

### A. Operational telemetry — Zabbix

Zabbix UPS/PAC merupakan sumber utama untuk pengamatan operasional fasilitas. Data harus ditelusuri per host dan item, termasuk item ID, key, unit, value type, timestamp, serta asal nilai.

Klasifikasi provenance:
- `PHYSICAL_SENSOR_CONFIRMED`
- `ZABBIX_TRAPPER_DERIVED`
- `AIOPS_DERIVED`
- `UNKNOWN`

Nama item saja tidak membuktikan bahwa sebuah nilai berasal langsung dari sensor fisik. Riwayat harus ditinjau khususnya ketika versi runtime sebelumnya pernah memiliki jalur push ke Zabbix atau menghasilkan nilai turunan/simulasi.

Ekspor historis Zabbix yang tersimpan di workspace proyek hanya boleh disebut sebagai dataset operasional terverifikasi apabila manifest, rentang waktu, item mapping, record count, dan checksum aktual tersedia.

### B. Public benchmark sources

Dataset publik digunakan sebagai evaluasi independen dan tidak otomatis menjadi bagian dari training atau inference produksi.

1. **LBNL Fault Detection and Diagnostics — RTU**
   - Official data catalogue: https://faultdetection.lbl.gov/data/
   - RTU page: https://faultdetection.lbl.gov/dataset/rtu/
   - Simulated RTU ZIP: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.zip
   - All three RTU files: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU_all_3.zip
   - DOI: https://doi.org/10.25984/1881324

   RTU benchmark mencakup fault-free dan faulty scenarios dari simulasi, pengujian laboratorium, serta pengukuran lapangan. RTU bukan PAC produksi; feature mapping harus didasarkan pada makna fisik, unit, sampling, dan konteks operasi.

2. **NASA PCoE Battery Data Set #5**
   - Official repository: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
   - Direct ZIP: https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip
   - Citation: B. Saha and K. Goebel (2007), “Battery Data Set,” NASA Prognostics Data Repository, NASA Ames Research Center.

   Dataset berisi eksperimen baterai Li-ion pada charging/discharging dengan temperatur berbeda dan pengukuran impedance. Dataset ini bukan representasi otomatis chemistry atau operasi baterai UPS produksi.

3. **NASA PCoE Randomized Battery Usage Data Set #11 — supplementary**
   - Direct ZIP: https://phm-datasets.s3.amazonaws.com/NASA/11.+Randomized+Battery+Usage+Data+Set.zip

   Dataset ini dapat menjadi benchmark tambahan untuk studi penggunaan baterai dan state of health; status akuisisi/pengujian harus dicatat terpisah.

### C. Acquisition and benchmark evidence status

Ringkasan Phase 87.3 menyatakan:
- Source references: verified.
- Manifest: created in staging.
- LBNL/NASA benchmark: `EXECUTED_SIMULATION`.
- Native archive acquisition: belum dibuktikan dengan file non-zero, SHA-256 arsip, dan input manifest.
- Native public-file benchmark: `NOT_VERIFIED` / `NOT_EXECUTED` sampai artefak tersebut tersedia.

Manifest historis `shadow_v5/PUBLIC_DATASET_ACQUISITION_MANIFEST.json` mencatat fixture status dan hash konten kosong. Hash kosong bukan checksum dataset. Lihat [PUBLIC_DATASETS_AND_BENCHMARKS.md](PUBLIC_DATASETS_AND_BENCHMARKS.md) dan [PUBLIC_DATASET_STATUS_MANIFEST.json](PUBLIC_DATASET_STATUS_MANIFEST.json).

### D. Separation policy

Pisahkan:
1. Zabbix real operational telemetry.
2. LBNL HVAC/RTU public benchmark.
3. NASA battery public benchmark.

Jangan mencampurkan sumber-sumber ini ke satu training set tanpa kompatibilitas domain, feature mapping, normalisasi, label quality, dan validasi anti-leakage yang dapat direproduksi.

## 3. Spesifikasi Data Telemetri yang Diolah oleh Machine Learning

Engine AIOps V11 mengolah data time-series dari perangkat infrastruktur daya kritis (**UPS**) dan pendingin ruangan data center (**PAC**). Berikut adalah rincian parameter, satuan, dan fungsi metrik yang digunakan sebagai input model:

### A. Perangkat UPS (Uninterruptible Power Supply - APC / Schneider)
| No | Nama Metrik / Parameter Zabbix | Deskripsi Fisik / Fungsi | Jenis Variabel | Resolusi / Jendela Waktu |
|----|--------------------------------|--------------------------|----------------|--------------------------|
| 1 | `battery.voltage` (*battery.voltage_upsHighPrecBatteryActualVoltage*) | Tegangan aktual baterai UPS. Indikator utama kesehatan sel baterai. | Kontinu | Real-time (60s polling) |
| 2 | `battery.capacity` (*battery.capacity_upsHighPrecBatteryCapacity*) | Persentase kapasitas simpan baterai saat ini. | Kontinu (Sparse) | Real-time (60s polling) |
| 3 | `output.load` (*output.load_upsHighPrecOutputLoad*) | Beban daya aktual pada inverter UPS (dalam persentase beban maksimum). | Kontinu | Real-time (60s polling) |
| 4 | `battery.runtime_remaining` (*battery.runtime_remaining_upsAdvBatteryRunTimeRemaining*) | Sisa waktu cadangan baterai saat pemadaman listrik (dalam detik). | Kontinu | Real-time (60s polling) |

### B. Perangkat PAC (Precision Air Conditioner - Mitsubishi / Schneider)
| No | Nama Metrik / Parameter Zabbix | Deskripsi Fisik / Fungsi | Jenis Variabel | Resolusi / Jendela Waktu |
|----|--------------------------------|--------------------------|----------------|--------------------------|
| 1 | `return.temp.c` | Suhu udara balik (*return air temperature*) ke unit PAC. | Kontinu | Real-time (60s polling) |
| 2 | `supply.temp.c` | Suhu udara suplai (*supply air temperature*) yang diembuskan ke cold aisle. | Kontinu | Real-time (60s polling) |
| 3 | `return.humidity.rh` | Tingkat kelembaban relatif (*Relative Humidity*) udara balik ruangan. | Kontinu | Real-time (60s polling) |
| 4 | `evaporator.fan.speed` | Kecepatan putar kipas evaporator PAC (RPM / persentase). | Kontinu | Real-time (60s polling) |
| 5 | `compressor.status` / `aiops.compressor.status` | Status operasional kompresor (aktif/mati). | Diskrit (Biner: 0/1) | Real-time (60s polling) |

---

## 4. Alur Kerja Rinci Pipeline Machine Learning (Step-by-Step Flow)

Proses pengolahan data dan prediksi pada engine AIOps berjalan dalam siklus tertutup setiap 60 detik melalui 5 tahapan utama:

```ascii
[ Step 1: Telemetry Ingestion (Zabbix API history.get & Benchmark Data) ]
                                   │
                                   ▼
[ Step 2: Quality Gating & Preprocessing ]
                                   │
                                   ├──► [ Status: INSUFFICIENT_DATA ] ──► (Action: ABSTAIN / Skip Prediction)
                                   │
                                   └──► [ Status: NORMAL / DEGRADED ] 
                                             │
                                             ▼
[ Step 3: Feature Extraction & Isolation (Continuous vs Discrete) ]
                                   │
                                   ▼
[ Step 4: Slope Regression & TTF / RUL Computation ]
                                   │
                                   ▼
[ Step 5: Zabbix Sender Pushback & Grafana Visualization ]
```

### Rincian Tiap Tahapan:
1. **Step 1: Telemetry Ingestion (Pengambilan Data dari Zabbix API)**
   - Engine mengeksekusi kueri `history.get` via Zabbix JSON-RPC API untuk mengambil deret waktu dari parameter UPS dan PAC.
2. **Step 2: Quality Gating & Preprocessing (Gerbang Kualitas)**
   - Validator memeriksa keberadaan nilai `NaN`, `Inf`, atau data kosong.
   - Mengkategorikan data ke dalam tiga status:
     - `NORMAL`: Data lengkap dan valid ($\ge N_{\min}$).
     - `DEGRADED_DATA`: Sebagian data terputus/jarang (*sparse*), pada implementasi V11 yang diaudit menggunakan forward-fill terbatas (maksimal dua titik); penggunaan imputasi harus dicatat dan tidak boleh menggunakan informasi masa depan.
     - `INSUFFICIENT_DATA`: Data tidak memenuhi syarat minimum, memicu logika **Abstain** (engine tidak mengeluarkan prediksi palsu).
3. **Step 3: Feature Extraction & Isolation (Pemisahan Fitur)**
   - Memisahkan variabel diskrit (seperti status biner kompresor `compressor.status` `0`/`1`) dari variabel kontinu (suhu, tegangan, kelembaban) untuk mencegah distorsi tren linier.
4. **Step 4: Slope Regression & TTF / RUL Computation (Pemodelan Prediktif)**
   - Menghitung gradien tren linier (*slope* $m$) menggunakan metode *least squares*:
     $$m = \frac{n \sum (t_i y_i) - \sum t_i \sum y_i}{n \sum (t_i^2) - (\sum t_i)^2}$$
   - Menghitung *Time to Failure* (TTF) terhadap ambang batas kritis ($Y_{\text{crit}}$):
     $$\text{TTF} = \frac{Y_{\text{crit}} - y_{\text{current}}}{m}$$
5. **Step 5: Zabbix Sender Pushback (Pengiriman Hasil)**
   - Mengirimkan metrik hasil analisis (`aiops.predicted.ttf`, `aiops.predicted.rul`, `aiops.compressor.status`) ke Zabbix server untuk ditampilkan pada dasbor Grafana.

---

## 5. Akurasi, Toleransi, Confidence, dan Batasan Validasi

### A. TTF/RUL accuracy

- TTF accuracy: `NOT_MEASURABLE` tanpa ground truth failure time yang sesuai untuk perangkat dan operating regime terkait.
- RUL accuracy: `NOT_MEASURABLE` tanpa ground truth end-of-life/capacity target yang tervalidasi.
- Nilai historis TTF ±15% dan RUL ±20% adalah target desain yang pernah ditulis; belum ada bukti eksperimen yang mengesahkan nilai itu sebagai error tolerance empiris.
- Jangan mengubah target desain menjadi klaim akurasi atau SLA model.

### B. Isolation Forest contamination

Konfigurasi `contamination=0.05` adalah parameter estimasi proporsi outlier yang digunakan model untuk menentukan threshold internal. Nilai ini bukan error rate 5%, bukan false-positive rate 5%, dan tidak berarti akurasi 95%.

Threshold dan score perlu dievaluasi menggunakan label atau proses review yang sesuai.

### C. Health Score

Health Score adalah indeks analitik yang dibentuk dari transformasi output model. Nilai dalam persen tidak otomatis merupakan probabilitas kesehatan fisik atau persentase kapasitas sisa perangkat.

Kalibrasi Health Score: `NOT_CALIBRATED` sampai ada metode kalibrasi dan validasi terhadap ground truth yang relevan.

### D. Confidence

Jumlah sampel, label HIGH/MEDIUM, atau status data NORMAL tidak otomatis merupakan probabilitas prediksi benar. Confidence harus membedakan:
- data sufficiency,
- data quality,
- model uncertainty,
- calibration evidence.

Implementasi V11 yang diaudit menentukan label confidence berdasarkan jumlah baris data (misalnya batas 60 baris), bukan koefisien determinasi R² sebagaimana pernah diklaim pada dokumen lama. Klaim R² harus dihapus kecuali benar-benar diimplementasikan dan diuji pada kandidat terkait.

### E. Sampling and quality gates

Pada source V11 yang diaudit:
- max data age: 300 detik;
- minimum samples pada quality gate: 10 titik;
- forward-fill limit: 2 titik;
- stale/future data dapat memicu hard gate.

Dokumentasi lama pernah menyebut minimum 12 titik. Kandidat V12 dapat menetapkan target berbeda, tetapi konfigurasi aktual harus dikonfirmasi dari source, test, dan laporan kandidat sebelum dinyatakan berlaku.

### F. Required benchmark metrics

Jika label valid tersedia, laporkan precision, recall, F1, confusion matrix, dan false-alarm rate untuk anomaly/fault detection.

Untuk regression/prognostics, laporkan MAE, RMSE, error distribution, dan per-unit performance hanya jika target ground truth sah tersedia.

Semua metrik harus mengikat:
- dataset version and checksum,
- model/source checksum,
- preprocessing version,
- train/validation/test split,
- random seed,
- execution timestamp,
- output artefact.

Public benchmark performance tidak boleh dinyatakan sebagai production UPS/PAC accuracy.

---
*Dokumen ini memuat baseline historis V11 serta batas validasi kandidat V12. Perbarui hanya berdasarkan source code dan evidence terbaru.*