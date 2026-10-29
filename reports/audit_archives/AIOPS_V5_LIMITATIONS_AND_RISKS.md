# Keterbatasan dan Risiko AIOps v5 (`AIOPS_V5_LIMITATIONS_AND_RISKS.md`)

1. **Ketiadaan Ground Truth Asli:** Metrik akurasi prediktif belum tervalidasi terhadap insiden nyata.
2. **Ketergantungan Fixture:** Pengujian saat ini menggunakan fixture mock offline karena ketiadaan ekspor *time-series* mentah dari Zabbix.
3. **Heuristik TTF:** TTF dihitung dari regresi linier *slope* dan berlaku sebagai proksi tren eksperimental, bukan jaminan mutlak sisa umur pakai (*remaining useful life*).
