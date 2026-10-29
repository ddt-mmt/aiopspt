# Changelog Robustness v5 (`ROBUSTNESS_V5_CHANGELOG.md`)

- **Versi:** v5 (Kandidat Terisolasi)
- **Perubahan Utama:**
  - Penambahan implementasi `get_sensor_history_v5()` dengan *Data Quality Gating* eksplisit (`NORMAL`, `DEGRADED_DATA`, `INSUFFICIENT_DATA`).
  - Pemisahan fitur kontinu vs diskret pada `calculate_multisensor_rul_v5()`.
  - Penambahan tingkat keyakinan (*confidence level*) pada hasil keluaran model.
  - Pembuatan suite pengujian offline (`test_aiops_v5_robustness.py` & `evaluate_aiops_v5_offline.py`).
- **Integritas:** Active source produksi (`script_aiops.py`) tidak tersentuh.
