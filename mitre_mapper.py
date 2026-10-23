"""
mitre_mapper.py
===============
ForensIQ MITRE ATT&CK Mapping Engine
Maps forensic anomaly signatures, timestomping, and tool footprints
to MITRE ATT&CK Enterprise techniques and outputs Navigator JSON layers.
"""

import os
import json
import pandas as pd
from config import FEAT_DIR, OUT_DIR, REPORT_DIR

CRED_TOOLS = ["cain", "123wasp", "pwdump", "mimikatz"]
SNIFFER_TOOLS = ["ethereal", "wireshark", "winpcap", "tcpdump"]
CMD_TOOLS = ["cmd.exe", "powershell", "wscript", "cscript"]


def run_mitre_mapping():
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    log_gap_path = os.path.join(FEAT_DIR, "log_gap_features.csv")
    pf_path = os.path.join(OUT_DIR, "prefetch", "prefetch_list.json")

    flagged = pd.read_csv(flagged_path) if os.path.exists(flagged_path) else pd.DataFrame()
    log_df = pd.read_csv(log_gap_path) if os.path.exists(log_gap_path) else pd.DataFrame()

    pf_names = []
    if os.path.exists(pf_path):
        try:
            with open(pf_path, "r", encoding="utf-8") as f:
                pf_names = [p.get("name", "").lower() for p in json.load(f)]
        except Exception:
            pass

    findings = {}

    # MFT timestomping (T1070.006)
    if "delta_mb" in flagged.columns:
        stomped = flagged[flagged["delta_mb"] < 60]
        if len(stomped) > 0:
            findings["T1070.006"] = {
                "technique": "Indicator Removal: Timestomp",
                "count": len(stomped),
                "evidence": stomped["path"].head(5).tolist(),
                "confidence": "HIGH" if len(stomped) > 50 else "MEDIUM"
            }

    # Event log clearing / gaps (T1070.001)
    if "gap" in log_df.columns and (log_df["gap"] == 1).sum() > 3:
        findings["T1070.001"] = {
            "technique": "Indicator Removal: Clear Windows Event Logs",
            "count": int((log_df["gap"] == 1).sum()),
            "evidence": ["Working-hour windows with zero recorded events"],
            "confidence": "HIGH"
        }

    # USB removable media (T1052.001)
    usb_txt = os.path.join(OUT_DIR, "usb", "usb_devices.txt")
    usb_hive = os.path.join(OUT_DIR, "usb", "SYSTEM")
    has_usb = ("usb_present" in flagged.columns and flagged["usb_present"].sum() > 0) or os.path.exists(usb_txt) or os.path.exists(usb_hive)
    if has_usb:
        findings["T1052.001"] = {
            "technique": "Exfiltration Over Physical Medium",
            "count": 1,
            "evidence": ["SYSTEM hive USBSTOR device records"],
            "confidence": "MEDIUM"
        }

    # Ransomware / Encrypted Data (T1486)
    if "is_archive" in flagged.columns and flagged["is_archive"].sum() > 20:
        findings["T1486"] = {
            "technique": "Data Encrypted for Impact",
            "count": int(flagged["is_archive"].sum()),
            "evidence": ["High volume of archive and encrypted files detected"],
            "confidence": "HIGH"
        }

    # Credential dumping (T1003.002)
    cred_hits = [n for n in pf_names if any(t in n for t in CRED_TOOLS)]
    if cred_hits:
        findings["T1003.002"] = {
            "technique": "OS Credential Dumping: Security Account Manager",
            "count": len(cred_hits),
            "evidence": cred_hits,
            "confidence": "HIGH"
        }

    # Network sniffing (T1040)
    sniff_hits = [n for n in pf_names if any(t in n for t in SNIFFER_TOOLS)]
    if sniff_hits:
        findings["T1040"] = {
            "technique": "Network Sniffing",
            "count": len(sniff_hits),
            "evidence": sniff_hits,
            "confidence": "HIGH"
        }

    os.makedirs(REPORT_DIR, exist_ok=True)
    report = {
        "framework": "MITRE ATT&CK v14",
        "techniques_detected": findings
    }
    out_path = os.path.join(REPORT_DIR, "mitre_mapping.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[+] MITRE ATT&CK techniques mapped: {list(findings.keys())} -> {out_path}")
    return findings


def export_navigator_layer(findings, out_path=None):
    if out_path is None:
        out_path = os.path.join(REPORT_DIR, "mitre_navigator_layer.json")

    colours = {"HIGH": "#f87171", "MEDIUM": "#fbbf24", "LOW": "#34d399"}
    layer = {
        "name": "ForensIQ ATT&CK Detection Layer",
        "versions": {"attack": "14", "navigator": "4.9", "layer": "4.5"},
        "domain": "enterprise-attack",
        "techniques": [
            {
                "techniqueID": tid,
                "color": colours.get(info.get("confidence", "MEDIUM"), "#a78bfa"),
                "comment": f"Count: {info.get('count', 1)}",
                "enabled": True,
                "score": info.get("count", 1)
            }
            for tid, info in findings.items()
        ]
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(layer, f, indent=2)
    print(f"[+] MITRE ATT&CK Navigator layer saved to {out_path}")


def main():
    findings = run_mitre_mapping()
    export_navigator_layer(findings)


if __name__ == "__main__":
    main()