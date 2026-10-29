# Reproduksibilitas AIOps v5 (`AIOPS_V5_REPRODUCIBILITY.md`)

Seluruh pengujian kandidat v5 dapat direproduksi secara lokal dan terisolasi dengan menjalankan:
```bash
python3 /root/grafan_aiops/test_aiops_v5_robustness.py
python3 /root/grafan_aiops/test_aiops_v5_extended.py
python3 /root/grafan_aiops/evaluate_aiops_v5_offline.py
```
Hasil eksekusi deterministik dijamin oleh penggunaan `random_state=42` pada model *IsolationForest*.
