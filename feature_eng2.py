
"""
feature_engineering.py
Upgraded feature engineering for ForensIQ
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import OUT_DIR, FEAT_DIR


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def build_macb_features():
    records = load_json(f"{OUT_DIR}/mft/mft_records.json", [])
    df = pd.DataFrame(records)

    if df.empty:
        raise RuntimeError("No MFT records found.")

    df = df[df["type"] == "file"].copy()

    for c in ["m_time","a_time","c_time","cr_time","size"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    now = int(pd.Timestamp.now().timestamp())

    df["delta_mc"] = (df.m_time-df.c_time).abs()
    df["delta_mb"] = (df.m_time-df.cr_time).abs()
    df["delta_ab"] = (df.a_time-df.cr_time).abs()
    df["future_m"] = (df.m_time>now).astype(int)
    df["zero_size_recent"] = ((df["size"]==0)&((now-df.m_time)<86400)).astype(int)
    df["is_deleted"] = df["is_deleted"].astype(int)

    lower=df["path"].str.lower()

    df["is_exe"]=lower.str.endswith(".exe").astype(int)
    df["is_archive"]=lower.str.endswith((".zip",".rar",".7z")).astype(int)
    df["temp_path"]=lower.str.contains(r"\\temp\\").astype(int)
    df["user_path"]=lower.str.contains(r"\\users\\").astype(int)

    pf=load_json(f"{OUT_DIR}/prefetch/prefetch_list.json",[])
    pf_names=" ".join([p["name"].lower() for p in pf])

    df["credential_tool"]=int(any(x in pf_names for x in ["mimikatz","pwdump","cain","123wasp"]))
    df["sniffer_tool"]=int(any(x in pf_names for x in ["wireshark","ethereal","tcpdump","winpcap"]))
    df["powershell_exec"]=int("powershell" in pf_names)
    df["cmd_exec"]=int("cmd" in pf_names)
    df["script_host"]=int(("wscript" in pf_names) or ("cscript" in pf_names))

    usb=int(os.path.exists(f"{OUT_DIR}/usb/SYSTEM"))
    df["usb_present"]=usb

    cols=[
        "delta_mc","delta_mb","delta_ab","future_m",
        "zero_size_recent","size","is_deleted",
        "is_exe","is_archive","temp_path","user_path",
        "credential_tool","sniffer_tool",
        "powershell_exec","cmd_exec","script_host",
        "usb_present"
    ]

    os.makedirs(FEAT_DIR,exist_ok=True)
    out=df[["path"]+cols]
    out.to_csv(f"{FEAT_DIR}/macb_features.csv",index=False)
    return out


def build_log_gap_features():
    events=load_json(f"{OUT_DIR}/evtx/parsed_events.json",[])
    df=pd.DataFrame(events)
    if df.empty:
        out=pd.DataFrame(columns=["hour","event_count","gap","log_z_score","is_workhour"])
        out.to_csv(f"{FEAT_DIR}/log_gap_features.csv",index=False)
        return out
    df["ts"]=pd.to_datetime(df["timestamp"],errors="coerce")
    df=df.dropna(subset=["ts"])
    df["hour"]=df["ts"].dt.floor("h")
    hourly=df.groupby("hour").size().rename("event_count").reset_index()
    rng=pd.date_range(hourly.hour.min(),hourly.hour.max(),freq="h")
    full=pd.DataFrame({"hour":rng}).merge(hourly,how="left").fillna(0)
    full["is_workhour"]=full.hour.dt.hour.between(8,18).astype(int)
    full["gap"]=((full.event_count==0)&(full.is_workhour==1)).astype(int)
    full["log_z_score"]=(full.event_count-full.event_count.mean())/(full.event_count.std()+1e-9)
    full.to_csv(f"{FEAT_DIR}/log_gap_features.csv",index=False)
    return full


def build_feature_matrix():
    macb=pd.read_csv(f"{FEAT_DIR}/macb_features.csv")
    features=[c for c in macb.columns if c!="path"]
    X_raw=macb[features].fillna(0).values
    scaler=StandardScaler()
    X=scaler.fit_transform(X_raw)
    np.save(f"{FEAT_DIR}/X_raw.npy",X_raw)
    np.save(f"{FEAT_DIR}/X_matrix.npy",X)
    macb["path"].to_csv(f"{FEAT_DIR}/file_index.csv",index=False)
    print(f"[+] Feature matrix: {X.shape}")
    print("[+] Features:",", ".join(features))
    return X

if __name__=="__main__":
    build_macb_features()
    build_log_gap_features()
    build_feature_matrix()
