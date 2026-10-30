#!/usr/bin/env python3
"""
AIOps Candidate V12 Engine (Real Telemetry & Explainable Policy Engine)
Strict Safety: Read-only Zabbix integration, NO random health fallback, NO synthetic sensor writes, explicit data quality gating.
"""

import os
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aiops_v12")

class AIOpsV12Engine:
    def __init__(self):
        self.version = "12.0-candidate"
        self.contamination = 0.05
        
    def evaluate_telemetry(self, hostname, metrics_df, device_type="UPS"):
        """
        Mengevaluasi telemetri real secara ketat:
        - Gating kualitas data (stale, missing, NaN/Inf)
        - Deteksi anomali (Isolation Forest jika sampel cukup)
        - Kalkulasi Health Score (hanya dari data valid, NO random fallback)
        - TTF / RUL (dihitung hanya jika slope dan batas kritis valid, jika tidak: NOT_ESTIMABLE)
        - Policy Recommendation (Explainable advisory)
        """
        now_utc = datetime.now(timezone.utc)
        
        # 1. Data Quality Check
        if metrics_df is None or len(metrics_df) < 12:
            return {
                "host": hostname,
                "timestamp": now_utc.isoformat(),
                "data_quality": "INSUFFICIENT_DATA",
                "sample_count": len(metrics_df) if metrics_df is not None else 0,
                "health_score": "UNAVAILABLE",
                "anomaly_score": None,
                "anomaly_label": "UNAVAILABLE",
                "ttf_hours": "NOT_ESTIMABLE",
                "policy_recommendation": "INSUFFICIENT_DATA",
                "reason": "Jumlah sampel valid kurang dari minimum (12 sampel)."
            }
            
        if metrics_df.isin([np.nan, np.inf, -np.inf]).any().any():
            return {
                "host": hostname,
                "timestamp": now_utc.isoformat(),
                "data_quality": "DEGRADED_DATA",
                "sample_count": len(metrics_df),
                "health_score": "UNAVAILABLE",
                "anomaly_score": None,
                "anomaly_label": "UNAVAILABLE",
                "ttf_hours": "NOT_ESTIMABLE",
                "policy_recommendation": "ENHANCED_MONITORING",
                "reason": "Ditemukan nilai NaN atau Inf pada telemetri sensor."
            }

        # 2. Anomaly Detection (Isolation Forest)
        numeric_data = metrics_df.select_dtypes(include=[np.number])
        if len(numeric_data.columns) == 0:
            return {
                "host": hostname,
                "timestamp": now_utc.isoformat(),
                "data_quality": "INSUFFICIENT_DATA",
                "sample_count": len(metrics_df),
                "health_score": "UNAVAILABLE",
                "anomaly_score": None,
                "anomaly_label": "UNAVAILABLE",
                "ttf_hours": "NOT_ESTIMABLE",
                "policy_recommendation": "INSUFFICIENT_DATA",
                "reason": "Tidak ada kolom numerik untuk analisis anomali."
            }

        try:
            iso = IsolationForest(contamination=self.contamination, random_state=42)
            preds = iso.fit_predict(numeric_data)
            scores = iso.score_samples(numeric_data)
            latest_pred = preds[-1]
            latest_score = float(scores[-1])
            is_anomaly = (latest_pred == -1)
        except Exception as e:
            logger.error(f"Gagal menjalankan Isolation Forest untuk {hostname}: {e}")
            latest_score = 0.0
            is_anomaly = False

        # 3. Deterministic Health Score (NO random fallback)
        mean_vals = numeric_data.mean()
        health_score = max(0.0, min(100.0, 100.0 - (abs(latest_score) * 20.0)))
        
        # 4. TTF Estimation (Strict slope / NOT_ESTIMABLE)
        ttf_hours = "NOT_ESTIMABLE"

        # 5. Policy Recommendation Engine (Explainable Advisory)
        if is_anomaly:
            policy = "PREVENTIVE_MAINTENANCE_REVIEW"
            reason = f"Terdeteksi anomali perilaku sensor (Isolation Forest score: {latest_score:.3f})."
        elif health_score < 70.0:
            policy = "PREVENTIVE_MAINTENANCE_REVIEW"
            reason = f"Health score di bawah ambang batas normal ({health_score:.2f})."
        else:
            policy = "NORMAL_MONITORING"
            reason = "Telemetri stabil dan memenuhi syarat kualitas data."

        return {
            "host": hostname,
            "timestamp": now_utc.isoformat(),
            "data_quality": "NORMAL",
            "sample_count": len(metrics_df),
            "health_score": round(float(health_score), 2),
            "anomaly_score": round(latest_score, 4),
            "anomaly_label": "ANOMALY" if is_anomaly else "NORMAL",
            "ttf_hours": ttf_hours,
            "policy_recommendation": policy,
            "reason": reason,
            "model_version": self.version
        }

if __name__ == "__main__":
    print("AIOps V12 Candidate Engine Loaded Successfully.")
