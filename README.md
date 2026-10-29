# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang untuk pemantauan prediktif (*Predictive Maintenance*), estimasi kondisi operasional, dan perhitungan *Time to Failure* (TTF) serta *Remaining Useful Life* (RUL) pada infrastruktur daya kritis (**UPS**) dan pendingin ruangan data center (**PAC**).

---

## 📋 Daftar Isi
1. [Arsitektur Sistem & Diagram Alur (Flowchart)](#1-arsitektur-sistem--diagram-alur-flowchart)
2. [Aliran Data & Integrasi Zabbix API](#2-aliran-data--integrasi-zabbix-api)
3. [Spesifikasi Machine Learning & Toleransi Akurasi](#3-spesifikasi-machine-learning--toleransi-akurasi)
4. [Struktur Direktori Repositori (Penjelasan Lengkap)](#4-struktur-direktori-repositori-penjelasan-lengkap)
5. [Panduan Pengujian Offline yang Aman](#5-panduan-pengujian-offline-yang-aman)
6. [Riwayat Insiden & Penanganan Rollback (Phase 63)](#6-riwayat-insiden--penanganan-rollback-phase-63)
7. [Batasan Validasi & Risiko](#7-batasan-validasi--risiko)

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

## 3. Spesifikasi Machine Learning & Toleransi Akurasi

- **Metode Regresi:** *Least squares linear regression slope estimation* untuk mendeteksi degradasi tren sebelum kegagalan.
- **Toleransi Margin Kesalahan:**
  - Estimasi TTF: **$\pm 15\%$** dari rentang observasi aktif.
  - Estimasi RUL: **$\pm 20\%$** untuk mengakomodasi sensor *sparse* (kapasitas baterai).
- **Ambang Batas Sampel Minimum ($N_{\min}$):** $\ge 12$ titik data valid dalam jendela waktu berjalan.

---

## 4. Struktur Direktori Repositori (Penjelasan Lengkap)

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

## 5. Panduan Pengujian Offline yang Aman

```bash
# Menjalankan unit test V11 Repaired dan Robustness V5
python3 tests/test_v11_repaired.py
python3 tests/test_aiops_v5_robustness.py
python3 tests/test_aiops_v5_extended.py
```

---

## 6. Riwayat Insiden & Penanganan Rollback (Phase 63)
- **Insiden Phase 63:** Deployment V11 awal gagal karena kurangnya entrypoint daemon `main()` loop.
- **Tindakan Koreksi (Phase 64–65):** Rollback aman ke baseline V10, perbaikan script V11 repaired, validasi shadow offline (`PASS`), dan aktivasi terkendali pada Phase 73.

---

## 7. Batasan Validasi & Risiko
- Akurasi RUL dinilai `NOT_MEASURABLE` secara mutlak tanpa catatan insiden kerusakan perangkat keras jangka panjang.
- Status definisi Stack Portainer tercatat `NOT_VERIFIED`.

---
*Pembaruan Terakhir: Fase 82 (Oktober 2026).*
