# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang untuk pemantauan prediktif (*Predictive Maintenance*), estimasi kondisi operasional, dan perhitungan *Time to Failure* (TTF) serta *Remaining Useful Life* (RUL) pada infrastruktur daya kritis (**UPS**) dan pendingin ruangan data center (**PAC**).

---

## 📋 Daftar Isi
1. [Arsitektur Sistem & Diagram Alur (Flowchart)](#1-arsitektur-sistem--diagram-alur-flowchart)
2. [Aliran Data (Data Flow Pipeline)](#2-aliran-data-data-flow-pipeline)
3. [Status Implementasi & Runtime Aktif](#3-status-implementasi--runtime-aktif)
4. [Quality Gating & Pencegahan Halusinasi Prediksi](#4-quality-gating--pencegahan-halusinasi-prediksi)
5. [Struktur Direktori & Inventaris Script Utama](#5-struktur-direktori--inventaris-script-utama)
6. [Panduan Pengujian Offline yang Aman](#6-panduan-pengujian-offline-yang-aman)
7. [Riwayat Insiden & Penanganan Rollback (Phase 63)](#7-riwayat-insiden--penanganan-rollback-phase-63)
8. [Batasan Validasi & Risiko](#8-batasan-validasi--risiko)

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
|   │ 1. Telemetry Fetch   │────▶│ 2. Data Quality Gating │────▶│ 3. TTF & RUL  │ |
|   │    (Zabbix API)      │     │ (NORMAL / DEGRADED /   │     │    Analysis   │ |
|   └──────────────────────┘     │  INSUFFICIENT DATA)    │     └───────┬───────┘ |
|                                └────────────────────────┘             │         |
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

Sistem bekerja dalam siklus tertutup (*closed-loop polling*) setiap 60 detik:
1. **Pengambilan Data (Ingestion):** Engine `script_aiops.py` terhubung ke Zabbix API untuk mengambil riwayat metrik sensor terkini dari host UPS dan PAC.
2. **Penyaringan Kualitas (Quality Gating):** Data mentah diperiksa terhadap nilai `NaN`, `Inf`, atau sampel yang kurang dari batas minimum. Status data dikategorikan menjadi:
   - `NORMAL`: Data lengkap dan valid, analisis dilanjutkan.
   - `DEGRADED_DATA`: Sebagian sensor *sparse* atau terputus, menggunakan interpolasi aman / nilai sebelumnya.
   - `INSUFFICIENT_DATA`: Data tidak mencukupi, sistem melakukan **Abstain** (tidak mengeluarkan prediksi palsu).
3. **Analisis Prediktif (TTF & RUL):** Menghitung tren degradasi linier (*slope regression*) untuk mengestimasi sisa waktu operasional (*Time to Failure*).
4. **Pengiriman Kembali (Feedback Loop):** Hasil analisis dikirimkan ke Zabbix via `zabbix_sender`, yang kemudian divisualisasikan secara langsung melalui dasbor Grafana.

---

## 3. Status Implementasi & Runtime Aktif

- **Host Produksi:** `prox-prod` (`10.28.1.110`)
- **Docker Compose Service:** `aiops_engine`
- **Docker Container Name:** `aiops_predictor_hpc`
- **Active Runtime Script:** `/app/script_aiops.py` (Identik dengan `script_aiops_v11_repaired.py`)
- **SHA-256 Checksum:** `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`
- **Status Container:** `running` (`RestartCount: 0`, stabil tanpa *restart loop*).

---

## 4. Quality Gating & Pencegahan Halusinasi Prediksi

Untuk mencegah prediksi keliru (*hallucination*) pada fasilitas data center:
- **Pemeriksaan Sampel Minimum:** Menolak perhitungan tren jika data historis kurang dari ambang batas aman.
- **Isolasi Fitur Diskrit:** Status biner kompresor atau status UPS dipisahkan dari perhitungan regresi kontinu (*slope TTF*).
- **Logika Abstain Otomatis:** Jika sensor mengalami *stale* (tidak ada pembaruan dalam jendela waktu tertentu), engine otomatis mengirim status `ABSTAIN` daripada memaksakan angka RUL yang tidak akurat.

---

## 5. Struktur Direktori & Inventaris Script Utama

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

## 6. Panduan Pengujian Offline yang Aman

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

## 7. Riwayat Insiden & Penanganan Rollback (Phase 63)

- **Insiden Phase 63:** Pada uji coba deployment V11 pertama, kontainer mengalami *restart loop* karena script kandidat tidak menyertakan pemanggilan daemon `main()` (`if __name__ == "__main__": main()`). Python mengeksekusi definisi fungsi lalu langsung exit dengan kode 0.
- **Tindakan Koreksi (Phase 64–65):** 
  1. Dilakukan *rollback* darurat ke baseline stabil V10 (`script_aiops_v10_backup.py`) sesuai runbook.
  2. Kandidat V11 diperbaiki dengan menambahkan daemon loop (`script_aiops_v11_repaired.py`).
  3. Dilakukan validasi shadow offline (`PASS`) dan aktivasi ulang terkendali pada Phase 73.

---

## 8. Batasan Validasi & Risiko

- **Akurasi RUL:** Status `NOT_MEASURABLE` secara statistik mutlak karena belum terkumpul catatan insiden kerusakan/kegagalan perangkat keras jangka panjang (*ground truth failure data*).
- **Portainer Stack Definition:** Status sinkronisasi stack di manajemen Portainer tercatat `NOT_VERIFIED` (memerlukan akses UI eksternal).

---
*Pembaruan Terakhir: Fase 81 (Oktober 2026).*
