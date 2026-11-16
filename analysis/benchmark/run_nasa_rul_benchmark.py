#!/usr/bin/env python3
"""
NASA PCoE Battery #5 — RUL (Remaining Useful Life) benchmark.

Tujuan (untuk tesis): mengubah klaim "akurasi NOT_MEASURABLE" menjadi
HASIL TERUKUR dengan ground truth nyata. Setiap sel baterai NASA punya
degradasi kapasitas per siklus; End-of-Life (EOL) didefinisikan sebagai
kapasitas turun ke 70% dari kapasitas rated 2.0 Ah = 1.4 Ah (ambang
standar literatur prognostik). Ini memberi LABEL sebenarnya.

Protokol evaluasi (leakage-aware, online-style):
  - Untuk tiap baterai, ambil deret kapasitas vs indeks siklus.
  - Tetapkan EOL aktual (siklus saat kapasitas pertama <= 1.4 Ah).
  - Untuk tiap "titik prediksi" pada fraksi umur p ∈ {0.5, 0.6, 0.7, 0.8}:
      * latih model HANYA dari siklus yang sudah teramati (<= titik itu)
      * prediksi siklus EOL (dan RUL = EOL_pred - current_cycle)
      * bandingkan dengan EOL aktual → error.
  - Laporkan MAE, RMSE, MAPE, dan distribusi error TANPA menyentuh data masa depan.

Model yang dibandingkan (baseline utk tesis):
  - naive  : RUL = 0 (tebak "sudah EOL")           [baseline bawah]
  - linear : ekstrapolasi regresi linear kapasitas [baseline slope, seperti engine]
  - sqrt   : model degradasi sqrt-fit (umum di literatur baterai)
  - exp    : model degradasi eksponensial

Output: metrics JSON + CSV per-prediksi + laporan Markdown.

Usage:
  python3 analysis/benchmark/run_nasa_rul_benchmark.py
"""
import csv
import json
import math
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.io

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "analysis" / "benchmark" / "data" / "nasa_battery_5" / "mat"
OUT = REPO / "analysis" / "benchmark" / "results" / "nasa_rul"
OUT.mkdir(parents=True, exist_ok=True)

RATED_AH = 2.0
EOL_FRACTION = 0.70
EOL_AH = RATED_AH * EOL_FRACTION          # 1.4 Ah
PREDICT_AT = [0.5, 0.6, 0.7, 0.8]          # fraction of observed life when we predict
RANDOM_SEED = 42


def load_capacity_series(mat_path):
    """Return (cycle_index, capacity_Ah) arrays for discharge cycles."""
    m = scipy.io.loadmat(str(mat_path))
    key = [k for k in m if not k.startswith("__")][0]
    cyc = m[key]["cycle"][0, 0]
    types = [t[0] for t in cyc["type"].ravel()]
    caps = []
    for i, t in enumerate(types):
        if t != "discharge":
            continue
        try:
            dd = cyc[0, i]["data"][0, 0]
            caps.append(float(dd["Capacity"][0, 0]))
        except Exception:
            caps.append(np.nan)
    caps = np.array(caps)
    idx = np.arange(len(caps))
    ok = np.isfinite(caps)
    return idx[ok], caps[ok]


def eol_cycle(idx, caps):
    """First cycle index where capacity <= EOL_AH. None if never reached."""
    below = np.where(caps <= EOL_AH)[0]
    if len(below) == 0:
        return None
    return int(idx[below[0]])


def model_linear(c_idx, c_cap):
    """Fit capacity = a*cycle + b; solve cycle where capacity = EOL_AH."""
    a, b = np.polyfit(c_idx, c_cap, 1)
    if a >= 0:
        return None
    x = (EOL_AH - b) / a
    return float(x)


def model_sqrt(c_idx, c_cap):
    """Fit capacity = a*sqrt(cycle)+b (battery degradation literature)."""
    s = np.sqrt(np.clip(c_idx, 0, None))
    a, b = np.polyfit(s, c_cap, 1)
    if a >= 0:
        return None
    # a*sqrt(x)+b = EOL → sqrt(x) = (EOL-b)/a
    val = (EOL_AH - b) / a
    if val < 0:
        return None
    return float(val ** 2)


