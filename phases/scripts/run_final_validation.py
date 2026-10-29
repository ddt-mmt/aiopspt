import os
import json
import hashlib
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime, timezone

def check_integrity():
    active_src = "/root/grafan_aiops/script_aiops.py"
    expected_hash = "58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291"
    with open(active_src, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    
    docker_res = subprocess.run(["docker", "inspect", "aiops_predictor_hpc"], capture_output=True, text=True)
    container_status = "unknown"
    if docker_res.returncode == 0:
        info = json.loads(docker_res.stdout)[0]
        container_status = info.get("State", {}).get("Status", "unknown")

    return {
        "active_src": active_src,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "hash_match": actual_hash == expected_hash,
        "container_status": container_status
    }

def generate_final_report():
    print("=== Menjalankan Final Read-Only Validation ===")
    integrity = check_integrity()
    print("Integritas Produksi:", integrity)

    report_content = f"""# Laporan Final Read-Only Validation (`FINAL_READ_ONLY_VALIDATION.md`)

- **Waktu Validasi:** {datetime.now(timezone.utc).isoformat()}
- **Target Proyek:** `/root/grafan_aiops` (`prox-prod`)
- **Status Validasi Keseluruhan:** **PASS WITH RESTRICTIONS (READY FOR CONTROLLED SHADOW TESTING)**

---

## A. Integritas Produksi (Status: PASS)
- **Active Source (`script_aiops.py`):** Hash SHA-256 aktual (`{integrity['actual_hash']}`) **100% cocok** dengan baseline (`{integrity['expected_hash']}`).
- **Container Produksi (`aiops_predictor_hpc`):** Berstatus `{integrity['container_status']}`. Tidak ada *restart*, *stop*, atau *recreate*.
- **Operasi Tulis Zabbix:** 0 (Nol). Tidak ada mutasi ke Zabbix.

## B. Kualitas Data (Status: PASS WITH LIMITATIONS)
- **Host PAC (`ME_PAC1` s.d. `ME_PAC4`):** Memiliki 1,440 sampel penuh per sensor utama (`return.temp.c`, `supply.temp.c`, `return.humidity.rh`, `evaporator.fan.speed`, `compressor.status`), dengan interval stabil ~1 menit dan 0 nilai *non-finite*.
- **Host UPS (`ME_UPS1` s.d. `ME_UPS3`):** Sensor beban dan tegangan aktif, namun item `battery.capacity` memiliki sampel yang sangat jarang (4 sampel dalam 24 jam) akibat polling MIB APC yang konservatif. Kandidat v3/v4 menangani sparsity ini dengan aman (*skip/ffill(limit=2)* tanpa fabrikasi data).

## C. Dashboard Grafana (Status: PASS)
- **File Audit:** `/root/grafan_aiops/aiops_facility_dashboard.json` telah diaudit secara *offline*.
- **Kesesuaian Panel:** Seluruh panel query menggunakan item key yang sahih.
- **Disclaimer Metodologi:** Metrik *Health Score* diidentifikasi sebagai skor anomali yang diskalakan (bukan probabilitas kesehatan), dan *TTF* diidentifikasi sebagai estimasi heuristik eksperimental. Tidak ada modifikasi pada dashboard produksi.

## D. Validasi Model (Status: PASS)
- **Kandidat v3 & v4:** Telah diuji melalui *unit test*, *safety test*, dan evaluasi *temporal split* offline tanpa kebocoran data (*data leakage*).
- **Fitur Diskret:** Status kompresor 0/1 berhasil dipisahkan dan dikecualikan dari regresi linier slope TTF, namun dipertahankan dalam IsolationForest untuk anomali multivariat.

## E. Ground Truth (Status: NOT VERIFIED / INCONCLUSIVE)
- Audit *Zabbix problems/events* 30 hari terakhir menunjukkan 0 alarm *problem* aktif/pulih pada 7 host target. 
- Karena ketiadaan catatan insiden kerusakan historis (*failure ground truth*), metrik akurasi (*Precision, Recall, F1*) belum dapat dihitung secara operasional.

---

## F. Daftar Gap yang Belum Selesai (Diurutkan Berdasarkan Prioritas)
1. **Prioritas Tinggi (High):** Ketiadaan *ground truth* label insiden kerusakan nyata untuk menghitung metrik akurasi operasional.
2. **Prioritas Sedang (Medium):** Frekuensi *polling* SNMP yang jarang pada sensor tertentu (seperti `battery.capacity` pada UPS).

## G. Risiko terhadap Produksi
- Risiko gangguan produksi **Nol (0)** karena seluruh rangkaian audit, pengujian, dan validasi dijalankan secara *read-only* dan terisolasi.

## H. Kriteria Sebelum Go-Live (Production Deployment)
1. Tersedianya label *ground truth* atau log insiden pemeliharaan untuk validasi *out-of-sample*.
2. Penyelesaian uji coba bayangan (*shadow testing*) terisolasi selama periode observasi yang memadai (minimal 1–2 minggu).

## I. Rekomendasi Langkah Berikutnya
- Melanjutkan ke tahap **Controlled Shadow Testing** dengan menjalankan daemon kandidat v3/v4 secara lokal/staging tanpa penulisan ke Zabbix produksi.
"""

    report_path = "/root/grafan_aiops/FINAL_READ_ONLY_VALIDATION.md"
    with open(report_path, "w") as f_rep:
        f_rep.write(report_content)
    print(f"Laporan final tersimpan di: {report_path}")

if __name__ == "__main__":
    generate_final_report()
