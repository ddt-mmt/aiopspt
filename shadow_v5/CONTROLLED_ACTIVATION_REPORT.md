# Laporan Controlled Activation Continuous Learning AIOps v5 (`CONTROLLED_ACTIVATION_REPORT.md`)

- **Tanggal Laporan:** 2026-10-14 04:32:05 UTC
- **Direktori Run Staging:** `/root/grafan_aiops/shadow_v5/outputs_controlled_activation_20261014_043125`
- **Status Akhir:** **PASS** (Pengujian preflight, fixture, dan live read-only berhasil dijalankan tanpa mutasi produksi).

---

## 1. Ringkasan Eksekutif
Pengaktifan terkontrol Continuous Learning Staging AIOps v5 telah diselesaikan melalui eksekusi foreground manual. Seluruh aturan keselamatan (tanpa mutasi Zabbix, tanpa restart container produksi, tanpa daemon permanen) dipatuhi secara mutlak.

---

## 2. Integritas Produksi & Checksum
- **Baseline SHA-256 `script_aiops.py`:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pra-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pasca-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Konsistensi Hash:** `MATCH (Tidak ada perubahan)`
- **Status Container Produksi (`aiops_predictor_hpc`):** `running`
- **Zabbix Writes:** `0` (Terverifikasi murni read-only).

---

## 3. Hasil Uji Fixture Data Quality
- **Normal Data Fixture:** `PASS`
- **NaN / Inf Handling:** `PASS`

---

## 4. Hasil Controlled Live Read-Only Collection
- **Status Live Run:** `SUCCESS` (2 siklus live PAC telemetry tervalidasi dengan sehat dan stabil).

---

## 5. Batasan dan Keterbatasan
1. Pengumpulan dijalankan secara interaktif/foreground dalam durasi singkat untuk memastikan kontrol penuh.
2. Belum ada ground truth insiden, sehingga evaluasi akurasi terawasi (*Precision, Recall, F1*) tetap ditandai `NOT VERIFIED`.

---

## 6. Daftar Artefak Run & Manifest
Semua artefak baru tersimpan di direktori run staging terisolasi.
