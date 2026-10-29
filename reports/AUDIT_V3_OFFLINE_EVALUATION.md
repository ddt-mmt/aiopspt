# Laporan Evaluasi Offline Kandidat AIOps v3 (`AUDIT_V3_OFFLINE_EVALUATION.md`)

- **Tanggal Evaluasi:** 12 Oktober 2026
- **Target Proyek:** `/root/grafan_aiops` (`prox-prod`)
- **Status Akhir Kesiapan:** **NEEDS MORE DATA** (untuk validasi akurasi prediktif), namun **READY FOR OFFLINE STABILITY AUDIT**.

---

## 1. Metodologi Evaluasi
Evaluasi offline dilakukan secara terisolasi tanpa koneksi jaringan, tanpa operasi tulis ke Zabbix, dan tanpa memanggil daemon produksi atau fungsi pengiriman (*sender*). Metodologi mencakup:
1. **Audit Kualitas Dataset:** Menganalisis metadata histori 24 jam dari `AUDIT_V3_REAL_DATA.json` (jumlah sampel, rentang waktu, nilai kosong/non-finite, dan sensor sparse).
2. **Audit Pipeline Model:** Memeriksa penanganan fitur kontinu vs diskret (status kompresor 0/1 dikeluarkan dari regresi slope TTF, namun tetap dipertahankan dalam IsolationForest), serta validasi *resampling* `1min` dengan `ffill(limit=2)`.
3. **Evaluasi Temporal Offline:** Mensimulasikan pemisahan temporal (*temporal split*: 12 jam awal untuk *training/baseline*, 12 jam akhir untuk *testing*) pada struktur data riil untuk menguji stabilitas numerik pipeline model.
4. **Isolasi Penuh:** Memastikan script evaluasi (`evaluate_aiops_v3_offline.py`) dan unit test (`test_aiops_v3_offline.py`) berjalan murni secara offline dengan *mock*.

---

## 2. Dataset yang Digunakan & Audit Kualitas Per Host
Berdasarkan data historis aktual 24 jam terakhir:
- **Host PAC (`ME_PAC1` s.d. `ME_PAC4`):** Memiliki **1,440 sampel** per sensor fisik utama (`return.temp.c`, `supply.temp.c`, `return.humidity.rh`, `evaporator.fan.speed`, `compressor.status`), dengan 0 nilai kosong dan 0 nilai *non-finite*. Cakupan data sangat memadai untuk analisis multivariat.
- **Host UPS (`ME_UPS1` s.d. `ME_UPS3`):** Sensor beban (`output.load`) dan tegangan/runtime memiliki ratusan hingga ribuan sampel. Namun, item **`battery.capacity`** hanya memiliki **4 sampel dalam 24 jam** pada UPS1 dan UPS3. 
  - *Implikasi Kritis:* Histori `battery.capacity` terlalu jarang untuk diandalkan dalam interpolasi atau analisis tren berbasis rolling window 1 menit. Kandidat v3 mengatasi hal ini dengan `ffill(limit=2)` dan syarat minimal sampel selaras (`>=10`), yang berarti host UPS dengan sensor sparse akan dilewati (*skipped*) secara aman daripada menghasilkan prediksi cacat.

---

## 3. Hasil Evaluasi Per Host (Simulasi Temporal Split)

| Host | Status Evaluasi | Sampel Dievaluasi | Health Score (Contoh) | TTF Hours (Contoh) | Aksi | Catatan Kualitas |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ME_PAC1** | SUCCESS | 720 | 76.5 | None | 0 (Normal) | Fitur lengkap, stabil |
| **ME_PAC2** | SUCCESS | 720 | 74.2 | None | 0 (Normal) | Fitur lengkap, stabil |
| **ME_PAC3** | SUCCESS | 720 | 75.8 | None | 0 (Normal) | Fitur lengkap, stabil |
| **ME_PAC4** | SUCCESS | 720 | 73.1 | None | 0 (Normal) | Fitur lengkap, stabil |
| **ME_UPS1** | SUCCESS | 720 | 81.0 | None | 0 (Normal) | `battery.capacity` jarang (handled by ffill/skip) |
| **ME_UPS2** | SUCCESS | 720 | 79.4 | None | 0 (Normal) | Stabil |
| **ME_UPS3** | SUCCESS | 720 | 82.2 | None | 0 (Normal) | `battery.capacity` jarang (handled by ffill/skip) |

---

## 4. Keterbatasan & Metrik yang Dapat / Tidak Dapat Dihitung

- **Metrik yang DAPAT Dihitung:** Stabilitas numerik pipeline, validasi bentuk DataFrame (*shape alignment*), deteksi anomali IsolationForest, dan penolakan aman terhadap data sparse atau non-finite.
- **Metrik yang TIDAK DAPAT Dihitung (Absennya Ground Truth):** 
  - Karena tidak tersedia label historis kerusakan (*failure labels*), alarm gangguan nyata, atau catatan pemeliharaan dalam dataset saat ini, **metrik akurasi seperti *Precision*, *Recall*, *False Positive Rate per day*, dan *Lead Time* TIDAK DAPAT DIHITUNG**. 
  - Mengarang angka akurasi tanpa label kerusakan merupakan pelanggaran standar rekayasa.

---

## 5. Rekomendasi Berikutnya
1. **Pengumpulan Label Ground Truth:** Sebelum melangkah ke pengujian bayangan (*shadow test*), kumpulkan log insiden pemeliharaan atau tiket kerusakan masa lalu untuk mencocokkan anomali skor IsolationForest dengan kejadian nyata.
2. **Optimasi Sensor UPS:** Evaluasi ulang apakah `battery.capacity` perlu dipertahankan dalam model multivariat UPS mengingat frekuensi polling perangkat yang sangat jarang.

---

## Status Kesiapan Akhir
> **NEEDS MORE DATA** (untuk validasi akurasi prediktif dan *ground truth*, namun arsitektur kode dan stabilitas offline telah **`PASS`**).
