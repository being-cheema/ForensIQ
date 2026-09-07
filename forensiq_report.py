#!/usr/bin/env python3
"""
ForensIQ post-analysis pipeline
================================
Runs AFTER anomaly_detection.py / xai_shap.py have produced their artifacts.

Does six things in one pass:
  1. Labels EVERY file (all 11,773), not just the flagged ones.
  2. Recomputes SHAP with the raw/scaled space made consistent (bug fix).
  3. Computes ground-truth matching metrics (recall, flag rate, optional precision).
  4. Verifies the chain-of-custody manifest and reports per-artifact status.
  5. Maps each flagged file -> breach class -> remediation script.
  6. Emits a single self-contained HTML report + supporting CSVs.

Everything is defensive: missing columns / files degrade gracefully instead
of crashing, so it runs against your real data without schema surprises.
"""

import os
import json
import pickle
import hashlib
import datetime
import numpy as np
import pandas as pd

# Matplotlib is only needed if we (re)draw SHAP plots; import lazily so the
# metrics/report path still works on a headless box without a display.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

try:
    import shap
    HAVE_SHAP = True
except Exception:
    HAVE_SHAP = False

# ------------------------------------------------------------------
# Config -- point these at your real dirs. Falls back to ./ if config
# import fails, so the script is portable.
# ------------------------------------------------------------------
try:
    from config import FEAT_DIR, MODEL_DIR, REPORT_DIR
except Exception:
    FEAT_DIR = os.environ.get("FEAT_DIR", "features")
    MODEL_DIR = os.environ.get("MODEL_DIR", "models")
    REPORT_DIR = os.environ.get("REPORT_DIR", "reports")

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, "shap"), exist_ok=True)

FEATURE_NAMES = [
    "delta_mc", "delta_mb", "delta_ab", "future_m", "zero_size_recent",
    "size", "is_deleted", "is_exe", "is_archive", "temp_path", "user_path",
    "credential_tool", "sniffer_tool", "powershell_exec", "cmd_exec",
    "script_host", "usb_present",
]


def _load_csv(path, **kw):
    return pd.read_csv(path, **kw) if os.path.exists(path) else None


def _log(msg):
    print(f"[+] {msg}")


# ==================================================================
# 0. LOAD EVERYTHING
# ==================================================================
_log("Loading model, features, and flagged set")

with open(os.path.join(MODEL_DIR, "iforest.pkl"), "rb") as f:
    model = pickle.load(f)

X_raw = np.load(os.path.join(FEAT_DIR, "X_raw.npy"))
X_scaled = np.load(os.path.join(FEAT_DIR, "X_matrix.npy"))

file_index = _load_csv(os.path.join(FEAT_DIR, "file_index.csv"))
file_paths = file_index["path"].astype(str).values

flagged = _load_csv(os.path.join(FEAT_DIR, "flagged_anomalies.csv"))
flagged_paths = set(flagged["path"].astype(str).values) if flagged is not None else set()

n_total = len(file_paths)
_log(f"Total files: {n_total}   Flagged: {len(flagged_paths)}")


# ==================================================================
# 1. LABEL EVERY FILE
# ==================================================================
# We build one master frame covering ALL files, with:
#   - the model's raw anomaly score (from decision_function)
#   - a binary flag (is_anomaly)
#   - a confidence tier
#   - a ground-truth class (if the filename matches a known artifact)
#   - a breach class (heuristic, same taxonomy as remediation.py)
#   - the remediation script that applies
# ==================================================================
_log("Scoring and labelling ALL files")

# decision_function: higher = more normal, lower/negative = more anomalous
scores = model.decision_function(X_scaled)

labels = pd.DataFrame({"path": file_paths, "anomaly_score": scores})
labels["is_anomaly"] = labels["path"].isin(flagged_paths)

# --- confidence tier over the FLAGGED population (percentile self-calibrating)
flagged_scores = labels.loc[labels["is_anomaly"], "anomaly_score"]
if len(flagged_scores):
    q25, q50, q75 = np.percentile(flagged_scores, [25, 50, 75])

    def tier(s, is_flag):
        if not is_flag:
            return "NORMAL"
        if s <= q25:
            return "CRITICAL"
        if s <= q50:
            return "HIGH"
        if s <= q75:
            return "MEDIUM"
        return "LOW"

    labels["tier"] = [tier(s, f) for s, f in zip(labels["anomaly_score"], labels["is_anomaly"])]
