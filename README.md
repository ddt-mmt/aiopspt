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
9. [Status Proyek Terkini — Phase 87.20](#status-proyek-terkini--5-november-2026-phase-8720)

---

## Status Proyek Terkini — 5 November 2026 (Phase 87.20)

- **V11 produksi:** dilaporkan tetap menjadi runtime aktif; baseline historis SHA-256 `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`.
- **V12:** kandidat staging dengan SHA-256 `17f01ec80e4af39509f36b976e1e580f455e6c497098308c9dbcc5f9e9673bce`; belum dideploy ke produksi.
- **Change Owner:** Didit — APPROVED berdasarkan deklarasi yang diberikan; identitas dan kewenangan belum diverifikasi independen.
- **Lima persetujuan stakeholder lainnya:** PENDING.
- **Pengecualian keamanan HTTP Zabbix:** PENDING; alternatif HTTPS belum diverifikasi.
- **Otorisasi perubahan produksi:** `NOT_GRANTED`.
- **Deployment V12 ke produksi:** `NO`.
- **Grafana produksi:** integrasi Option D belum diotorisasi atau dilaksanakan.

Status di atas berasal dari laporan fase yang tersedia, bukan pemeriksaan live runtime dalam Phase 87.20. Lihat [status proyek](docs/PROJECT_CURRENT_STATUS.md), [riwayat fase](docs/PHASE_HISTORY.md), dan [audit struktur repository](docs/REPOSITORY_STRUCTURE.md).

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

## 5. Struktur Direktori Repositori

Inventaris path repository yang dapat diamati langsung di GitHub tersedia pada [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md). Dokumen tersebut memisahkan path yang teramati dari layout workspace historis `/root/grafan_aiops`.

**Catatan:** inventaris tersebut belum dapat diklaim lengkap secara rekursif. Path yang hanya disebut pada dokumentasi lama tidak boleh dianggap pasti ada pada branch GitHub saat ini. Untuk inventaris final, diperlukan ekspor recursive Git tree atau `git ls-tree -r --name-only HEAD` dari clone bersih.

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
*Pembaruan dokumentasi: 5 November 2026 (Phase 87.20). Phase 87.19 mempublikasikan dokumentasi ke GitHub dengan deployment produksi tetap diblokir. Phase 87.20 memperbaiki README, kronologi fase, status proyek, dan audit struktur repository. Inventaris struktur tetap diberi batasan sampai recursive Git tree tersedia. Otorisasi produksi tetap `NOT_GRANTED`; V12 belum dideploy ke produksi.*
