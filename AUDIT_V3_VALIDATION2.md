# Laporan Validasi dan Audit Keselamatan Kandidat AIOps v3 (`AUDIT_V3_VALIDATION2.md`)

- **Tanggal Audit:** 12 Oktober 2026
- **Target Proyek:** `/root/grafan_aiops` (`prox-prod`)
- **Status Validasi:** **PASS WITH LIMITATIONS** (Aman secara arsitektur, isolasi mock lulus, tidak ada efek samping produksi).

---

## Task 1 — Verifikasi Audit & Metrik Real Data Zabbix

Berdasarkan analisis file `/root/grafan_aiops/AUDIT_V3_REAL_DATA.json`, berikut adalah verifikasi angka aktual untuk setiap host:

### 1. Host PAC (`ME_PAC1`, `ME_PAC2`, `ME_PAC3`, `ME_PAC4`)
- **Sampel 24 Jam (Sensor Fisik Utama):** 
  - `return.temp.c`, `supply.temp.c`, `return.humidity.rh`, `evaporator.fan.speed`: masing-masing memiliki **1,440 sampel** (interval polling stabil ~1 menit).
  - Status kompresor (`compressor.1.status` atau `compressor.status`): **1,440 sampel**.
- **Rentang Histori:** Dari `2026-10-11T04:25:00+00:00` hingga `2026-10-12T04:25:00+00:00`.
- **Nilai Invalid / Non-Finite:** **0** (seluruh nilai numerik valid, tidak ada NaN atau inf).
- **Metadata Error:** Tidak ada error SNMP pada sensor fisik PAC.
- **Catatan & Fakta Terverifikasi:** Seluruh PAC memenuhi syarat minimum sampel (`>10` sampel selaras) dan tidak menggunakan item trapper AIOps sebagai input.

### 2. Host UPS (`ME_UPS1`, `ME_UPS2`, `ME_UPS3`)
- **Sampel 24 Jam:**
  - `output.load`: **1,277 (UPS1)**, **1,223 (UPS2)**, **1,090 (UPS3)** sampel.
  - `battery.voltage`: **128 (UPS1)**, **11 (UPS2)**, **314 (UPS3)** sampel.
  - `battery.runtime_remaining`: **172 (UPS1)**, **208 (UPS2)**, **966 (UPS3)** sampel.
  - `battery.capacity`: **4 (UPS1)**, **53 (UPS2)**, **4 (UPS3)** sampel.
- **Batasan Terverifikasi (`PASS WITH LIMITATIONS`):** 
  - Item `battery.capacity` memiliki cakupan sampel yang sangat jarang pada UPS1 dan UPS3 (hanya 4 sampel dalam 24 jam). Hal ini disebabkan oleh perilaku polling SNMP APC MIB yang jarang memperbarui kapasitas jika nilai tidak berubah signifikan. Kandidat v3 menangani hal ini melalui resampling `1min` dengan `ffill(limit=2)` dan validasi minimal 10 sampel selaras.
  - Item `battery.temperature` pada UPS1 dan UPS2 mendeteksi error SNMP `noSuchName` dan berhasil dikecualikan oleh fungsi `get_ups_sensor_dict()`.

---

## Task 2 — Review Logika Kandidat v3

1. **Fitur Diskret dalam IsolationForest vs Regresi Slope:**
   - Status kompresor diskret (0/1) **dikeluarkan** dari regresi slope utama di v3 (menggunakan filter `continuous_candidates`), sehingga slope linier tidak menghitung tren yang salah dari nilai diskret 0/1.
   - Fitur diskret **tetap dimasukkan** ke dalam IsolationForest untuk mendeteksi anomali multivariat bersama variabel kontinu, yang merupakan desain yang disengaja untuk menangkap kegagalan mekanis (misal kompresor mati saat beban tinggi).
2. **Penanganan Data Kosong, Resampling, & `ffill(limit=2)`:**
   - Resampling `1min` menyelaraskan timestamp asinkron antar sensor. Penggunaan `ffill(limit=2)` memastikan gap transmisi singkat ditutup tanpa merembeskan data lama secara berlebihan, dan pemanggilan `.dropna()` memastikan tidak ada baris yang menyisakan NaN.
3. **Semantik `TTF=None` & Hirarki Metrik:**
   - Ketika tren stabil atau positif (tidak ada degradasi menuju nilai kritis), v3 mengembalikan `TTF = None`. Ini dibedakan dari kondisi darurat (`TTF <= 24` jam). Skor IsolationForest direpresentasikan sebagai skor anomali yang diskalakan ke Health Score (0–100%), bukan sebagai probabilitas statistik absolut.

---

## Task 3 — Uji Keamanan Terisolasi (`test_aiops_v3_safety.py`)

File pengujian keselamatan baru telah dibuat di `/root/grafan_aiops/test_aiops_v3_safety.py`. Pengujian ini menggunakan *mock* dan *stub* untuk menguji jalur eksekusi tanpa koneksi jaringan ke Zabbix.

**Hasil Eksekusi Unit Test Keselamatan:**
```bash
python3 -m py_compile /root/grafan_aiops/test_aiops_v3_safety.py && python3 /root/grafan_aiops/test_aiops_v3_safety.py
```
**Output Aktual:**
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.404s

OK
```

### Rincian Pengujian yang Berhasil Dilakukan:
1. **Sensor Hilang / Stale:** Ketika Zabbix mengembalikan item kosong atau timestamp tua, fungsi memicu `ValueError`, menghentikan siklus, dan memanggil `sender.send.assert_not_called()` (tidak ada data yang dikirim ke Zabbix).
2. **Nilai Non-Finite:** Data mengandung `NaN` atau `inf` ditolak seketika oleh `calculate_multisensor_rul()` tanpa menghasilkan nilai sintetis/random.
3. **Semantik TTF=None:** Diverifikasi bahwa `TTF=None` menghasilkan status aksi normal (`0`) bila *health* sehat.

---

## Ringkasan & Rekomendasi
- **Fakta Terverifikasi:** Kandidat v3 aman secara fungsional, mematuhi seluruh batasan read-only, dan lulus uji isolasi keamanan.
- **Rekomendasi:** Lakukan evaluasi *out-of-sample* terhadap log historis gangguan nyata sebelum dipertimbangkan untuk di-deploy ke lingkungan produksi pada fase berikutnya.
- **Konfirmasi:** Active source `script_aiops.py` tidak diubah, container tidak disentuh, tidak ada data yang ditulis ke Zabbix.
