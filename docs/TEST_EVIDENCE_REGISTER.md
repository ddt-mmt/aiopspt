# TEST EVIDENCE REGISTER — AIOPS ZABBIX/GRAFANA

Dokumen ini meregistrasi seluruh rangkaian pengujian (*test cases* dan *test executions*) yang tercatat dalam riwayat pengembangan sistem AIOps dari versi awal sampai V11.

## 1. Metodologi Penghitungan Test
- **Unique Test Cases:** Jumlah kasus pengujian unik berdasarkan fungsi dan skenario pengujian yang didefinisikan dalam script test (`test_aiops_v5_robustness.py`, `test_aiops_v5_extended.py`, `test_v11_repaired.py`, dll.).
- **Test Executions:** Jumlah total eksekusi test yang tercatat dalam laporan validasi.
- **Operational Observation Cycles:** Siklus polling/observasi produksi yang berjalan kontinu setiap 60 detik.

---

## 2. Register Pengujian Utama

| ID Test | Nama Test / Script | Fase / Versi | Lingkungan | Hasil | Jumlah Kasus Unik | Bukti & Referensi Laporan | Catatan |
|---------|--------------------|--------------|------------|-------|-------------------|--------------------------|---------|
| T-V5-01 | `test_aiops_v5_robustness.py` | V5 / Robustness | Offline Staging | PASS | 3 | `ROBUSTNESS_V5_VALIDATION.md` | Lulus uji robustness data kualitas |
| T-V5-02 | `test_aiops_v5_extended.py` | V5 / Extended | Offline Staging | PASS | 4 | `ROBUSTNESS_V5_RETEST_REPORT.md` | Uji penolakan NaN/Inf & TTF abstain |
| T-V10-01| `test_aiops_v10_hardening.py` | V10 / Hardening | Offline Staging | PASS | 5 | `shadow_runner_v10.py` | Validasi hardening pra-V11 |
| T-V11-01| `test_v11_repaired.py` | V11 / Repair | Offline Staging | PASS | 3 | `PHASE_65_V11_OFFLINE_SHADOW_VALIDATION_REPORT.md` | Verifikasi entrypoint `main()` |
| T-V11-02| `test_v11_shadow_observation.py`| V11 / Shadow | Offline Staging | PASS | 4 | `PHASE_66_V11_EXTENDED_SHADOW_OBSERVATION_REPORT.md` | Shadow observation test |
| T-V11-03| `test_v11_shadow_extended.py` | V11 / Extended | Offline Staging | PASS | 4 | `PHASE_66_V11_EXTENDED_SHADOW_OBSERVATION_REPORT.md` | Extended shadow telemetry |
| T-G36-01| `run_phase_g36_anomaly_eval.py`| Phase G36 | Offline Staging | PASS | 6 | `run_phase_g36_anomaly_eval.py` | Evaluasi anomali 365d |

---

## 3. Rekapitulasi Hasil Pengujian
- **Total Unique Test Cases Terverifikasi:** 29 test case di seluruh modul pengujian utama.
- **Total PASS:** 29
- **Total FAIL (Setelah Retest & Repair):** 0 (Fase 63 entrypoint fail telah diperbaiki di Phase 64-65).
- **Total BLOCKED:** 0 (Staging staging beroperasi normal).
- **Total NOT_VERIFIED:** Komponen Portainer Stack Definition (memerlukan akses UI Portainer eksternal).
