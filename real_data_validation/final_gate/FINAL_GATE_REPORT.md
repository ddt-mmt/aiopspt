# Laporan Final Gate AIOps v5 (`FINAL_GATE_REPORT.md`)

- **Tanggal Laporan:** 12 Oktober 2026
- **Keputusan Akhir:** **`GO-EXPLORATORY-SHADOW`**

## 1. Keputusan Akhir & Rasional
Keputusan akhir adalah **`GO-EXPLORATORY-SHADOW`**. Kandidat v5 terbukti stabil secara numerik, lulus seluruh uji keselamatan, penanganan anomali, dan integritas produksi terjaga 100%. Namun, karena ketiadaan *ground truth* insiden operasional, sistem belum memenuhi syarat untuk *GO-PRODUCTION* dan hanya diizinkan untuk observasi *shadow testing* terisolasi tanpa memengaruhi tindakan operasional.

## 2. Hasil per Host (Rekonsiliasi Final)
- **ME_PAC1:** 9,936 sampel | Health: 34.55 | TTF: Abstain | Action: 2 (Replace)
- **ME_PAC2:** 9,936 sampel | Health: 31.42 | TTF: Abstain | Action: 2 (Replace)
- **ME_PAC3:** 4,002 sampel | Health: 68.21 | TTF: Abstain | Action: 1 (Maintenance)
- **ME_PAC4:** 4,003 sampel | Health: 67.95 | TTF: 8760.0h | Action: 1 (Maintenance)
- **ME_UPS2:** 92 sampel | Health: 68.96 | TTF: Abstain | Action: 1 (Maintenance)
- **ME_UPS3:** 26 sampel | Health: 59.21 | TTF: Abstain | Action: 1 (Maintenance)
- **ME_UPS1:** 5 sampel selaras $ightarrow$ Tercatat sebagai **`INSUFFICIENT_ALIGNED_SAMPLES`** (dilewati dengan aman).

## 3. Temuan Kritis & Keterbatasan
1. Ketiadaan *ground truth* (0 *problem events* di Zabbix dalam 30 hari terakhir).
2. Sparsity pada sensor UPS tertentu (seperti `ME_UPS1` dengan 5 sampel selaras).
3. TTF 8760 jam pada ME_PAC4 merupakan batas maksimal (*cap*) regresi linier.
4. *Health Score* adalah skor anomali multivariat IsolationForest yang diskalakan, bukan probabilitas kesehatan.

## 4. Interpretasi Metrik
- **Health Score:** Indikator anomali multivariat terstandar.
- **TTF (Time-to-Failure):** Heuristik eksperimental berbasis tren linier; melakukan *abstain* (`None`) saat tren stabil.
- **Confidence:** Berdasarkan ukuran sampel (`HIGH` untuk sampel >= 60, `MEDIUM` untuk < 60).
- **Action Status:** Berdasarkan aturan ambang batas kesehatan dan TTF.

## 5. Status Integritas Produksi
- **Active Source SHA-256:** `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` (Cocok dengan baseline `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
- **Container Status:** `running` (RestartCount: `0`).
- **Zabbix Writes:** 0 (Nol).

## 6. Syarat Minimum untuk Melanjutkan (*Go-Live*)
1. Tersedianya dataset *ground truth* pemeliharaan atau insiden historis yang terverifikasi.
2. Observasi *shadow testing* terisolasi minimal 14 hari tanpa kegagalan kritis.
