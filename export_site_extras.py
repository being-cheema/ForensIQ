"""
export_site_extras.py
=====================
Exports the claims audit into site/extras.json for the results site. Reads only finished outputs:
  reports/shap_feature_firing/claims_check.csv, reports/image1_audit/claims_check.csv,
  reports/study_v3/feature_audit.csv, reports/study_v3/feature_audit_clean.csv

The threshold sweep and SHAP feature-firing exports that used to live here are gone: the site now reads the
pre-registered study (reports/study_v3/final/*/site.json, copied to web/src/data/study/).

Run:  python export_site_extras.py
"""

import os
import json

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(BASE, "reports")


def claims():
    out = []
    for src, path in (("Image 1 audit", os.path.join(R, "image1_audit", "claims_check.csv")),
                      ("SHAP and features", os.path.join(R, "shap_feature_firing", "claims_check.csv"))):
        for r in pd.read_csv(path).to_dict("records"):
            out.append({"area": src, "claim": str(r["claim"]), "verdict": str(r["verdict"]).upper(),
                        "evidence": str(r["evidence"])})
    return out


def audit():
    """Feature audit (study v3): the 8 legacy features that were dead, and the two that were fixed.
    Values are the percent of files with a non-zero value, per disk."""
    legacy = pd.read_csv(os.path.join(R, "study_v3", "feature_audit.csv"))
    clean = pd.read_csv(os.path.join(R, "study_v3", "feature_audit_clean.csv"))
    pick = lambda df, f: {r["disk"]: round(float(r["pct_nonzero"]), 2) for r in df[df["feature"] == f].to_dict("records")}
    dead = ["credential_tool", "sniffer_tool", "powershell_exec", "cmd_exec", "script_host", "usb_present", "future_m", "is_deleted"]
    fixed = ["after_hours_touch", "per_file_prefetch_hit"]
    added = ["m_before_cr", "is_script"]
    return {"dead": [{"feature": f, "nonzero": pick(legacy, f)} for f in dead],
            "fixed": [{"feature": f, "before": pick(legacy, f), "after": pick(clean, f)} for f in fixed],
            "added": [{"feature": f, "nonzero": pick(clean, f)} for f in added]}


if __name__ == "__main__":
    data = {"claims": claims(), "audit": audit()}
    p = os.path.join(BASE, "site", "extras.json")
    with open(p, "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print("[+] wrote", p, os.path.getsize(p) // 1024, "KB")