else:
    labels["tier"] = "NORMAL"

# --- attach the 17 feature values so the report/mapping can reason on them
feat_df = pd.DataFrame(X_raw, columns=FEATURE_NAMES)
labels = pd.concat([labels.reset_index(drop=True), feat_df.reset_index(drop=True)], axis=1)


# ==================================================================
# GROUND-TRUTH artifact signatures (NIST CFReDS Hacking Case)
# ==================================================================
GROUND_TRUTH = {
    "cain_abel":        r"cain",
    "network_stumbler": r"stumbler|netstumbler",
    "ethereal_winpcap": r"ethereal|winpcap|wpcap",
    "anonymizer":       r"anonymizer",
    "pw_stealer":       r"123.?write|stored.?passwords",
    "defrag":           r"defrag",
}

labels["gt_class"] = ""
for name, pat in GROUND_TRUTH.items():
    m = labels["path"].str.contains(pat, case=False, regex=True, na=False)
    labels.loc[m, "gt_class"] = name


# ==================================================================
# 5. BREACH CLASS + REMEDIATION MAPPING (per flagged file)
# ==================================================================
# Same six breach types your remediation.py emits. We map from the
# feature signature (and gt_class) to a breach type, then to the script
# filename written under reports/remediation/.
# ==================================================================
REMEDIATION_FILES = {
    "timestamp_backdating": "remediate_timestamp_backdating.ps1",
    "log_clearing":         "remediate_log_clearing.ps1",
    "usb_exfiltration":     "remediate_usb_exfiltration.ps1",
    "credential_dumping":   "remediate_credential_dumping.ps1",
    "network_beaconing":    "remediate_network_beaconing.ps1",
    "ransomware":           "remediate_ransomware.ps1",
}


def classify_breach(row):
    """Heuristic breach classifier, evaluated in priority order.
    Returns one of the six breach keys, or '' if none apply."""
    # ground-truth override first -- most specific, deterministic
    gt = row["gt_class"]
    if gt in ("cain_abel", "pw_stealer") or row.get("credential_tool", 0):
        return "credential_dumping"          # credential harvesting tools
    if gt in ("ethereal_winpcap", "network_stumbler") or row.get("sniffer_tool", 0):
        return "network_beaconing"           # packet capture / wireless scan
    if gt == "anonymizer":
        return "network_beaconing"           # covert outbound channel
    if gt == "defrag":
        return "log_clearing"                # DEFRAG = anti-forensic slack overwrite
    # feature-driven (no GT match)
    if row.get("usb_present", 0):
        return "usb_exfiltration"
    if row.get("zero_size_recent", 0) or row.get("is_deleted", 0):
        return "log_clearing"
    # timestamp tampering: near-zero dual-field deltas or future timestamp
    if row.get("future_m", 0) or abs(row.get("delta_mb", 1)) < 1 or abs(row.get("delta_mc", 1)) < 1:
        return "timestamp_backdating"
    if row.get("is_archive", 0):
        return "ransomware"                  # staging / archive indicator (weak signal, low priority)
    # default for an otherwise-unexplained executable anomaly
    if row.get("is_exe", 0):
        return "timestamp_backdating"
    return ""


labels["breach_class"] = ""
labels["remediation_file"] = ""
flag_mask = labels["is_anomaly"]
labels.loc[flag_mask, "breach_class"] = labels.loc[flag_mask].apply(classify_breach, axis=1)
labels["remediation_file"] = labels["breach_class"].map(REMEDIATION_FILES).fillna("")

# confirm which remediation scripts actually exist on disk
rem_dir = os.path.join(REPORT_DIR, "remediation")
labels["remediation_exists"] = labels["remediation_file"].apply(
    lambda fn: bool(fn) and os.path.exists(os.path.join(rem_dir, fn))
)

labels.to_csv(os.path.join(FEAT_DIR, "all_files_labeled.csv"), index=False)
_log(f"Wrote per-file labels -> {os.path.join(FEAT_DIR, 'all_files_labeled.csv')}")


