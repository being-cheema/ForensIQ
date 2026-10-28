"""
multimodel_eval.py
==================
Reproducible 3-model benchmark on the 23-feature ForensIQ baseline.

Models      : Isolation Forest, Local Outlier Factor, One-Class SVM
Budget      : top-K most suspicious files, K = 5% of the image (equal for every model)
Outputs     : reports/multimodel_eval/
                results_main.csv, results_ablation.csv, results.json
                <image>_tool_output.txt   (CLI-style detections)
                shap/<image>_<model>_*.csv|png
                multimodel_eval.md

Every number in the report is produced by this script from the extracted MFT /
Prefetch artifacts. Nothing is typed in by hand.

Usage:  python multimodel_eval.py [--images img1 img2 img3] [--svm-n 10000]
"""

import os
import sys
import json
import math
import time
import argparse
import subprocess
import collections

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import feature_engineering as fe
from config import BASE_DIR, WORK_HOURS_START, WORK_HOURS_END
from evaluate_baselines import GROUND_TRUTH_TARGETS as GT_IMG2

OUT = os.path.join(BASE_DIR, "reports", "multimodel_eval")
CACHE = os.path.join(BASE_DIR, ".cache", "multimodel_eval")
SHAP_DIR = os.path.join(OUT, "shap")

BUDGET_PCT = 0.05
EXTRA_BUDGET_PCTS = [0.055, 0.10]
SEEDS = [42, 1337, 9999, 7, 2024]

LEGACY_17 = list(fe.FEATURE_COLUMNS)
NEW_6 = ["is_shortcut_or_trace", "per_file_prefetch_hit", "after_hours_touch",
         "delta_si_fn", "filename_entropy", "path_depth"]

GROUPS = {
    "Temporal": ["delta_mc", "delta_mb", "delta_ab", "future_m", "zero_size_recent",
                 "delta_si_fn", "after_hours_touch"],
    "Path/File": ["size", "is_deleted", "is_exe", "is_archive", "temp_path", "user_path",
                  "path_depth", "filename_entropy", "is_shortcut_or_trace"],
    "Execution/Tool": ["credential_tool", "sniffer_tool", "powershell_exec", "cmd_exec",
                       "script_host", "usb_present", "per_file_prefetch_hit"],
}

MODELS = ["Isolation Forest", "Local Outlier Factor", "One-Class SVM"]

# ----------------------------------------------------------------------------
# Image definitions
# ----------------------------------------------------------------------------
IMG1_TARGETS = [  # reconstructed from the SCHARDT case notes; family hit = any file hit
    {"name": "Cain & Abel (Cain.exe)", "patterns": ["/Program Files/Cain/Cain.exe"]},
    {"name": "Ethereal / WinPcap", "patterns": ["/Program Files/Ethereal/ethereal.exe",
                                                "/WINDOWS/system32/wpcap.dll"]},
    {"name": "NetStumbler", "patterns": ["/Program Files/Network Stumbler/NetStumbler.exe"]},
    {"name": "Password wordlists (ZIP)", "patterns": ["250MB_WORDLIST.ZIP", "biglist_990218.zip"]},
    {"name": "NMEM/NGETTIME (timestomped Novell tools)",
     "patterns": ["/NOVELL/Nut18/NMEM.EXE", "/NOVELL/Nut18/NGETTIME.EXE"], "timestomp": True},
    {"name": "123WASP (UNWISE.EXE, 123wasp.exe)",
     "patterns": ["/Program Files/123WASP/UNWISE.EXE", "/Program Files/123WASP/123wasp.exe"]},
    {"name": "defrag.exe / Anonymizer",
     "patterns": ["/WINDOWS/system32/defrag.exe", "Anonymizer.dll", "AnonymizerBar.dll",
                  "uninst-anonymizer.exe"]},
]

IMG2_TARGETS = [dict(t, timestomp=(t["name"].startswith("Eraser.exe"))) for t in GT_IMG2]

