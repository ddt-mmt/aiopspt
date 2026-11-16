#!/usr/bin/env python3
"""
LBNL RTU — Fault Detection & Diagnostics (FDD) benchmark.

Tujuan (untuk tesis): mengukur PRESISI/SENSITIVITAS deteksi anomali terhadap
label kerusakan NYATA (dari nama file LBNL), bukan sekadar menghitung berapa
banyak titik "dianggap anomali". Ini mengubah klaim "sampel terkumpul" menjadi
metrik terukur (precision, recall, F1, false-alarm rate, confusion matrix).

Desain evaluasi (leakage-aware):
  - Train HANYA pada data baseline (sehat): X_train = potongan awal baseline.
  - Uji pada:
      * baseline sisa (sisa potongan) → label SEHAT  (false-alarm diukur di sini)
      * tiap file faulty             → label RUSAK
  - Detektor:
      * IsoForest (kontaminasi 0.05, seed 42) — engine AIOps
      * Baseline statistik Robust-Z (|z|>3.5)  — pembanding
  - Fitur: kolom numerik yang bermakna fisik (suhu, tekanan, arus, daya).
  - Unit pengujian: tiap baris waktu. Metrik dihitung pada level baris
    (persis seperti cara sistem menandai sampel per-siklus).

CATATAN DOMAIN: RTU != PAC produksi. Ini benchmark konsep; jangan pindahkan
threshold apa pun ke perangkat produksi.

Usage:
  python3 analysis/benchmark/run_lbnl_fdd_benchmark.py
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
SIM = REPO / "analysis" / "benchmark" / "data" / "lbnl_rtu" / "extracted" / "Simulated RTU"
OUT = REPO / "analysis" / "benchmark" / "results" / "lbnl_fdd"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
CONTAMINATION = 0.05
ROBUST_Z = 3.5
MAX_ROWS_PER_FILE = 6000

# Physical, fault-relevant numeric columns in the simulated schema.
FEATURES = [
    "RTU_COMP_WATT", "RTU_OA_FLOW", "RTU_OA_TEMP", "RTU_RA_TEMP",
    "RTU_REFG_COND_PRES", "RTU_REFG_COND_TEMP", "RTU_REFG_SUCT_PRES",
    "RTU_REFG_SUCT_TEMP", "RTU_SA_FAN_WATT", "RTU_SA_FLOW", "RTU_SA_TEMP",
    "RTU_TOT_WATT",
]


def load_numeric(path, max_rows=MAX_ROWS_PER_FILE):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        cols = [c for c in FEATURES if c in (r.fieldnames or [])]
        for i, row in enumerate(r):
            if i >= max_rows:
                break
            try:
                rows.append([float(row[c]) for c in cols])
            except (ValueError, TypeError, KeyError):
                continue
    return np.array(rows, dtype=float), cols


def robust_z_flags(X_train, X_test):
    med = np.median(X_train, axis=0)
    mad = np.median(np.abs(X_train - med), axis=0)
    mad[mad == 0] = 1e-9
    z = np.abs((X_test - med) / (1.4826 * mad))
    return (z.max(axis=1) > ROBUST_Z).astype(int)


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    far = fp / (fp + tn) if (fp + tn) else 0.0
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4), "false_alarm_rate": round(far, 4), "accuracy": round(acc, 4)}


def main():
    from sklearn.ensemble import IsolationForest

    baseline_files = sorted(SIM.glob("RTU_sim_baseline*.csv"))
    faulty_files = sorted([f for f in SIM.glob("*.csv") if "baseline" not in f.name])
    if not baseline_files:
        raise SystemExit(f"No baseline CSV in {SIM}")

    base, cols = load_numeric(baseline_files[0])
    if len(base) < 1000:
        raise SystemExit("baseline too small")
    split = int(len(base) * 0.5)
    X_train, X_test_normal = base[:split], base[split:]

    iso = IsolationForest(contamination=CONTAMINATION, random_state=SEED).fit(X_train)

    # ---- healthy test (false alarms) ----
    iso_normal = (iso.predict(X_test_normal) == -1).astype(int)
    rz_normal = robust_z_flags(X_train, X_test_normal)

    per_file = []
    y_true_all, y_iso_all, y_rz_all = [], [], []
    # register normal rows
    y_true_all += [0] * len(X_test_normal)
    y_iso_all += list(iso_normal)
    y_rz_all += list(rz_normal)

    for f in faulty_files:
        Xb, _ = load_numeric(f)
        if len(Xb) < 50:
            continue
        y_iso = (iso.predict(Xb) == -1).astype(int)
        y_rz = robust_z_flags(X_train, Xb)
        y_true_all += [1] * len(Xb)
        y_iso_all += list(y_iso)
        y_rz_all += list(y_rz)
        per_file.append({
            "file": f.name, "n_rows": int(len(Xb)),
            "iso_flag_rate": round(float(y_iso.mean()), 4),
            "rz_flag_rate": round(float(y_rz.mean()), 4),
        })

    result = {
        "benchmark": "LBNL RTU — Fault Detection (IsolationForest vs Robust-Z)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "protocol": {
            "train": "baseline first 50% (assumed healthy)",
            "test_normal": "baseline last 50%",
            "test_faulty": f"{len(faulty_files)} simulated fault files",
            "unit": "row (1-min sample)",
            "features": cols,
            "isolation_forest_contamination": CONTAMINATION,
            "robust_z_threshold": ROBUST_Z,
        },
        "data_source": {
            "dataset": "lbnl_rtu_fdd",
            "manifest": "analysis/benchmark/DATASET_ACQUISITION_MANIFEST.json",
            "archive_sha256": "9de1dc2e0d997d6e9f130ded3eb3c196fdf4b36005e60f9978351f44e452e5fa",
            "subset": "Simulated RTU (25 files: 1 baseline + 24 faulty)",
        },
        "metrics_isolation_forest": metrics(y_true_all, y_iso_all),
        "metrics_robust_z_baseline": metrics(y_true_all, y_rz_all),
        "per_fault_file": per_file,
    }
    (OUT / "lbnl_fdd_metrics.json").write_text(json.dumps(result, indent=2))

    report = [
        "# LBNL RTU — Fault Detection Benchmark Results",
        f"Generated: {result['generated_utc']}",
        f"Train: {result['protocol']['train']}",
        f"Features: {', '.join(cols)}",
        "",
        "## Isolation Forest (engine AIOps)",
        f"- precision={result['metrics_isolation_forest']['precision']}  "
        f"recall={result['metrics_isolation_forest']['recall']}  "
        f"f1={result['metrics_isolation_forest']['f1']}  "
        f"false_alarm_rate={result['metrics_isolation_forest']['false_alarm_rate']}",
        f"- confusion: {result['metrics_isolation_forest']}",
        "",
        "## Robust-Z statistical baseline",
        f"- precision={result['metrics_robust_z_baseline']['precision']}  "
        f"recall={result['metrics_robust_z_baseline']['recall']}  "
        f"f1={result['metrics_robust_z_baseline']['f1']}  "
        f"false_alarm_rate={result['metrics_robust_z_baseline']['false_alarm_rate']}",
        f"- confusion: {result['metrics_robust_z_baseline']}",
        "",
        "## Per-fault detection rate (Isolation Forest)",
        "",
        "| Fault file | rows | ISO flag rate | RobZ flag rate |",
        "|---|---|---|---|",
    ]
    for p in per_file:
        report.append(f"| {p['file']} | {p['n_rows']} | {p['iso_flag_rate']} | {p['rz_flag_rate']} |")
    report += [
        "",
        "## Catatan interpretasi",
        "- Recall = fraksi baris faulty yang benar ditandai; precision = fraksi tanda yang benar.",
        "- False-alarm-rate diukur pada data SEHAT yang ditahan (held-out baseline).",
        "- RTU != PAC produksi: ini benchmark konsep. Jangan pindahkan threshold ke produksi.",
    ]
    (OUT / "LBNL_FDD_REPORT.md").write_text("\n".join(report))

    print(json.dumps({
        "isolation_forest": result["metrics_isolation_forest"],
        "robust_z": result["metrics_robust_z_baseline"],
    }, indent=2))
    print(f"-> {OUT/'lbnl_fdd_metrics.json'}")


if __name__ == "__main__":
    main()
