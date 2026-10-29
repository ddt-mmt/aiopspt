# Rencana Uji Rendam 24 Jam Staging AIOps v5 (`SOAK_TEST_PLAN.md`)

- **Tanggal Penyusunan:** 2026-10-14
- **Direktori Staging:** `/root/grafan_aiops/shadow_v5/`
- **Direktori Output Run Mendatang:** `/root/grafan_aiops/shadow_v5/outputs_soak_test_<timestamp>/`
- **Baseline Script Produksi:** `/root/grafan_aiops/script_aiops.py` (SHA-256: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`)
- **Status Rencana:** **MENUNGGU PERSETUJUAN OPERATOR**

---

## 1. Tujuan & Ruang Lingkup
Melaksanakan uji rendam (*Soak Test*) staging selama 24 jam penuh untuk menguji ketahanan, stabilitas memori, penanganan timeout, dan kualitas data berkelanjutan dari *Staging Continuous Collector* (`continuous_collector.py`) tanpa melakukan mutasi pada sistem produksi.

---

## 2. Target Pemantauan (Host & Item)
- **UPS Hosts (3 Unit):** `ME_UPS1`, `ME_UPS2`, `ME_UPS3`
- **PAC Hosts (4 Unit):** `ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`
- **Metode Pengambilan Data:** Murni *read-only* melalui Zabbix API (`host.get`, `item.get`, `history.get`). Tidak ada operasi `item.create`, `host.update`, atau `Sender` (*Trapper writes*).

---

## 3. Parameter Operasional & Interval
- **Interval Polling:** 60 detik per siklus (mencocokkan interval sampling standar fasilitas).
- **Durasi Target:** 24 Jam (1,440 siklus).
- **Timeout & Retry:** Timeout API 10 detik, maksimal 3 retry dengan *exponential backoff*.
- **Graceful Shutdown:** Mendukung penanganan sinyal interupsi (Ctrl+C / SIGINT) untuk menutup file CSV/JSON dengan aman tanpa korupsi state.

---

## 4. Resource Budget & Estimasi Kapasitas Disk
- **Kapasitas Disk Tersedia:** 869 GB (/dev/mapper/almalinux-root).
- **Estimasi Volume Data per Siklus:** ~2 KB per host (~14 KB per siklus).
- **Estimasi Volume 24 Jam:** 1,440 siklus × 14 KB ≈ 20 MB (sangat aman jauh di bawah batas disk).
- **Konsumsi Memory/CPU:** Menggunakan subprocess/script Python terisolasi di staging, estimasi RAM < 150 MB, CPU < 2%.

---

## 5. Kondisi Penghentian Darurat (Kill-Switch)
Uji rendam akan dihentikan seketika jika:
1. Terdeteksi adanya percobaan penulisan (*write*) atau mutasi ke Zabbix.
2. Terjadi lonjakan anomali memori (*memory leak*) atau penggunaan CPU di atas 80% pada kontainer/host staging.
3. Disk usage staging melebihi batas aman yang ditentukan (misal > 5 GB).
4. Terjadi putus koneksi total ke Zabbix API yang tidak pulih setelah retry berkali-kali.

---

## 6. Prosedur Recovery & Checkpoint
- Setiap siklus menulis log ringkasan (`collector_run_<epoch>.json`) dan menambahkan baris ke file CSV terisolasi per host di `/root/grafan_aiops/shadow_v5/telemetry_store/`.
- Jika terjadi restart pada proses collector, data sebelumnya tetap utuh dan append-only (*immutable history*).

---

## 7. Persyaratan Persetujuan Operator
Pengujian 24 jam penuh **TIDAK AKAN DIMULAI** sebelum operator memberikan persetujuan eksplisit berdasarkan rencana ini.
