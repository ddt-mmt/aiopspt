# Perbaikan Sumber Data & Panel Dashboard — 2026-11-16

Melanjutkan `PRODUCTION_DEPLOYMENT_20261116.md`. Setelah deploy, audit panel
menemukan **dua bug sumber data** (item Zabbix menunjuk OID yang salah). Keduanya
diperbaiki **di sumbernya**, bukan disamarkan di panel.

---

## Temuan: akar masalah ada di definisi item Zabbix (SNMP OID)

### F-9 — Humidity PAC terbaca ~550 %RH (mustahil; maks 100%)

**Diagnosis (bukti SNMP langsung):** perangkat Schneider (PAC1/PAC2) mengekspos
**tiga** sensor yang semuanya bernama "Return Humidity" dengan satuan berbeda:

| OID (index) | Satuan perangkat | Divisor | Raw | Nilai benar |
|---|---|---|---|---|
| `.17` | **%RH** | 10 | 448 | **44.8 %RH** ← yang benar |
| `.18` | **gr/lbm** (absolute humidity) | 100 | 5149 | 51.49 gr/lb |
| `.19` | g/Kg | 100 | 736 | 7.36 g/Kg |

Zabbix **menunjuk `.18`** (absolute humidity) tetapi memberi label `%RH` dan
multiplier ×0.1 → **549 %RH**. Cross-check: `.18`=51.5 gr/lb ≈ `.19`=7.36 g/kg
(konsisten sebagai kelembapan absolut), sedangkan PAC3/PAC4 (Carel) yang benar
membaca ~51–54 %RH. Jadi item-nya salah pilih sensor, bukan sekadar salah skala.

**Perbaikan:** item template `Template_Schneider_Uniflair_PAC_Custom` (itemid 60380)
`snmp_oid` `.18` → **`.17`** (multiplier ×0.1 dipertahankan, benar untuk divisor 10).

**Hasil terverifikasi:**

| Host | Sebelum | Sesudah |
|---|---|---|
| ME_PAC1 | 546 %RH ❌ | **45 %RH** ✅ |
| ME_PAC2 | 551 %RH ❌ | **47.3 %RH** ✅ |
| ME_PAC3 (Carel) | 54.2 %RH ✅ | 54.2 %RH ✅ (tak diubah) |
| ME_PAC4 (Carel) | 51.7 %RH ✅ | 51.6 %RH ✅ (tak diubah) |

### F-10 — Battery temperature UPS mati (0 / seri kosong)

**Diagnosis:** item `battery.temperature[upsHighPrecBatteryTemperature]` menunjuk
OID `.318.1.1.1.2.3.2.0`, yang dijawab perangkat dengan **`noSuchName`** (tidak ada
di MIB perangkat ini) → seri kosong. OID `.2.3.2.0` tidak ada; suhu baterai asli
ada di `.318.1.1.1.2.2.2.0` (`upsAdvBatteryTemperature`).

**Perbaikan:** item template `APC UPS by SNMP` (itemid 34201) `snmp_oid`
`.2.3.2.0` → **`.2.2.2.0`**; **multiplier ×0.1 DIHAPUS** karena OID itu sudah
dalam derajat utuh (25, bukan 250).

**Hasil terverifikasi:**

| Host | Sebelum | Sesudah |
|---|---|---|
| ME_UPS1 | 0 (mati) | **25 °C** ✅ |
| ME_UPS2 | 0 (mati) | **22 °C** ✅ |
| ME_UPS3 | 0 (mati) | perangkat **tidak punya** OID suhu baterai (sysObjectID `.318.1.3.23.2`, firmware berbeda) → item dinonaktifkan dengan jelas, bukan menampilkan 0 palsu |

---

## Perbaikan panel (dashboard → v8)

| Panel | Sebelum | Sesudah |
|---|---|---|
| 10 | "UPS Output Load, Battery Temp & Voltage" — **3 satuan dalam 1 sumbu** (%, ℃, V) → skala hancur | **"UPS Output Load (%) & Battery Voltage (V)"** — 2 sumbu (kiri %, kanan V) |
| 11 | "PAC Return Temp, Supply Temp & Humidity" — °C + %RH + (550 salah) 1 sumbu | **"PAC Return/Supply Temp (°C) & Return Humidity (%RH)"** — 2 sumbu; sensor diperbaiki |
| 12 | — | **BARU: "UPS Battery Temperature (℃)"** — panel sendiri (satuan ketiga) |
| 13 | — | **BARU: "TTF & Tolerance Band per Host"** (tabel) — menampilkan rentang toleransi TTF, analogi indikator bahan bakar |
| 5,7 | deskripsi teks biasa | deskripsi jujur: ambang & sifat "bukan probabilitas / belum terkalibrasi" |

Verifikasi: `verify_dashboard_bindings.py` → **63/63 target resolve, 0 gagal**.

---

## Catatan penting untuk tesis

1. **Histori lama masih menampilkan nilai salah.** Perbaikan berlaku **ke depan**;
   data historis `.18` (~550 %RH) tetap ada di database Zabbix dan akan tampak bila
   rentang waktu dashboard mencakup sebelum 2026-11-16. Untuk tesis, sajikan dengan
   jendela waktu **setelah** perbaikan, atau beri anotasi pada grafik.
2. **Skala sensor bersifat per-perangkat.** PAC1/PAC2 (Schneider) dan PAC3/PAC4
   (Carel) memakai OID & tata letak berbeda; jangan generalisasi satu mapping SNMP
   ke semua unit. Ini poin metodologis yang layak ditulis.
3. **"Perbaiki di sumber" lebih benar daripada "perbaiki di panel".** Memperbaiki
   OID membuat **semua konsumen** (Grafana, engine AIOps, alert) membaca nilai benar
   sekaligus, bukan hanya satu grafik.

## Rollback
- Item: `analysis/deployment/backup_20261116/humidity_items_before.json`,
  `battery_temp_item_before.json`.
- Dashboard: `analysis/deployment/backup_20261116/grafana_dashboard_before.json`.
- Bukti sesudah: `source_fixes_evidence.txt`, `source_items_after.json`.
