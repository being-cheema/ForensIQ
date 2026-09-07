import json
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from config import OUT_DIR, FEAT_DIR


# Build MACB delta features from MFT records
def build_macb_features():
    with open(f"{OUT_DIR}/mft/mft_records.json", "r") as f:
        records = json.load(f)

    df = pd.DataFrame(records)

    # Keep only file records
    df = df[df["type"] == "file"].copy()

    # Ensure timestamps are numeric
    timestamp_cols = ["m_time", "c_time", "a_time", "cr_time"]
    for col in timestamp_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["size"] = pd.to_numeric(df["size"], errors="coerce").fillna(0)

    # MACB deltas
    df["delta_mc"] = (df["m_time"] - df["c_time"]).abs()
    df["delta_mb"] = (df["m_time"] - df["cr_time"]).abs()
    df["delta_ab"] = (df["a_time"] - df["cr_time"]).abs()

    now_ts = int(pd.Timestamp.now().timestamp())

    df["future_m"] = (df["m_time"] > now_ts).astype(int)

    df["zero_size_recent"] = (
        (df["size"] == 0) &
        ((now_ts - df["m_time"]) < 86400)
    ).astype(int)

    feature_cols = [
        "delta_mc",
        "delta_mb",
        "delta_ab",
        "future_m",
        "zero_size_recent",
        "size"
    ]

    out_df = df[["path"] + feature_cols].fillna(0)

    os.makedirs(FEAT_DIR, exist_ok=True)

    out_df.to_csv(
        f"{FEAT_DIR}/macb_features.csv",
        index=False
    )

    print(f"[+] MACB features: {len(out_df)} rows")

    return out_df


macb_df = build_macb_features()


# Build event log continuity features
def build_log_gap_features():
    with open(f"{OUT_DIR}/evtx/parsed_events.json", "r") as f:
        events = json.load(f)

    df = pd.DataFrame(events)

    df["ts"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df = df.dropna(subset=["ts"])

    df["hour"] = df["ts"].dt.floor("h")

    hourly = (
        df.groupby("hour")
        .size()
        .rename("event_count")
        .reset_index()
    )

    full_range = pd.date_range(
        start=hourly["hour"].min(),
        end=hourly["hour"].max(),
        freq="h"
    )

    full = pd.DataFrame({"hour": full_range})

    full = (
        full.merge(hourly, on="hour", how="left")
        .fillna(0)
    )

    full["is_workhour"] = (
        full["hour"].dt.hour.between(8, 18)
    ).astype(int)

    full["gap"] = (
        (full["event_count"] == 0) &
        (full["is_workhour"] == 1)
    ).astype(int)

    full["log_z_score"] = (
        (full["event_count"] - full["event_count"].mean())
        / (full["event_count"].std() + 1e-9)
    )

    out = full[
        [
            "hour",
            "event_count",
            "gap",
            "log_z_score",
            "is_workhour"
        ]
    ]

    out.to_csv(
        f"{FEAT_DIR}/log_gap_features.csv",
        index=False
    )

    print(f"[+] Log gap features: {len(out)} hours")

    return out


log_df = build_log_gap_features()


# Build the unified normalised feature matrix
def build_feature_matrix():
    macb = pd.read_csv(
        f"{FEAT_DIR}/macb_features.csv"
    )

    feature_cols = [
        "delta_mc",
        "delta_mb",
        "delta_ab",
        "future_m",
        "zero_size_recent",
        "size"
    ]

    X_raw = macb[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    np.save(f"{FEAT_DIR}/X_matrix.npy", X)
    np.save(f"{FEAT_DIR}/X_raw.npy", X_raw)

    macb["path"].to_csv(
        f"{FEAT_DIR}/file_index.csv",
        index=False
    )

    print(f"[+] Feature matrix: {X.shape}")

    return X, macb["path"].values


X, file_paths = build_feature_matrix()