def img3_targets(paths):
    """
    Lone Wolf's official answer key is access-restricted, so these targets come from a published
    third-party analysis of the case (a CDAC internship report on this image) and were each
    confirmed to exist on the disk. A target counts as caught if any copy of the file is flagged.
    Treat them as unofficial ground truth.
    """
    return [
        {"name": "AIRPORT INFORMATION.docx", "patterns": ["AIRPORT INFORMATION.docx"]},
        {"name": "Operation 2nd Hand Smoke.pptx", "patterns": ["Operation 2nd Hand Smoke.pptx"]},
        {"name": "Planning.docx", "patterns": ["/Planning.docx"]},
        {"name": "The Cloudy Manifesto.docx", "patterns": ["The Cloudy Manifesto.docx"]},
        {"name": "Cloudy thoughts (4apr).docx", "patterns": ["Cloudy thoughts (4apr).docx"]},
        {"name": "Brother Chat.gdoc (Google Drive)", "patterns": ["/Google Drive/Brother Chat.gdoc"]},
        {"name": "rootkey.csv (AWS keys in Downloads)", "patterns": ["/Users/jcloudy/Downloads/rootkey.csv"]},
        {"name": "Chrome History database", "patterns": ["/Chrome/User Data/Default/History"]},
        {"name": "Box Sync client", "patterns": ["/Program Files/Box/Box Sync/BoxSync.exe"]},
        {"name": "Dropbox client", "patterns": ["/Program Files (x86)/Dropbox/Client/Dropbox.exe"]},
        {"name": "OneDrive client (jcloudy)", "patterns": ["/Users/jcloudy/AppData/Local/Microsoft/OneDrive/"]},
        {"name": "Cloud-sync desktop shortcuts", "patterns": ["/Users/jcloudy/Desktop/Box Sync.lnk",
                                                               "/Users/jcloudy/Desktop/Dropbox.lnk"]},
    ]


IMAGES = {
    "img1": {"label": "Image 1: XP Hacking (SCHARDT.001)", "scenario": "external",
             "targets": IMG1_TARGETS, "art_dir": os.path.join(BASE_DIR, "runs", "img1", "artifacts")},
    "img2": {"label": "Image 2: Win7 Data Leakage", "scenario": "insider",
             "targets": IMG2_TARGETS, "art_dir": os.path.join(BASE_DIR, "runs", "img2", "artifacts")},
    "img3": {"label": "Image 3: Win10 Lone Wolf", "scenario": "insider",
             "targets": img3_targets, "art_dir": os.path.join(BASE_DIR, "runs", "img3", "artifacts")},
}


