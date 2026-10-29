"""
export_site_extras.py
=====================
Exports the threshold-sweep, SHAP feature-firing and claims-audit results into site/extras.json
for the results site. Reads only finished outputs (no model fitting):
  reports/threshold_sweep/{full_sweep.csv, stable_thresholds.json}
  reports/shap_feature_firing/{feature_firing.csv, claims_check.csv}
  reports/image1_audit/claims_check.csv

Run after threshold_sweep.py, shap_feature_firing.py and image1_audit.py:  python export_site_extras.py
"""

import os
import json

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(BASE, "reports")
CONFIG_LABEL = {"IF-23": "Isolation Forest (23)", "LOF-23": "LOF (23)", "OCSVM-23": "One-Class SVM (23)",
                "IF-17": "Isolation Forest (17, original)"}
MODEL_SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OC-SVM"}


def sweep():
    df = pd.read_csv(os.path.join(R, "threshold_sweep", "full_sweep.csv"))
    st = json.load(open(os.path.join(R, "threshold_sweep", "stable_thresholds.json")))["stable_thresholds"]
    out = {}
    for (img, cfg), g in df.groupby(["image", "config"], sort=False):
        g = g.sort_values("threshold_pct")
        s = st.get(f"{img}/{cfg}", {})
        out.setdefault(img, {})[cfg] = {
            "label": CONFIG_LABEL.get(cfg, cfg), "targets": int(g["targets_total"].iloc[0]),
            "pct": g["threshold_pct"].tolist(), "recall": g["recall_pct"].round(2).tolist(),
            "std": g["recall_std_pct"].round(2).tolist(), "hits": g["hits_mean"].round(2).tolist(),
            "precision": g["precision_pct"].round(4).tolist(), "K": g["K_mean"].round(1).tolist(),
            "ge90": {r: v.get("first_recall_ge_90") for r, v in s.get("per_randomization", {}).items()},
            "agree90": s.get("agree", {}).get("first_recall_ge_90"),
            "agreement": s.get("per_threshold_agree_count"),
        }
    return out


def firing():
    f = pd.read_csv(os.path.join(R, "shap_feature_firing", "feature_firing.csv"))
    out = {}
    for img, g in f.groupby("image", sort=False):
        counts, rows = [], {}
        for (fs, model), h in g.groupby(["feature_set", "model"], sort=False):
            base = model.split(" (")[0]
            counts.append({"set": int(fs), "model": MODEL_SHORT.get(base, base),
                           "fired": int(h["status"].str.startswith("fired").sum()), "of": len(h)})
            if base == "Isolation Forest":
                for r in h.to_dict("records"):
                    e = rows.setdefault(r["feature"], {"feature": r["feature"], "constant": bool(r["constant"]),
                                                       "nonzero_pct": round(float(r["nonzero_pct"]), 2)})
                    e[f"s{int(fs)}"] = {"status": r["status"], "shap": round(float(r["mean_abs_shap"]), 4),
                                        "cause": str(r["root_cause"])}
        out[img] = {"counts": counts, "features": list(rows.values())}
    return out


def claims():
    out = []
    for src, path in (("Image 1 audit", os.path.join(R, "image1_audit", "claims_check.csv")),
                      ("SHAP and features", os.path.join(R, "shap_feature_firing", "claims_check.csv"))):
        for r in pd.read_csv(path).to_dict("records"):
            out.append({"area": src, "claim": str(r["claim"]), "verdict": str(r["verdict"]).upper(),
                        "evidence": str(r["evidence"])})
    return out


if __name__ == "__main__":
    data = {"sweep": sweep(), "firing": firing(), "claims": claims()}
    p = os.path.join(BASE, "site", "extras.json")
    with open(p, "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print("[+] wrote", p, os.path.getsize(p) // 1024, "KB")
