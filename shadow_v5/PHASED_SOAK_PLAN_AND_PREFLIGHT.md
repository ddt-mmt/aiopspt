# Rencana Uji Rendam Bertahap & Laporan Preflight (`PHASED_SOAK_PLAN_AND_PREFLIGHT.md`)

- **Tanggal Penyusunan:** 2026-10-14 05:40:00 UTC
- **Direktori Staging:** `/root/grafan_aiops/shadow_v5/`
- **Baseline Script Produksi (`script_aiops.py`):** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Status Dokumen:** **`MENUNGGU PERSETUJUAN OPERATOR (BELUM DIJALANKAN)`**

---

## 1. Latar Belakang & Kesenjangan Audit
Berdasarkan *Post-Soak Audit Report* (`POST_SOAK_AUDIT_REPORT.md`), sesi pengumpulan data staging sebelumnya terbukti berjalan selama **3 siklus** dengan total durasi **54,06 detik**. Klaim uji rendam 24 jam penuh belum terbukti secara empiris. Untuk menutup kesenjangan bukti ketahanan jangka panjang tanpa mengorbankan keselamatan produksi, disusunlah rencana uji rendam operasional bertahap (*Phased Operational Soak Test Plan*).

---

## 2. Rencana Tahapan Pelaksanaan (Phased Roadmap)

### Tahap 1: Short Validation Run (1 Jam / 60 Siklus)
- **Tujuan:** Memvalidasi stabilitas kolektor, penanganan timeout API, dan integritas penyimpanan *append-only* selama 1 jam berturut-turut.
- **Kriteria Kelulusan:** Success rate $\ge$ 98%, tidak ada memory leak, nol mutasi Zabbix.

### Tahap 2: Extended Staging Pilot (6 Jam / 360 Siklus)
- **Tujuan:** Menguji ketahanan menengah terhadap fluktuasi jaringan Zabbix API dan pengumpulan data multi-sensor yang berkelanjutan.
- **Kriteria Kelulusan:** Success rate $\ge$ 99%, tidak ada akumulasi error API berturut-turut > 5 kali.

### Tahap 3: Full 24-Hour Soak Test (24 Jam / 1.440 Siklus)
- **Tujuan:** Membuktikan stabilitas operasional jangka panjang penuh sesuai target awal.
- **Kriteria Kelulusan:** Success rate $\ge$ 99.5%, konsistensi checkpoint terjaga, penggunaan disk stabil di bawah batas aman.

---

## 3. Kriteria Kelulusan Terukur (Measurable Acceptance Criteria)
- **Cakupan Host:** 100% dari 7 host target (`ME_UPS1`–`ME_UPS3`, `ME_PAC1`–`ME_PAC4`) terpantau secara aktif di setiap siklus.
- **Success Rate Siklus:** $\ge$ 99% dari total siklus yang dijadwalkan berhasil memproses telemetri valid atau *abstain* dengan benar.
- **Gap Data & Stale Check:** Telemetri *stale* ditandai secara eksplisit tanpa merusak struktur DataFrame.
- **Penggunaan Resource:** RAM staging stabil (< 150 MB), CPU < 5%, pertumbuhan disk < 50 MB untuk total 24 jam.
- **Integritas Checkpoint:** Data tersimpan secara *append-only* tanpa duplikasi timestamp komposit `(clock, metric)`.

---

## 4. Prasyarat Operasional & Prosedur Sesi Terputus
1. **Pemeriksaan Proses Ganda:** Sebelum memulai, pastikan tidak ada proses kolektor lama yang berjalan (`ps aux | grep -i continuous_collector`).
2. **Prosedur Sesi Terputus:** Jika terminal atau sesi SSH terputus, operator **tidak boleh** langsung meluncurkan proses baru. Operator wajib:
   - Memeriksa proses aktif (`ps aux | grep python`).
   - Memeriksa file checkpoint terakhir di `/root/grafan_aiops/shadow_v5/telemetry_store/`.
   - Melanjutkan sesi hanya setelah memastikan tidak ada konflik penulisan file CSV.
3. **Mekanisme Kill-Switch / Safe Stop:** Interupsi manual via `Ctrl+C` (`SIGINT`) menutup file dengan aman. Ambang batas operasional: RAM < 80%, Disk Staging < 5 GB, Timeout per siklus 120 detik, Max API error berturut-turut = 5.

---

## 5. Daftar Prasyarat yang Belum Terpenuhi (Unfulfilled Prerequisites)
- **Persetujuan Eksplisit Operator:** Sesuai instruksi, pengujian bertahap ini **belum dimulai** dan menunggu persetujuan operator.
- **Sesi Eksekusi Terpantau:** Membutuhkan alokasi sesi terminal interaktif atau operator siaga selama Tahap 1 dan Tahap 2.

---

## 6. Batasan Keselamatan Mutlak
- Jangan melakukan *reboot* host.
- Jangan menghentikan, me-restart, atau membuat ulang container produksi `aiops_predictor_hpc`.
- Jangan mengubah `/root/grafan_aiops/script_aiops.py`.
- Jangan melakukan operasi tulis ke Zabbix.
- Jangan mengubah konfigurasi produksi, database, dashboard, alert, atau data Zabbix.
- Jangan mengaktifkan cron, systemd service, timer, atau daemon permanen.
- Semua pekerjaan baru tetap terisolasi di `/root/grafan_aiops/shadow_v5/`.
