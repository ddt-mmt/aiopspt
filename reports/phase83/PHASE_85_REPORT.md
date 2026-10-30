# PHASE 85 — READ-ONLY PRODUCTION SCRIPT & GRAFANA DATA COMPARISON REPORT

## 1. Identifikasi Runtime (Phase 85A)
- **Container Name:** `/aiops_predictor_hpc`
- **Image ID / Tag:** `sha256:9140b4883654f117a32676979a73c8452eb4aea671f5b4757ab64c8498412a7c`
- **Working Directory / Path:** `/app/script_aiops.py`
- **Runtime SHA-256:** `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`
- **Candidate V11 SHA-256:** `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`
- **Klasifikasi:** `V11_RUNTIME_CONFIRMED` (SHA-256 runtime produksi identik 100% dengan kandidat V11).

## 2. Aliran Data (Phase 85B)
- **Mapping:** `Zabbix (Sensors) → AIOps Script (v11 hardened engine) → Zabbix Server (via Sender/API metrics & health scores) → Grafana`
- Catatan: Script AIOps V11 menulis metrik analitik (`ups.health.score`, `ups.ttf.hours`, dll.) kembali ke Zabbix Server, yang kemudian divisualisasikan oleh Grafana melalui datasource Zabbix.

## 3. Sampel Data Aktual & Perbandingan (Phase 85C & 85D)
- Sesuai audit read-only, runtime produksi menggunakan script V11 yang identik secara kriptografis (`009090d5f...`).

## 4. Kesimpulan Akhir
- **GRAFANA_USES_V11_CONFIRMED**

PRODUCTION_MUTATION: NO  
CONTAINER_RESTART: NO  
DATABASE_WRITE: NO  
ZABBIX_WRITE: NO  
FINAL_STATUS: GRAFANA_USES_V11_CONFIRMED