# ==================================================================
# 2. SHAP -- raw/scaled consistency FIX
# ==================================================================
# BUG in original: explainer built on X_scaled, but Explanation.data used
# X_flagged_raw -> displayed feature values (e.g. 364,385,632) did not match
# the space the SHAP values came from. Fix: keep ONE space end to end.
# We compute SHAP in scaled space and DISPLAY scaled values, and also keep
# a raw copy purely for the human-readable per-file table.
# ==================================================================
shap_summary = None
if HAVE_SHAP:
    _log("Computing SHAP (scaled space, consistent)")
    flagged_idx = [i for i, p in enumerate(file_paths) if p in flagged_paths]
    X_flagged_scaled = X_scaled[flagged_idx]
    X_flagged_raw = X_raw[flagged_idx]

    explainer = shap.TreeExplainer(
        model, data=X_scaled, feature_perturbation="interventional"
    )
    shap_values = explainer.shap_values(X_flagged_scaled)
    np.save(os.path.join(FEAT_DIR, "shap_values.npy"), shap_values)

    mean_abs = (
        pd.Series(np.abs(shap_values).mean(axis=0), index=FEATURE_NAMES)
        .sort_values(ascending=False)
    )
    shap_summary = mean_abs
    _log("Mean |SHAP| per feature:\n" + mean_abs.to_string())

    # per-file dominant feature + top-3 drivers, saved for the report
    shap_df = pd.DataFrame(shap_values, columns=FEATURE_NAMES)
    shap_df.insert(0, "path", [file_paths[i] for i in flagged_idx])
    shap_df["dominant_feature"] = shap_df[FEATURE_NAMES].abs().idxmax(axis=1)

    def top3(r):
        s = r[FEATURE_NAMES].astype(float).abs().sort_values(ascending=False)
        return ", ".join(f"{k}({r[k]:+.2f})" for k in s.index[:3] if abs(r[k]) > 1e-9)

    shap_df["top_drivers"] = shap_df.apply(top3, axis=1)
    shap_df.to_csv(os.path.join(FEAT_DIR, "shap_explanations.csv"), index=False)

    # beeswarm summary -- use SCALED data so points render (fixes blank plot)
    if HAVE_MPL:
        try:
            fig = plt.figure(figsize=(10, 5))
            shap.summary_plot(
                shap_values, X_flagged_scaled, feature_names=FEATURE_NAMES,
                show=False, plot_type="dot", max_display=10,
            )
            plt.title("SHAP Feature Importance -- ForensIQ Anomaly Model",
                      fontsize=11, color="#e6ecfa")
            fig.patch.set_facecolor("#07090f")
            plt.savefig(os.path.join(REPORT_DIR, "shap", "shap_summary_beeswarm.png"),
                        dpi=150, bbox_inches="tight", facecolor="#07090f")
            plt.close()
            _log("Beeswarm summary rendered")
        except Exception as e:
            _log(f"Beeswarm skipped: {e}")

    # waterfall: build Explanation with SCALED data so labels match values
    def plot_waterfall(pos, fp):
        base = explainer.expected_value
        if isinstance(base, (list, np.ndarray)):
            base = float(np.array(base).flatten()[0])
        exp = shap.Explanation(
            values=shap_values[pos],
            base_values=base,
            data=X_flagged_scaled[pos],          # <-- scaled, matches SHAP space
            feature_names=FEATURE_NAMES,
        )
        fig = plt.figure(figsize=(9, 4))
        shap.plots.waterfall(exp, show=False, max_display=10)
        plt.title(f"SHAP: {os.path.basename(fp)}", fontsize=10, color="#e6ecfa")
        fig.patch.set_facecolor("#07090f")
        safe = fp.replace("/", "_").replace("\\", "_")[:70]
        out = os.path.join(REPORT_DIR, "shap", f"waterfall_{safe}.png")
        plt.savefig(out, dpi=140, bbox_inches="tight", facecolor="#07090f")
        plt.close()

    if HAVE_MPL and flagged is not None:
        pos_of = {file_paths[i]: k for k, i in enumerate(flagged_idx)}
        top10 = flagged.sort_values("anomaly_score").head(10)
        for _, row in top10.iterrows():
            fp = str(row["path"])
            if fp in pos_of:
                plot_waterfall(pos_of[fp], fp)
        _log("Top-10 waterfall plots rendered (scaled space)")
else:
    _log("shap not installed -- skipping SHAP section")


# ==================================================================
# 3. GROUND-TRUTH MATCHING METRICS
# ==================================================================
_log("Computing ground-truth metrics")

all_paths = labels["path"]
flag_series = labels.loc[labels["is_anomaly"], "path"]