def model_exp(c_idx, c_cap):
    """Fit capacity = a*exp(b*cycle)+c; solve numerically for EOL_AH."""
    # fit log-linear on (cap - floor) for stability
    floor = float(np.min(c_cap)) * 0.5
    y = np.clip(c_cap - floor, 1e-6, None)
    b, loga = np.polyfit(c_idx, np.log(y), 1)
    a = math.exp(loga)
    if b >= 0:
        return None
    # a*exp(b*x)+floor = EOL_AH → exp(b*x) = (EOL_AH-floor)/a
    ratio = (EOL_AH - floor) / a
    if ratio <= 0:
        return None
    x = math.log(ratio) / b
    return float(x)


MODELS = {"naive": None, "linear": model_linear, "sqrt": model_sqrt, "exp": model_exp}


def evaluate():
    mat_files = sorted(DATA.glob("*.mat"))
    if not mat_files:
        raise SystemExit(f"No .mat files in {DATA}")

    rows = []
    per_battery = []
    for mat in mat_files:
        idx, caps = load_capacity_series(mat)
        if len(idx) < 20:
            continue
        eol = eol_cycle(idx, caps)
        bid = mat.stem
        # Validity: must START healthy (first capacity above EOL) — filters out
        # randomized-protocol cells that begin already-degraded (EOL at cycle 0).
        valid_start = float(caps[0]) > EOL_AH
        per_battery.append({
            "battery": bid, "n_discharge_cycles": int(len(idx)),
            "cap_first": round(float(caps[0]), 4), "cap_last": round(float(caps[-1]), 4),
            "eol_cycle": eol, "reached_eol": eol is not None,
            "valid_for_rul": bool(valid_start and eol is not None),
        })
        if eol is None or not valid_start:
            continue  # excluded from RUL error stats (never EOL, or started degraded)

        for frac in PREDICT_AT:
            cutoff_cycle = int(eol * frac)
            mask = idx <= cutoff_cycle
            if mask.sum() < 10:
                continue
            c_idx = idx[mask]
            c_cap = caps[mask]
            actual_rul = eol - int(c_idx[-1])

            for name, fn in MODELS.items():
                if name == "naive":
                    pred_eol = int(c_idx[-1])       # assume already at EOL
                else:
                    pe = fn(c_idx.astype(float), c_cap.astype(float))
                    pred_eol = pe if pe is not None else int(c_idx[-1])
                pred_rul = pred_eol - int(c_idx[-1])
                err = pred_rul - actual_rul
                rows.append({
                    "battery": bid, "predict_at_frac": frac,
                    "cutoff_cycle": int(c_idx[-1]), "actual_eol": eol,
                    "actual_rul": actual_rul, "model": name,
                    "pred_eol": round(float(pred_eol), 2),
                    "pred_rul": round(float(pred_rul), 2),
                    "error": round(float(err), 2),
                    "abs_error": round(abs(float(err)), 2),
                    "pct_error": round(abs(float(err)) / max(actual_rul, 1) * 100, 2),
                })

    def _agg(subset_rows):
        out = {}
        for name in MODELS:
            errs = np.array([r["error"] for r in subset_rows if r["model"] == name], dtype=float)
            if len(errs) == 0:
                continue
            ae = np.abs(errs)
            out[name] = {
                "n_predictions": int(len(errs)),
                "MAE_cycles": round(float(ae.mean()), 3),
                "RMSE_cycles": round(float(np.sqrt((errs ** 2).mean())), 3),
                "bias_mean_error": round(float(errs.mean()), 3),
                "median_abs_error": round(float(np.median(ae)), 3),
                "max_abs_error": round(float(ae.max()), 3),
                "p90_abs_error": round(float(np.percentile(ae, 90)), 3),
            }
        return out

    CANONICAL = {"B0005", "B0006", "B0007", "B0018"}
    metrics = _agg(rows)                                  # all valid cells that reached EOL
    metrics_canonical = _agg([r for r in rows if r["battery"] in CANONICAL])

    result = {
        "benchmark": "NASA PCoE Battery #5 — RUL regression",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "protocol": {
            "eol_definition_Ah": EOL_AH,
            "eol_fraction_of_rated": EOL_FRACTION,
            "rated_Ah": RATED_AH,
            "predict_at_life_fractions": PREDICT_AT,
            "leakage_control": "model trained only on cycles <= prediction point; future cycles never used",
            "unit": "discharge cycles",
        },
        "data_source": {
            "dataset": "nasa_pcoe_battery_5",
            "manifest": "analysis/benchmark/DATASET_ACQUISITION_MANIFEST.json",
            "archive_sha256": "82302a7db4fc1b34e0b6676326610438d43b816bdf11a69d1d012a464ef2f92e",
        },
        "validity_filter": {
            "rule": "battery is valid for RUL if its FIRST discharge capacity > EOL_Ah (i.e., it starts healthy) and it later reaches EOL",
            "reason": "Cells B0025-B0056 include randomized/alternate protocols that begin below rated EOL; counting them makes EOL fire at cycle 0 and corrupts the metric. Excluded from headline metrics.",
            "canonical_subset": ["B0005", "B0006", "B0007", "B0018"],
            "canonical_note": "These four are the cells used in the majority of published NASA RUL studies; reported separately for literature comparability.",
        },
        "batteries_analyzed": per_battery,
        "metrics_by_model": metrics,
        "metrics_by_model_canonical_subset": metrics_canonical,
    }

    (OUT / "nasa_rul_metrics.json").write_text(json.dumps(result, indent=2))

    # per-prediction CSV
    with open(OUT / "nasa_rul_predictions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # short report
    report = [
        "# NASA Battery #5 — RUL Benchmark Results",
        f"Generated: {result['generated_utc']}",
        f"EOL threshold: {EOL_AH} Ah ({int(EOL_FRACTION*100)}% of {RATED_AH} Ah rated)",
        f"Predict at life fractions: {PREDICT_AT}",
        f"Leakage control: {result['protocol']['leakage_control']}",
        "",
        f"Batteries valid for RUL (started healthy and reached EOL): "
        f"{sum(1 for b in per_battery if b['valid_for_rul'])} / {len(per_battery)}",
        "",
        "## Metrics — ALL valid cells (unit: discharge cycles)",
        "",
        "| Model | n | MAE | RMSE | bias | median | p90 | max |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, m in metrics.items():
        report.append(f"| {name} | {m['n_predictions']} | {m['MAE_cycles']} | {m['RMSE_cycles']} | "
                      f"{m['bias_mean_error']} | {m['median_abs_error']} | {m['p90_abs_error']} | {m['max_abs_error']} |")
    report += [
        "",
        "## Metrics — CANONICAL subset (B0005/B0006/B0007/B0018, literature-standard cells)",
        "",
        "| Model | n | MAE | RMSE | bias | median | p90 | max |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, m in metrics_canonical.items():
        report.append(f"| {name} | {m['n_predictions']} | {m['MAE_cycles']} | {m['RMSE_cycles']} | "
                      f"{m['bias_mean_error']} | {m['median_abs_error']} | {m['p90_abs_error']} | {m['max_abs_error']} |")
    report += [
        "",
        "## Catatan interpretasi",
        "- Angka MAE/RMSE di atas adalah error jumlah SIKLUS, bukan hari. Konversi ke waktu",
        "  bergantung pada pola pemakaian; NASA menguji dengan banyak siklus cepat.",
        "- 'naive' adalah baseline bawah (selalu menebak RUL=0); model berguna harus jauh lebih baik.",
        "- Hasil ini TIDAK boleh diklaim sebagai akurasi UPS produksi: kimia/sel/kondisi berbeda.",
        "  Ini benchmark metodologi prognostik, bukan replika baterai UPS data center.",
    ]
    (OUT / "NASA_RUL_REPORT.md").write_text("\n".join(report))

    # print summary
    print(json.dumps(metrics, indent=2))
    print(f"\n-> {OUT/'nasa_rul_metrics.json'}")
    return result


if __name__ == "__main__":
    evaluate()
