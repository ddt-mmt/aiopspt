# BATASAN VALIDASI DAN KETERBATASAN — AIOPS ZABBIX/GRAFANA

Dokumen ini mendokumentasikan keterbatasan teknis, asumsi ground truth, kualitas data, serta komponen yang belum sepenuhnya terverifikasi dalam sistem AIOps.

## 1. Akurasi RUL (Remaining Useful Life)
- **Status Validasi:** `NOT_MEASURABLE` / `PENDING_LONG_TERM_GROUND_TRUTH`.
- **Penjelasan:** Meskipun perhitungan regresi slope TTF dan *data quality gating* (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`) berfungsi dengan benar pada level analitik, akurasi prediksi RUL aktual terhadap kegagalan perangkat keras (UPS/PAC) secara mutlak belum dapat diukur secara statistik tanpa catatan insiden kegagalan historis jangka panjang yang memadai.

## 2. Kualitas Data dan Sensor Stale
- Sejumlah sensor (seperti `battery.capacity` pada UPS atau fan speed pada PAC) bersifat *sparse* atau mengalami pembaruan interval yang tidak tetap.
- Algoritma V11 menerapkan penanganan nilai hilang (*missing values*) dan *abstain* untuk mencegah prediksi palsu (*hallucination*) ketika data telemetri tidak mencukupi atau *stale*.

## 3. Definisi Stack Portainer
- **Status:** `NOT_VERIFIED`.
- **Penjelasan:** Sinkronisasi konfigurasi stack di dalam manajemen kontainer Portainer belum diaudit langsung melalui API Portainer eksternal (bersifat read-only dari sisi host Docker CLI).

## 4. Lingkungan Pengujian dan Produksi
- Pengujian simulasi dan offline dilakukan di lingkungan staging (`prox-dev`).
- Operasional aktif V11 berjalan di kontainer `aiops_predictor_hpc` pada host `prox-prod` (`10.28.1.110`) dengan protokol komunikasi read-only dan Zabbix Sender lokal.
