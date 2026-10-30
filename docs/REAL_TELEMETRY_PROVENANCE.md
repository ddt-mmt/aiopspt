# REAL TELEMETRY PROVENANCE DAN SUMBER PENGAMBILAN DATA GLOBAL

Dokumen ini merinci sumber pengambilan data global (*data sources*) serta provenansi telemetri yang digunakan oleh sistem AIOps Zabbix/Grafana, baik telemetri operasional aktual maupun dataset benchmark publik.

## 1. Sumber Data Operasional Utama (Primary Operational Source)
Sumber utama dan satus-satunya yang digunakan secara operasional (*live production*) oleh engine AIOps (`script_aiops.py` / V11 / V12) adalah **Zabbix Server** (`http://10.28.1.110/zabbix`).
- **Infrastruktur Terkait:** Perangkat UPS dan PAC di data center HPC Cibinong.
- **Protokol:** Zabbix JSON-RPC API (`history.get`) dan Zabbix Sender.

## 2. Dataset Publik & Benchmark Global Pendukung (*Public Benchmarks*)
Selain telemetri operasional riil dari Zabbix, sistem juga memanfaatkan dataset benchmark publik standar akademik untuk memvalidasi *robustness* model machine learning terhadap anomali ekstrem yang jarang terjadi di operasional harian:
1. **LBNL Fault Detection and Diagnostics (FDD) Dataset:** Digunakan untuk memvalidasi pola kegagalan termal dan penurunan efisiensi unit penyejuk udara (*Precision Air Conditioner* / PAC).
2. **NASA Prognostics Center of Excellence (PCoE) Battery Dataset:** Digunakan untuk menguji keakuratan estimasi *Remaining Useful Life* (RUL) dan kurva degradasi tegangan/kapasitas sel baterai UPS.
- **Manifesto & Path Pendukung:** Artefak dan manifest terkait tersimpan pada direktori `/root/grafan_aiops/shadow_v5/` (seperti `PUBLIC_DATASET_ACQUISITION_MANIFEST.json`).

## 3. Pemisahan Data (Data Separation)
- **Zero Contamination:** Dataset benchmark publik / sintetis **tidak pernah** dicampur ke dalam arus inferensi *real-time* produksi. Dataset publik hanya digunakan pada tahap eksperimen, validasi offline, dan pengujian unit (*shadow testing*).
- **Ground Truth Isolation:** Telemetri operasional dari Zabbix diperlakukan sebagai sumber kebenaran tunggal untuk sistem produksi (*production pipeline*).
