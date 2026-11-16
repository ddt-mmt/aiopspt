# NEXT_STEPS — Rencana Remediasi AIOps

Urutan: **P0 aman-kan dulu → P1 perbaiki wiring → P2 baru ukur akurasi.**
Setiap langkah disertai perintah **verifikasi read-only** agar dapat dibuktikan sebelum/sesudah.

> ⚠️ Semua perintah di bawah bersifat READ-ONLY sampai langkah yang ditandai **[WRITE]**.
> Jangan jalankan langkah [WRITE] pada dashboard/Zabbix produksi tanpa persetujuan (ikuti
> prosedur otorisasi Phase 87 yang sudah ada, mis. `production_change_authorization`).

---

## P0 — Amankan & hentikan pencemaran data (SEGERA, tanpa deployment)

### 0.1 Rotasi kredensial & rahasia
- **[WRITE di Zabbix/GitHub, bukan di kode]** Ganti password `admin` Zabbix (`<REDACTED-ZABBIX-PASSWORD>`).
- Revoke GitHub PAT `ghp_…` pada `git remote -v`; buat ulang PAT scoped (repo-only) atau pakai SSH.
- Pindahkan kredensial ke env / secret manager; hapus literal `<REDACTED-ZABBIX-PASSWORD>` dari file ter-track.
- Opsional: `git filter-repo` untuk purge dari history (koordinasi dgn pemilik repo).

**Verifikasi:**
```bash
git grep -nE '<REDACTED-ZABBIX-PASSWORD>|ghp_[A-Za-z0-9]{20,}' HEAD || echo "BERSIH"
```

### 0.2 Hentikan synthetic write + fallback acak (di kode, tanpa langsung prod)
Ubah `src/script_aiops.py` agar:
- **Tidak** mengirim `output.load`/`battery.temp`/`battery.voltage`/`return.temp.c`/`supply.temp.c`/`return.humidity.rh`/`evaporator.fan.speed`/`compressor.status`.
- Saat gate gagal: kirim `UNAVAILABLE` (atau nilai sentinel) untuk health/ttf/action — **bukan** `np.random`.

Sudah tersedia sebagai referensi: `src/script_aiops_v12_candidate.py` (`NO random health fallback, NO synthetic sensor writes`).

**Verifikasi (tanpa deploy):** jalankan test offline
```bash
python3 tests/test_v11_repaired.py      # regresi baseline
# jalankan sanity kandidat V12 (offline)
python3 -c "import importlib.util,types; spec=importlib.util.spec_from_file_location('v12','src/script_aiops_v12_candidate.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('V12 load OK')"
```

### 0.3 Pisahkan / tandai history sintetik
Nilai lama pada key sensor (output.load dll.) yang berasal dari trapper engine perlu **dipisahkan** dari nilai SNMP agar tidak mencemari analisa. Tidak perlu hapus; cukup tandai sumbernya.

**Verifikasi:** item trapper vs SNMP tetap terpisah (lihat `analysis/evidence/data_volume_compare.json`).

---

## P1 — Perbaiki wiring data (staging dulu, lalu produksi)

### 1.1 Betulkan item key mandatory
- UPS: `battery.capacity` → `battery.capacity[upsHighPrecBatteryCapacity]`
- UPS: `battery.runtime_remaining` → `battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]`
- PAC: `compressor.status` → `compressor.1.status` (atau key SNMP yang valid)
- Pastikan `output.load`, `battery.voltage`, `battery.temp` engine baca dari `[SNMP]`, bukan trapper.

**Verifikasi:**
```bash
ZABBIX_PASS=... python3 analysis/scripts/collect_evidence.py
# lalu cek: tiap key mandatory punya n>0 dan lastclock segar di
# analysis/evidence/zabbix_item_inventory.json
```

### 1.2 Betulkan panel dashboard
- Ganti query by `name` → by `key_` (plugin Zabbix mendukung field `item`), atau samakan `name`.
- Minimal: `ups.output.load` (→ `UPS output.load`), `ups.battery.temp`, `ups.battery.voltage`; `return.temp.c`, `supply.temp.c`, `return.humidity.rh`.

**Verifikasi:** untuk tiap target panel, `item.get` with `filter.name`/`key_` harus mengembalikan tepat 1 match (lihat §2.5 README).

### 1.3 Deploy kandidat V12 (setelah 1.1 & 1.2 hijau) **[WRITE]**
- Bangun image dgn `src/script_aiops_v12_candidate.py`, jalankan mode **shadow** dulu.
- Bandingkan output V12 vs V11 selama periode shadow; bila bersih, promosikan.
- Ikuti gate otorisasi produksi yang sudah ada (Phase 87.x) — jangan bypass.

**Verifikasi:**
```bash
docker ps --format '{{.Names}} {{.Image}}'
docker logs <container> 2>&1 | tail -30   # cari 'UNAVAILABLE', BUKAN angka acak
```

---

## P2 — Baru kemudian: ukur & klaim akurasi

### 2.1 Ground truth
- Kumpulkan catatan insiden/kegagalan perangkat (UPS/PAC) — tanpa ini TTF/RUL tetap `NOT_MEASURABLE`.

### 2.2 Model prognostik dengan ketidakpastian
- Ganti slope linear tunggal → regresi dengan **interval prediksi** (bootstrap/quantile), atau SOH-based RUL.
- Laporkan **interval + asumsi**, bukan satu angka.

### 2.3 Kalibrasi & metrik
- Kalibrasi Health Score terhadap ground truth.
- Laporkan precision/recall/F1/FAR (deteksi) dan MAE/RMSE + distribusi error (prognostik) bila label valid ada.
- Ikat tiap metrik ke: versi model, checksum dataset, split, seed, timestamp (lihat `docs/ML_WORKFLOW_AND_ACCURACY.md` §5F).

---

## Checklist cepat

- [ ] P0.1 Revoke PAT + rotasi password + purge literal dari repo
- [ ] P0.2 Hapus synthetic write & `np.random` (ujicoba kode V12)
- [ ] P0.3 Tandai/pisahkan history sintetik
- [ ] P1.1 Betulkan key mandatory (UPS battery.capacity, PAC compressor.status)
- [ ] P1.2 Betulkan panel dashboard (query by key)
- [ ] P1.3 Deploy V12 via shadow → promote (gate otorisasi)
- [ ] P2.1 Ground truth insiden
- [ ] P2.2 Model + interval ketidakpastian
- [ ] P2.3 Kalibrasi & metrik terikat checksum

---

## Perintah verifikasi ringkas (read-only)

```bash
# 1) Rahasia masih bocor di repo?
git grep -nE '<REDACTED-ZABBIX-PASSWORD>|ghp_[A-Za-z0-9]{20,}' HEAD || echo "BERSIH"

# 2) Refresh semua bukti (read-only ke Zabbix)
ZABBIX_PASS=... python3 analysis/scripts/collect_evidence.py

# 3) Container masih menjalankan script lama (V11)?
docker inspect aiops_predictor_hpc --format '{{.Config.Cmd}}'
docker exec aiops_predictor_hpc md5sum /app/script_aiops.py   # banding dengan src/

# 4) Cek dashboard targets (true/1 match) — lihat analysis/README.md §2.5
```
