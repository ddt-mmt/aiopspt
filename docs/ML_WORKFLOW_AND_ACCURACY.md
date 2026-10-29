# AIOps Machine Learning Workflow, Pipeline Flow & Accuracy Tolerances

Dokumen ini menyajikan rincian teknis mengenai alur kerja (*workflow*) mesin prediktif AIOps V11, spesifikasi teknis pengambilan data Zabbix API, sumber data (*data sources*) dan provenansinya, tahapan pemrosesan, formulasi matematis regresi, serta toleransi akurasi prediksi dari hasil pengolahan model.

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

Engine AIOps V11 divalidasi dan dilatih menggunakan kombinasi data operasional nyata (*real-world operational telemetry*) dari infrastruktur data center serta dataset benchmark publik standar industri:

### A. Sumber Data Produksi / Real Telemetry (Zabbix 365-Day Historical Data)
- **Asal Sumber:** Diekstraksi langsung dari histori database Zabbix server pada fasilitas HPC (`prox-prod`, IP `10.28.1.110`) mencakup rentang data historis hingga 365 hari.
- **Karakteristik:** Berisi pembacaan sensor asinkron dari perangkat fisik nyata (UPS APC/Schneider dan PAC Mitsubishi/Schneider) yang mengalami fluktuasi beban termal dan daya operasional harian sesungguhnya.
- **Manifesto & Export Path:** Artefak ekstraksi tersimpan di direktori `/root/grafan_aiops/real_data_validation_365d/` (mencakup `zabbix_events_365d.csv`, manifes ekspor, dan laporan kualitas data).

### B. Sumber Data Dataset Publik & Benchmark Pendukung (*Public Benchmarks*)
Untuk menguji kekhususan (*robustness*) deteksi anomali dan degradasi baterai/kompresor, model juga divalidasi terhadap dataset benchmark publik standar akademik:
1. **LBNL Fault Detection and Diagnostics (FDD) Dataset:** Digunakan untuk memvalidasi pola kegagalan termal dan penurunan efisiensi unit penyejuk udara (*Precision Air Conditioner* / PAC).
2. **NASA Prognostics Center of Excellence (PCoE) Battery Dataset:** Digunakan untuk menguji keakuratan estimasi *Remaining Useful Life* (RUL) dan kurva degradasi tegangan/kapasitas sel baterai UPS.
- **Manifesto & Path:** Artefak dan manifest tersimpan pada direktori `/root/grafan_aiops/shadow_v5/` (seperti `PUBLIC_DATASET_ACQUISITION_MANIFEST.json`).

---

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
     - `DEGRADED_DATA`: Sebagian data terputus/jarang (*sparse*), diatasi dengan interpolasi terkontrol (*forward/backward fill* yang dibatasi).
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

## 5. Toleransi Akurasi Prediksi & Batas Keyakinan (*Accuracy Tolerances*)

Mengingat kompleksitas lingkungan data center HPC dan ketiadaan riwayat kegagalan perangkat keras jangka panjang (*ground truth failure data*), toleransi akurasi dan batas keyakinan model didefinisikan secara konservatif sebagai berikut:

### A. Toleransi Margin Kesalahan (*Margin of Error*)
- **Estimasi TTF (Time to Failure):** 
  - Toleransi kesalahan deviasi waktu: **$\pm 15\%$ dari total rentang waktu observasi aktif** (dengan asumsi kondisi beban termal dan daya stabil).
  - Jika terjadi fluktuasi beban mendadak (*load spike*), model secara otomatis memperlebar rentang keyakinan dan mengirimkan status peringatan `DEGRADED_DATA`.
- **Estimasi RUL (Remaining Useful Life):**
  - Menggunakan tingkat toleransi konservatif **$\pm 20\%$** untuk mengakomodasi variasi pembacaan sensor *sparse* (seperti kapasitas baterai UPS).

### B. Batas Keyakinan & Mekanisme Abstain (*Confidence Intervals & Abstention*)
- **Ambang Batas Minimum Sampel ($N_{\min}$):** Model menolak memproduksi prediksi RUL jika jumlah sampel historis valid dalam jendela waktu berjalan kurang dari 12 titik data ($n < 12$).
- **Derajat Keyakinan (*Confidence Score*):**
  - *High Confidence (>85%):* Data berstatus `NORMAL`, koefisien determinasi regresi linier ($R^2 > 0.75$).
  - *Medium Confidence (50%–85%):* Data berstatus `DEGRADED_DATA` dengan interpolasi ringan.
  - *Zero Confidence (Abstain):* Data berstatus `INSUFFICIENT_DATA` atau tren linier mendatar ($m \approx 0$). Pada kondisi ini, sistem **tidak mengeluarkan prediksi RUL** untuk menghindari alarm palsu.

---
*Dokumen ini merupakan bagian dari spesifikasi teknis AIOps V11.*
