# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang untuk pemantauan prediktif (*Predictive Maintenance*), estimasi kondisi operasional, dan perhitungan *Time to Failure* (TTF) serta *Remaining Useful Life* (RUL) pada infrastruktur daya kritis (**UPS**) dan pendingin ruangan data center (**PAC**).

---

## 📋 Daftar Isi
1. [Arsitektur Sistem & Diagram Alur](#1-arsitektur-sistem--diagram-alur-flowchart)
2. [Aliran Data & Integrasi Zabbix API](#2-aliran-data--integrasi-zabbix-api)
3. [Spesifikasi Machine Learning & Batas Validasi](#3-spesifikasi-machine-learning--batas-validasi)
4. [Public Datasets & Benchmark Independen](#4-public-datasets--benchmark-independen)
5. [Struktur Direktori Repositori](#5-struktur-direktori-repositori-penjelasan-lengkap)
6. [Panduan Pengujian Offline](#6-panduan-pengujian-offline-yang-aman)
7. [Riwayat Insiden & Penanganan Rollback](#7-riwayat-insiden--penanganan-rollback-phase-63)
8. [Batasan Validasi & Risiko](#8-batasan-validasi--risiko)

---

## 1. Arsitektur Sistem & Diagram Alur (Flowchart)

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

## 2. Aliran Data & Integrasi Zabbix API

1. **Zabbix API Extraction (`history.get`, `host.get`, `item.get`):** Engine menarik deret waktu (*time-series*) dari sensor fisik UPS dan PAC.
2. **Quality Gating & Preprocessing:** Data diperiksa dari nilai `NaN`/`Inf`. Status dikelompokkan menjadi `NORMAL`, `DEGRADED_DATA`, atau `INSUFFICIENT_DATA` (Abstain).
3. **Feature Isolation:** Variabel diskrit (status biner kompresor) dipisahkan dari variabel kontinu.
4. **Slope Regression:** Menghitung gradien tren linier (*least squares*) untuk estimasi TTF & RUL.
5. **Zabbix Sender Pushback:** Hasil dikirimkan kembali ke Zabbix dan divisualisasikan pada Grafana.

---

## 3. Spesifikasi Machine Learning & Batas Validasi

Dokumentasi ini membedakan konfigurasi algoritma, target desain, dan akurasi yang benar-benar terukur.

- **Isolation Forest:** konfigurasi `contamination=0.05` pada implementasi V11 adalah parameter model, bukan error rate 5% dan bukan bukti akurasi 95%.
- **Health Score:** merupakan indeks analitik yang diturunkan dari output model. Nilai 80% tidak boleh ditafsirkan sebagai probabilitas 80% bahwa perangkat sehat.
- **TTF/RUL:** akurasi aktual masih `NOT_MEASURABLE` tanpa ground truth kegagalan/akhir umur yang representatif untuk perangkat produksi.
- **Target desain historis:** TTF ±15% dan RUL ±20% pernah dicantumkan pada dokumen lama. Angka tersebut belum terbukti sebagai toleransi empiris dan tidak boleh dipublikasikan sebagai akurasi teruji.
- **Kualitas data:** implementasi V11 yang diaudit menggunakan batas usia data 300 detik, forward-fill terbatas maksimal dua titik, dan pemeriksaan sampel minimum 10 titik pada quality gate terkait. Nilai konfigurasi kandidat V12 harus diverifikasi dari source dan test terbaru sebelum dinyatakan berlaku.
- **Confidence:** jumlah sampel atau label HIGH/MEDIUM saja bukan probabilitas akurasi yang terkalibrasi. Klaim confidence harus didukung kalibrasi dan evaluasi yang terukur.

Lihat [ML Workflow and Accuracy](docs/ML_WORKFLOW_AND_ACCURACY.md) untuk rincian keterbatasan dan [Public Datasets and Benchmarks](docs/PUBLIC_DATASETS_AND_BENCHMARKS.md) untuk sumber pembanding.

## 4. Public Datasets & Benchmark Independen

Dataset publik digunakan sebagai benchmark penelitian offline yang terpisah dari telemetri operasional Zabbix.

### LBNL Fault Detection and Diagnostics — RTU

- [Halaman dataset RTU resmi](https://faultdetection.lbl.gov/dataset/rtu/)
- [Unduh simulated RTU dataset ZIP](https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.zip)
- [Unduh semua tiga file dataset RTU](https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU_all_3.zip)
- [Katalog seluruh dataset LBNL FDD](https://faultdetection.lbl.gov/data/)
- DOI: [10.25984/1881324](https://doi.org/10.25984/1881324)

LBNL RTU merupakan benchmark HVAC/rooftop unit. Dataset ini dapat mendukung evaluasi konsep fault detection untuk domain pendinginan, tetapi bukan replika PAC produksi. Halaman unduhan dapat meminta informasi pengguna dan cookies. Ikuti proses resmi dan jangan membuat identitas unduhan palsu.

### NASA PCoE Battery

- [Repository resmi NASA PCoE](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)
- [Unduh NASA Battery Data Set #5](https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip)
- [Unduh NASA Randomized Battery Usage Data Set #11](https://phm-datasets.s3.amazonaws.com/NASA/11.+Randomized+Battery+Usage+Data+Set.zip)

NASA Battery #5 berisi eksperimen baterai lithium-ion dengan charging/discharging pada temperatur berbeda serta pengukuran impedance. Dataset ini adalah benchmark metodologi baterai, bukan representasi otomatis dari chemistry dan karakteristik baterai UPS produksi.

### Status akuisisi dan benchmark

Berdasarkan ringkasan Phase 87.3, framework dan simulasi benchmark dilaporkan telah dijalankan. Bukti yang tersedia belum menunjukkan arsip publik asli dengan ukuran file non-zero, checksum, dan input manifest yang mengikat hasil ke dataset tersebut.

Karena itu:
- Native LBNL acquisition: `NOT_VERIFIED`.
- Native NASA acquisition: `NOT_VERIFIED`.
- Simulation benchmark: `EXECUTED_SIMULATION`, sebagaimana dilaporkan.
- Real-file public benchmark: `NOT_EXECUTED` sampai bukti arsip dan hasil evaluasi tersedia.
- Dataset publik tidak dicampurkan ke production Zabbix pipeline.

Status rinci dan tautan unduhan ada di [docs/PUBLIC_DATASETS_AND_BENCHMARKS.md](docs/PUBLIC_DATASETS_AND_BENCHMARKS.md) dan [dataset status manifest](docs/PUBLIC_DATASET_STATUS_MANIFEST.json).

## 5. Struktur Direktori Repositori (Penjelasan Lengkap)

Repositori ini disusun secara modular agar bersih dan mudah dipahami:

```text
/root/grafan_aiops/
├── README.md                          # Dokumentasi utama proyek
├── src/                               # 📂 Core Source Engine (script utama, kandidat V11, backup V10)
├── config/                            # 📂 Konfigurasi Stack (docker-compose.yml, Dockerfile, Grafana dashboard)
├── docs/                              # 📂 Dokumentasi Teknis (Inventaris Script, Test Register, ML Workflow, Kebijakan Data)
├── reports/                           # 📂 Laporan Resmi (Phase 62 s.d. 81, Rekonsiliasi, Pre-activation)
│   └── audit_archives/                # Arsip laporan historis (AIOps, Audit V3/V5, Robustness, Shadow V5)
├── phases/                            # 📂 Script Eksekusi Tahapan Pengembangan & Utilitas Pendukung
│   ├── scripts/                       # Skrip eksekusi fase (Phase 45-46 preflight, run_*.py)
│   ├── utils/                         # Utilitas audit, ekstraksi, dan perbaikan OID Zabbix
│   └── legacy/                        # Arsip backup awal
├── tests/                             # 📂 Test Suite (Unit test V11, Robustness v5, Hardening v10/v9)
├── real_data_validation/              # Data hasil ekspor validasi riwayat nyata per-host/sensor
└── real_data_validation_365d/         # Arsip ekspor data historis 365 hari Zabbix beserta run logs
```

### Keterangan Fungsi Setiap Direktori & File Kategori:
- **`src/`**: Berisi script engine utama (`script_aiops.py`), V11 Repaired (`script_aiops_v11_repaired.py`), serta kandidat versi historis (`script_aiops.py.candidate.v2` s.d. `v10`).
- **`config/`**: Berisi konfigurasi deployment Docker Compose (`docker-compose.yml`, `Dockerfile`) dan skema dasbor Grafana (`aiops_facility_dashboard.json`).
- **`docs/`**: Berisi panduan arsitektur, daftar inventaris script (`SCRIPT_INVENTORY.md`), register bukti pengujian (`TEST_EVIDENCE_REGISTER.md`), riwayat fase (`PHASE_HISTORY.md`), alur ML (`ML_WORKFLOW_AND_ACCURACY.md`), dan kebijakan penyimpanan dataset (`DATA_STORAGE_AND_GITHUB_POLICY.md`).
- **`reports/`**: Berisi laporan formal setiap fase pelaksanaan deployment (Phase 62 s.d. 81).
- **`reports/audit_archives/`**: Berisi arsip laporan forensik historis, validasi robustness v5, shadow test v5, dan audit Zabbix v3.
- **`phases/`**: Berisi kumpulan script eksekusi otomatis yang digunakan selama proses pengembangan bertahap (*Phased Development*).
- **`tests/`**: Berisi seluruh file pengujian unit dan otomatisasi untuk memverifikasi fungsionalitas engine.

---

## 6. Panduan Pengujian Offline yang Aman

```bash
# Menjalankan unit test V11 Repaired dan Robustness V5
python3 tests/test_v11_repaired.py
python3 tests/test_aiops_v5_robustness.py
python3 tests/test_aiops_v5_extended.py
```

---

## 7. Riwayat Insiden & Penanganan Rollback (Phase 63)
- **Insiden Phase 63:** Deployment V11 awal gagal karena kurangnya entrypoint daemon `main()` loop.
- **Tindakan Koreksi (Phase 64–65):** Rollback aman ke baseline V10, perbaikan script V11 repaired, validasi shadow offline (`PASS`), dan aktivasi terkendali pada Phase 73.

---

## 8. Batasan Validasi & Risiko
- Akurasi RUL dinilai `NOT_MEASURABLE` secara mutlak tanpa catatan insiden kerusakan perangkat keras jangka panjang.
- Status definisi Stack Portainer tercatat `NOT_VERIFIED`.

---
*Pembaruan dokumentasi: 30 Oktober 2026. Dataset publik dicatat sebagai referensi; akuisisi arsip dan benchmark real-file belum terverifikasi.*
