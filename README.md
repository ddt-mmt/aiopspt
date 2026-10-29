# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang untuk pemantauan prediktif (*Predictive Maintenance*), estimasi kondisi operasional, dan perhitungan *Time to Failure* (TTF) serta *Remaining Useful Life* (RUL) pada infrastruktur daya kritis (**UPS**) dan pendingin ruangan data center (**PAC**).

---

## 📋 Daftar Isi
1. [Arsitektur Sistem & Diagram Alur (Flowchart)](#1-arsitektur-sistem--diagram-alur-flowchart)
2. [Aliran Data (Data Flow Pipeline)](#2-aliran-data-data-flow-pipeline)
3. [Spesifikasi Machine Learning & Cara Kerja Algoritma](#3-spesifikasi-machine-learning--cara-kerja-algoritma)
4. [Quality Gating & Pencegahan Halusinasi Prediksi](#4-quality-gating--pencegahan-halusinasi-prediksi)
5. [Status Implementasi & Runtime Aktif](#5-status-implementasi--runtime-aktif)
6. [Struktur Direktori & Inventaris Script Utama](#6-struktur-direktori--inventaris-script-utama)
7. [Panduan Pengujian Offline yang Aman](#7-panduan-pengujian-offline-yang-aman)
8. [Riwayat Insiden & Penanganan Rollback (Phase 63)](#8-riwayat-insiden--penanganan-rollback-phase-63)
9. [Batasan Validasi & Risiko](#9-batasan-validasi--risiko)

---

## 1. Arsitektur Sistem & Diagram Alur (Flowchart)

Berikut adalah diagram alur end-to-end (*flowchart*) operasional engine AIOps dari pengumpulan telemetri Zabbix hingga visualisasi di Grafana:

```ascii
+---------------------------------------------------------------------------------+
|                       ZABBIX MONITORING SERVER & SNMP AGENTS                    |
|   (UPS: APC/Schneider Battery Voltage, Capacity, Output Load, Runtime Remaining) |
|   (PAC: Mitsubishi/Schneider Return Temp, Supply Temp, Humidity, Fan Speed)     |
+---------------------------------------------------------------------------------+
                                         │
                                         │ (Polling Interval: 60 Seconds)
                                         ▼
+---------------------------------------------------------------------------------+
|                         DOCKER CONTAINER: aiops_predictor_hpc                   |
|                        Runtime Engine: /app/script_aiops.py                     |
|                                                                                 |
|   ┌──────────────────────┐     ┌────────────────────────┐     ┌───────────────┐ |
|   │ 1. Telemetry Fetch   │────▶│ 2. Data Quality Gating │────▶│ 3. ML Model   │ |
|   │    (Zabbix API)      │     │ (NORMAL / DEGRADED /   │     │ (Slope TTF &  │ |
|   └──────────────────────┘     │  INSUFFICIENT DATA)    │     │  RUL Analysis)│ |
|                                └────────────────────────┘     └───────┬───────┘ |
|                                                                       │         |
|                                                                       ▼         |
|                                ┌──────────────────────────────────────────────┐ |
|                                │ 4. Zabbix Sender (Local Metric Pushback)     │ |
|                                │    - aiops.compressor.status                 │ |
|                                │    - aiops.predicted.ttf / rül               │ |
|                                └──────────────────────┬───────────────────────┘ |
+-------------------------------------------------------│-------------------------+
                                                        │
                                                        ▼
+---------------------------------------------------------------------------------+
|                       ZABBIX DATABASE & HISTORY STORAGE                         |
+---------------------------------------------------------------------------------+
                                         │
                                         │ (Datasource Query)
                                         ▼
+---------------------------------------------------------------------------------+
|                       GRAFANA DASHBOARD FACILITY VISUALIZATION                  |
|               (aiops_facility_dashboard.json / Real-time Alerting)              |
+---------------------------------------------------------------------------------+
```

---

## 2. Aliran Data (Data Flow Pipeline)

Sistem bekerja dalam siklus tertutup (*closed-loop polling*) setiap 60 detik melalui tahapan berikut:
1. **Pengambilan Telemetri (Ingestion):** Engine menghubungi Zabbix API untuk menarik riwayat metrik (*historical history*) dari sensor daya UPS dan pendingin PAC.
2. **Penyaringan Kualitas (Quality Gating):** Validator memeriksa apakah data mentah mengandung nilai `NaN`, `Inf`, atau sampel yang tidak memenuhi syarat minimum.
3. **Eksekusi Model Machine Learning:** Data yang lolos gerbang kualitas diproses oleh modul regresi linier dan analisis tren untuk menghitung *Time to Failure* (TTF).
4. **Pengiriman Umpan Balik (Feedback Loop):** Hasil prediksi dikirimkan kembali ke Zabbix melalui `zabbix_sender` agar dapat divisualisasikan secara real-time pada dasbor Grafana.

---

## 3. Spesifikasi Machine Learning & Cara Kerja Algoritma

Mesin prediktif dalam engine AIOps V11 dirancang khusus untuk menangani karakteristik fasilitas data center (UPS dan PAC) tanpa memerlukan pelatihan ulang (*retraining*) yang berat secara online. Berikut adalah rincian cara kerja per tahapannya:

### Tahap A: Normalisasi & Ekstraksi Fitur (*Feature Extraction & Preprocessing*)
- **Input:** Deret waktu (*time-series*) dari sensor fisik (misalnya: *battery voltage*, *return temperature*, *fan speed*).
- **Penanganan Sensor Sparse:** Sensor yang melaporkan data secara jarang (*sparse*, misal `battery.capacity`) diberi bobot toleransi jeda waktu (*tolerance window*) agar tidak memicu error data hilang.
- **Pemisahan Fitur Diskrit & Kontinu:** 
  - Fitur diskrit (seperti status biner kompresor `0` atau `1`) dipisahkan secara ketat dari perhitungan regresi kontinu untuk mencegah distorsi tren linier.

### Tahap B: Gerbang Kualitas Data (*Data Quality Gating*)
Sebelum model melakukan regresi, data dievaluasi ke dalam 3 status:
1. **`NORMAL`**: Jumlah data historis mencukupi ($\ge N_{\min}$) dan bebas dari anomali `NaN`/`Inf`.
2. **`DEGRADED_DATA`**: Sebagian data hilang namun dapat diinterpolasi secara aman menggunakan nilai observasi terakhir (*forward/backward fill* yang dikendalikan).
3. **`INSUFFICIENT_DATA`**: Data kurang dari ambang batas minimum. Model otomatis melakukan **Abstain** (mengirim status abstain, tidak memproduksi angka RUL halusinasi).

### Tahap C: Perhitungan Tren & Regresi Linier (*Slope Regression for TTF*)
Untuk mendeteksi degradasi komponen sebelum terjadi kegagalan (*Predictive Maintenance*), model menggunakan pendekatan regresi linier berbasis waktu (*least squares slope estimation*):
- Misalkan $X = [t_1, t_2, \dots, t_n]$ adalah waktu observasi dan $Y = [y_1, y_2, \dots, y_n]$ adalah nilai pembacaan sensor.
- Model menghitung gradien tren (*slope*, $m$):
  $$m = \frac{n \sum (t_i y_i) - \sum t_i \sum y_i}{n \sum (t_i^2) - (\sum t_i)^2}$$
- **Time to Failure (TTF):** Jika gradien $m$ mengarah ke ambang batas kritis (*critical threshold* $Y_{\text{crit}}$), sisa waktu menuju kegagalan diestimasi secara proporsional:
  $$\text{TTF} = \frac{Y_{\text{crit}} - y_{\text{current}}}{m}$$
- **Remaining Useful Life (RUL):** Dihitung berdasarkan sisa durasi operasional aman sebelum komponen melewati batas toleransi pabrikan.

### Tahap D: Output & Pushback
- Model menghasilkan metrik keluaran:
  - `aiops.compressor.status` (Status operasional)
  - `aiops.predicted.ttf` (Estimasi waktu menuju kegagalan)
  - `aiops.predicted.rul` (Sisa umur manfaat komponen)
- Metrik ini dikirimkan ke Zabbix menggunakan utilitas `zabbix_sender`.

---

## 4. Quality Gating & Pencegahan Halusinasi Prediksi

- **Pencegahan Data Leakage:** Mencegah penggunaan interpolasi masa depan (`bfill`) dalam pelatihan atau evaluasi offline.
- **Logika Abstain Ketat:** Apabila tren linier mendatar ($m \approx 0$) pada sensor non-kritis atau data tidak stabil, engine tidak memaksakan estimasi RUL fiktif.

---

## 5. Status Implementasi & Runtime Aktif

- **Host Produksi:** `prox-prod` (`10.28.1.110`)
- **Docker Compose Service:** `aiops_engine`
- **Docker Container Name:** `aiops_predictor_hpc`
- **Active Runtime Script:** `/app/script_aiops.py` (Identik dengan `script_aiops_v11_repaired.py`)
- **SHA-256 Checksum:** `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`
- **Status Container:** `running` (`RestartCount: 0`, stabil tanpa *restart loop*).

---

## 6. Struktur Direktori & Inventaris Script Utama

```text
/root/grafan_aiops/
├── README.md                          # Dokumentasi utama proyek
├── docker-compose.yml                 # Konfigurasi stack Docker
├── Dockerfile                         # Definisi image kontainer AIOps
├── script_aiops_v11_repaired.py       # Kandidat runtime utama V11 (Repaired)
├── script_aiops_v10_backup.py         # Backup baseline stabil V10 (Phase 60)
├── aiops_facility_dashboard.json      # Konfigurasi dasbor Grafana fasilitas
├── aiops_dashboards.yaml              # Provisioning config Grafana
├── docs/                              # Dokumentasi pendukung audit
│   ├── SCRIPT_INVENTORY.md            # Inventaris lengkap 62 script & artefak
│   ├── TEST_EVIDENCE_REGISTER.md      # Register pengujian (29 unique test cases)
│   ├── PHASE_HISTORY.md               # Kronologi lengkap fase pengembangan
│   └── VALIDATION_LIMITATIONS.md      # Catatan batasan RUL & kualitas data
└── PHASE_81_DOCUMENTATION_AND_TEST_EVIDENCE_AUDIT_REPORT.md # Laporan audit final
```

---

## 7. Panduan Pengujian Offline yang Aman

Seluruh pengujian unit dan robustness dapat dijalankan secara lokal di lingkungan staging/offline tanpa memengaruhi backend Zabbix produksi:

```bash
# 1. Masuk ke direktori proyek
cd /root/grafan_aiops

# 2. Jalankan unit test V11 Repaired (memverifikasi entrypoint main loop)
python3 test_v11_repaired.py

# 3. Jalankan test robustness & extended V5
python3 test_aiops_v5_robustness.py
python3 test_aiops_v5_extended.py
```

---

## 8. Riwayat Insiden & Penanganan Rollback (Phase 63)

- **Insiden Phase 63:** Pada uji coba deployment V11 pertama, kontainer mengalami *restart loop* karena script kandidat tidak menyertakan pemanggilan daemon `main()` (`if __name__ == "__main__": main()`). Python mengeksekusi definisi fungsi lalu langsung exit dengan kode 0.
- **Tindakan Koreksi (Phase 64–65):** 
  1. Dilakukan *rollback* darurat ke baseline stabil V10 (`script_aiops_v10_backup.py`) sesuai runbook.
  2. Kandidat V11 diperbaiki dengan menambahkan daemon loop (`script_aiops_v11_repaired.py`).
  3. Dilakukan validasi shadow offline (`PASS`) dan aktivasi ulang terkendali pada Phase 73.

---

## 9. Batasan Validasi & Risiko

- **Akurasi RUL:** Status `NOT_MEASURABLE` secara statistik mutlak karena belum terkumpul catatan insiden kerusakan/kegagalan perangkat keras jangka panjang (*ground truth failure data*).
- **Portainer Stack Definition:** Status sinkronisasi stack di manajemen Portainer tercatat `NOT_VERIFIED` (memerlukan akses UI eksternal).

---
*Pembaruan Terakhir: Fase 81 (Oktober 2026).*
