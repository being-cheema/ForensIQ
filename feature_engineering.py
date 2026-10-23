"""
feature_engineering.py
======================
ForensIQ Canonical Feature Engineering Pipeline
Extracts 17 numerical forensic features from MFT records, Event Logs, Prefetch,
and Registry artifacts for Isolation Forest anomaly detection.
Supports both legacy Windows XP and modern Windows 7/10 datasets.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import (
    OUT_DIR,
    FEAT_DIR,
    WORK_HOURS_START,
    WORK_HOURS_END
)

FEATURE_COLUMNS = [
    "delta_mc", "delta_mb", "delta_ab", "future_m", "zero_size_recent",
    "size", "is_deleted", "is_exe", "is_archive", "temp_path", "user_path",
    "credential_tool", "sniffer_tool", "powershell_exec", "cmd_exec",
    "script_host", "usb_present"
]


def load_json(path, default=None):
    """Safely load a JSON file, returning default if missing or corrupted."""
    if default is None:
        default = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def get_active_event_log_path():
    """
    Smart candidate selector (Report 3 Step 3):
    Prioritizes modern EVTX if it exists and has content, otherwise legacy EVT.
    """
    evtx_path = os.path.join(OUT_DIR, "evtx", "parsed_events.json")
    if os.path.exists(evtx_path) and os.path.getsize(evtx_path) > 10:
        return evtx_path

    evt_path = os.path.join(OUT_DIR, "evt", "parsed_events.json")
    if os.path.exists(evt_path) and os.path.getsize(evt_path) > 10:
        return evt_path

    return evtx_path if os.path.exists(evtx_path) else evt_path


def build_macb_features():
    """
    Builds the 17 forensic feature columns from MFT records, prefetch, and USB artifacts.
    Includes dataset-relative calibration (H-2) and empty MFT guards (M-3).
    """
    mft_path = os.path.join(OUT_DIR, "mft", "mft_records.json")
    if not os.path.exists(mft_path):
        raise FileNotFoundError(f"[!] MFT records file not found at: {mft_path}")

    records = load_json(mft_path, [])
    if not records:
        print("[!] Warning: MFT records file is empty.")
        df = pd.DataFrame(columns=["path", "type", "m_time", "c_time", "a_time", "cr_time", "size", "is_deleted"])
    else:
        df = pd.DataFrame(records)

    # Filter to file records only
    if "type" in df.columns:
        df = df[df["type"] == "file"].copy()
    else:
        df = pd.DataFrame()

    if df.empty:
        print("[!] Warning: Zero file records found in MFT. Creating empty feature table.")
        empty_out = pd.DataFrame(columns=["path"] + FEATURE_COLUMNS)
        os.makedirs(FEAT_DIR, exist_ok=True)
        empty_out.to_csv(os.path.join(FEAT_DIR, "macb_features.csv"), index=False)
        return empty_out

    # Numeric timestamp conversion
    timestamp_cols = ["m_time", "c_time", "a_time", "cr_time"]
    for col in timestamp_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["size"] = pd.to_numeric(df["size"], errors="coerce").fillna(0)
    df["is_deleted"] = df.get("is_deleted", False).astype(int)

    # MACB delta features (timestomping & backdating detection)
    df["delta_mc"] = (df["m_time"] - df["c_time"]).abs()
    df["delta_mb"] = (df["m_time"] - df["cr_time"]).abs()
    df["delta_ab"] = (df["a_time"] - df["cr_time"]).abs()

    # Dynamic reference timestamp derived from dataset max (H-2):
    # Prevents historical images (2004 XP / 2018 Lone Wolf) from producing all-zero features
    max_m = df["m_time"].max()
    now_ts = int(max_m) if pd.notna(max_m) and max_m > 0 else int(pd.Timestamp.now().timestamp())

    df["future_m"] = (df["m_time"] > now_ts).astype(int)
    df["zero_size_recent"] = ((df["size"] == 0) & ((now_ts - df["m_time"]) < 86400) & (df["m_time"] > 0)).astype(int)

    # Path heuristics
    path_lower = df["path"].astype(str).str.lower()
    df["is_exe"] = path_lower.str.endswith((".exe", ".dll", ".sys", ".scr")).astype(int)
    df["is_archive"] = path_lower.str.endswith((".zip", ".rar", ".7z", ".tar", ".gz")).astype(int)
    df["temp_path"] = path_lower.str.contains(r"[\\/]temp[\\/]|[\\/]tmp[\\/]", regex=True).astype(int)
    df["user_path"] = path_lower.str.contains(r"[\\/]users[\\/]|[\\/]documents and settings[\\/]", regex=True).astype(int)

    # Correlate with prefetch execution evidence
    pf_path = os.path.join(OUT_DIR, "prefetch", "prefetch_list.json")
    pf = load_json(pf_path, [])
    pf_names = " ".join([p.get("name", "").lower() for p in pf])

    df["credential_tool"] = int(any(x in pf_names for x in ["mimikatz", "pwdump", "cain", "123wasp", "stored"]))
    df["sniffer_tool"] = int(any(x in pf_names for x in ["wireshark", "ethereal", "tcpdump", "winpcap", "netstumbler"]))
    df["powershell_exec"] = int("powershell" in pf_names)
    df["cmd_exec"] = int("cmd" in pf_names)
    df["script_host"] = int(("wscript" in pf_names) or ("cscript" in pf_names))

    # Correlate with USB artifact evidence
    usb_file = os.path.join(OUT_DIR, "usb", "SYSTEM")
    usb_txt = os.path.join(OUT_DIR, "usb", "usb_devices.txt")
    usb_detected = os.path.exists(usb_file) or os.path.exists(usb_txt)
    df["usb_present"] = int(usb_detected)

    # Assemble output frame
    out_df = df[["path"] + FEATURE_COLUMNS].fillna(0)

    os.makedirs(FEAT_DIR, exist_ok=True)
    out_csv = os.path.join(FEAT_DIR, "macb_features.csv")
    out_df.to_csv(out_csv, index=False)
    print(f"[+] MACB features computed: {len(out_df):,} files -> {out_csv}")
    return out_df


def build_log_gap_features():
    """
    Builds event log continuity and log clearing gap features.
    Configurable with corporate policy work hours (Report 4 Gap 5).
    """
    active_log_path = get_active_event_log_path()
    events = load_json(active_log_path, [])

    if not events:
        out = pd.DataFrame(columns=["hour", "event_count", "gap", "log_z_score", "is_workhour"])
        os.makedirs(FEAT_DIR, exist_ok=True)
        out.to_csv(os.path.join(FEAT_DIR, "log_gap_features.csv"), index=False)
        print("[i] No parsed event logs available for log gap analysis.")
        return out

    df = pd.DataFrame(events)
    df["ts"] = pd.to_datetime(df.get("timestamp", []), errors="coerce", utc=True)
    df = df.dropna(subset=["ts"])

    if df.empty:
        out = pd.DataFrame(columns=["hour", "event_count", "gap", "log_z_score", "is_workhour"])
        os.makedirs(FEAT_DIR, exist_ok=True)
        out.to_csv(os.path.join(FEAT_DIR, "log_gap_features.csv"), index=False)
        return out

    df["hour"] = df["ts"].dt.floor("h")
    hourly = df.groupby("hour").size().rename("event_count").reset_index()

    full_range = pd.date_range(start=hourly["hour"].min(), end=hourly["hour"].max(), freq="h", tz="UTC")
    full = pd.DataFrame({"hour": full_range}).merge(hourly, on="hour", how="left").fillna(0)

    # Configurable policy work hours
    full["is_workhour"] = full["hour"].dt.hour.between(WORK_HOURS_START, WORK_HOURS_END).astype(int)
    full["gap"] = ((full["event_count"] == 0) & (full["is_workhour"] == 1)).astype(int)

    mean_count = full["event_count"].mean()
    std_count = full["event_count"].std() + 1e-9
    full["log_z_score"] = (full["event_count"] - mean_count) / std_count

    out = full[["hour", "event_count", "gap", "log_z_score", "is_workhour"]]
    os.makedirs(FEAT_DIR, exist_ok=True)
    out.to_csv(os.path.join(FEAT_DIR, "log_gap_features.csv"), index=False)
    print(f"[+] Log gap features computed: {len(out):,} hourly bins -> {FEAT_DIR}/log_gap_features.csv")
    return out


def build_feature_matrix():
    """
    Standardizes the raw feature matrix for Isolation Forest anomaly detection.
    Guards against missing CSV (M-4).
    """
    macb_path = os.path.join(FEAT_DIR, "macb_features.csv")
    if not os.path.exists(macb_path):
        raise FileNotFoundError(f"[!] macb_features.csv not found at: {macb_path}")

    macb = pd.read_csv(macb_path)
    if macb.empty or len(macb) == 0:
        print("[!] Feature DataFrame is empty. Skipping matrix generation.")
        X_empty = np.empty((0, len(FEATURE_COLUMNS)))
        np.save(os.path.join(FEAT_DIR, "X_raw.npy"), X_empty)
        np.save(os.path.join(FEAT_DIR, "X_matrix.npy"), X_empty)
        pd.DataFrame(columns=["path"]).to_csv(os.path.join(FEAT_DIR, "file_index.csv"), index=False)
        return X_empty, np.array([])

    feature_cols = [c for c in FEATURE_COLUMNS if c in macb.columns]
    X_raw = macb[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    np.save(os.path.join(FEAT_DIR, "X_raw.npy"), X_raw)
    np.save(os.path.join(FEAT_DIR, "X_matrix.npy"), X_scaled)

    macb["path"].to_csv(os.path.join(FEAT_DIR, "file_index.csv"), index=False)

    print(f"[+] Feature matrix scaled: {X_scaled.shape} -> {FEAT_DIR}/X_matrix.npy")
    return X_scaled, macb["path"].values


def main():
    print("=" * 65)
    print("      ForensIQ Feature Engineering Engine")
    print("=" * 65)
    build_macb_features()
    build_log_gap_features()
    build_feature_matrix()
    print("=" * 65)
    print("      Feature Engineering Complete")
    print("=" * 65)


if __name__ == "__main__":
    main()