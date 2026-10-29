# AIOps Multi-Device Predictive Engine for HPC Data Center (Power & Thermal Facility)

Sistem AIOps ini dirancang untuk pemantauan prediktif (*Predictive Maintenance*) dan estimasi kondisi operasional infrastruktur daya (*UPS*) dan pendingin (*PAC*) pada data center High-Performance Computing (HPC).

---

## 1. Status Implementasi Saat Ini
- **Runtime Produksi Aktif:** Kontainer `aiops_predictor_hpc` (`grafan_aiops-aiops_engine`).
- **Versi Engine Berjalan:** V11 Repaired Candidate (`script_aiops_v11_repaired.py`), SHA-256: `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`.
- **Status Operasional:** Aktif beroperasi dan dalam tahap observasi berkelanjutan (*Observation Continues* / Phase 74–80).

---

## 2. Arsitektur dan Aliran Data Aktual
1. **Pengumpulan Telemetri:** Engine menarik data sensor secara periodik dari server Zabbix (mendukung perangkat UPS APC/Schneider dan PAC Mitsubishi/Schneider).
2. **Quality Gating & Analisis:** Data divalidasi melalui gerbang kualitas (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`), menangani sensor *sparse* dan mencegah regresi slope TTF (*Time to Failure*).
3. **Pengiriman Hasil (Zabbix Sender):** Hasil prediksi status operasional dan estimasi RUL dikirimkan kembali ke Zabbix item terkait.
4. **Visualisasi (Grafana):** Dasbor Grafana (`aiops_facility_dashboard.json`) menampilkan metrik prediktif secara real-time.

---

## 3. Komponen Produksi, Staging, Zabbix, dan Grafana
- **Produksi (`prox-prod`, `10.28.1.110`):** Menjalankan kontainer `aiops_predictor_hpc` dengan runtime V11.
- **Zabbix Server:** Backend penyimpanan metrik dan manajemen alert.
- **Grafana:** Antarmuka visualisasi dasbor fasilitas data center.
- **Portainer Stack Definition:** Status sinkronisasi stack (*NOT_VERIFIED*).

---

## 4. Versi Script dan Status Penggunaan
- **`script_aiops.py` (Runtime):** `009090d5f7cc6a2f` (V11 Repaired) — **AKTIF**.
- **`script_aiops_v11_repaired.py`:** `009090d5f7cc6a2f` — Kandidat V11 utama.
- **`script_aiops_v10_backup.py`:** `58f8065f171a34c6` — Backup stabil V10 (Phase 60).
- **Kandidat Lama (V3–V10):** Diarsipkan untuk referensi historis (*deprecated*).

---

## 5. Cara Menjalankan Test Offline yang Aman
Seluruh pengujian dijalankan secara lokal tanpa mutasi ke backend produksi:
```bash
# Menjalankan unit test V11 Repaired & Robustness V5
python3 /root/grafan_aiops/test_v11_repaired.py
python3 /root/grafan_aiops/test_aiops_v5_robustness.py
python3 /root/grafan_aiops/test_aiops_v5_extended.py
```

---

## 6. Daftar Pengujian dan Ringkasan Hasil
- **Total Unique Test Cases:** 29 test case.
- **Hasil:** 29 PASS, 0 FAIL, 0 BLOCKED.
- Rincian lengkap tersedia di [Test Evidence Register](docs/TEST_EVIDENCE_REGISTER.md).

---

## 7. Riwayat Kegagalan, Blocker, dan Perbaikannya
- **Insiden Phase 63:** Deployment awal V11 gagal karena kandidat script tidak memiliki daemon `main()` loop (`if __name__ == "__main__": main()`), menyebabkan kontainer exit langsung.
- **Tindakan Koreksi (Phase 64–65):** Dilakukan *rollback* aman ke baseline V10, penambahan entrypoint `main()` pada V11 repaired candidate, validasi shadow offline (`PASS`), dan aktivasi ulang terkendali pada Phase 73.

---

## 8. Status Aktivasi V11 dan Observasi Produksi
- **Waktu Aktivasi:** 29 Oktober 2026, 03:39 UTC.
- **Status Container:** `running` dengan `RestartCount: 0` (stabil sepenuhnya).
- **Status Observasi:** *Observation Continues* (Phase 74–80) untuk memastikan kestabilan jangka panjang.

---

## 9. Batasan Kualitas Data dan Validasi RUL
- Akurasi RUL aktual belum dapat diukur secara mutlak (*NOT_MEASURABLE*) tanpa catatan historis kegagalan jangka panjang.
- Sistem menggunakan mekanisme *abstain* untuk menangani sensor *stale* atau data tidak mencukupi.

---

## 10. Prosedur Validasi Checksum dan Rollback
- Checksum runtime dapat diverifikasi dengan:
  ```bash
  docker exec aiops_predictor_hpc sha256sum /app/script_aiops.py
  ```
- Prosedur rollback terdokumentasi menggunakan backup V10 (`script_aiops_v10_backup.py`).

---

## 11. Dokumen Pendukung Terkait
- [Script Inventory](docs/SCRIPT_INVENTORY.md)
- [Test Evidence Register](docs/TEST_EVIDENCE_REGISTER.md)
- [Phase History](docs/PHASE_HISTORY.md)
- [Validation & Limitations](docs/VALIDATION_LIMITATIONS.md)

---
*Pembaruan Terakhir: Fase 81 (Oktober 2026).*
