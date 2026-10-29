# PHASE_70 — Final Runbook Review & Activation Plan

## 1. Ringkasan Keputusan Operator Saat Ini
- **Persetujuan Melanjutkan Tinjauan:** YA.
- **Persetujuan Eksekusi Deployment:** BELUM (menunggu keputusan final operator berdasarkan tinjauan runbook ini).
- **Target Jendela Pemeliharaan:** Sesegera mungkin setelah pemeriksaan akhir disetujui.
- **Target Aktivasi:** Hanya kandidat V11 hasil perbaikan (`script_aiops_v11_repaired.py`, SHA-256 `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`).

---

## 2. Bukti dan Checksum yang Diverifikasi

| Artefak / Dokumen | Path | SHA-256 Checksum | Status Verifikasi |
| :--- | :--- | :--- | :--- |
| **Baseline V10 (Script)** | `/root/grafan_aiops/script_aiops.py` | `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291` | `MATCH` |
| **Kandidat V11 (Repaired)** | `/root/grafan_aiops/script_aiops_v11_repaired.py` | `009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef` | `MATCH` |
| **Paket Phase 68** | `/root/grafan_aiops/PHASE_68_V11_DEPLOYMENT_APPROVAL_PACKAGE.md` | `e6b9cda0b89bdb49d1d64b03a9adf69d854558549589fb6508b087d9c4c84798` | `MATCH` |
| **Laporan Phase 69** | `/root/grafan_aiops/PHASE_69_FINAL_PREACTIVATION_VERIFICATION_REPORT.md` | `caa071a1caf574ac03990f86751a864f52475b50d4005023858d0091156c1605` | `MATCH` |

- **Status Container Produksi:** `aiops_predictor_hpc` (`Status: running`, `RestartCount: 0`).

---

## 3. Tabel Perintah yang Diusulkan, Host Target, Efek, dan Status Tinjauan

| Perintah yang Diusulkan | Host / Target | Efek Operasional | Status Tinjauan |
| :--- | :--- | :--- | :--- |
| `cp script_aiops_v11_repaired.py script_aiops.py` | Host: `prox-prod` (`/root/grafan_aiops`) | Mengganti file script runtime dengan versi V11 yang telah diperbaiki. | `APPROVED_FOR_PLANNED_EXECUTION` |
| `docker compose restart aiops_predictor_hpc` | Host: `prox-prod` (`/root/grafan_aiops`) | Merefresh container AIOps untuk memuat script V11 baru secara terisolasi. | `APPROVED_FOR_PLANNED_EXECUTION` |
| `docker logs --tail 100 -f aiops_predictor_hpc` | Host: `prox-prod` | Memantau log startup dan siklus polling daemon secara real-time. | `APPROVED_FOR_PLANNED_EXECUTION` |

---

## 4. Urutan Aktivasi Tertulis (Deployment Runbook)

1. **Pre-Checks:** Pastikan jendela pemeliharaan aktif dan operator siaga. Verifikasi checksum script kandidat V11 (`009090d5f7cc6a2f8c68e783cbc79879af4e115ff06fd4fa5ce5052f25c06cef`).
2. **Backup Baseline:** Amankan salinan script baseline V10 (`script_aiops.py`) ke folder backup terisolasi.
3. **Replacement:** Salin `script_aiops_v11_repaired.py` menjadi `script_aiops.py`.
4. **Container Restart:** Jalankan `docker compose restart aiops_predictor_hpc`.
5. **Immediate Inspection:** Periksa log container dalam 60 detik pertama untuk memastikan daemon menginisialisasi loop dengan benar dan tidak mengalami *restart loop* (mengatasi isu Phase 63).

---

## 5. Urutan Verifikasi Kesehatan (Post-Activation Verification)

1. **Container Stability:** Verifikasi `docker inspect aiops_predictor_hpc --format '{{.State.Status}} (RestartCount: {{.RestartCount}})'` (`RestartCount` harus tetap `0`).
2. **Polling Cycles:** Konfirmasi log menunjukkan siklus polling multi-device (3 UPS dan 4 PAC) berjalan setiap 60 detik.
3. **Zabbix Integration:** Verifikasi pengambilan telemetri dari Zabbix API dan pengiriman metrik V11 (`processed`, `failed: 0`) sukses tanpa error unhandled.
4. **Quality Gates:** Pastikan gate validasi data aktif menyaring data `STALE`, `FUTURE`, atau `INSUFFICIENT` secara presisi.

---

## 6. Runbook Rollback

1. **Pemicu (Trigger):** Terdeteksi *restart loop*, error unhandled beruntun, atau hilangnya pengiriman metrik selama > 3 menit pasca-aktivasi.
2. **Eksekusi Rollback:**
   - Kembalikan script runtime ke baseline V10 (`58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
   - Jalankan `docker compose restart aiops_predictor_hpc`.
3. **Verifikasi Pemulihan:**
   - Konfirmasi container kembali stabil dengan `RestartCount` tidak bertambah dan alur metrik V10 baseline pulih sepenuhnya.

---

## 7. Stop Conditions

Aktivasi wajib dihentikan atau dibatalkan seketika jika:
- Checksum file kandidat tidak cocok dengan acuan.
- Container langsung mengalami *restart loop* setelah restart.
- Terjadi kegagalan koneksi fatal ke Zabbix API atau Sender.
- Log menunjukkan *unhandled exception* pada modul analisis V11.

---

## 8. Risiko yang Masih Terbuka

- Ketiadaan *ground truth* kegagalan perangkat keras riil (`RUL_ACCURACY = NOT_MEASURABLE`), dimitigasi melalui pengujian keandalan sistem dan *quality gates* data yang ketat.

---

## 9. Pemeriksaan yang Memerlukan Persetujuan Operator
- Keputusan akhir operator untuk memberikan izin eksekusi perintah aktivasi pada jendela pemeliharaan yang dijadwalkan.

---

## 10. Pernyataan Penutup & Status Akhir

- **Apakah produksi berubah selama Phase 70?** Tidak. Produksi 100% tidak berubah (*read-only*).
- **Apakah baseline V10 masih aktif?** Ya. Produksi saat ini masih berjalan stabil pada baseline V10 (`58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
- **Apakah rencana aktivasi dan rollback cukup spesifik?** Ya. Perintah, target, verifikasi, dan pemicu rollback telah dijabarkan secara rinci.
- **Risiko yang belum terselesaikan:** Ketiadaan ground truth RUL, yang bersifat inheren pada model prediktif tanpa insiden historis terkait.
- **Status Akhir:** `READY_FOR_FINAL_OPERATOR_DECISION`
