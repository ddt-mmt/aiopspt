# Perbandingan Model AIOps v3, v4, dan v5 (`AIOPS_V5_MODEL_COMPARISON.md`)

- **v3:** Memperbaiki penarikan history Zabbix dan menghapus *data leakage* (`bfill`).
- **v4:** Menambahkan deteksi otomatis prioritas key `aiops.*`.
- **v5:** Memperkenalkan *Data Quality Gating* eksplisit (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`), pemisahan fitur diskret dari regresi slope TTF, penanganan sensor *sparse* (seperti `battery.capacity`), serta indikator *confidence*.
