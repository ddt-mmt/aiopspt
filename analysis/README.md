# Analisa AIOps Power & Thermal Facility (HPC)

**Tanggal analisa:** 2026-11-16
**Dashboard target:** `http://10.28.1.110:3000/d/aiops-facility-hpc/aiops-power-and-thermal-facility-hpc-a` (uid `aiops-facility-hpc-a`)
**Sumber repo:** `/root/grafan_aiops` (git `origin` → `github.com/ddt-mmt/aiopspt`)
**Metode:** read-only. Tidak ada perubahan pada Zabbix, Grafana, atau container produksi.

> Ringkasan satu paragraf: mesin *learning*-nya memang **belum sempurna** — tapi masalahnya **bukan (terutama) di akurasi/toleransi prediksi**. Akar masalah yang saya temukan lebih mendasar: **dashboard produksi yang Anda buka sedang menampilkan nilai sintetik (acak/derived), bukan telemetri sensor asli**, dan sebagian panel menunjuk ke item yang **tidak ada**. Ketidakpastian "akurasi TTF/RUL" yang Anda rasakan adalah gejala yang benar dari penyebab ini — bukan sekadar model yang perlu di-tuning.

---

## 0. TL;DR temuan (severity di depan)

| # | Temuan | Severity | Bukti |
|---|--------|----------|-------|
| **F-1** | **Runtime produksi menulis nilai SINTETIK** ke tag sensor asli. `output.load`, `battery.temp`, `battery.voltage` (UPS) dan `return.temp.c`, `supply.temp.c`, `return.humidity.rh`, `evaporator.fan.speed`, `compressor.status` (PAC) di-overwrite tiap 60 s dengan rumus acak yang diturunkan dari Health Score — **bukan dari sensor SNMP**. | 🔴 **Kritis** | `src/script_aiops.py:345-357, 405-421`; history menunjukkan trapper menimpa nilai SNMP |
| **F-2** | **Health Score acak saat quality-gate gagal.** Setiap kegagalan gate (yang terjadi **tiap siklus**) memicu `np.random.uniform(65,85)`. Itulah kenapa angka naik-turun tak wajar — bukan model yang "belajar". | 🔴 **Kritis** | `src/script_aiops.py:334, 341, 394, 401`; distribusi 30d stdev 4–6.5, min 33–39 |
| **F-3** | **TTF praktis selalu konstan `8760`** (≈1 tahun, batas atas clamp) untuk semua 7 host → prediksi tidak informatif. | 🟠 Tinggi | log container; history `ups.ttf.hours` = 8760 terus |
| **F-4** | **Panel dashboard rusak/tidak menampilkan data**: 2 panel raw-telemetry men-dashboard-kan item yang **tidak ada** (`ups.output.load`, `ups.battery.temp`, `ups.battery.voltage`), dan item `return.temp.c` dll. dicari **berdasarkan `name` yang salah**. | 🟠 Tinggi | `config/aiops_facility_dashboard.json` vs `item.get` → `NO MATCH` |
| **F-5** | **Kredensial hardcoded di repo yang di-push ke GitHub.** `ZABBIX_PASS=<REDACTED-ZABBIX-PASSWORD>` (admin!) tersebar di ≥ 15 file + `.json` item Zabbix + log. | 🔴 **Kritis (keamanan)** | `git grep <REDACTED-ZABBIX-PASSWORD> HEAD` |
| **F-6** | **Akar "akurasi tak bisa dipastikan" sudah didokumentasikan sendiri** dengan benar (TTF/RUL `NOT_MEASURABLE`, `contamination=0.05` ≠ akurasi 95%, Health Score bukan probabilitas). Jadi ketidakpastian Anda **valid** — dan konsisten dengan F-1/F-2. | 🟡 Info | `docs/ML_WORKFLOW_AND_ACCURACY.md` §5 |
| **F-7** | **Fitur wajib PAC `compressor.status` / UPS `battery.capacity` hampir selalu kosong/stale** → quality gate hampir selalu `INSUFFICIENT_DATA` → hampir selalu masuk jalur acak F-2. | 🟠 Tinggi | log: `Timestamp NaT/None untuk sensor …` di hampir semua host |

**Kesimpulan:** dashboard tampak "hidup", tapi nilai yang terlihat **tidak mewakili kondisi fisik perangkat**. Analisa akurasi lebih lanjut tidak bermakna sebelum F-1/F-2/F-4 diperbaiki.

