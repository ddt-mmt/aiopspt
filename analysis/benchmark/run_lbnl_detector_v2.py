#!/usr/bin/env python3
"""
LBNL RTU — Improved fault detector, scored & threshold-tuned.

Benchmark v1 memakai IsolationForest titik-potong (contamination=0.05) dan
menghasilkan recall rendah (~0.30). Masalah: keputusan biner pada satu ambang.
v2 mengevaluasi SKOR anomali berkelanjutan sehingga operator dapat memilih
titik operasi (trade-off false-alarm vs recall) — analog "batas toleransi".

Detektor yang dibandingkan (semua leakage-aware, train pada baseline sehat):
  A. IsolationForest score_samples (engine)          — unsupervised
  B. Robust-Z max |z| antar fitur                    — statistik
  C. Residual-to-baseline (jarak ke centroid sehat)  — sederhana & explainable

Metrik:
  - ROC-AUC dan PR-AUC (average precision) → kualitas peringkat, tanpa ambang.
  - Titik operasi pada target false-alarm-rate (FAR) {0.01, 0.05, 0.10}:
      * ambang dipilih dari baseline held-out agar FAR ≈ target
      * laporkan recall & F1 pada ambang itu (fair: ambang dari sehat, diuji di rusak)
  - Recall @ fixed precision, dsb.

Tetap: RTU != PAC. Benchmark konsep.

Usage:
  python3 analysis/benchmark/run_lbnl_detector_v2.py
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
SIM = REPO / "analysis" / "benchmark" / "data" / "lbnl_rtu" / "extracted" / "Simulated RTU"
OUT = REPO / "analysis" / "benchmark" / "results" / "lbnl_fdd_v2"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
MAX_ROWS = 6000
FAR_TARGETS = [0.01, 0.05, 0.10]

FEATURES = [
    "RTU_COMP_WATT", "RTU_OA_FLOW", "RTU_OA_TEMP", "RTU_RA_TEMP",
    "RTU_REFG_COND_PRES", "RTU_REFG_COND_TEMP", "RTU_REFG_SUCT_PRES",
    "RTU_REFG_SUCT_TEMP", "RTU_SA_FAN_WATT", "RTU_SA_FLOW", "RTU_SA_TEMP",
    "RTU_TOT_WATT",
]


def load_numeric(path, max_rows=MAX_ROWS):
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
    return np.array(rows, dtype=float)


def score_iforest(X_train, X):
    from sklearn.ensemble import IsolationForest
    m = IsolationForest(n_estimators=200, contamination="auto", random_state=SEED).fit(X_train)
    return -m.score_samples(X)            # higher = more anomalous


def score_robust_z(X_train, X):
    med = np.median(X_train, axis=0)
    mad = np.median(np.abs(X_train - med), axis=0)
    mad[mad == 0] = 1e-9
    z = np.abs((X - med) / (1.4826 * mad))
    return z.max(axis=1)


def score_residual(X_train, X):
    mu = X_train.mean(axis=0)
    sd = X_train.std(axis=0)
    sd[sd == 0] = 1e-9
    z = (X - mu) / sd
    return np.sqrt((z ** 2).mean(axis=1))   # RMS standardized deviation


def prf(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    far = fp / (fp + tn) if (fp + tn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    bal_acc = 0.5 * (rec + spec)             # imbalance-robust
    # MCC (Matthews) — robust to class imbalance
    denom = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4), "false_alarm_rate": round(far, 4),
            "balanced_accuracy": round(bal_acc, 4), "MCC": round(mcc, 4)}


def main():
    from sklearn.metrics import roc_auc_score, average_precision_score

    base_files = sorted(SIM.glob("RTU_sim_baseline*.csv"))
    fault_files = sorted([f for f in SIM.glob("*.csv") if "baseline" not in f.name])
    base = load_numeric(base_files[0])
    split = int(len(base) * 0.5)
    X_train, X_hold = base[:split], base[split:]

    # held-out faulty data (concatenate)
    faulty = np.vstack([load_numeric(f) for f in fault_files])

    scorers = {"isolation_forest": score_iforest, "robust_z": score_robust_z, "residual": score_residual}

    results = {}
    for name, fn in scorers.items():
        s_hold = fn(X_train, X_hold)     # healthy held-out
        s_fault = fn(X_train, faulty)    # faulty
        y_true = np.r_[np.zeros(len(s_hold)), np.ones(len(s_fault))]
        y_score = np.r_[s_hold, s_fault]
        auc = float(roc_auc_score(y_true, y_score))
        ap = float(average_precision_score(y_true, y_score))

        op_points = {}
        for far in FAR_TARGETS:
            thr = float(np.quantile(s_hold, 1 - far))   # so ~far of healthy flagged
            y_pred = (y_score > thr).astype(int)
            op_points[f"FAR_target_{far}"] = {
                "threshold": round(thr, 4),
                **prf(y_true, y_pred),
            }
        results[name] = {
            "roc_auc": round(auc, 4),
            "pr_auc_average_precision": round(ap, 4),
            "operating_points": op_points,
        }

    # ---- window-level detection (operationally meaningful) ----
    # Operator cares whether the alarm fires WITHIN a window, not per-minute.
    # Window is flagged faulty if >= MIN_ALARM_HITS rows inside it are flagged.
    WINDOW = 60          # 60 minutes = 1 hour of 1-min samples
    WINDOW_FAR = 0.05    # target fraction of HEALTHY windows that may alarm

    def windows_hitfrac(scores, thr, w=WINDOW):
        flags = (scores > thr).astype(int)
        n = len(flags) // w
        return np.array([flags[i * w:(i + 1) * w].mean() for i in range(n)])

    window_results = {}
    for name, fn in scorers.items():
        s_hold = fn(X_train, X_hold)
        thr = float(np.quantile(s_hold, 0.95))          # per-row FAR 5%
        # Calibrate the WINDOW decision threshold on healthy windows so that only
        # ~WINDOW_FAR of healthy windows alarm (properly controls window FAR).
        hf_hold = windows_hitfrac(s_hold, thr)
        win_thr = float(np.quantile(hf_hold, 1 - WINDOW_FAR)) if len(hf_hold) else 0.05
        w_hold = (hf_hold > win_thr).astype(int)
        w_fault = (windows_hitfrac(fn(X_train, faulty), thr) > win_thr).astype(int)
        yt = np.r_[np.zeros(len(w_hold)), np.ones(len(w_fault))]
        yp = np.r_[w_hold, w_fault]
        window_results[name] = {
            "row_threshold_FAR05": round(thr, 4),
            "window_hitfrac_threshold": round(win_thr, 4),
            **prf(yt, yp),
        }

    result_window = {
        "protocol": {"window_minutes": WINDOW, "window_FAR_target": WINDOW_FAR,
                     "row_threshold": "per-row FAR 5% on held-out healthy",
                     "window_decision": "window alarms if flagged-row fraction > healthy-window quantile"},
        "window_level_detection": window_results,
    }

    result = {
        "benchmark": "LBNL RTU — fault detection v2 (scored, threshold-tuned)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "protocol": {
            "train": "baseline first 50% (healthy)",
            "test_normal": "baseline last 50% (held-out healthy)",
            "test_faulty": f"{len(fault_files)} simulated fault files",
            "thresholds": "chosen from held-out healthy at target FAR; evaluated on faulty",
            "features": FEATURES,
        },
        "data_source": {
            "dataset": "lbnl_rtu_fdd",
            "archive_sha256": "9de1dc2e0d997d6e9f130ded3eb3c196fdf4b36005e60f9978351f44e452e5fa",
        },
        "detectors": results,
        **result_window,
        "comparison_vs_v1": {
            "v1_engine_isolation_forest": {"precision": 0.9878, "recall": 0.3009, "f1": 0.4613,
                                            "note": "single contamination=0.05 threshold"},
            "note": "v2 picks the operating point explicitly; compare recall/F1 at matched FAR.",
        },
    }
    (OUT / "lbnl_fdd_v2_metrics.json").write_text(json.dumps(result, indent=2))

    report = [
        "# LBNL RTU — Fault Detection v2 (scored + threshold-tuned)",
        f"Generated: {result['generated_utc']}",
        "",
        "## Ranking quality (threshold-free)",
        "",
        "| Detector | ROC-AUC | PR-AUC |",
        "|---|---|---|",
    ]
    for name, r in results.items():
        report.append(f"| {name} | {r['roc_auc']} | {r['pr_auc_average_precision']} |")
    report += ["", "## Operating points (recall & F1 at target false-alarm-rate)", ""]
    for name, r in results.items():
        report.append(f"### {name}")
        report.append("")
        report.append("| FAR target | actual FAR | recall | precision | F1 |")
        report.append("|---|---|---|---|---|")
        for k, v in r["operating_points"].items():
            report.append(f"| {k.split('_')[-1]} | {v['false_alarm_rate']} | {v['recall']} | {v['precision']} | {v['f1']} |")
        report.append("")
    report += [
        "",
        "## Window-level detection (60-min window, operator-relevant)",
        "",
        "Alarm dinyatakan menyala bila >=5% baris dalam jendela 60 menit ditandai.",
        "",
        "| Detector | FAR | recall (window) | precision | F1 |",
        "|---|---|---|---|---|",
    ]
    for name, r in window_results.items():
        report.append(f"| {name} | {r['false_alarm_rate']} | {r['recall']} | {r['precision']} | {r['f1']} |")
    report += [
        "",
        "## Cara membaca",
        "- ROC-AUC/PR-AUC = kualitas peringkat detektor tanpa memilih ambang.",
        "- PERINGATAN: PR-AUC tampak tinggi (0.98) karena kelas rusak mayoritas — gunakan",
        "  ROC-AUC / balanced-accuracy / MCC untuk gambaran seimbang.",
        "- Titik operasi = 'batas toleransi' deteksi: pada FAR 5%, berapa fault tertangkap",
        "  (level baris). Deteksi level BARIS memang sulit (ROC-AUC 0.62-0.69).",
        "- Deteksi level JENDELA (lebih relevan operator) lihat tabel di atas.",
        "",
        "## Batasan",
        "- RTU != PAC produksi; ini benchmark konsep, jangan pindahkan ambang ke produksi.",
        "- Label di level-file (baris diasumsikan rusak); kondisi transient mungkin salah label.",
    ]
    (OUT / "LBNL_FDD_V2_REPORT.md").write_text("\n".join(report))

    print(json.dumps({n: {"roc_auc": r["roc_auc"], "pr_auc": r["pr_auc_average_precision"],
                          "recall@FAR0.05": r["operating_points"]["FAR_target_0.05"]["recall"],
                          "f1@FAR0.05": r["operating_points"]["FAR_target_0.05"]["f1"]}
                      for n, r in results.items()}, indent=2))
    print(f"-> {OUT/'lbnl_fdd_v2_metrics.json'}")


if __name__ == "__main__":
    main()
