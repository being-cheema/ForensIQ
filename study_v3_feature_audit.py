"""
study_v3_feature_audit.py
=========================
Per-feature audit of the ForensIQ feature sets on the three disks.

  python study_v3_feature_audit.py --set legacy23   -> reports/study_v3/feature_audit.{md,csv}
  python study_v3_feature_audit.py --set clean      -> reports/study_v3/feature_audit_clean.{md,csv}

For every feature and disk: nunique, % non-zero, constant?, plus a one-line diagnosis. The legacy audit
also tests each suspected bug directly against the extracted artifacts. Ground truth is not used.
"""
import os
import sys
import json
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--set", default="legacy23", choices=["legacy23", "clean"])
ARGS = ap.parse_args()
os.environ["FORENSIQ_FEATURE_SET"] = ARGS.set

import numpy as np
import pandas as pd
import multimodel_eval as M
from config import BASE_DIR, WORK_HOURS_START, WORK_HOURS_END

OUT = os.path.join(BASE_DIR, "reports", "study_v3")
TAGS = ["img1", "img2", "img3"]
SUFFIX = "" if ARGS.set == "legacy23" else "_clean"

TOOL_SUBSTR = {
    "credential_tool": ["mimikatz", "pwdump", "cain", "123wasp", "stored"],
    "sniffer_tool": ["wireshark", "ethereal", "tcpdump", "winpcap", "netstumbler"],
    "powershell_exec": ["powershell"], "cmd_exec": ["cmd"], "script_host": ["wscript", "cscript"],
}
DISK_LEVEL = ["credential_tool", "sniffer_tool", "powershell_exec", "cmd_exec", "script_host", "usb_present"]


def load(tag):
    art = M.IMAGES[tag]["art_dir"]
    df, raw, feats = M.build_features(art, tag)
    pf = M.fe.load_json(os.path.join(art, "prefetch", "prefetch_list.json"), [])
    return art, df, raw, feats, pf


def evidence(tag, art, df, raw, pf, feat):
    """One-line, data-backed diagnosis for a legacy feature on one disk (None when nothing special)."""
    n = len(df)
    if feat in DISK_LEVEL:
        k = df[feat].nunique()
        extra = ""
        if feat in TOOL_SUBSTR:
            names = [p["name"].lower() for p in pf]
            hit = [p["name"] for p in pf if any(s in p["name"].lower() for s in TOOL_SUBSTR[feat])]
            extra = "; prefetch names matching hard-coded substrings: %d %s" % (len(hit), hit[:3])
        if feat == "cmd_exec":
            hit = [p["name"] for p in pf if "cmd" in p["name"].lower() and not p["name"].upper().startswith("CMD.EXE")]
            extra += "; non-cmd.exe false matches (substring 'cmd'): %s" % hit[:3]
        if feat == "usb_present":
            extra = "; set whenever usb/SYSTEM or usb_devices.txt exists (file always written)"
        return "disk-level constant (nunique=%d, value=%s on all %d rows)%s" % (k, df[feat].iloc[0], n, extra)
    if feat == "future_m":
        ref = raw["m_time"].max()
        return "reference=max(m_time)=%d so m_time>ref is false for all rows; 0 by construction" % ref
    if feat == "is_deleted":
        return "mft_records.json: %d deleted rows among %d MFT records (dirs excluded)" % (
            int(pd.Series(json.load(open(os.path.join(art, "mft", "mft_records.json"))))
                .map(lambda r: bool(r.get("is_deleted"))).sum()), len(raw) + 0)
    if feat == "zero_size_recent":
        return "size==0 and within 24h of max(m_time): %d rows" % int(df[feat].sum())
    if feat == "after_hours_touch":
        return "UTC hours vs %02d-%02d window: %.1f%% of files flagged using the UTC clock (machine local time is not UTC)" % (
            WORK_HOURS_START, WORK_HOURS_END, 100 * df[feat].mean())
    if feat == "per_file_prefetch_hit":
        keys_json = {p.get("name", "").upper().rsplit("-", 1)[0] for p in pf}
        nm = df["path"].str.rsplit("/", n=1).str[-1].str.upper()
        old = int(nm.isin(keys_json).sum())
        exact, pref = M.prefetch_keys(art, raw)
        matched_keys_old = len(keys_json & set(nm))
        selfhit = int(((df[feat] == 1) & nm.str.endswith(".PF")).sum())
        old = int(df[feat].sum())
        return ("%d of the %d files flagged by the legacy builder are the .pf files themselves (legacy also added the un-split 'NAME.EXE-HASH.PF' key, "
                "so each .pf file matched itself); prefetch_list.json has %d entries (%d distinct exe names, %d matched to a file name by the split key); "
                "MFT lists %d /Prefetch/*.pf records (json has fewer where this exceeds its entry count); %d names are 29-char truncated"
                % (selfhit, old, len(pf), len(keys_json), matched_keys_old,
                   int(df["path"].str.contains(r"/prefetch/[^/]+\.pf$", case=False, regex=True).sum()), len(pref)))
    return None


