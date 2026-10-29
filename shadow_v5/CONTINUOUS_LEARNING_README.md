# AIOps Shadow v5 — Continuous Learning & Staging Collector (`CONTINUOUS_LEARNING_README.md`)

Direktori: `/root/grafan_aiops/shadow_v5/`

## 1. Ikhtisar Arsitektur
Modul ini menyediakan infrastruktur *Continuous Learning* dan *Always-On Shadow Monitoring* staging untuk engine AIOps v5. Seluruh komponen dirancang agar beroperasi secara independen, aman, dan terisolasi tanpa memutasi sistem produksi atau Zabbix.

## 2. Komponen Utama
- **`continuous_collector.py`:** Collector berkala yang mengambil data telemetri aktual dari Zabbix API melalui metode *read-only* murni, melakukan validasi kualitas data (stale & sparsity check), serta menyimpan data ke store lokal staging (`/telemetry_store/`).
- **`continuous_eval_pipeline.py`:** Pipeline evaluasi offline untuk memproses dataset historis staging, memeriksa nilai hilang (*missing values*), dan menghasilkan laporan kualitas fitur.
- **`shadow_v5_continuous_dashboard.json`:** Konfigurasi dashboard Grafana staging untuk memantau status collector, kualitas data, dan health score.

## 3. Aturan Keselamatan Mutlak
- Tanpa mutasi Zabbix (0 write operations).
- Tanpa restart container produksi (`aiops_predictor_hpc`).
- Tanpa notifikasi eksternal atau auto-remediation.
