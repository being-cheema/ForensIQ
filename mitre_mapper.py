# Create the MITRE mapping engine

import json
import os
import pandas as pd

from config import FEAT_DIR, OUT_DIR, REPORT_DIR

CRED_TOOLS = ["cain", "123wasp", "pwdump", "mimikatz"]
SNIFFER_TOOLS = ["ethereal", "wireshark", "winpcap", "tcpdump"]
CMD_TOOLS = ["cmd.exe", "powershell", "wscript", "cscript"]


def run_mitre_mapping():
    flagged = pd.read_csv(f"{FEAT_DIR}/flagged_anomalies.csv")
    log_df = pd.read_csv(f"{FEAT_DIR}/log_gap_features.csv")

    with open(f"{OUT_DIR}/prefetch/prefetch_list.json") as f:
        pf_names = [p["name"].lower() for p in json.load(f)]

    findings = {}

    # MFT timestamp stomping
    stomped = flagged[flagged["delta_mb"] < 60]

    if len(stomped) > 0:
        findings["T1070.006"] = {
            "count": len(stomped),
            "evidence": stomped["path"].head(5).tolist(),
            "confidence": "HIGH" if len(stomped) > 50 else "MEDIUM"
        }

    # Event log clearing / gaps
    if (log_df["gap"] == 1).sum() > 3:
        findings["T1070.001"] = {
            "count": int((log_df["gap"] == 1).sum()),
            "evidence": ["Working-hour windows with zero events"],
            "confidence": "HIGH"
        }

    # USB removable media
    usb_txt = os.path.join(OUT_DIR, "usb", "usb_devices.txt")
    usb_hive = os.path.join(OUT_DIR, "usb", "SYSTEM")

    if ("usb_present" in flagged.columns and flagged["usb_present"].sum() > 0) or os.path.exists(usb_txt) or os.path.exists(usb_hive):
        findings["T1052.001"] = {
            "count": 1,
            "evidence": ["SYSTEM hive USBSTOR entries"],
            "confidence": "MEDIUM"
        }

    # Ransomware (Data Encrypted for Impact)
    if "is_archive" in flagged.columns and flagged["is_archive"].sum() > 20:
        findings["T1486"] = {
            "count": int(flagged["is_archive"].sum()),
            "evidence": ["High volume of archive files detected"],
            "confidence": "HIGH"
        }

    # Credential dumping tools
    cred_hits = [
        n for n in pf_names
        if any(t in n for t in CRED_TOOLS)
    ]

    if cred_hits:
        findings["T1003.002"] = {
            "count": len(cred_hits),
            "evidence": cred_hits,
            "confidence": "HIGH"
        }

    # Network sniffing tools
    sniff_hits = [
        n for n in pf_names
        if any(t in n for t in SNIFFER_TOOLS)
    ]

    if sniff_hits:
        findings["T1040"] = {
            "count": len(sniff_hits),
            "evidence": sniff_hits,
            "confidence": "HIGH"
        }

    report = {
        "framework": "MITRE ATT&CK v14",
        "techniques_detected": findings
    }

    out_path = f"{REPORT_DIR}/mitre_mapping.json"

    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[+] MITRE: {list(findings.keys())}")

    return findings


mitre_findings = run_mitre_mapping()


# Export ATT&CK Navigator layer JSON
def export_navigator_layer(findings, out_path):
    colours = {
        "HIGH": "#f87171",
        "MEDIUM": "#fbbf24",
        "LOW": "#34d399"
    }

    layer = {
        "name": "ForensIQ Detection Layer — SCHARDT.001",
        "versions": {
            "attack": "14",
            "navigator": "4.9",
            "layer": "4.5"
        },
        "domain": "enterprise-attack",
        "techniques": [
            {
                "techniqueID": tid,
                "color": colours.get(info["confidence"], "#a78bfa"),
                "comment": f"Count:{info['count']}",
                "enabled": True,
                "score": info["count"]
            }
            for tid, info in findings.items()
        ]
    }

    with open(out_path, "w") as f:
        json.dump(layer, f, indent=2)

    print(f"[+] Navigator layer in {out_path}")


export_navigator_layer(
    mitre_findings,
    f"{REPORT_DIR}/mitre_navigator_layer.json"
)