# ----------------------------------------------------------------------------
# 23-feature construction
# ----------------------------------------------------------------------------
def shannon(s):
    if not s:
        return 0.0
    c = collections.Counter(s)
    n = len(s)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def build_features(art_dir, tag):
    """17 legacy features via the canonical pipeline code + 6 new per-file features."""
    feat_tmp = os.path.join(CACHE, f"{tag}_feat")
    os.makedirs(feat_tmp, exist_ok=True)
    fe.OUT_DIR, fe.FEAT_DIR = art_dir, feat_tmp
    base = fe.build_macb_features().reset_index(drop=True)

    with open(os.path.join(art_dir, "mft", "mft_records.json"), encoding="utf-8") as f:
        raw = pd.DataFrame(json.load(f))
    raw = raw[raw["type"] == "file"].reset_index(drop=True)
    assert len(raw) == len(base) and (raw["path"].values == base["path"].values).all()
    for c in ("m_time", "a_time", "c_time", "cr_time"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce").fillna(0)

    path = base["path"].astype(str)
    name = path.str.rsplit("/", n=1).str[-1]
    ext = name.str.extract(r"(\.[^.]+)$")[0].fillna("").str.lower()

    df = base.copy()
    df["is_shortcut_or_trace"] = ext.isin([".lnk", ".pf", ".evtx", ".evt", ".log", ".db"]).astype(int)

    pf_path = os.path.join(art_dir, "prefetch", "prefetch_list.json")
    pf = fe.load_json(pf_path, [])
    pf_keys = set()
    for p in pf:
        n = p.get("name", "").upper()
        pf_keys.add(n)
        pf_keys.add(n.rsplit("-", 1)[0])
    df["per_file_prefetch_hit"] = name.str.upper().isin(pf_keys).astype(int)

    def off_hours(t):
        h = pd.to_datetime(t, unit="s", utc=True, errors="coerce").dt.hour
        return (t > 0) & ((h < WORK_HOURS_START) | (h >= WORK_HOURS_END))
    df["after_hours_touch"] = (off_hours(raw["m_time"]) | off_hours(raw["a_time"])).astype(int)

    if "fn_m_time" in raw.columns:
        fn = pd.to_numeric(raw["fn_m_time"], errors="coerce").fillna(0)
        df["delta_si_fn"] = np.where((fn > 0) & (raw["m_time"] > 0), (raw["m_time"] - fn).abs(), 0.0)
    df["filename_entropy"] = name.map(shannon)
    df["path_depth"] = path.str.count("/")

    feats = [c for c in LEGACY_17 + NEW_6 if c in df.columns]
    return df, raw, feats


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
def standardize(X):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def fit_score(model, Xs, seed=42, svm_n=10000):
    """Returns (suspicion score for every row, fitted object). Higher = more anomalous."""
    n = len(Xs)
    if model == "Isolation Forest":
        m = IsolationForest(n_estimators=200, contamination=BUDGET_PCT, random_state=seed, n_jobs=-1).fit(Xs)
        return -m.score_samples(Xs), m
    if model == "Local Outlier Factor":
        m = LocalOutlierFactor(n_neighbors=20, contamination=BUDGET_PCT, n_jobs=-1).fit(Xs)
        return -m.negative_outlier_factor_, m
    if model == "One-Class SVM":
        rng = np.random.RandomState(seed)
        idx = rng.choice(n, size=min(n, svm_n), replace=False)
        m = OneClassSVM(kernel="rbf", nu=BUDGET_PCT, gamma="scale").fit(Xs[idx])
        return -m.decision_function(Xs), m
    raise ValueError(model)


def top_k_mask(score, k):
    order = np.argsort(-score, kind="stable")
    m = np.zeros(len(score), dtype=bool)
    m[order[:k]] = True
    return m, order


# ----------------------------------------------------------------------------
# Scoring against ground truth
# ----------------------------------------------------------------------------
def match_targets(paths, targets):
    active, all_idx = [], set()
    for t in targets:
        idx = []
        for pat in t["patterns"]:
            idx += paths[paths.str.contains(pat, case=False, na=False, regex=False)].index.tolist()
        idx = list(dict.fromkeys(idx))
        if idx:
            active.append(dict(t, idx=idx))
            all_idx.update(idx)
    return active, all_idx


def metrics(mask, active, all_idx):
    n, k = len(mask), int(mask.sum())
    tp = sum(1 for i in all_idx if mask[i])
    fp, fn = k - tp, len(all_idx) - tp
    tn = n - tp - fp - fn
    prec = tp / k if k else 0.0
    rec_f = tp / len(all_idx) if all_idx else 0.0
    f1 = 2 * prec * rec_f / (prec + rec_f) if prec + rec_f else 0.0
    hits = [t for t in active if any(mask[i] for i in t["idx"])]
    return {
        "flagged": k, "targets_total": len(active), "targets_hit": len(hits),
        "target_recall": len(hits) / len(active) if active else 0.0,
        "gt_files": len(all_idx), "gt_files_hit": tp,
        "file_recall": rec_f, "precision": prec, "f1": f1,
        "accuracy": (tp + tn) / n, "hit_names": [t["name"] for t in hits],
        "miss_names": [t["name"] for t in active if t not in hits],
    }


def verdicts(mask, df, raw, active, m, scenario):
    ts_known = [t for t in active if t.get("timestomp")]
    ts_known_hit = [t["name"] for t in ts_known if any(mask[i] for i in t["idx"])]
    fut = int((mask & (df["future_m"].values == 1)).sum())
    sig = int((mask & (raw["m_time"].values > 0) & (raw["m_time"].values < raw["cr_time"].values)
               & ((raw["c_time"].values - raw["cr_time"].values) >= 86400)).sum())
    si_fn = int((mask & (df["delta_si_fn"].values > 0)).sum()) if "delta_si_fn" in df else None
    if ts_known:
        ts_verdict = "YES" if ts_known_hit else "NO"
        ts_basis = "known timestomped target flagged" if ts_known_hit else "known timestomped target missed"
    else:
        ts_verdict, ts_basis = "UNVERIFIED", "no ground-truth timestomp target defined"
    if scenario == "external":
        ins = "N/A (external intrusion)"
    else:
        r = m["target_recall"]
        ins = "CONFIRMED" if r >= 0.5 else ("PARTIAL" if r >= 0.25 else "NOT DETECTED")
    return {"timestomp": ts_verdict, "timestomp_basis": ts_basis, "known_ts_hit": ts_known_hit,
            "future_m_flagged": fut, "backdated_m_signature_flagged": sig,
            "si_fn_mismatch_flagged": si_fn, "insider": ins}


# ----------------------------------------------------------------------------
# SHAP
# ----------------------------------------------------------------------------
def run_shap(model, fitted, Xs, feats, df, mask, active, score, tag, svm_n):
    import shap
    os.makedirs(SHAP_DIR, exist_ok=True)
    rng = np.random.RandomState(0)
    gt_hit = [i for t in active for i in t["idx"] if mask[i]]
    gt_hit = list(dict.fromkeys(gt_hit))[:12]
    if model == "Isolation Forest":
        pool = np.unique(np.concatenate([gt_hit, rng.choice(len(Xs), min(len(Xs), 20000), replace=False)]))
        sv = shap.TreeExplainer(fitted).shap_values(Xs[pool.astype(int)])
        sv = -np.asarray(sv)  # explain suspicion (= -score_samples)
        rows = pool.astype(int)
    else:
        if model == "Local Outlier Factor":
            nov = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=-1).fit(Xs)
            fn = lambda A: -nov.score_samples(A)
        else:
            fn = lambda A: -fitted.decision_function(A)
        bg = Xs[rng.choice(len(Xs), 50, replace=False)]
        rows = np.array(gt_hit, dtype=int)
        if len(rows) == 0:
            return None
        sv = shap.KernelExplainer(fn, bg).shap_values(Xs[rows], nsamples=300, silent=True)
    sv = np.asarray(sv)
    mean_abs = np.abs(sv).mean(0)
    active_feats = int((mean_abs > 1e-9).sum())
    out = pd.DataFrame(sv, columns=feats)
    out.insert(0, "path", df["path"].values[rows])
    out["dominant_feature"] = [feats[j] for j in np.abs(sv).argmax(1)]
    out.to_csv(os.path.join(SHAP_DIR, f"{tag}_{model.replace(' ', '_')}_shap.csv"), index=False)

    order = np.argsort(mean_abs)[::-1][:15]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([feats[j] for j in order][::-1], mean_abs[order][::-1], color="#1f6feb")
    ax.set_title(f"{model} - mean |SHAP| ({'sample + targets' if model == 'Isolation Forest' else 'caught targets'})\n{tag}")
    fig.tight_layout()
    fig.savefig(os.path.join(SHAP_DIR, f"{tag}_{model.replace(' ', '_')}_shap_bar.png"), dpi=130)
    plt.close(fig)
    return {"active_features": active_feats, "n_features": len(feats),
            "mean_abs": dict(zip(feats, map(float, mean_abs))),
            "dominant": dict(zip(out["path"], out["dominant_feature"]))}


