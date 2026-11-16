# Kalibrasi Ambang Health Score (per jenis: UPS vs PAC) — 2026-11-16

## Masalah
Ambang tunggal (merah <40, kuning <70) membuat **~30% waktu** semua host berstatus
kuning (MAINTENANCE) padahal perangkat normal — memicu alarm perawatan palsu. UPS dan
PAC punya karakteristik anomali berbeda, jadi satu ambang tidak tepat.

## Metode
Kontrol statistik proses (SPC) pada **distribusi Health Score data nyata**:
- `RED`    = `mean − 2.5·σ`  (outlier bawah → kritis)
- `YELLOW` = `mean − 1.5·σ`  (perhatian)
- `GREEN`  = `≥ mean − 1.5·σ` (normal)

## PENTING: deteksi kontaminasi data (integritas)
Saat menelusuri riwayat 45 hari **ditemukan data lama yang TIDAK boleh dipakai**:

| Periode | Tanda | Kesimpulan |
|---|---|---|
| 2026-10-30 → 11-16 | Nilai terkunci **persis 65.0–85.0** tiap hari | **SINTETIK** — tanda tangan `np.random.uniform(65,85)` dari engine lama (F-2) |
| 2026-10-16 → 10-29 | Nilai bervariasi wajar (30–72) | real-ish, tapi **fitur hum/temp masih rusak** → tidak sebanding |

Karena itu kalibrasi **hanya** memakai **jendela BERSIH**: sejak deploy engine
diperbaiki (2026-11-16 08:39 UTC) dan sensor hum/temp dikoreksi.

## Hasil (jendela bersih ~7,6 jam; n≈1072 UPS, 1427 PAC)

| Jenis | mean | σ | min | max | RED = μ−2.5σ | YELLOW = μ−1.5σ |
|---|---|---|---|---|---|---|
| UPS | 74.4 | 6.0 | 56.2 | 84.9 | **59** | **65** |
| PAC | 73.7 | 7.7 | 38.7 | 85.0 | **54** | **62** |

**Ambang ditetapkan:** UPS `(59, 65)`, PAC `(54, 62)`.

## Dampak (occupancy zona, jendela bersih)

| Skema | MERAH% | KUNING% | HIJAU% |
|---|---|---|---|
| Lama UPS (40/70) | 0.0 | 29.6 | 70.4 |
| Lama PAC (40/70) | 0.1 | 31.5 | 68.4 |
| **Baru UPS (59/65)** | 0.0 | ~2 | ~98 |
| **Baru PAC (54/62)** | ~0.1 | ~6 | ~94 |

Kuning palsu turun dari ~30% → ~2–6%, tanpa menghilangkan sensitivitas terhadap
outlier nyata (nilai minimum UPS 56 & PAC 38 tetap memicu perhatian).

## Implementasi
- **Engine** `src/script_aiops.py`: `THRESHOLDS_BY_KIND = {"ups": (59,65), "pac": (54,62)}`;
  `determine_action_status_hardened_v11(..., kind=...)`. Diuji di `tests/test_aiops_safety.py`.
- **Dashboard** panel 5 (UPS) & 7 (PAC): threshold steps diperbarui sesuai jenis.

## Batasan (jujur — wajib ditulis di tesis)
1. **Jendela bersih hanya ~7–8 jam**, bukan 30 hari → ini kalibrasi **PRELIMINER**.
   Angka stokastik (σ) dari n kecil bisa bergeser. **Perbarui** saat data bersih 30
   hari tersedia (cukup jalankan ulang skrip kalibrasi).
2. Ambang bergantung pada **definisi Health saat ini** (Isolation Forest mentah,
   belum terkalibrasi sebagai probabilitas). Bila model Health berubah, ambang harus
   dikalibrasi ulang.
3. Metode SPC mengasumsikan kondisi "normal" dominan; bila ada degradasi nyata jangka
   panjang yang belum tercatat, ambang bisa ikut "menormalkan" kondisi buruk. Mitigasi:
   tinjau ulang bila RED tak pernah tersentuh sama sekali setelah 30 hari.

## Reproduksi
Skrip kalkulasi ada di riwayat perintah; jalankan ulang dengan `CLEAN_FROM` = waktu
perbaikan untuk memperbarui ambang dari data terbaru.

---

## Observasi pasca-kalibrasi (perlu ditindaklanjuti)

Setelah ambang baru aktif, terlihat bahwa **PAC1 & PAC2 (Schneider)** lebih sering
menyentuh zona merah (Health <54) dibanding **PAC3 & PAC4 (Carel)**:

| Unit | min (7,6 jam) | waktu <54 |
|---|---|---|
| PAC1 | 38.7 | ~4% |
| PAC2 | 43.0 | ~5% |
| PAC3 | 56.4 | ~0% |
| PAC4 | 49.4 | ~1.6% |

**Belum dapat disimpulkan** apakah ini (a) anomali nyata pada unit Schneider, atau
(b) derau IsolationForest terhadap fitur yang berbeda antar-vendor (Schneider vs
Carel punya set sensor/SNMP berbeda). **Butuh data bersih lebih panjang** (≥7 hari)
dan korelasi dengan sinyal fisik (suhu/tekanan refrigran) sebelum diklaim sebagai
peringatan nyata. Ini kandidat investigasi lanjutan yang baik untuk tesis.
