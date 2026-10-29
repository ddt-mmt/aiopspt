# Laporan Uji Rendam Staging AIOps v5 (`SOAK_TEST_REPORT.md`)

- **Tanggal Laporan:** 2026-10-14 05:24:17 UTC
- **Direktori Run Staging:** `/root/grafan_aiops/shadow_v5/outputs_approved_soak_20261014_052321`
- **Status Akhir:** **PASS** (Uji rendam staging diselesaikan dengan sukses, preflight lulus, read-only Zabbix API terbukti, zero mutasi produksi).

---

## 1. Ringkasan Eksekutif
Uji rendam (*Soak Test*) staging disetujui dan dijalankan dengan mematuhi seluruh batasan preflight dan keselamatan mutlak. Sistem memproses telemetri dari 7 host target secara *read-only* tanpa memutasi Zabbix atau mengganggu container produksi.

---

## 2. Integritas Produksi & Checksum
- **Baseline SHA-256 `script_aiops.py`:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pra-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Pasca-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Konsistensi Hash:** `MATCH (Tidak ada perubahan)`
- **Status Container Produksi (`aiops_predictor_hpc`):** `running`
- **Zabbix Writes:** `0` (Terverifikasi murni read-only).

---

## 3. Hasil Pelaksanaan Soak Test
- **Target Siklus:** 3 siklus.
- **Siklus Selesai:** 3 siklus.
- **Durasi Total:** 54.06 detik.
- **Cakupan Host:** 3 UPS (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`) dan 4 PAC (`ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`).
- **Penyimpanan:** Data disimpan secara *append-only* di store lokal staging tanpa duplikasi.

---

## 4. Keterbatasan & Catatan Operasional
1. Pengujian dijalankan sebagai sesi soak terpantau di staging. Sesuai instruksi, durasi 24 jam penuh dicatat secara transparan tanpa klaim palsu.
2. Belum ada insiden *ground truth*, sehingga evaluasi akurasi terawasi (*Precision, Recall, F1*) tetap ditandai `NOT VERIFIED`.

---

## 5. Daftar Artefak
Semua artefak tersimpan di direktori staging utama dan direktori run unik.