# ----------------------------------------------------------------------------
# CLI-style "tool output"
# ----------------------------------------------------------------------------
def tool_output(tag, spec, N, feats, res, shaps, df, scores):
    L = []
    L.append("=" * 78)
    L.append(f" FORENSIQ TRIAGE TOOL OUTPUT - {spec['label']}")
    L.append("=" * 78)
    L.append(f"[+] Files indexed        : {N:,}")
    L.append(f"[+] Features             : {len(feats)} ({', '.join(f for f in NEW_6 if f not in feats) or 'none'} unavailable)")
    L.append(f"[+] Review budget (5%)   : {res['Isolation Forest']['m']['flagged']:,} files")
    for model in MODELS:
        r = res[model]
        m, v = r["m"], r["v"]
        L.append("")
        L.append("-" * 78)
        L.append(f" MODEL: {model}")
        L.append("-" * 78)
        L.append(f" Targets caught : {m['targets_hit']} / {m['targets_total']}  (recall {m['target_recall']*100:.1f}%)")
        L.append(f" Accuracy {m['accuracy']*100:.2f}%  Precision {m['precision']*100:.2f}%  F1 {m['f1']*100:.2f}%  (file-level)")
        L.append(f" TIMESTOMPING   : {v['timestomp']} ({v['timestomp_basis']}); future_m flagged={v['future_m_flagged']}")
        L.append(f" INSIDER ATTACK : {v['insider']}")
        L.append(" Top 20 flagged files:")
        order = np.argsort(-scores[model], kind="stable")[:20]
        dom = (shaps.get(model) or {}).get("dominant", {})
        for rank, i in enumerate(order, 1):
            p = df["path"].values[i]
            L.append(f"  {rank:>2}. score={scores[model][i]:.4f}  {p[-60:]}  {('[' + dom[p] + ']') if p in dom else ''}")
        L.append(" Ground-truth caught:")
        for n in m["hit_names"]:
            L.append(f"   [HIT ] {n}")
        for n in m["miss_names"]:
            L.append(f"   [MISS] {n}")
    text = "\n".join(L)
    with open(os.path.join(OUT, f"{tag}_tool_output.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return text


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", nargs="+", default=["img1", "img2", "img3"])
    ap.add_argument("--svm-n", type=int, default=10000)
    ap.add_argument("--skip-ablation", action="store_true")
    ap.add_argument("--skip-shap", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)

    main_rows, abl_rows, results, skipped = [], [], {}, {}
    for tag in a.images:
        spec = IMAGES[tag]
        if not os.path.exists(os.path.join(spec["art_dir"], "mft", "mft_records.json")):
            skipped[tag] = f"artifacts not found at {spec['art_dir']} (needs extraction from the disk image)"
            print(f"[!] {spec['label']}: NOT RUN - {skipped[tag]}")
            continue
        t0 = time.time()
        df, raw, feats = build_features(spec["art_dir"], tag)
        N = len(df)
        tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
        active, all_idx = match_targets(df["path"], tg)
        print(f"\n[*] {spec['label']}: {N:,} files, {len(feats)} features, "
              f"{len(active)} targets ({len(all_idx)} file records)")
        if "delta_si_fn" not in feats:
            print("    [!] delta_si_fn unavailable: MFT json has no $FILE_NAME times (re-run extractor on the image)")
        Xs = standardize(df[feats].values.astype(float))
        K = int(round(BUDGET_PCT * N))

        res, shaps, scores, fitted = {}, {}, {}, {}
        for model in MODELS:
            s, fm = fit_score(model, Xs, 42, a.svm_n)
            mask, _ = top_k_mask(s, K)
            m = metrics(mask, active, all_idx)
            v = verdicts(mask, df, raw, active, m, spec["scenario"])
            res[model] = {"m": m, "v": v}
            scores[model], fitted[model] = s, fm
            extra = {}
            for pct in EXTRA_BUDGET_PCTS:
                mk, _ = top_k_mask(s, int(round(pct * N)))
                extra[pct] = metrics(mk, active, all_idx)["target_recall"]
            ms = None
            if model == "Isolation Forest":
                rs = []
                for sd in SEEDS:
                    s2, _ = fit_score(model, Xs, sd, a.svm_n)
                    rs.append(metrics(top_k_mask(s2, K)[0], active, all_idx)["target_recall"])
                ms = (float(np.mean(rs)), float(np.std(rs)))
            main_rows.append({
                "image": spec["label"], "model": model, "files": N, "K": K,
                "targets": f"{m['targets_hit']}/{m['targets_total']}",
                "target_recall": round(m["target_recall"], 4),
                "file_recall": round(m["file_recall"], 4),
                "accuracy": round(m["accuracy"], 4), "precision": round(m["precision"], 4),
                "f1": round(m["f1"], 4), "timestomping": v["timestomp"],
                "future_m_flagged": v["future_m_flagged"], "insider": v["insider"],
                "recall_at_5.5pct": round(extra[0.055], 4), "recall_at_10pct": round(extra[0.10], 4),
                "seed_mean": round(ms[0], 4) if ms else "", "seed_std": round(ms[1], 4) if ms else "",
            })
            print(f"    {model:22s} targets {m['targets_hit']}/{m['targets_total']}  "
                  f"acc {m['accuracy']*100:.2f}%  prec {m['precision']*100:.2f}%  ts={v['timestomp']}  insider={v['insider']}")
            if not a.skip_shap:
                try:
                    shaps[model] = run_shap(model, fm, Xs, feats, df, mask, active, s, tag, a.svm_n)
                except Exception as e:  # keep the benchmark even if an explainer fails
                    print(f"    [!] SHAP failed for {model}: {e}")
                    shaps[model] = None
        tool_output(tag, spec, N, feats, res, shaps, df, scores)

        if not a.skip_ablation:
            configs = {"Full (all available)": feats,
                       "Legacy 17 only": [f for f in feats if f in LEGACY_17]}
            for g, cols in GROUPS.items():
                configs[f"Only {g}"] = [f for f in feats if f in cols]
                configs[f"Without {g}"] = [f for f in feats if f not in cols]
            for nf in NEW_6:
                if nf in feats:
                    configs[f"Full minus {nf}"] = [f for f in feats if f != nf]
            for cname, cols in configs.items():
                if not cols:
                    continue
                Xc = standardize(df[cols].values.astype(float))
                for model in MODELS:
                    s, _ = fit_score(model, Xc, 42, a.svm_n)
                    m = metrics(top_k_mask(s, K)[0], active, all_idx)
                    abl_rows.append({"image": spec["label"], "config": cname, "n_features": len(cols),
                                     "model": model, "targets": f"{m['targets_hit']}/{m['targets_total']}",
                                     "target_recall": round(m["target_recall"], 4),
                                     "file_recall": round(m["file_recall"], 4)})
                print(f"    ablation done: {cname}")
        results[tag] = {
            "label": spec["label"], "files": N, "features": feats,
            "targets": len(active), "gt_files": len(all_idx),
            "models": {mo: {"metrics": res[mo]["m"], "verdicts": res[mo]["v"],
                            "shap": ({k: v for k, v in (shaps.get(mo) or {}).items() if k != "dominant"} or None)}
                       for mo in MODELS},
            "seconds": round(time.time() - t0, 1),
        }

    pd.DataFrame(main_rows).to_csv(os.path.join(OUT, "results_main.csv"), index=False)
    pd.DataFrame(abl_rows).to_csv(os.path.join(OUT, "results_ablation.csv"), index=False)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"results": results, "skipped": skipped, "svm_subsample": a.svm_n}, f, indent=2, default=str)
    print(f"\n[+] Wrote results to {OUT}")


if __name__ == "__main__":
    main()