def main():
    rows, notes, tzs = [], [], {}
    data = {t: load(t) for t in TAGS}
    for t in TAGS:
        art, df, raw, feats, pf = data[t]
        if ARGS.set == "clean":
            tzs[t] = (df.attrs.get("tz_bias_minutes"), df.attrs.get("tz_source"))
        else:
            tzs[t] = M.local_utc_bias_minutes(art)
        for f in feats:
            v = df[f]
            rows.append({"disk": t, "feature": f, "n_rows": len(df), "nunique": int(v.nunique()),
                         "pct_nonzero": round(100 * float((v != 0).mean()), 3),
                         "constant": bool(v.nunique() <= 1),
                         "diagnosis": evidence(t, art, df, raw, pf, f) if ARGS.set == "legacy23" else
                         ("constant" if v.nunique() <= 1 else "varies")})
    res = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    res.to_csv(os.path.join(OUT, f"feature_audit{SUFFIX}.csv"), index=False)

    allfeats = list(dict.fromkeys(res["feature"]))
    L = ["# Feature audit: %s set" % ARGS.set, "",
         "Generated by `study_v3_feature_audit.py --set %s`. Ground truth is not used." % ARGS.set, ""]
    L += ["## Time zones read from each SYSTEM hive", "",
          "| disk | bias (min, UTC = local + bias) | local offset | source |", "|---|---|---|---|"]
    for t in TAGS:
        b, s = tzs[t]
        L.append("| %s | %s | UTC%+d:%02d | %s |" % (t, b, -b // 60 if b else 0, abs(b) % 60, s))
    L += ["", "## Per-feature results", "",
          "Columns per disk: nunique / % non-zero. Constant on all 3 disks = **ALL-CONST**.", "",
          "| feature | img1 | img2 | img3 | verdict |", "|---|---|---|---|---|"]
    allconst = []
    for f in allfeats:
        sub = res[res.feature == f].set_index("disk")
        cells = ["%d / %.2f%%%s" % (sub.loc[t, "nunique"], sub.loc[t, "pct_nonzero"],
                                    " (const)" if sub.loc[t, "constant"] else "") if t in sub.index else "n/a"
                 for t in TAGS]
        ac = bool(sub["constant"].all()) and len(sub) == 3
        if ac:
            allconst.append(f)
        L.append("| `%s` | %s | %s | %s | %s |" % (f, *cells, "**ALL-CONST**" if ac else
                                                  ("const on %s" % ",".join(sub.index[sub.constant]) if sub.constant.any() else "varies")))
    L += ["", "Features constant on all three disks: %s" % (", ".join("`%s`" % f for f in allconst) or "none"), ""]
    if ARGS.set == "legacy23":
        L += ["## Diagnoses (evidence per disk)", ""]
        for f in allfeats:
            d = res[(res.feature == f) & (res.diagnosis.notna())]
            if d.empty:
                continue
            L.append("### `%s`" % f)
            for _, r in d.iterrows():
                L.append("- %s: %s" % (r.disk, r.diagnosis))
            L.append("")
        L += ["## Name-based leakage check", "",
              "`credential_tool` / `sniffer_tool` test prefetch names against `cain`, `123wasp`, `ethereal`, `winpcap`, "
              "`netstumbler`, which are the names of img1's own answer-key tools (IMG1_TARGETS in multimodel_eval.py). "
              "Those substrings are scenario knowledge baked into the feature builder: ground-truth leakage, "
              "besides being constant per disk.", ""]
    with open(os.path.join(OUT, f"feature_audit{SUFFIX}.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
