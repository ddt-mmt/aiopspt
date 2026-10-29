# Laporan Controlled Live-Read-Only Shadow Monitoring AIOps v5 (`SHADOW_V5_CONTROLLED_LIVE_REPORT.md`)

- **Tanggal Laporan:** 2026-10-14 04:14:28 UTC
- **Target Direktori Staging:** `/root/grafan_aiops/shadow_v5`
- **Status Akhir:** **PASS WITH WARNINGS** (Telemetri aktual terbaca read-only, namun ground truth insiden masih 0 sehingga akurasi terawasi belum diverifikasi).

---

## 1. Ringkasan Eksekutif
Pengujian *Controlled Live-Read-Only Shadow Monitoring* AIOps v5 telah dijalankan sebanyak 3 siklus terkontrol menggunakan data telemetri aktual dari Zabbix API secara ketat *read-only*. Seluruh aturan keselamatan (tanpa mutasi Zabbix, tanpa restart container, tanpa notifikasi eksternal) dipatuhi secara mutlak.

---

## 2. Hasil Pra-Shadow (Preflight)
- **Active Script (`script_aiops.py`):** `/root/grafan_aiops/script_aiops.py`
- **Baseline SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Aktual Pra-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Aktual Pasca-Run SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Konsistensi Hash:** `MATCH (Tidak ada perubahan)`
- **Status Container Produksi (`aiops_predictor_hpc`):** `running`
- **Koneksi Zabbix API:** Berhasil (`7.0.23`)

---

## 3. Metode Pengambilan Data & Bukti Read-Only
- **Metode:** Skrip menggunakan `zapi.host.get`, `zapi.item.get`, dan `zapi.history.get` tanpa memanggil metode mutasi (`item.create`, `host.update`, `event.*`, atau `Sender`).
- **Zabbix Writes:** `0` (Nol mutasi jaringan).

---

## 4. Hasil Per Siklus & Host Terproses
- **Total Siklus Pengamatan:** 3 siklus.
- **Host Terproses:** 3 UPS (`ME_UPS1, ME_UPS2, ME_UPS3`) dan 4 PAC (`ME_PAC1, ME_PAC2, ME_PAC3, ME_PAC4`).

---

## 5. Evaluasi Alert Lokal & Kualitas Data
- **Ambang Persistensi:** 3 siklus berturut-turut untuk kandidat alert.
- **Kandidat Alert Ditemukan:** 0 kandidat.
- **Notifikasi Eksternal / Auto-Remediation:** Dinonaktifkan sepenuhnya (`False`).

---

## 6. Batasan dan Keterbatasan
1. Belum ada insiden *ground truth* tercatat di Zabbix dalam 30 hari terakhir, sehingga metrik akurasi (*Precision, Recall, F1*) belum dapat dihitung.
2. Sensor `battery.capacity` pada UPS bersifat *sparse* dan ditangani secara aman dengan pengecualian/abstain sesuai arsitektur v5.

---

## 7. Manifest SHA-256 File Staging
Semua artefak tersimpan di `/root/grafan_aiops/shadow_v5`.
