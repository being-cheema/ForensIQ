# Compute burst scores across MFT modification times

import json
import os
import pandas as pd
import numpy as np
import datetime
from collections import Counter

from config import OUT_DIR, FEAT_DIR

# Load MFT records
with open(f"{OUT_DIR}/mft/mft_records.json", "r") as f:
    records = json.load(f)

df = pd.DataFrame(records)

# Keep only valid files with modification timestamps
df = df[(df["type"] == "file") & (df["m_time"] > 0)].copy()
df.reset_index(drop=True, inplace=True)

# Ensure timestamps are integers
df["m_time"] = df["m_time"].astype(int)

# ------------------------------------------------------------------
# 1-second burst bucket
# ------------------------------------------------------------------
mtime_counts = Counter(df["m_time"].values)
df["burst_count"] = df["m_time"].map(mtime_counts)

# ------------------------------------------------------------------
# 60-second burst bucket
# ------------------------------------------------------------------
df["m_time_min"] = df["m_time"] // 60
min_counts = Counter(df["m_time_min"].values)
df["burst_60s"] = df["m_time_min"].map(min_counts)

# Log-scaled versions
df["log_burst_count"] = np.log1p(df["burst_count"])
df["log_burst_60s"] = np.log1p(df["burst_60s"])

# Display largest burst groups
burst_groups = (
    df[df["burst_count"] > 10]
    .groupby("m_time")[["path"]]
    .count()
)

print("\nTop burst timestamps:")
for ts, cnt in (
    burst_groups.sort_values("path", ascending=False)
    .head(5)
    .iterrows()
):
    dt = datetime.datetime.fromtimestamp(
        int(ts),
        tz=datetime.timezone.utc
    )
    print(f"{dt.isoformat()} — {int(cnt['path'])} files")

# Save burst features
df[
    [
        "path",
        "burst_count",
        "burst_60s",
        "log_burst_count",
        "log_burst_60s",
    ]
].to_csv(
    f"{FEAT_DIR}/burst_features.csv",
    index=False
)

# ==================================================================
# Merge burst features and retrain Isolation Forest (v2)
# ==================================================================

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

from config import CONTAMINATION, MODEL_DIR

macb = pd.read_csv(f"{FEAT_DIR}/macb_features.csv")
burst = pd.read_csv(f"{FEAT_DIR}/burst_features.csv")

merged = (
    macb.merge(
        burst[
            [
                "path",
                "log_burst_count",
                "log_burst_60s",
            ]
        ],
        on="path",
        how="left",
    )
    .fillna(0)
)

FEAT_V2 = [
    "delta_mc",
    "delta_mb",
    "delta_ab",
    "future_m",
    "zero_size_recent",
    "size",
    "log_burst_count",
    "log_burst_60s",
]

# Scale features
scaler = StandardScaler()
X_v2 = scaler.fit_transform(merged[FEAT_V2].values)

# Train model
model_v2 = IsolationForest(
    n_estimators=200,
    contamination=CONTAMINATION,
    random_state=42,
)

model_v2.fit(X_v2)

labels_v2 = model_v2.predict(X_v2)
scores_v2 = model_v2.decision_function(X_v2)

# Save model
with open(f"{MODEL_DIR}/iforest_v2.pkl", "wb") as f:
    pickle.dump(model_v2, f)

# Save results
results_v2 = merged[["path"]].copy()
results_v2["anomaly_score_v2"] = scores_v2
results_v2["is_anomaly_v2"] = (labels_v2 == -1).astype(int)

results_v2.to_csv(
    f"{FEAT_DIR}/flagged_anomalies_v2.csv",
    index=False
)

# Compare with v1
v1 = pd.read_csv(
    f"{FEAT_DIR}/flagged_anomalies.csv"
)["is_anomaly"].sum()

v2 = (labels_v2 == -1).sum()

print(f"\n[+] v1 flagged: {v1}")
print(f"[+] v2 (+burst): {v2}")