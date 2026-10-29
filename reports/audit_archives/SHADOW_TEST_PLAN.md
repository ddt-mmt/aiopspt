# Rencana Pengujian Shadow Testing (`SHADOW_TEST_PLAN.md`)

- **Tujuan:** Merancang kerangka pengujian bayangan (*shadow testing*) terisolasi untuk engine AIOps kandidat v3/v4 tanpa mengganggu sistem produksi atau Zabbix server.
- **Prinsip Utama:**
  1. *Zero Production Disruption:* Kontainer produksi (`aiops_predictor_hpc`) dan skrip aktif (`script_aiops.py`) tidak boleh diubah atau direstart.
  2. *Zero Zabbix Mutation:* Tidak ada panggilan API penulisan (`item.create`, `item.update`, `history.push`, `sender.send`) ke Zabbix produksi.
  3. *Isolated Fixture & Logging:* Seluruh eksekusi membaca dari data historis/fixture lokal dan mencatat keluaran ke file JSON terisolasi (`SHADOW_TEST_RESULTS.json`).
- **Langkah Pelaksanaan:**
  - Tahap 1: Validasi statis kode kandidat (sudah selesai).
  - Tahap 2: Eksekusi harness offline (`shadow_test_aiops.py`).
  - Tahap 3: Pengujian keselamatan mock (`shadow_test_aiops_safety.py`).
  - Tahap 4: Tinjauan kesiapan akhir (`SHADOW_TEST_READINESS.md`).