---

## 1. Arsitektur yang benar vs yang benar-benar berjalan

**Yang seharusnya (per `THESIS_METHODOLOGY.md` & diagram README):**

```
Sensor SNMP UPS/PAC ──► Zabbix ──► Engine AIOps (IsolationForest + slope TTF)
                                          └─► Zabbix trapper (health, ttf, action)
                                                 └─► Grafana
```
Telemetri sensor = **read-only** bagi engine; engine hanya menulis balik *metrik turunan* (`*.health.score`, `*.ttf.hours`, `*.action.status`).

**Yang sebenarnya berjalan** (dari `src/script_aiops.py` + log container + Zabbix):

```
Sensor SNMP ──► Zabbix
                   ▲
                   │  Tiap 60 s, engine MENGIRIM nilai buatan ke key sensor ASLI:
                   │     output.load     = 65 + (100-health)*0.15
                   │     battery.temp    = 26 + (100-health)*0.05
                   │     battery.voltage = 54 - (100-health)*0.04
                   │     return.temp.c   = 24 + (100-health)*0.05   ... dst (PAC)
                   │  → menimpa/mendampingi nilai sensor SNMP asli.
                   └── Engine AIOps (script_aiops.py)  ──► Grafana
```

Kode penentu (`src/script_aiops.py`):

```python
# baris 345-347 (UPS) — nilai BUATAN diturunkan dari health, bukan sensor
sim_load = round(65.0 + (100 - health) * 0.15, 1)
sim_temp = round(26.0 + (100 - health) * 0.05, 1)
sim_volt = round(54.0 - (100 - health) * 0.04, 1)
...
packet = [
    ItemValue(hostname, 'ups.health.score', health),
    ItemValue(hostname, 'ups.ttf.hours', ttf),
    ItemValue(hostname, 'ups.action.status', action),
    ItemValue(hostname, 'output.load', sim_load),      # ← menimpa makna sensor asli
    ItemValue(hostname, 'battery.temp', sim_temp),     # ←
    ItemValue(hostname, 'battery.voltage', sim_volt),  # ←
]
```

Dan **fallback acak** saat gate gagal (terjadi tiap siklus):

```python
# baris 334 / 341 (UPS), 394 / 401 (PAC)
health = round(float(np.random.uniform(65.0, 85.0)), 2)
ttf = 8760.0
action = 1
```

CATATAN: kandidat V12 (`src/script_aiops_v12_candidate.py`) **sudah menghapus** fallback acak dan synthetic write (`NO random health fallback, NO synthetic sensor writes`) — tetapi **belum di-deploy** (container masih menjalankan `script_aiops.py`, md5 identik dengan `script_aiops.py`/`v11_repaired`).

---

## 2. Bukti empiris

### 2.1 Nilai sintetik menimpa sensor asli

Perbandingan 30 hari, host **ME_UPS1** (`analysis/evidence/data_volume_compare.json`):

| Item | Jenis | Terakhir | Min | Max |
|------|-------|---------:|----:|----:|
| `output.load` (trapper) | **SINTETIK** | 69.8 | 67.2 | 70.2 |
| `output.load[upsHighPrecOutputLoad]` (SNMP) | **ASLI** | 48.9 | 46.7 | 53.0 |
| `battery.voltage` (trapper) | **SINTETIK** | 52.7 | 52.6 | 53.4 |
| `battery.voltage[upsHighPrecBatteryActualVoltage]` (SNMP) | **ASLI** | 215.9 | 191.2 | 217.0 |

Beban inverter UPS asli ≈ **48.9%**, tapi dashboard menampilkan ≈ **68–70%** (buatan). Tegangan baterai asli ≈ **216 V**, dashboard ≈ **53 V**. Angka sintetik bergerak sangat halus (rentang sempit) karena hanya fungsi dari Health Score — pola khas sinyal buatan, bukan fisika sensor.

### 2.2 Health Score = acak saat gate gagal (yang mana hampir selalu)

Distribusi `*.health.score` 30 hari:

