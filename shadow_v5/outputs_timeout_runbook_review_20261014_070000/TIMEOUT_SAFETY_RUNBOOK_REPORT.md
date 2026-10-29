# Laporan Timeout Safety & Operator Runbook Review (`TIMEOUT_SAFETY_RUNBOOK_REPORT.md`)

- **Tanggal Review:** 2026-10-14 07:00:00 UTC
- **Direktori Staging Audit Terisolasi:** `/root/grafan_aiops/shadow_v5/outputs_timeout_runbook_review_20261014_070000`
- **Baseline Script Produksi (`script_aiops.py`):** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
- **Keputusan Akhir Review:** **`BLOCKED`**

---

## 1. Ringkasan Eksekutif
Review ini melakukan analisis mendalam secara statis terhadap pustaka `zabbix_utils` versi 2.0.4, implementasi timeout pada `continuous_collector.py`, serta menyusun runbook operasional beserta analisis risiko penghentian darurat (*kill-switch* / `Ctrl+C`). Berdasarkan investigasi lokal, meskipun `zabbix_utils` menyediakan timeout HTTP default 30 detik pada level koneksi/request, **tidak ada mekanisme timeout level siklus (*cycle-level timeout watchdog*)** atau proteksi *non-blocking I/O* yang menjamin proses dapat dihentikan secara instan jika terjadi hang jaringan. Oleh karena itu, sesuai dengan instruksi keselamatan, keputusan akhir dinyatakan **`BLOCKED`** sampai prasyarat teknis timeout terpenuhi.

---

## 2. Analisis Statis & Bukti Lokal Timeout Pustaka (`zabbix_utils`)
- **Versi Pustaka Terpasang:** `zabbix-utils 2.0.4` (lokasi: `/usr/local/lib/python3.9/site-packages`).
- **Inspeksi Signature Konstruktor `ZabbixAPI`:**
  `__init__(self, url=None, token=None, user=None, password=None, ..., timeout=30)`
- **Perilaku & Perbedaan Jenis Timeout:**
  1. *Timeout Koneksi / Request:* Diatur secara default ke 30 detik oleh `zabbix_utils` untuk setiap panggilan HTTP request API (`host.get`, `item.get`, `history.get`). Namun, dalam `continuous_collector.py`, parameter `timeout` tidak diteruskan secara eksplisit saat inisialisasi `ZabbixAPI(url=..., user=..., password=...)`, sehingga bergantung sepenuhnya pada default pustaka (30 detik). Status: **`VERIFIED` (Default 30s)** / **`NOT VERIFIED` (Explicitly configured)**.
  2. *Timeout Keseluruhan Siklus (*Cycle Timeout*):* Tidak ada. Collector melakukan iterasi pada 7 host secara sekuensial. Jika setiap host memakan waktu mendekati batas request timeout atau mengalami retry (`max_retries=3`), total durasi satu siklus dapat melampaui batas 120 detik tanpa ada mekanisme *watchdog* otomatis yang membatalkan siklus. Status: **`FAILED` / `NOT VERIFIED`**.
  3. *Timeout Proses / Penghentian Cepat (*Process Timeout / Non-blocking I/O*):* Python `time.sleep` dan sinkronisasi socket berbasis `requests`/`urllib3` bersifat sinkron dan memblokir thread eksekusi saat menunggu respons jaringan. Interupsi manual (`Ctrl+C` / `SIGINT`) mungkin mengalami penundaan (*delayed response*) jika proses sedang tertahan di dalam pemanggilan blok I/O jaringan yang sedang menunggu timeout socket 30 detik. Status: **`NOT VERIFIED`**.

---

## 3. Matriks Status Kontrol Keamanan & Timeout

| Komponen Kontrol | Status | Evidensi & Catatan Analisis |
| :--- | :--- | :--- |
| SHA-256 Produksi (`script_aiops.py`) | **`VERIFIED`** | Hash konsisten dengan baseline (`58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`). |
| Status Container Produksi | **`VERIFIED`** | Container `aiops_predictor_hpc` tetap *running* tanpa restart. |
| Kepatuhan Zabbix Read-Only | **`VERIFIED`** | Hanya menggunakan operasi `get` (`zabbix_writes = 0`). |
| HTTP Request Timeout (`zabbix_utils`) | **`REPORTED`** | Default pustaka 30 detik, namun tidak didefinisikan secara eksplisit di skrip. |
| **Cycle-Level Timeout (120s max)** | **`FAILED` / `NOT VERIFIED`** | Tidak ada pengawas waktu siklus (*watchdog*) di level kolektor. |
| **Safe Process Termination (`Ctrl+C`)** | **`NOT VERIFIED`** | Berisiko tertahan (*blocking*) saat menunggu socket I/O timeout. |

