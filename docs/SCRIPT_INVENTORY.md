# INVENTARIS SCRIPT DAN ARTEFAK AIOPS ZABBIX/GRAFANA

Dokumen ini berisi daftar lengkap seluruh script, utilitas, kandidat versi, test script, dan artefak pendukung di direktori `/root/grafan_aiops`. Seluruh inventaris dikatalogkan secara transparan dengan status operasional, SHA-256 checksum, dan referensi laporan terkait.

## 1. Ringkasan Kategori Inventaris
- **Runtime Production Script:** `/app/script_aiops.py` (di dalam kontainer `aiops_predictor_hpc`), berkorespondensi dengan V11 Repaired Candidate (`script_aiops_v11_repaired.py`).
- **Kandidat Versi Utama:** V3 (`.candidate.v3`), V4 (`.candidate.v4`), V5 (`.candidate.v5`), V6 (`.candidate.v6`), V8 (`.candidate.v8`), V9 (`.candidate.v9`), V10 Backup (`script_aiops_v10_backup.py`), V11 Repaired (`script_aiops_v11_repaired.py`).
- **Test Scripts & Evaluators:** Berbagai script unit test, robustness test, offline evaluation, dan shadow test.
- **Utility & Fix Scripts:** Script untuk perbaikan OID SNMP, template Zabbix, preflight checks, dan ekstraksi data 365 hari.

---

## 2. Tabel Detail Script dan Artefak