| Host | n | min | max | mean | stdev |
|------|---:|----:|----:|-----:|------:|
| ME_UPS1 | 5000 | 33.45 | 72.25 | 64.03 | 6.55 |
| ME_UPS2 | 5000 | 37.19 | 72.58 | 64.22 | 6.05 |
| ME_UPS3 | 5000 | 39.21 | 67.21 | 58.42 | 4.04 |
| ME_PAC1 | 5000 | 39.41 | 64.77 | 54.64 | 5.08 |
| ME_PAC2 | 5000 | 39.14 | 64.63 | 55.60 | 4.63 |
| ME_PAC3 | 5000 | 34.13 | 65.78 | 51.93 | 4.66 |
| ME_PAC4 | 5000 | 37.53 | 67.57 | 56.58 | 6.07 |

Nilai berayun tiap menit dengan stdev besar dan **cenderung < 70** → memaksa `action=1 (MAINTENANCE)` hampir permanen, padahal tidak ada indikasi degradasi nyata. Ini konsisten dengan `np.random.uniform(65,85)` dipanggil ulang setiap kali gate gagal.

### 2.3 TTF konstan 8760

`ups.ttf.hours` & `pac.ttf.hours` di semua host = **8760.0** (batas clamp `max(0,min(8760,…))`). Artinya cabang slope **tidak pernah menghasilkan nilai berbeda** — baik karena `slope` ≈ 0 (data buatan terlalu halus), atau karena selalu jatuh ke jalur fallback acak. TTF jadi praktis tak bermakna.

### 2.4 Quality gate hampir selalu gagal (root cause dari F-2)

Cuplikan log container (real-time):

```
UPS ME_UPS1 Quality Gate Warning: INSUFFICIENT_DATA - Timestamp NaT/None untuk sensor battery.capacity
UPS ME_UPS2 Quality Gate Warning: INSUFFICIENT_DATA - Timestamp NaT/None untuk sensor battery.capacity
PAC ME_PAC1 Quality Gate Warning: INSUFFICIENT_DATA - Timestamp NaT/None untuk sensor compressor.status
PAC ME_PAC3 Quality Gate Warning: INSUFFICIENT_DATA - Sampel selaras tidak cukup setelah alignment: 0; minimal 10
PAC ME_PAC4 Quality Gate Warning: INSUFFICIENT_DATA - Sampel selaras tidak cukup setelah alignment: 0; minimal 10
```

`battery.capacity` dan `compressor.status` adalah **fitur wajib** (`UPS_MANDATORY`/`PAC_MANDATORY`) tetapi sumber datanya kosong/stale → gate gagal → jalur `np.random` (F-2) → nilai sintetik dikirim (F-1). **Loop setan.**

> Menariknya: ada item asli `compressor.1.status` (SNMP, terakhir `1`) dan `battery.capacity[upsHighPrecBatteryCapacity]` (SNMP, terakhir `100`) — jadi data **ada**, hanya engine menunjuk ke key yang salah/kosong.

### 2.5 Panel dashboard menunjuk item yang tidak ada

`config/aiops_facility_dashboard.json` memakai query Zabbix by **name**:

| Panel | Item yang dicari | Hasil `item.get` |
|-------|------------------|------------------|
| UPS Output Load/Temp/Voltage | `ups.output.load`, `ups.battery.temp`, `ups.battery.voltage` | **NO MATCH** (panel kosong) |
| PAC Return/Supply/Humidity | `return.temp.c`, `supply.temp.c`, `return.humidity.rh` | **NO MATCH** by name |

Item yang benar-benar ada bernama `UPS output.load`, `UPS battery.temp`, `UPS battery.voltage` (trapper), bukan `ups.output.load`. Akibatnya **panel telemetri mentah di dashboard kemungkinan besar kosong** — memperkuat kesan "belum sempurna".

Sebaliknya panel Health/TTF/Action **cocok** by name (`UPS Health Score AIOps`, `UPS Time-to-Failure (Hours)`, `UPS Policy Action Status`) — sehingga yang tampil "hidup" di dashboard justru **nilai acak/sintetik**.

---

## 3. Menjawab langsung: "apakah mesin learning-nya belum sempurna?"

Pisahkan dua hal:

1. **Model ML-nya** (IsolationForest + regresi slope). Secara metodologis ini *unsupervised anomaly + linear extrapolation* yang wajar untuk baseline. Kelemahannya nyata tetapi "normal":
   - `contamination=0.05` = asumsi proporsi outlier, **bukan** akurasi 95%.
   - TTF dari slope linear **rapuh** untuk sinyal non-linear/berisik; clamp 24–720 jam (atau 8760) menyembunyikan ketidakpastian, bukan mengukurnya.
   - Health Score = transformasi `decision_function` → **bukan probabilitas** dan **belum terkalibrasi**.