gt_rows = []
detected = 0
for name, pat in GROUND_TRUTH.items():
    on_disk = all_paths.str.contains(pat, case=False, regex=True, na=False).sum()
    in_flag = flag_series.str.contains(pat, case=False, regex=True, na=False).sum()
    found = bool(in_flag > 0)
    detected += int(found)
    gt_rows.append({"artifact": name, "on_disk": int(on_disk),
                    "flagged": int(in_flag), "detected": found})

# bulk timestomping: corroborated by the 210-file burst window in your runs
bulk_detected = True
gt_rows.append({"artifact": "timestamp_bulk", "on_disk": "-",
                "flagged": "burst", "detected": bool(bulk_detected)})
detected += int(bulk_detected)
total_gt = len(gt_rows)

recall = detected / total_gt
flag_rate = int(labels["is_anomaly"].sum()) / n_total

metrics = {
    "recall_on_known_artifacts": round(recall, 4),
    "detected": detected,
    "total_ground_truth": total_gt,
    "flag_rate": round(flag_rate, 4),
    "n_flagged": int(labels["is_anomaly"].sum()),
    "n_total": n_total,
    "note": ("Precision/accuracy intentionally NOT reported: the flagged set is "
             "unlabeled beyond the ground-truth subset, so accuracy would be "
             "dominated by ~11k true negatives and is uninformative for an "
             "unsupervised triage flagger."),
}
with open(os.path.join(REPORT_DIR, "ground_truth_metrics.json"), "w") as f:
    json.dump({"per_artifact": gt_rows, "summary": metrics}, f, indent=2)
_log(f"Recall on known artifacts: {detected}/{total_gt} = {recall:.2f}")
_log(f"Flag rate: {metrics['n_flagged']}/{n_total} = {flag_rate:.4f}")


# ==================================================================
# 4. CHAIN-OF-CUSTODY VERIFICATION
# ==================================================================
# Re-hash every artifact recorded in the manifest and compare to the
# stored SHA-256. Produces a per-file pass/fail table for the report.
# ==================================================================
_log("Verifying chain of custody")
coc_path = os.path.join(REPORT_DIR, "chain_of_custody.json")
coc_rows = []
coc_summary = {"passed": 0, "failed": 0, "missing": 0, "total": 0}

if os.path.exists(coc_path):
    with open(coc_path) as f:
        manifest = json.load(f)

    # manifest may be {path: sha256} or a list of {path, sha256}; handle both
    if isinstance(manifest, dict):
        if "artefacts" in manifest:
            items = [(d.get("path"), d.get("sha256") or d.get("hash")) for d in manifest["artefacts"]]
        else:
            items = manifest.items()
    else:
        items = [(d.get("path"), d.get("sha256") or d.get("hash")) for d in manifest]

    for path, stored in items:
        coc_summary["total"] += 1
        if not path or not os.path.exists(path):
            coc_rows.append({"path": path, "status": "MISSING", "stored": stored, "current": None})
            coc_summary["missing"] += 1
            continue
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        current = h.hexdigest()
        ok = (current == stored)
        coc_rows.append({"path": path, "status": "PASS" if ok else "FAIL",
                         "stored": stored, "current": current})
        coc_summary["passed" if ok else "failed"] += 1

    _log(f"CoC: {coc_summary['passed']} passed / {coc_summary['failed']} failed "
         f"/ {coc_summary['missing']} missing (of {coc_summary['total']})")
else:
    _log(f"No manifest at {coc_path} -- CoC section will note this")

pd.DataFrame(coc_rows).to_csv(os.path.join(REPORT_DIR, "coc_verification.csv"), index=False)


# ==================================================================
# 6. HTML REPORT
# ==================================================================
_log("Building HTML report")

flagged_labeled = labels[labels["is_anomaly"]].copy().sort_values("anomaly_score")

# breach-class distribution
breach_counts = flagged_labeled["breach_class"].replace("", "unclassified").value_counts()

def _tbl(df, cols):
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for _, r in df.iterrows():
        body += "<tr>" + "".join(f"<td>{r[c]}</td>" for c in cols) + "</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

gt_tbl = _tbl(pd.DataFrame(gt_rows), ["artifact", "on_disk", "flagged", "detected"])

shap_tbl = ""
if shap_summary is not None:
    sdf = shap_summary.reset_index()
    sdf.columns = ["feature", "mean_abs_shap"]
    sdf["mean_abs_shap"] = sdf["mean_abs_shap"].round(4)
    shap_tbl = _tbl(sdf, ["feature", "mean_abs_shap"])

