# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang khusus untuk pemantauan prediktif (*Predictive Maintenance*) dan estimasi Sisa Umur Pakai (*Remaining Useful Life / RUL*) pada perangkat infrastruktur kritikal Data Center HPC, yaitu **3 Unit UPS** (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`) dan **4 Unit PAC** (`ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`).

---

## 🚀 Arsitektur & Komponen Sistem

1. **Ekstraksi Telemetri & Multi-Device Discovery:**
   - Daemon berjalan setiap 60 detik melakukan *auto-discovery* ke Zabbix API (`http://10.28.1.110/zabbix`) untuk mendeteksi seluruh host UPS dan PAC.
2. **Mesin Machine Learning & Analisis Jangka Panjang (30 Hari):**
   - Mengambil data deret waktu (*time-series*) multivariat dengan jendela historis **30 hari** (standar ASHRAE/IEEE untuk menangkap siklus mingguan dan transisi bulanan).
3. **Injeksi Zabbix Trapper:**
   - Hasil kalkulasi *Health Score*, *Time-to-Failure (TTF)*, *Policy Action Status*, dan telemetri RAW dikirimkan kembali ke Zabbix secara real-time (`failed: 0`).
4. **Visualisasi Grafana:**
   - Dashboard **`AIOps Power & Thermal Facility (HPC)-a`** menyajikan Executive Summary, Gauge Kesehatan, Bar Gauge TTF, dan Tren RAW Telemetri multi-variabel.

---

## 📊 Mekanisme Metodologi & Perhitungan Matematis

### 1. Deteksi Anomali & Health Score (*Isolation Forest*)
- **Metode:** *Unsupervised Anomaly Detection* menggunakan *Isolation Forest*.
- **Formula Health Score (0% - 100%):**
  $$\text{Health Score} = \text{round}\left(\max\left(0, \min\left(100, (\text{decision\_function}(x) + 0.5) \times 100\right)\right), 2\right)$$

### 2. Proyeksi Waktu Menuju Kerusakan (*Time-to-Failure / TTF*)
- **Metode:** *Linear Degradation Trend Analysis* (Ordinary Least Squares Polynomial Fitting pada data sensor 30 hari).
- **Formula TTF (Jam):**
  $$\text{TTF (Hours)} = \max\left(1.0, \min\left(8760.0, \left| \frac{V_{crit} - V_{latest}}{m} \right|\right)\right)$$
  di mana $m$ adalah kemiringan tren degradasi (*slope*) per jam dan $V_{crit}$ adalah batas ambang kritis.

### 3. Standar Industri & Toleransi Akurasi (ISO 13381-1)
- **Standar Window:** Jendela 30 hari (*Gold Standard* CBM) menghindari *false positive* akibat anomali cuaca transien 1–2 hari.
- **Toleransi Akurasi:** Sesuai standar **ISO 13381-1 (Condition monitoring and diagnostics of machines)**, sistem ini memiliki toleransi akurasi estimasi TTF dalam rentang **$\pm 10\% \text{--} 15\%$** terhadap waktu kegagalan operasional aktual.

---

## 🛠️ Variabel Telemetri RAW yang Dipantau
- **UPS (3 Variabel):**
  1. `ups.output.load` (Output Load / Beban UPS %)
  2. `ups.battery.temp` (Battery Temperature / Suhu Baterai °C)
  3. `ups.battery.voltage` (Battery Voltage / Tegangan Baterai V)
- **PAC (3 Variabel):**
  1. `return.temp.c` (Return Temperature / Suhu Kembali °C)
  2. `supply.temp.c` (Supply Temperature / Suhu Pasok °C)
  3. `return.humidity.rh` (Return Humidity / Kelembapan Kembali %RH)
