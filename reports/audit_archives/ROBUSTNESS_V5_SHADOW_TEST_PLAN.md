# Rencana Shadow Test Robustness v5 (`ROBUSTNESS_V5_SHADOW_TEST_PLAN.md`)

- **Tujuan:** Menjalankan pengujian bayangan (*shadow testing*) terisolasi untuk kandidat v5.
- **Aturan Keselamatan:**
  - Tanpa modifikasi script aktif (`script_aiops.py`).
  - Tanpa restart/recreate kontainer produksi.
  - Tanpa mutasi atau penulisan ke Zabbix produksi.
- **Pelaksanaan:** Pengujian replay historis offline dan pencatatan hasil ke artefak JSON terisolasi (`ROBUSTNESS_V5_TEST_RESULTS.json`).