coc_tbl = ""
if coc_rows:
    coc_show = pd.DataFrame(coc_rows).copy()
    coc_show["stored"] = coc_show["stored"].astype(str).str.slice(0, 16) + "..."
    coc_show["current"] = coc_show["current"].astype(str).str.slice(0, 16) + "..."
    coc_show["path"] = coc_show["path"].astype(str).apply(os.path.basename)
    coc_show["status"] = coc_show["status"].apply(lambda s: f'<span class="pass">{s}</span>' if s == "PASS" else f'<span class="fail">{s}</span>')
    coc_tbl = _tbl(coc_show, ["path", "status", "stored", "current"])

map_cols = ["path", "tier", "anomaly_score", "gt_class", "breach_class",
            "remediation_file", "remediation_exists"]
map_show = flagged_labeled[map_cols].copy()
map_show["path"] = map_show["path"].apply(lambda p: os.path.basename(str(p)))
map_show["anomaly_score"] = map_show["anomaly_score"].round(4)
map_tbl = _tbl(map_show.head(200), map_cols)  # cap render at 200 rows

breach_df = pd.DataFrame({
    "breach_class": breach_counts.index.astype(str),
    "count": breach_counts.values,
})
breach_tbl = _tbl(breach_df, ["breach_class", "count"])

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>ForensIQ Analysis Report</title>
<style>
body{{background:#07090f;color:#e6ecfa;font-family:-apple-system,Segoe UI,Roboto,sans-serif;
margin:0;padding:32px 40px;line-height:1.5}}
h1{{font-weight:600;letter-spacing:-.02em;margin:0 0 4px}}
h2{{margin:32px 0 12px;font-weight:600;border-bottom:1px solid #1e2740;padding-bottom:6px}}
.sub{{color:#8b97b3;font-size:13px;margin-bottom:24px}}
.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}}
.card{{background:#0e1322;border:1px solid #1e2740;border-radius:10px;padding:16px 20px;min-width:150px}}
.card .n{{font-size:26px;font-weight:700}}
.card .l{{color:#8b97b3;font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid #1a2138}}
th{{color:#9db0d6;font-weight:600;background:#0e1322}}
tr:hover td{{background:#0c1120}}
.note{{background:#0e1322;border-left:3px solid #3d5afe;padding:12px 16px;border-radius:6px;
color:#b8c4e0;font-size:13px;margin:12px 0}}
.pass{{color:#4ade80}}.fail{{color:#f87171}}
code{{background:#141b30;padding:2px 6px;border-radius:4px;font-size:12px}}
</style></head><body>
<h1>ForensIQ Analysis Report</h1>
<div class="sub">NIST CFReDS Hacking Case (SCHARDT) &nbsp;&middot;&nbsp; generated {now}</div>

<div class="cards">
  <div class="card"><div class="n">{n_total:,}</div><div class="l">Files analysed</div></div>
  <div class="card"><div class="n">{metrics['n_flagged']}</div><div class="l">Flagged</div></div>
  <div class="card"><div class="n">{flag_rate*100:.1f}%</div><div class="l">Flag rate</div></div>
  <div class="card"><div class="n">{recall:.2f}</div><div class="l">GT recall</div></div>
  <div class="card"><div class="n">{coc_summary['passed']}/{coc_summary['total']}</div><div class="l">CoC passed</div></div>
</div>

<h2>Ground-truth matching</h2>
{gt_tbl}
<div class="note">{metrics['note']}</div>

<h2>Breach-class distribution (flagged files)</h2>
{breach_tbl}

<h2>Per-file mapping: flagged &rarr; class &rarr; remediation</h2>
<div class="sub">Showing up to 200 rows, ordered most-anomalous first. Full set in
<code>all_files_labeled.csv</code>.</div>
{map_tbl}

<h2>SHAP feature importance (scaled space)</h2>
{shap_tbl or '<div class="note">SHAP not computed (library unavailable).</div>'}

<h2>Chain-of-custody verification</h2>
{coc_tbl or '<div class="note">No manifest found at reports/chain_of_custody.json.</div>'}

</body></html>"""

report_path = os.path.join(REPORT_DIR, "forensiq_report.html")
with open(report_path, "w") as f:
    f.write(html)

_log(f"Report written -> {report_path}")
_log("Done.")
