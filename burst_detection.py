"""
burst_detection.py
==================
MFT Temporal Modification Burst Analysis & Isolation Forest v2
Analyzes rapid modification bursts across 1-second and 60-second windows
to detect automated bulk timestomping, ransomware encryption bursts, or batch destruction.
"""

import json
import os
import pickle
import datetime
from collections import Counter
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import OUT_DIR, FEAT_DIR, MODEL_DIR, CONTAMINATION


def run_burst_detection():
    mft_path = os.path.join(OUT_DIR, "mft", "mft_records.json")
    if not os.path.exists(mft_path):
        print(f"[!] MFT records not found at {mft_path}. Skipping burst detection.")
        return False

    with open(mft_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        print("[!] MFT records empty. Skipping burst detection.")
        return False

    df = pd.DataFrame(records)
    if "type" not in df.columns or "m_time" not in df.columns:
        print("[!] Unexpected MFT records schema. Skipping burst detection.")
        return False

    df = df[(df["type"] == "file") & (df["m_time"] > 0)].copy()
    if df.empty:
        print("[!] No valid file entries with m_time > 0 found. Skipping burst detection.")
        return False

    df.reset_index(drop=True, inplace=True)
    df["m_time"] = pd.to_numeric(df["m_time"], errors="coerce").fillna(0).astype(int)

    # 1-second burst bucket
    mtime_counts = Counter(df["m_time"].values)
    df["burst_count"] = df["m_time"].map(mtime_counts)

    # 60-second burst bucket
    df["m_time_min"] = df["m_time"] // 60
    min_counts = Counter(df["m_time_min"].values)
    df["burst_60s"] = df["m_time_min"].map(min_counts)

    df["log_burst_count"] = np.log1p(df["burst_count"])
    df["log_burst_60s"] = np.log1p(df["burst_60s"])

    # Display largest burst groups
    burst_groups = df[df["burst_count"] > 10].groupby("m_time")[["path"]].count()
    if not burst_groups.empty:
        print("\n[+] Top temporal modification bursts:")
        for ts, cnt in burst_groups.sort_values("path", ascending=False).head(5).iterrows():
            try:
                dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
                print(f"    - {dt.isoformat()} : {int(cnt['path']):,} files modified simultaneously")
            except Exception:
                pass

    os.makedirs(FEAT_DIR, exist_ok=True)
    burst_csv = os.path.join(FEAT_DIR, "burst_features.csv")
    df[["path", "burst_count", "burst_60s", "log_burst_count", "log_burst_60s"]].to_csv(burst_csv, index=False)
    print(f"[+] Burst features saved to {burst_csv}")

    # Retrain Isolation Forest v2 with burst features
    macb_path = os.path.join(FEAT_DIR, "macb_features.csv")
    if not os.path.exists(macb_path):
        print(f"[!] macb_features.csv missing at {macb_path}. Skipping model v2.")
        return False

    macb = pd.read_csv(macb_path)
    merged = macb.merge(df[["path", "log_burst_count", "log_burst_60s"]], on="path", how="left").fillna(0)

    feat_v2 = [
        "delta_mc", "delta_mb", "delta_ab", "future_m",
        "zero_size_recent", "size", "log_burst_count", "log_burst_60s"
    ]
    feat_cols = [c for c in feat_v2 if c in merged.columns]
    X_v2 = StandardScaler().fit_transform(merged[feat_cols].values)

    model_v2 = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42)
    model_v2.fit(X_v2)

    labels_v2 = model_v2.predict(X_v2)
    scores_v2 = model_v2.decision_function(X_v2)

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "iforest_v2.pkl"), "wb") as f:
        pickle.dump(model_v2, f)

    results_v2 = merged[["path"]].copy()
    results_v2["anomaly_score_v2"] = scores_v2
    results_v2["is_anomaly_v2"] = (labels_v2 == -1).astype(int)

    out_v2 = os.path.join(FEAT_DIR, "flagged_anomalies_v2.csv")
    results_v2.to_csv(out_v2, index=False)

    flagged_v1_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    v1_count = 0
    if os.path.exists(flagged_v1_path):
        v1_count = pd.read_csv(flagged_v1_path)["is_anomaly"].sum()

    v2_count = int((labels_v2 == -1).sum())
    print(f"[+] Model v1 flagged: {v1_count} files")
    print(f"[+] Model v2 (+burst features) flagged: {v2_count} files -> {out_v2}")
    return True


if __name__ == "__main__":
    run_burst_detection()