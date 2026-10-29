# Metodologi AIOps dan Pemodelan Prediktif (Remaining Useful Life / RUL) untuk Infrastruktur Data Center HPC

Dokumen ini merinci arsitektur, metode matematis, dan algoritma Machine Learning yang digunakan dalam sistem AIOps (*Artificial Intelligence for IT Operations*) untuk prediksi kegagalan (*Predictive Maintenance*) pada perangkat UPS (*Uninterruptible Power Supply*) dan PAC (*Precision Air Conditioning*) di Data Center HPC.

---

## 1. Arsitektur Sistem & Alur Data
Sistem dibangun secara modular menggunakan pendekatan kontainerisasi (Docker) yang berinteraksi dengan sistem monitoring Zabbix dan divisualisasikan melalui Grafana:
1. **Ekstraksi Telemetri:** Script secara periodik (daemon setiap 60 detik) menarik data historis telemetri sensor dari Zabbix API (contoh: *Output Load* UPS dan *Return Temperature* PAC).
2. **Pemrosesan & Machine Learning:** Data historis dianalisis menggunakan algoritma *Unsupervised Anomaly Detection* dan *Linear Regression Trend Analysis*.
3. **Injeksi Balik (Zabbix Trapper):** Hasil kalkulasi berupa *Health Score*, *Time-to-Failure (TTF)*, dan *Policy Action Status* dikirimkan kembali ke Zabbix menggunakan *Zabbix Trapper Protocol*.
4. **Visualisasi & Pengambilan Kebijakan:** Grafana mengambil metrik tersebut untuk menyajikan *Executive Summary*, *RUL Prediction*, dan *Action Recommendation* bagi pengambil kebijakan.

---

## 2. Pemodelan Deteksi Anomali (*Isolation Forest*)
Untuk mendeteksi kondisi abnormal pada perangkat, digunakan algoritma **Isolation Forest**. Algoritma ini sangat efektif untuk data deret waktu (*time-series*) industri karena tidak memerlukan label data kerusakan (*unsupervised*).

### Formula & Prinsip Kerja:
1. Diberikan matriks data historis sensor $X = \{x_1, x_2, ..., x_n\}$.
2. Model membangun ensemble dari *Isolation Trees* (iTrees) dengan mempartisi ruang fitur secara rekursif.
3. Path length $h(x)$ (jumlah cabang yang dilalui untuk mengisolasi sampel $x$) berbanding terbalik dengan tingkat anomaly: sampel anomali memiliki path length yang lebih pendek karena posisinya yang terisolasi dari kluster mayoritas (normal).
4. *Anomaly Score* $s(x, n)$ didefinisikan sebagai:
   $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
   di mana $E(h(x))$ adalah rata-rata path length pada sekumpulan iTrees, dan $c(n)$ adalah faktor normalisasi rata-rata path length BST (Binary Search Tree).

---

## 3. Kalkulasi Skor Kesehatan Ekosistem (*Health Score*)
*Anomaly score* mentah dari Isolation Forest dikonversi menjadi **Health Score** ternormalisasi dalam rentang **0% hingga 100%** agar mudah diinterpretasikan oleh operator dan sistem pengambil keputusan:

$$\text{Health Score} = \text{round}\left(\max\left(0, \min\left(100, (\text{decision\_function}(x) + 0.5) \times 100\right)\right), 2\right)$$

* **100%:** Kondisi operasional sangat stabil / optimal.
* **< 70%:** Mulai terdeteksi anomali atau degradasi performa.
* **< 40%:** Kondisi kritis / anomali berat.

---

## 4. Pemodelan Sisa Umur / Waktu Menuju Kerusakan (*Time-to-Failure / RUL*)
Untuk menjawab pertanyaan *"Kapan perangkat akan mengalami kerusakan?"*, sistem menggunakan **Linear Degradation Trend Analysis** (Ordinary Least Squares Polynomial Fitting pada data sensor historis jangka pendek):

1. **Ekstraksi Tren Nilai Sensor Terakhir ($N = 50$ data point terakhir):**
   $$t = \text{Waktu dalam jam (hours)}$$
   $$v = \text{Nilai sensor (Load / Temperature)}$$
2. **Regresi Polinomial Linear ($v = mt + c$):**
   Mencari slope degradasi $m$ (laju perubahan nilai per jam):
   $$m = \frac{N\sum(tv) - \sum t \sum v}{N\sum t^2 - (\sum t)^2}$$
3. **Estimasi Batas Kritis (*Critical Threshold*):**
   Batas ambang kritis $V_{crit}$ didefinisikan secara statistik berdasarkan deviasi standar dari mean historis:
   $$V_{crit} = \mu_{v} + (3 \times \sigma_{v})$$
4. **Kalkulasi Time-to-Failure (TTF dalam Jam):**
   $$\text{TTF (Hours)} = \max\left(24.0, \min\left(720.0, \left| \frac{V_{crit} - v_{latest}}{m} \right|\right)\right)$$
   *(Dibatasi dalam rentang preventif 24 jam hingga 720 jam / 30 hari untuk menghindari proyeksi yang tidak realistis).*

---

## 5. Kerangka Pengambilan Kebijakan Pemeliharaan (*Policy Action Framework*)
Berdasarkan kombinasi *Health Score* dan *Time-to-Failure (TTF)*, sistem mengklasifikasikan status kebijakan ke dalam 3 level tindakan preventif:

| Kode Status | Label Kebijakan | Kriteria Pemicu (*Trigger Criteria*) | Rekomendasi Tindakan |
| :---: | :--- | :--- | :--- |
| **0** | **NORMAL (Aman)** | $\text{Health} \ge 70\%$ dan $\text{TTF} > 720$ jam | Operasional normal, pemantauan rutin. |
| **1** | **MAINTENANCE (Preventif)** | $40\% \le \text{Health} < 70\%$ atau $24 < \text{TTF} \le 720$ jam | Jadwalkan *Preventive Maintenance* (pembersihan filter, uji baterai). |
| **2** | **REPLACE (Segera Ganti)** | $\text{Health} < 40\%$ atau $\text{TTF} \le 24$ jam | Tindakan darurat: *Urgent Replacement* komponen sebelum terjadi *down-time*. |
