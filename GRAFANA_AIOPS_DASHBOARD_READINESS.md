# Laporan Audit Kesiapan Dashboard Grafana AIOps (`GRAFANA_AIOPS_DASHBOARD_READINESS.md`)

- **Tanggal Audit:** 12 Oktober 2026
- **Target Proyek:** `/root/grafan_aiops` (`prox-prod`)
- **Status Kesiapan Dashboard:** **READY WITH RESTRICTIONS** (Panel Trapper siap, panel telemetri real-time PAC telah pulih setelah koreksi OID Schneider/Carel, namun penamaan metrik TTF dan Health Score memerlukan pelabelan disclaimer metodologis).

---

## 1. Inventarisasi Panel & Sumber Data (`aiops_facility_dashboard.json`)

Berdasarkan pemindaian struktur JSON dashboard (`aiops_facility_dashboard.json`), terdapat 11 panel utama (termasuk row header):
1. **Panel [2] ⚡ UPS Policy Action Status** (Stat) — Target item: `UPS Policy Action Status` (Host: `$ups_host`).
2. **Panel [3] ❄️ PAC Policy Action Status** (Stat) — Target item: `PAC Policy Action Status` (Host: `$pac_host`).
3. **Panel [5] ⚡ UPS Health Score (%)** (Gauge) — Target item: `UPS Health Score AIOps` (Host: `$ups_host`).
4. **Panel [6] ⚡ UPS Time-to-Failure (TTF)** (Bargauge) — Target item: `UPS Time-to-Failure (Hours)` (Host: `$ups_host`).
5. **Panel [7] ❄️ PAC Health Score (%)** (Gauge) — Target item: `PAC Health Score AIOps` (Host: `$pac_host`).
6. **Panel [8] ❄️ PAC Time-to-Failure (TTF)** (Bargauge) — Target item: `PAC Time-to-Failure (Hours)` (Host: `$pac_host`).
7. **Panel [10] ⚡ UPS Output Load, Battery Temp & Voltage** (Time Series) — Target items: `ups.output.load`, `ups.battery.temp`, `ups.battery.voltage`.
8. **Panel [11] ❄️ PAC Return Temp, Supply Temp & Humidity** (Time Series) — Target items: `return.temp.c`, `supply.temp.c`, `return.humidity.rh`.

---

## 2. Hasil Verifikasi Ketersediaan Item
- **Item Trapper AIOps (`*.health.score`, `*.ttf.hours`, `*.action.status`):** Tersedia dan dibuat otomatis oleh daemon saat siklus eksekusi berjalan.
- **Item Telemetri PAC (`return.temp.c`, `supply.temp.c`, `return.humidity.rh`):** Tersedia dan telah divalidasi aktif (`State: 0`) setelah koreksi OID instance Schneider Uniflair (`ME_PAC1`, `ME_PAC2`) dan Carel (`ME_PAC3`, `ME_PAC4`).
- **Item UPS (`ups.output.load`, `ups.battery.temp`, `ups.battery.voltage`):** Tersedia pada host UPS.

---

## 3. Catatan Metodologi & Koreksi Tampilan
1. **Skor Kesehatan (Health Score):** Dihitung berdasarkan *decision function* IsolationForest (skor anomali multivariat). Panel harus diberi catatan bahwa nilai ini adalah **skor anomali yang diskalakan**, bukan probabilitas statistik kerusakan.
2. **Time-to-Failure (TTF):** Dihitung menggunakan regresi linier sederhana (*slope* deret waktu). Nilai ini bersifat **heuristik eksperimental dan belum tervalidasi** secara operasional karena ketiadaan label *ground truth* kerusakan historis.
3. **Penanganan Data Kosong (Unknown/Insufficient Data):** Pastikan panel tidak menampilkan data *stale* atau *fallback* acak (pada kandidat v3/v4, fallback acak telah dihapus dan diganti dengan *skip* aman).

---

## 4. Kesimpulan & Rekomendasi
Dashboard Grafana saat ini siap untuk digunakan dalam pengujian bayangan (*shadow testing*), dengan catatan bahwa deskripsi panel perlu diperjelas mengenai keterbatasan model prediktif (TTF eksperimental dan skor anomali).

> **READY WITH RESTRICTIONS**
*(Tidak ada perubahan pada dashboard produksi atau provisioning yang dilakukan; seluruh audit bersifat read-only).*
