# AIOps Dataset Storage Locations & GitHub Policy

Dokumen ini menjelaskan di mana sumber dataset (baik data real Zabbix maupun dataset publik) disimpan secara lokal di dalam server, serta kebijakan (*policy*) pengunggahan data tersebut ke GitHub.

---

## 1. Lokasi Penyimpanan Dataset Secara Lokal (*Local Storage Paths*)

Seluruh data historis, eksekusi shadow, dan log validasi tersimpan di dalam direktori proyek `/root/grafan_aiops/`:

1. **Zabbix 365-Day Historical Data (`real_data_validation_365d/`):**
   - **Path:** `/root/grafan_aiops/real_data_validation_365d/`
   - **Ukuran Total:** ~95 MB
   - **Isi Utama:** Kumpulan file CSV hasil ekstraksi telemetri 365 hari (`zabbix_events_365d.csv`), manifes ekspor, laporan kualitas data (`DATA_QUALITY_REPORT.md`), serta checksum sha256.
   
2. **Real Data Validation & Output Sederhana (`real_data_validation/`):**
   - **Path:** `/root/grafan_aiops/real_data_validation/`
   - **Isi Utama:** File CSV per-host dan per-sensor untuk UPS dan PAC (`ME_PAC1_return.temp.c.csv`, `ME_UPS1_battery.voltage.csv`, dll.), serta laporan akurasi pengujian offline.

3. **Shadow Test & Benchmark Publik (`shadow_v5/`):**
   - **Path:** `/root/grafan_aiops/shadow_v5/`
   - **Ukuran Total:** ~1.7 MB
   - **Isi Utama:** Manifes akuisisi dataset publik (seperti LBNL FDD dan NASA PCoE battery), laporan validasi, dan skrip shadow runner.

---

## 2. Kebijakan Pengunggahan ke GitHub (*GitHub Storage & Push Policy*)

### Apakah boleh di-upload ke GitHub?
- **Untuk Skrip, Dokumentasi, Manifes JSON, dan Laporan Markdown:** **SANGAT BOLEH DAN DIANJURKAN.** Seluruh kode sumber, runbook, file konfigurasi dasbor Grafana, Dockerfile, dan laporan fase sudah di-push ke `https://github.com/ddt-mmt/aiopspt`.
- **Untuk Raw Telemetry CSV (File Data Mentah Berukuran Besar seperti `zabbix_events_365d.csv` atau folder `real_data_validation_365d/`):** **TIDAK DISARANKAN / DIBATASI** dengan alasan berikut:
  1. **Batasan Ukuran File GitHub:** GitHub memiliki batas ketat **100 MB per file**. Beberapa file ekspor mentah berukuran besar rentan melewati batas ini atau mendekati batas maksimal, yang memerlukan Git LFS (*Large File Storage*).
  2. **Sensitivitas Infrastruktur:** Data CSV mentah mencakup parameter operasional fasilitas data center spesifik (`prox-prod`, IP internal, struktur ID item Zabbix). Meskipun bukan kredensial rahasia, praktik terbaik rekayasa mengarahkan agar data mentah produksi lokal dikecualikan dari repository publik.
  3. **Rekomendasi:** Repository GitHub difokuskan pada **reproducibility code, test suite, dan dokumentasi lengkap**. Pengguna yang ingin menjalankan ulang (*reproduce*) analisis dapat mengekstrak data dari server Zabbix mereka sendiri menggunakan skrip ekstraksi yang telah disediakan dalam repository (misalnya `run_phase_g28_corrected_extraction.py` atau `zabbix_365d_audit.py`).

---
*Dokumen ini merupakan panduan penyimpanan artefak proyek AIOps V11.*
