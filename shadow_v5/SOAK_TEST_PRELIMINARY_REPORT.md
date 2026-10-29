# Laporan Uji Pendahuluan Staging AIOps v5 (`SOAK_TEST_PRELIMINARY_REPORT.md`)

- **Tanggal Laporan:** 2026-10-14 04:40:01 UTC
- **Direktori Run Staging:** `/root/grafan_aiops/shadow_v5/outputs_soak_preliminary_20261014_043923`
- **Status Akhir:** **PASS** (Uji pendahuluan foreground berhasil dijalankan, read-only Zabbix API terbukti, tanpa mutasi produksi).

---

## 1. Ringkasan Eksekutif
Uji pendahuluan staging (*preliminary soak test*) dijalankan secara manual/foreground sebanyak 2 siklus dengan interval terkontrol. Seluruh pembatasan keselamatan dipatuhi secara mutlak.

---

## 2. Integritas Produksi & Checksum
- **Baseline SHA-256 `script_aiops.py`:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pra-Uji SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pasca-Uji SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Konsistensi Hash:** `MATCH (Tidak ada perubahan)`
- **Status Container Produksi (`aiops_predictor_hpc`):** `running`
- **Zabbix Writes:** `0` (Terverifikasi murni read-only melalui metode `host.get`, `item.get`, `history.get`).

---

## 3. Metrik Kinerja Uji Pendahuluan
- **Total Siklus Dijalankan:** 2 siklus.
- **Durasi Total Wall-Clock:** 36.22 detik.
- **Rata-rata Durasi per Siklus:** 18.11 detik.
- **Konsumsi Resource Staging:** Memori stabil (< 120 MB), CPU minimal (< 2%), pertumbuhan disk minimal (< 1 MB).

---

## 4. Keterbatasan & Pengamatan
1. Pengujian dibatasi pada 2 siklus di foreground untuk memastikan stabilitas dan kemampuan penghentian aman (*graceful shutdown*).
2. Belum ada ground truth insiden, sehingga evaluasi akurasi terawasi (*Precision, Recall, F1*) tetap ditandai `NOT VERIFIED`.
3. Sesuai instruksi operator, pengujian 24 jam penuh **TIDAK DIMULAI** dan uji pendahuluan ini berhenti di sini.

---

## 5. Daftar Artefak Run & Manifest
Semua artefak baru tersimpan di direktori run staging terisolasi.