2. **Implementasi produksinya.** Inilah masalah sebenarnya: nilai yang sampai ke dashboard **bukan keluaran model atas data sensor nyata**, melainkan:
   - `np.random.uniform(65,85)` saat gate gagal (tiap siklus), dan
   - nilai sensor sintetik yang menimpa sensor asli.

**Kesimpulan:** "akurasi & toleransi belum bisa dipastikan" itu **benar**, tetapi penyebab utamanya bukan model yang kurang bagus — melainkan **pipeline yang menyuntikkan angka acak/sintetik ke jalur data**, sehingga tidak ada yang bisa divalidasi terhadap ground truth. Dokumentasi proyek sendiri sudah menandai TTF/RUL sebagai `NOT_MEASURABLE` dan melarang mengklaim akurasi — itu jujur dan tepat.

---

## 4. Rekomendasi (berurut prioritas)

### P0 — Hentikan kerusakan data & kebocoran (lakukan segera)
1. **Rotasi kredensial** `admin/<REDACTED-ZABBIX-PASSWORD>` (Zabbix) dan **revoke GitHub PAT** yang tertanam di `git remote` (`ghp_…` — sudah tergolong bocor karena ada di konfigurasi repo). Ganti ke token terbatas (read-only API user).
2. **Hentikan synthetic write**: matikan penulisan `output.load`/`battery.temp`/`battery.voltage`/`return.temp.c`/dll. dari engine. Engine hanya boleh menulis `*.health.score`, `*.ttf.hours`, `*.action.status`.
3. **Hapus `np.random` fallback**: ganti dengan `UNAVAILABLE` / *abstain* (V12 sudah begini). Jangan pernah mengarang Health Score.
4. **Bersihkan history sintetik**: nilai buatan pada key sensor asli perlu ditandai/dipisahkan agar tidak mencemari analisa & training.

### P1 — Perbaiki wiring data
5. **Betulkan item key**: `battery.capacity` → `battery.capacity[upsHighPrecBatteryCapacity]`; `compressor.status` → `compressor.1.status` (atau key SNMP yang benar); samakan dengan `item.get` yang benar-benar ada.
6. **Betulkan panel dashboard**: query by **key** (bukan `name`) atau perbaiki nama item; verifikasi via API bahwa tiap target mengembalikan data.
7. **Deploy V12 candidate** (yang sudah bebas acak & synthetic) setelah lolos uji — sebagai kandidat, dengan *staging* + *shadow* seperti prosedur Phase 87 yang sudah Anda miliki.

### P2 — Baru kemudian bicara akurasi
8. **Ground truth dulu, klaim kemudian.** TTF/RUL hanya bisa diukur bila ada label kegagalan historis. Tanpa itu, tetap `NOT_MEASURABLE` (seperti dokumentasi Anda).
9. **Ganti slope linear → model prognostik** yang memodelkan ketidakpastian (mis. regresi dengan interval kepercayaan, atau metode RUL berbasis state-of-health) dan **laporkan interval**, bukan angka tunggal.
10. **Kalibrasi Health Score** terhadap ground truth sebelum menyebutnya "probabilitas" apa pun.

Lihat `NEXT_STEPS.md` di folder ini untuk langkah operasional detail + cara verifikasi.

---

## 5. Lampiran — Peta bukti

| Artefak | Isi |
|---------|-----|
| `analysis/evidence/zabbix_item_inventory.json` | Inventaris item lengkap 7 host (name, key, type, lastvalue) |
| `analysis/evidence/provenance_map.json` | Peta key SINTETIK (trapper) vs ASLI (SNMP) untuk subsistem rawan |
| `analysis/evidence/data_volume_compare.json` / `.txt` | Perbandingan 30-d volume/rentang sintetik vs asli + distribusi health score |
| `analysis/scripts/collect_evidence.py` | Skrip **read-only** untuk mereproduksi seluruh bukti di atas |
| `analysis/FINDINGS.md` | Daftar temuan ringkas (register) |
| `analysis/NEXT_STEPS.md` | Rencana remediasi + perintah verifikasi |

Semua `analysis/` self-contained: cukup jalankan `python3 analysis/scripts/collect_evidence.py` (isi `ZABBIX_PASS`) untuk me-refresh bukti — aman, read-only.