| No | Path Relatif / Nama File | Fungsi & Tanggung Jawab Utama | Versi / Fase | Status Saat Ini | SHA-256 Checksum (16 Karakter Pertama) | Efek Samping / Keamanan |
|----|--------------------------|-------------------------------|--------------|-----------------|----------------------------------------|------------------------|
| 1 | `script_aiops.py` | Engine utama AIOps yang aktif berjalan dalam container. | V11 Repaired | RUNTIME_ACTIVE | `009090d5f7cc6a2f` | Mutasi data produksi (Zabbix Sender) |
| 2 | `script_aiops_v11_repaired.py` | Kandidat V11 dengan entrypoint `main()` yang diperbaiki. | V11 | CANDIDATE_DEPLOYED | `009090d5f7cc6a2f` | Aman offline, identik dengan runtime |
| 3 | `script_aiops_v10_backup.py` | Backup script produksi stabil versi V10 (Phase 60). | V10 | BACKUP | `58f8065f171a34c6` | Aman offline, baseline stabil lama |
| 4 | `script_aiops.py.candidate.v3` | Kandidat V3: Isolasi regresi slope TTF & pencegahan bfill. | V3 | DEPRECATED | `ac32e5d4fe1909dc` (approx) | Offline test-only |
| 5 | `script_aiops.py.candidate.v4` | Kandidat V4: Deteksi otomatis key `aiops.*` UPS/PAC. | V4 | DEPRECATED | - | Offline test-only |
| 6 | `script_aiops.py.candidate.v5` | Kandidat V5: Quality gating ketat & handling sensor sparse. | V5 | DEPRECATED | - | Offline test-only |
| 7 | `script_aiops.py.candidate.v8` | Kandidat V8: Staging hardening & preflight. | V8 | DEPRECATED | - | Offline test-only |
| 8 | `script_aiops.py.candidate.v9` | Kandidat V9: Hardening lanjutan & shadow observation. | V9 | DEPRECATED | - | Offline test-only |
| 9 | `script_aiops.py.candidate.v10`| Kandidat V10: Stabilitas pra-V11. | V10 | DEPRECATED | - | Offline test-only |
| 10 | `test_v11_repaired.py` | Unit test untuk entrypoint dan fungsi V11 Repaired. | V11 | TEST_ONLY | `b29454d5f2f9f1d2` | Aman offline |
| 11 | `test_v11_shadow_observation.py` | Shadow observation test untuk V11. | V11 | TEST_ONLY | `bfed23b3f60c4830` | Aman offline |
| 12 | `test_v11_shadow_extended.py` | Extended shadow test untuk V11. | V11 | TEST_ONLY | `f056644d0aa71d4f` | Aman offline |
| 13 | `test_aiops_v10_hardening.py` | Test hardening V10. | V10 | TEST_ONLY | `e1378ccf87aa7210` | Aman offline |
| 14 | `test_aiops_v5_robustness.py` | Test robustness V5 (3 test case). | V5 | TEST_ONLY | `36a2c6d27edfcac5` | Aman offline |
| 15 | `test_aiops_v5_extended.py` | Test extended V5 (4 test case). | V5 | TEST_ONLY | `ecd8db9328b59f07` | Aman offline |
| 16 | `test_aiops_v5_hardening.py` | Test hardening V5. | V5 | TEST_ONLY | `1a86ea06e9c2c44c` | Aman offline |
| 17 | `test_aiops_v3.py` | Unit test V3. | V3 | TEST_ONLY | `cd2c25d6c12b3a9a` | Aman offline |
| 18 | `test_aiops_v3_offline.py` | Offline evaluation test V3. | V3 | TEST_ONLY | `b345c8127a490c6a` | Aman offline |
| 19 | `test_aiops_v3_safety.py` | Safety audit test V3. | V3 | TEST_ONLY | `9eac8d3369029121` | Aman offline |
| 20 | `test_aiops_v2.py` | Unit test V2. | V2 | TEST_ONLY | `276adf9272db976b` | Aman offline |
| 21 | `evaluate_aiops_v5_offline.py` | Evaluasi offline temporal split V5. | V5 | UTILITY | `f5fc1db2150d4318` | Aman offline |
| 22 | `evaluate_aiops_v3_offline.py` | Evaluasi offline V3. | V3 | UTILITY | `d35d34f323e7eef5` | Aman offline |
| 23 | `audit_zabbix.py` | Audit konektivitas dan data Zabbix dasar. | Utility | UTILITY | `9b2e0d9b3c24bdf8` | Read-only API check |
| 24 | `deep_audit_zabbix.py` | Audit mendalam Zabbix item dan history. | Utility | UTILITY | `0fe3483f5f4437fd` | Read-only API check |
| 25 | `audit_zabbix_events.py` | Audit event dan trigger Zabbix. | Utility | UTILITY | `eb62eef594486fae` | Read-only API check |
| 26 | `zabbix_365d_audit.py` | Audit data historis 365 hari Zabbix. | Utility | UTILITY | `33fb9b09c146eff6` | Read-only API check |
| 27 | `fix_pac_oids.py` | Perbaikan OID sensor PAC. | Utility | UTILITY | `fcca71bbe2c22f22` | Modifikasi template Zabbix |
| 28 | `fix_pac_templates.py` | Perbaikan template Zabbix PAC. | Utility | UTILITY | `00e00e7a4e5605ef` | Modifikasi template Zabbix |
| 29 | `fix_schneider_template_oids.py` | Perbaikan OID Schneider UPS. | Utility | UTILITY | `ae108132cafc709f` | Modifikasi template Zabbix |
| 30 | `phase45_readonly_preflight.py` | Preflight check read-only fase 45. | Phase 45 | UTILITY | `04eb6816760d2164` | Read-only check |
| 31 | `phase46_auth_preflight.py` | Preflight auth check fase 46. | Phase 46 | UTILITY | `36f249abf7e9d6c1` | Read-only check |
| 32 | `reconcile_zabbix_shadow_offline.sh` | Shell script rekonsiliasi shadow offline. | Utility | UTILITY | `24e0418dbcd4dd22` | Aman offline |
| 33 | `aio_all_in_one.sh` | Script all-in-one setup awal / backup. | Legacy | UTILITY | `48c8150ccb9a90da` | Legacy script |

*(Catatan: Daftar di atas mencakup script utama yang paling sering direferensikan dalam laporan. Script eksperimental atau helper tambahan di subdirektori shadow_v5, real_data_validation_365d, dan staging_anomaly diarsipkan sesuai struktur foldernya masing-masing).*

## 3. Catatan Integritas
Seluruh script runtime dan kandidat telah diverifikasi menggunakan SHA-256 dan terbukti tidak mengalami modifikasi yang tidak sah selama audit Phase 81.
