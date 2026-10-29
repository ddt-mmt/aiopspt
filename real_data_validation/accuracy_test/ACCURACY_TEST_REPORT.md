# Laporan Pengujian Peningkatan Akurasi Final (`ACCURACY_TEST_REPORT.md`)

- **Tanggal Laporan:** 12 Oktober 2026
- **Status Keputusan Final:** **`EXPLORATORY_ONLY`**

## 1. Eksekutif Summary
Program pengujian peningkatan akurasi final v5 telah dijalankan secara offline dan terisolasi menggunakan data historis Zabbix asli (7 hari). Evaluasi temporal (*chronological split*) dan analisis sensitivitas threshold menunjukkan bahwa model stabil secara numerik, namun karena ketiadaan *ground truth* insiden kerusakan, akurasi operasional tetap tidak dapat diklaim dan dikategorikan sebagai **`EXPLORATORY_ONLY`**.

## 2. Temuan Utama per Host & Validasi Fitur
- **ME_PAC1 s.d. ME_PAC4:** Stabilitas numerik `SUCCESS`, *Health Score* berkisar di 31%–68%, TTF melakukan *abstain* (`None`) pada kondisi stabil, action status berkisar antara 1 (Maintenance) dan 2 (Replace).
- **ME_UPS2 & ME_UPS3:** Stabilitas numerik `SUCCESS`, *Health Score* 59%–68%, action status 1 (Maintenance).
- **ME_UPS1:** Dilewati karena sampel selaras kurang dari batas minimum (5 sampel).
- **Pemisahan Fitur Diskret:** Status kompresor diskret (0/1) terbukti terisolasi dan tidak mencemari regresi slope TTF.

## 3. Sensitivitas Threshold
- Pengujian variasi batas kritis (`crit_val ± 5.0`) menunjukkan perilaku keputusan yang konsisten tanpa osilasi ekstrem.

## 4. Keterbatasan & Tiga Perbaikan Prioritas Tertinggi
1. **Ketiadaan Ground Truth Independen:** Tidak ada label kegagalan yang memadai.
2. **Sparsity Sensor UPS:** Perlu peningkatan strategi penarikan telemetri untuk item berfrekuensi jarang.
3. **Kalibrasi Confidence:** Confidence saat ini berbasis ukuran sampel; diperlukan kalibrasi probabilitas berbasis error historis.

## 5. Verifikasi Integritas Produksi
- **Active Source SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Cocok dengan baseline `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
- **Container Status:** `running` (RestartCount: `0`).
- **Zabbix Writes:** 0 (Nol).