---

## 4. Runbook Operator untuk Pengawasan (Draf Referensi)
Meskipun status saat ini **`BLOCKED`**, runbook berikut mendokumentasikan prosedur operasional yang diperlukan kelak setelah prasyarat timeout dipenuhi:

### A. Pra-Pemeriksaan (Pre-Flight Check)
1. **Verifikasi Hash Produksi:**
   ```bash
   sha256sum /root/grafan_aiops/script_aiops.py
   ```
   *Harus sama persis dengan:* `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
2. **Verifikasi Status Container Produksi:**
   ```bash
   docker ps --filter "name=aiops_predictor_hpc"
   ```
   *Harus berstatus `Up` tanpa restart baru.*
3. **Verifikasi Ketiadaan Proses Kolektor Lama:**
   ```bash
   ps aux | grep -i continuous_collector
   ```
   *Tidak boleh ada proses kolektor yang aktif.*

### B. Pelaksanaan Terpantaunya Tahap 1 (Foreground)
1. Jalankan kolektor di terminal foreground terdedikasi:
   ```bash
   python3 continuous_collector.py
   ```
2. **Pemantauan Metrik Selama 1 Jam (60 Siklus):**
   - Amati output log per siklus (durasi per siklus harus < 120 detik).
   - Pantau penggunaan RAM host (`free -m`, harus < 80%).
   - Pantau ukuran disk staging (`du -sh /root/grafan_aiops/shadow_v5/`, harus < 5 GB).
   - Pastikan error API berturut-turut tidak melebihi 5 kali.

### C. Prosedur Penghentian Manual & Penanganan Putus Koneksi (SSH Disconnect)
- **Peringatan Kritis tentang `Ctrl+C`:** Menekan `Ctrl+C` mengirim sinyal `SIGINT`. Namun, jika proses kolektor sedang tertahan di tengah pemanggilan socket jaringan (`blocking I/O`), Python mungkin tidak segera menangani sinyal hingga timeout soket (30 detik) tercapai. Operator **tidak boleh** mengasumsikan penghentian instan; operator harus menunggu hingga siklus aktif selesai atau menggunakan terminal terpisah untuk melakukan *graceful kill* (`kill -SIGTERM <PID>`) jika diperlukan.
- **Jika SSH Terputus:** Jangan panik dan jangan langsung meluncurkan proses baru. Periksa proses aktif (`ps aux | grep python`) dan file checkpoint di `telemetry_store/` untuk memastikan tidak terjadi konflik tulis (*race condition*).

### D. Verifikasi Pasca-Run (Post-Run Audit)
1. Periksa file JSON ringkasan siklus di direktori staging.
2. Hitung ulang SHA-256 `script_aiops.py` untuk memastikan integritas produksi.
3. Verifikasi status kontainer produksi.

---

## 5. Prasyarat yang Belum Terpenuhi (Blocking Prerequisites)
Sebelum Tahap 1 dapat diubah statusnya dari `BLOCKED` menjadi `READY FOR OPERATOR APPROVAL`:
1. **Implementasi Timeout Eksplisit di Konstruktor `ZabbixAPI`:** Parameter `timeout` (misal 30 atau 60 detik) harus diteruskan secara eksplisit ke pemanggilan `ZabbixAPI(...)` di `continuous_collector.py`.
2. **Mekanisme Watchdog Siklus:** Penambahan pembatas waktu (*timeout guard* / thread watchdog) di level siklus pengumpulan telemetri untuk menjamin bahwa satu siklus tidak akan berjalan melebihi 120 detik dalam kondisi jaringan lambat.
3. **Penanganan Non-Blocking I/O / Signal Handler:** Memastikan penangkapan sinyal interupsi dapat memutuskan operasi tunggu jaringan secara aman.

---

## 6. Rekomendasi Akhir kepada Operator
- **Status Keputusan:** **`BLOCKED`**.
- **Alasan:** Risiko timeout siklus yang belum terlindungi oleh watchdog otomatis dan potensi penundaan respons interupsi manual (*blocking I/O*) membuat pelaksanaan tanpa perbaikan kode pendukung memiliki risiko operasional.
- **Tindakan Lanjutan:** Jangan menjalankan Tahap 1. Pertimbangkan untuk menambahkan parameter timeout eksplisit pada skrip staging tanpa mengubah skrip produksi, atau tunggu sampai perbaikan timeout diterapkan pada kerangka pengujian staging.
