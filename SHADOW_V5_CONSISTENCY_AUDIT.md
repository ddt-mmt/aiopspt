# Laporan Audit Konsistensi Shadow Test v5 (`SHADOW_V5_CONSISTENCY_AUDIT.md`)

- **Tanggal Audit:** 12 Oktober 2026
- **Status Kesimpulan:** **CONDITIONAL GO**

## 1. Verifikasi Integritas Produksi (PASS)
- **Active Source (`script_aiops.py`):** Hash SHA-256 aktual (`58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`) cocok dengan baseline (`58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
- **Container Produksi (`aiops_predictor_hpc`):** Berstatus `running` (tidak tersentuh).
- **Zabbix Writes:** 0 (Nol).

## 2. Temuan Audit Konsistensi

### A. Selisih Health Score
- *Laporan Lama:* PAC 73–76%, UPS 78–82%.
- *CSV/JSON Terbaru:* UPS 48.11–58.69, PAC 43.48–49.88.
- *Penyebab:* Perbedaan dihasilkan oleh variasi data generator mock (`np.random.uniform`) pada run eksekusi yang berbeda. Model IsolationForest merespons distribusi titik data acak tersebut secara independen.

### B. Alasan Action Status 1 (Maintenance)
- Aturan keputusan aksi (`determine_action_status`):
  - Jika `Health < 40` atau `TTF <= 24` $ightarrow$ `2 (REPLACE)`
  - Jika `Health < 70` atau `TTF <= 720` $ightarrow$ `1 (MAINTENANCE)`
  - Lainnya $ightarrow$ `0 (NORMAL)`
- Karena seluruh host pada run tersebut memiliki Health di bawah 70% (kisaran 43%–58%) dan TTF PAC berada di 132.73 jam (<= 720 jam), sistem secara konsisten menetapkan Action Status ke **1 (Maintenance)**.

### C. Asal-Usul Data
- Data pada CSV/JSON merupakan **offline mock fixtures**, bukan telemetri *live* produksi. Oleh karena itu, metrik hasil shadow test ini merefleksikan pengujian stabilitas logika algoritma, bukan performa operasional aktual perangkat keras.

## 3. Rekomendasi & Keputusan
- **Keputusan:** **CONDITIONAL GO** untuk melanjutkan ke tahap validasi *staging* berikutnya secara terisolasi.
