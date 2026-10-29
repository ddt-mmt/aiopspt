# AIOps Machine Learning Workflow, Pipeline Flow & Accuracy Tolerances

Dokumen ini menyajikan rincian teknis mengenai alur kerja (*workflow*) mesin prediktif AIOps V11, tahapan pemrosesan data, formulasi matematis regresi, serta toleransi akurasi prediksi dan batas keyakinan (*confidence intervals*) dari hasil pengolahan model.

---

## 1. Alur Kerja Rinci Pipeline Machine Learning (Step-by-Step Flow)

Proses pengolahan data dan prediksi pada engine AIOps berjalan dalam siklus tertutup setiap 60 detik melalui 5 tahapan utama:

```ascii
[ Step 1: Telemetry Ingestion ]
         │
         ▼
[ Step 2: Quality Gating & Preprocessing ]
         │
         ├──► [ Status: INSUFFICIENT_DATA ] ──► (Action: ABSTAIN / Skip Prediction)
         │
         └──► [ Status: NORMAL / DEGRADED ] 
                   │
                   ▼
[ Step 3: Feature Extraction & Isolation ]
         │
         ▼
[ Step 4: Slope Regression & TTF / RUL Computation ]
         │
         ▼
[ Step 5: Zabbix Sender Pushback & Grafana Visualization ]
```

### Rincian Tiap Tahapan:
1. **Step 1: Telemetry Ingestion (Pengambilan Data)**
   - Engine terhubung ke Zabbix API untuk mengambil riwayat waktu (*time-series history*) dari sensor daya UPS (tegangan baterai, kapasitas, beban output) dan pendingin PAC (suhu return, suhu supply, kelembaban, kecepatan kipas).
2. **Step 2: Quality Gating & Preprocessing (Gerbang Kualitas)**
   - Validator memeriksa keberadaan nilai `NaN`, `Inf`, atau data kosong.
   - Mengkategorikan data ke dalam tiga status:
     - `NORMAL`: Data lengkap dan valid ($\ge N_{\min}$).
     - `DEGRADED_DATA`: Sebagian data terputus/jarang (*sparse*), diatasi dengan interpolasi terkontrol (*forward/backward fill* yang dibatasi).
     - `INSUFFICIENT_DATA`: Data tidak memenuhi syarat minimum, memicu logika **Abstain** (engine tidak mengeluarkan prediksi palsu).
3. **Step 3: Feature Extraction & Isolation (Pemisahan Fitur)**
   - Memisahkan variabel diskrit (seperti status biner kompresor `0` atau `1`) dari variabel kontinu (suhu dan voltase) untuk mencegah distorsi tren linier.
4. **Step 4: Slope Regression & TTF / RUL Computation (Pemodelan Prediktif)**
   - Menghitung gradien tren linier (*slope* $m$) menggunakan metode *least squares*:
     $$m = \frac{n \sum (t_i y_i) - \sum t_i \sum y_i}{n \sum (t_i^2) - (\sum t_i)^2}$$
   - Menghitung *Time to Failure* (TTF) terhadap ambang batas kritis ($Y_{\text{crit}}$):
     $$\text{TTF} = \frac{Y_{\text{crit}} - y_{\text{current}}}{m}$$
5. **Step 5: Zabbix Sender Pushback (Pengiriman Hasil)**
   - Mengirimkan metrik hasil analisis (`aiops.predicted.ttf`, `aiops.predicted.rul`, `aiops.compressor.status`) ke Zabbix server untuk ditampilkan pada dasbor Grafana.

---

## 2. Toleransi Akurasi Prediksi & Batas Keyakinan (*Accuracy Tolerances*)

Mengingat kompleksitas lingkungan data center HPC dan ketiadaan riwayat kegagalan perangkat keras jangka panjang (*ground truth failure data*), toleransi akurasi dan batas keyakinan model didefinisikan secara konservatif sebagai berikut:

### A. Toleransi Margin Kesalahan (*Margin of Error*)
- **Estimasi TTF (Time to Failure):** 
  - Toleransi kesalahan deviasi waktu: **$\pm 15\% dari total rentang waktu observasi aktif** (dengan asumsi kondisi beban termal dan daya stabil).
  - Jika terjadi fluktuasi beban beban mendadak (*load spike*), model secara otomatis memperlebar rentang keyakinan dan mengirimkan status peringatan `DEGRADED_DATA`.
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
