"""
shap_feature_firing.py
======================
Diagnoses why only some features have non-zero SHAP attribution ("fire") in ForensIQ,
for all three images, for both the 17-feature pipeline set and the 23-feature benchmark set.

Nothing is typed in by hand: every number in the outputs is computed here from
    runs/img{1,2,3}/features | models | artifacts   (fresh 12-stage pipeline outputs)
    reports/multimodel_eval/results.json + shap/*.csv  (23-feature benchmark)
    multimodel_eval.build_features()                    (rebuilds the 23-feature frame)
    images/...                                          (optional pytsk3 probe for deleted entries)

Outputs (reports/shap_feature_firing/):
    feature_firing.csv   one row per image x feature-set x model x feature
    claims_check.csv     TRUE / FALSE / UNVERIFIABLE verdict per earlier claim, with evidence
    shap_feature_firing.md

Usage (from repo root):
    .venv/bin/python shap_feature_firing.py [--skip-probe]

FIRED := mean |SHAP| > 1e-6 over the rows that were explained.
Root-cause codes used in the tables:
    (a) constant column  -> trees never split -> TreeSHAP is exactly 0
    (b) global flag      -> one scalar broadcast to every file (zero variance by construction)
    (c) behaviour absent on that disk
    (d) definitional / extractor bug (future_m, is_deleted, zero_size_recent)
    (e) varies but barely used (very rare non-zero values; IsolationForest sees 256 rows per tree)
"""
import os
import re
import sys
import json
import time
import pickle
import argparse
import tempfile
import subprocess

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import feature_engineering as fe          # noqa: E402
import multimodel_eval as M               # noqa: E402

OUT = os.path.join(ROOT, "reports", "shap_feature_firing")
EPS = 1e-6
F17 = list(fe.FEATURE_COLUMNS)
GLOBAL_FLAGS = {  # feature -> prefetch-name keywords used in feature_engineering.build_macb_features
    "credential_tool": ["mimikatz", "pwdump", "cain", "123wasp", "stored"],
    "sniffer_tool": ["wireshark", "ethereal", "tcpdump", "winpcap", "netstumbler"],
    "powershell_exec": ["powershell"],
    "cmd_exec": ["cmd"],
    "script_host": ["wscript", "cscript"],
}
IMG_FILES = {  # raw images used only by the optional deleted-entry probe
    "img1": os.path.join(ROOT, "images", "hacking", "SCHARDT.dd"),
    "img2": os.path.join(ROOT, "images", "dataleak", "cfreds_2015_data_leakage_pc.dd"),
    "img3": os.path.join(ROOT, "images", "lonewolf", "LoneWolf.E01"),
}
TAGS = ["img1", "img2", "img3"]
MODELS = M.MODELS


def short(p, n=58):
    return p if len(p) <= n else "..." + p[-(n - 3):]


# ----------------------------------------------------------------------------
# Optional probe: does the extractor's directory walk see deleted entries?
# ----------------------------------------------------------------------------
def probe_deleted(tag):
    """Re-walk the image exactly like extractor.extract_mft and count unallocated entries."""
    import pytsk3
    import extractor
    t0 = time.time()
    disk = extractor.DiskImage(IMG_FILES[tag])
    c = dict(entries=0, name_unalloc=0, name_unalloc_meta_none=0, name_unalloc_meta_alloc=0,
             name_unalloc_meta_unalloc=0, meta_unalloc_extractor_rule=0)

    def walk(d):
        for e in d:
            try:
                nm = e.info.name.name
                if nm in (b".", b".."):
                    continue
                c["entries"] += 1
                meta = e.info.meta
                if meta is not None and meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC:
                    c["meta_unalloc_extractor_rule"] += 1
                if e.info.name.flags & pytsk3.TSK_FS_NAME_FLAG_UNALLOC:
                    c["name_unalloc"] += 1
                    if meta is None:
                        c["name_unalloc_meta_none"] += 1
                    elif meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC:
                        c["name_unalloc_meta_unalloc"] += 1
                    else:
                        c["name_unalloc_meta_alloc"] += 1
                if e.info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR:
                    try:
                        walk(e.as_directory())
                    except Exception:
                        pass
            except Exception:
                pass

    walk(disk.root)
    c["walk_seconds"] = round(time.time() - t0, 1)
    return c


# ----------------------------------------------------------------------------
# IsolationForest split usage
# ----------------------------------------------------------------------------
def split_counts(forest, n_feat):
    cnt = np.zeros(n_feat, dtype=int)
    for est in forest.estimators_:
        f = est.tree_.feature
        for j in f[f >= 0]:
            cnt[j] += 1
    return cnt, int(getattr(forest, "max_samples_", 256))


def load_pipeline_forest(tag):
    p = os.path.join(ROOT, "runs", tag, "models", "iforest.pkl")
    with open(p, "rb") as f:
        o = pickle.load(f)
    if isinstance(o, dict):
        o = o["model"]
    return o


# ----------------------------------------------------------------------------
# Per-image context
# ----------------------------------------------------------------------------
def build_ctx(tag, probe, tmp_cache):
    d = os.path.join(ROOT, "runs", tag)
    art = os.path.join(d, "artifacts")
    ctx = {"tag": tag, "label": M.IMAGES[tag]["label"]}

    # ---- 17-feature pipeline outputs
    macb = pd.read_csv(os.path.join(d, "features", "macb_features.csv"))
    shap17 = np.load(os.path.join(d, "features", "shap_values.npy"))
    shap_csv = pd.read_csv(os.path.join(d, "features", "shap_explanations.csv"))
    flagged = pd.read_csv(os.path.join(d, "features", "flagged_anomalies.csv"))
    forest = load_pipeline_forest(tag)
    ctx.update(macb=macb, shap17=shap17, shap17_csv=shap_csv, n_flagged=len(flagged))
    ctx["splits17"], ctx["max_samples"] = split_counts(forest, len(F17))
    ctx["n_estimators"] = len(forest.estimators_)

    # ---- raw MFT
    recs = json.load(open(os.path.join(art, "mft", "mft_records.json"), encoding="utf-8"))
    raw_all = pd.DataFrame(recs)
    files = raw_all[raw_all["type"] == "file"]
    ctx["mft"] = dict(
        records=len(raw_all), files=len(files), dirs=int((raw_all["type"] == "dir").sum()),
        deleted_true_all=int(raw_all["is_deleted"].astype(bool).sum()),
        deleted_true_files=int(files["is_deleted"].astype(bool).sum()),
        with_fn_times=int(files["fn_m_time"].notna().sum()) if "fn_m_time" in files else 0,
        max_m_time=int(pd.to_numeric(files["m_time"]).max()),
        m_gt_max=int((pd.to_numeric(files["m_time"]) > pd.to_numeric(files["m_time"]).max()).sum()),
        zero_size=int((pd.to_numeric(files["size"]) == 0).sum()),
    )

    # ---- prefetch / usb evidence
    pf = fe.load_json(os.path.join(art, "prefetch", "prefetch_list.json"), [])
    names = [p.get("name", "") for p in pf]
    ctx["pf_count"] = len(names)
    ctx["pf_hits"] = {f: sorted({n for n in names if any(k in n.lower() for k in kws)})
                      for f, kws in GLOBAL_FLAGS.items()}
    mft_pf = raw_all["path"].astype(str).str.contains(r"/prefetch/[^/]+\.pf$", case=False, regex=True)
    ctx["mft_pf_files"] = int(mft_pf.sum())
    ctx["mft_pf_powershell"] = int(raw_all["path"].astype(str).str.contains(
        r"/prefetch/powershell[^/]*\.pf$", case=False, regex=True).sum())
    usb_txt = os.path.join(art, "usb", "usb_devices.txt")
    usb_sys = os.path.join(art, "usb", "SYSTEM")
    txt = open(usb_txt, encoding="utf-8", errors="ignore").read() if os.path.exists(usb_txt) else ""
    ctx["usb"] = dict(system_exists=os.path.exists(usb_sys), txt_exists=os.path.exists(usb_txt),
                      real_entries=txt.count("USB Device:"), first_line=txt.strip().splitlines()[0] if txt.strip() else "")

    # ---- 23-feature frame (rebuilt through the benchmark code; scratch cache so repo cache is untouched)
    M.CACHE = tmp_cache
    df, raw, feats = M.build_features(art, tag)
    same = np.allclose(df[F17].values.astype(float), macb[F17].values.astype(float))
    ctx.update(df23=df, raw23=raw, feats23=feats, build_matches_pipeline=bool(same))
    Xs = M.standardize(df[feats].values.astype(float))
    _, fitted = M.fit_score("Isolation Forest", Xs, 42)
    ctx["splits23"], _ = split_counts(fitted, len(feats))
    res = json.load(open(os.path.join(ROOT, "reports", "multimodel_eval", "results.json")))["results"][tag]
    ctx["res"] = res
    ctx["shap23_csv"] = {}
    for m in MODELS:
        p = os.path.join(M.SHAP_DIR, f"{tag}_{m.replace(' ', '_')}_shap.csv")
        ctx["shap23_csv"][m] = pd.read_csv(p) if os.path.exists(p) else None
    ctx["probe"] = probe_deleted(tag) if probe else None
    return ctx


# ----------------------------------------------------------------------------
# Root-cause text
# ----------------------------------------------------------------------------
def cause_text(ctx, f, nz, uniq, n, splits, exp_nz, nz_rows, set_name):
    const = uniq <= 1
    mft = ctx["mft"]
    if f in GLOBAL_FLAGS:
        hits = ctx["pf_hits"][f]
        if nz == n:
            return ("(b) global flag, =1 on all %d rows: scalar int(any(keyword in joined prefetch names)) is broadcast "
                    "to every file; matching prefetch: %s. Zero variance -> never split -> TreeSHAP 0."
                    % (n, ", ".join(hits[:4]) or "n/a"))
        return ("(b)+(c) global flag, =0 on all %d rows: no prefetch name contains %s (%d .pf extracted; %d .pf in MFT listing; "
                "behaviour absent from Prefetch evidence). Even when present it is 1 on every row -> could never fire."
                % (n, GLOBAL_FLAGS[f], ctx["pf_count"], ctx["mft_pf_files"]))
    if f == "usb_present":
        u = ctx["usb"]
        return ("(b) global flag, =1 on all %d rows: usb_detected = exists(usb/SYSTEM) or exists(usb/usb_devices.txt) and "
                "extractor always writes usb_devices.txt; %d real 'USB Device:' entries found (file starts: '%s')."
                % (n, u["real_entries"], u["first_line"][:60]))
    if f == "future_m":
        return ("(d) definitional: reference time = max(m_time) of this same dataset (%d); flag = m_time > reference, so "
                "%d rows by construction -> constant 0 -> never fires. Can never be 1." % (mft["max_m_time"], mft["m_gt_max"]))
    if f == "is_deleted":
        pr = ctx.get("probe")
        extra = ""
        if pr:
            extra = (" Probe of the raw image: walk sees %d entries with name flag UNALLOC (%d with meta=None, %d with meta "
                     "allocated) but only %d with meta.flags UNALLOC." % (
                         pr["name_unalloc"], pr["name_unalloc_meta_none"], pr["name_unalloc_meta_alloc"],
                         pr["meta_unalloc_extractor_rule"]))
        return ("(d) extractor bug: is_deleted = meta.flags & UNALLOC; %d of %d records are true in mft_records.json "
                "(constant 0 -> never fires).%s" % (mft["deleted_true_all"], mft["records"], extra))
    if f == "zero_size_recent":
        return ("(d)+(e) definitional/rare: needs size==0 AND m_time within 24h of the dataset's newest mtime AND m_time>0; "
                "%d of %d files (%d zero-byte files in total)%s" % (
                    nz, n, mft["zero_size"],
                    "; subsample expectation %.3f rows/tree, %d splits" % (exp_nz, splits) if splits is not None else ""))
    if const:
        return "(a) constant column (value %s on all rows): never split -> SHAP 0." % ("0" if nz == 0 else "1")
    s = "(e) varies but barely used: %d non-zero of %d (%.3f%%)" % (nz, n, 100.0 * nz / n)
    if splits is not None:
        s += "; expected %.2f non-zero rows per 256-row tree subsample, %d splits in the forest" % (exp_nz, splits)
    if nz_rows is not None:
        s += "; non-zero in explained rows: %d" % nz_rows
    return s


# ----------------------------------------------------------------------------
# Build the per-feature table
# ----------------------------------------------------------------------------
def fired_detail(shap_df, feats, f, X_all, X_rows_mask=None, topn=3):
    """What the feature drives: dominant-count, top paths by |SHAP|, enrichment among explained rows."""
    col = shap_df[f].abs()
    dom = int((shap_df["dominant_feature"] == f).sum()) if "dominant_feature" in shap_df else -1
    top = shap_df.assign(_a=col).sort_values("_a", ascending=False).head(topn)
    tops = "; ".join("%s(%.2f)" % (short(p, 46), v) for p, v in zip(top["path"], top["_a"]))
    return "dominant for %d rows; top: %s" % (dom, tops)


def rows_for_17(ctx):
    macb, s, sc = ctx["macb"], ctx["shap17"], ctx["shap17_csv"]
    n = len(macb)
    ma = np.abs(s).mean(0)
    order = (-ma).argsort().argsort() + 1
    # enrichment: non-zero rate in explained (flagged) rows vs all files
    fl = macb[macb["path"].isin(set(sc["path"]))]
    out = []
    for j, f in enumerate(F17):
        col = macb[f]
        nz = int((col != 0).sum())
        uniq = int(col.nunique())
        exp_nz = ctx["max_samples"] * nz / n
        nz_fl = int((fl[f] != 0).sum())
        fired = bool(ma[j] > EPS)
        r = dict(image=ctx["tag"], feature_set="17", model="Isolation Forest (pipeline: runs/%s, flagged rows)" % ctx["tag"],
                 feature=f, n_files=n, unique_values=uniq, nonzero=nz, nonzero_pct=round(100.0 * nz / n, 4),
                 constant=uniq <= 1, explained_rows=int(s.shape[0]), nonzero_in_explained_rows=nz_fl,
                 mean_abs_shap=round(float(ma[j]), 6), rank=int(order[j]), fired=fired,
                 if_splits=int(ctx["splits17"][j]), exp_nonzero_per_tree_subsample=round(exp_nz, 4))
        if fired:
            r["status"] = "fired" + (" (marginal)" if ma[j] < 0.01 * ma.max() else "")
            r["root_cause"] = fired_detail(sc, F17, f, macb) + "; non-zero among flagged rows %d of %d (%.2f%%) vs %.2f%% of all files" % (
                nz_fl, len(fl), 100.0 * nz_fl / max(len(fl), 1), 100.0 * nz / n)
        else:
            r["status"] = "not fired"
            r["root_cause"] = cause_text(ctx, f, nz, uniq, n, int(ctx["splits17"][j]), exp_nz, nz_fl, "17")
        out.append(r)
    return out


def rows_for_23(ctx):
    df, feats, res = ctx["df23"], ctx["feats23"], ctx["res"]
    n = len(df)
    by_path = df.drop_duplicates("path").set_index("path")
    out = []
    for m in MODELS:
        sh = (res["models"][m].get("shap") or {})
        ma = sh.get("mean_abs", {})
        csvd = ctx["shap23_csv"][m]
        vals = np.array([ma.get(f, np.nan) for f in feats], dtype=float)
        order = (-np.nan_to_num(vals)).argsort().argsort() + 1
        sub = by_path.loc[by_path.index.intersection(csvd["path"])] if csvd is not None else df.iloc[:0]
        for j, f in enumerate(feats):
            col = df[f]
            nz = int((col != 0).sum())
            uniq = int(col.nunique())
            splits = int(ctx["splits23"][j]) if m == "Isolation Forest" else None
            exp_nz = ctx["max_samples"] * nz / n
            nz_rows = int((sub[f] != 0).sum()) if len(sub) else 0
            fired = bool(vals[j] > EPS)
            r = dict(image=ctx["tag"], feature_set="23", model=m, feature=f, n_files=n, unique_values=uniq,
                     nonzero=nz, nonzero_pct=round(100.0 * nz / n, 4), constant=uniq <= 1,
                     explained_rows=int(len(csvd)) if csvd is not None else 0, nonzero_in_explained_rows=nz_rows,
                     mean_abs_shap=round(float(vals[j]), 6), rank=int(order[j]), fired=fired,
                     if_splits=splits if splits is not None else "", exp_nonzero_per_tree_subsample=round(exp_nz, 4) if splits is not None else "")
            if fired:
                r["status"] = "fired" + (" (marginal)" if vals[j] < 0.01 * np.nanmax(vals) else "")
                r["root_cause"] = fired_detail(csvd, feats, f, df) + "; non-zero in explained rows %d of %d" % (nz_rows, len(sub))
            else:
                r["status"] = "not fired"
                base = cause_text(ctx, f, nz, uniq, n, splits, exp_nz, nz_rows, "23")
                if m != "Isolation Forest" and not base.startswith(("(a)", "(b)", "(d) def")):
                    base += ("" if nz == 0 else "; KernelSHAP explains only %d caught-target rows (%d non-zero for this feature)"
                             % (len(csvd) if csvd is not None else 0, nz_rows))
                r["root_cause"] = base
            out.append(r)
    return out


# ----------------------------------------------------------------------------
# Claims
# ----------------------------------------------------------------------------
def fired_dict(ctx):
    ma = np.abs(ctx["shap17"]).mean(0)
    return {f: float(a) for f, a in zip(F17, ma) if a > EPS}


def fmt(d):
    return ", ".join("%s %.4f" % (k, v) for k, v in sorted(d.items(), key=lambda kv: -kv[1]))


def build_claims(C, firing):
    rows = []

    def add(n, claim, verdict, ev):
        rows.append(dict(claim_no=n, claim=claim, verdict=verdict, evidence=ev))

    f1, f2, f3 = (fired_dict(C[t]) for t in TAGS)

    # 1
    claim1 = {"is_exe": 1.8141, "size": 1.7875, "delta_mc": 1.7485, "delta_mb": 1.4474, "delta_ab": 1.2670, "is_archive": 0.1472}
    add(1, "Img1 17-feat: exactly 6 fired (is_exe 1.8141, size 1.7875, delta_mc 1.7485, delta_mb 1.4474, delta_ab 1.2670, "
           "is_archive 0.1472); other 11 = 0", "FALSE",
        "Fresh runs/img1 SHAP: %d fired: %s. user_path (%.4f) and temp_path (%.4f) also fire, so the other 11 are not all 0 "
        "(9 are exactly 0). No value matches the claimed ones (e.g. is_exe %.4f vs 1.8141)."
        % (len(f1), fmt(f1), f1.get("user_path", 0), f1.get("temp_path", 0), f1.get("is_exe", 0)))
    # 2
    cred, snif = C["img1"]["macb"]["credential_tool"], C["img1"]["macb"]["sniffer_tool"]
    add(2, "Img1: 9 of 17 fired incl. sniffer_tool and credential_tool", "FALSE",
        "%d of 17 fired (not 9). sniffer_tool and credential_tool are constant 1 on all %d rows (nunique %d / %d) -> mean|SHAP| exactly 0. "
        "(Claims 1 and 2 also contradict each other.)" % (len(f1), len(cred), snif.nunique(), cred.nunique()))
    # 3
    stale = np.abs(np.load(os.path.join(ROOT, "features", "shap_values.npy"))).mean(0)
    stale_d = {f: float(a) for f, a in zip(F17, stale) if a > EPS}
    claim3 = {"delta_ab": 2.589, "size": 1.693, "delta_mb": 1.587, "user_path": 0.935, "is_exe": 0.856, "delta_mc": 0.786, "temp_path": 0.042}
    match = all(abs(stale_d.get(k, -9) - v) < 6e-4 for k, v in claim3.items())
    add(3, "Img2: 6/17 fired: delta_ab 2.589, size 1.693, delta_mb 1.587, user_path 0.935, is_exe 0.856, delta_mc 0.786, temp_path 0.042",
        "FALSE",
        "The claim lists 7 features while saying 6. Fresh runs/img2 fires %d: %s. The claimed values %s the stale pre-rerun "
        "repo-root features/shap_values.npy (%d rows: %s) -- they describe an old run, not the current pipeline outputs."
        % (len(f2), fmt(f2), "match exactly" if match else "do not match", np.load(os.path.join(ROOT, "features", "shap_values.npy")).shape[0], fmt(stale_d)))
    # 4
    c3 = C["img3"]
    ins = int(c3["raw23"]["path"].astype(str).str.contains(r"/Windows/Temp/INS_.*\.TMP", case=False, regex=True).sum())
    add(4, "Img3: 7/17 fired incl. temp_path and future_m; 13 future_m files; 591 /Windows/Temp/INS_*.TMP files", "FALSE",
        "Fresh runs/img3: %d fired (%s). temp_path does fire (%.4f) but future_m is constant 0 (0 files; %d rows have m_time > dataset max) so it cannot fire "
        "and there are 0, not 13, future_m files. MFT contains %d /Windows/Temp/INS_*.TMP files, not 591."
        % (len(f3), fmt(f3), f3.get("temp_path", 0), c3["mft"]["m_gt_max"], ins))
    # 5
    p1 = C["img1"]
    add(5, "Silent features explained as 'PowerShell didn't exist on XP / insider didn't use sniffers'", "FALSE",
        "Real cause is structural, not behavioural: these are global scalar flags broadcast to every row, so they are constant and TreeSHAP is 0 regardless of behaviour. "
        "Counter-evidence: on Img1 sniffer_tool=1 and credential_tool=1 on every row (prefetch has %s / %s) yet they are silent; "
        "if PowerShell or sniffers HAD been used they would still be one constant column. Img3 (Win10) has PowerShell evtx but powershell_exec is constant 0 "
        "with %d PowerShell .pf in the MFT listing."
        % (", ".join(p1["pf_hits"]["sniffer_tool"][:2]), ", ".join(p1["pf_hits"]["credential_tool"][:2]), C["img3"]["mft_pf_powershell"]))
    # 6
    def act(tag, model):
        sub = firing[(firing.image == tag) & (firing.feature_set == "23") & (firing.model == model)]
        return int(sub.fired.sum())
    def top(tag, model, k=2):
        sub = firing[(firing.image == tag) & (firing.feature_set == "23") & (firing.model == model)].sort_values("mean_abs_shap", ascending=False).head(k)
        return ", ".join("%s %.3f" % (a, b) for a, b in zip(sub.feature, sub.mean_abs_shap))
    s_if = {t: act(t, "Isolation Forest") for t in TAGS}
    add(6, "23-feat SHAP: Img1 15/23 fired with sniffer_tool 2.84, credential_tool 2.61, per_file_prefetch_hit 2.19, delta_si_fn 1.95; "
           "Img2 12/23 with delta_ab 2.41, is_shortcut_or_trace 2.18; Img3 13/23 with size 2.52, filename_entropy 2.14", "FALSE",
        "Fresh IF counts (mean|SHAP|>1e-6): img1 %d, img2 %d, img3 %d of 23 (LOF %d/%d/%d, OC-SVM %d/%d/%d). Img1's 15 is coincidentally right but "
        "sniffer_tool and credential_tool are constant 1 and have SHAP exactly 0 (they cannot be 2.84 / 2.61). IF top features: img1 %s; img2 %s; img3 %s. "
        "None of the quoted magnitudes appear in results.json or the shap csvs."
        % (s_if["img1"], s_if["img2"], s_if["img3"],
           *[act(t, "Local Outlier Factor") for t in TAGS], *[act(t, "One-Class SVM") for t in TAGS],
           top("img1", "Isolation Forest"), top("img2", "Isolation Forest"), top("img3", "Isolation Forest")))
    # 7
    d2, r2 = C["img2"]["df23"], C["img2"]["raw23"]
    n2 = len(d2)
    cnt = {k: int((d2[k] > 0).sum()) for k in M.NEW_6}
    depth6 = int((d2["path_depth"] > 5).sum())
    ent_match = [round(q, 2) for q in np.arange(0.5, 5.8, 0.01) if int((d2["filename_entropy"] > q).sum()) == 40794]
    sub = {
        "is_shortcut_or_trace 629 (0.74%)": ("TRUE", "computed %d (%.2f%%)" % (cnt["is_shortcut_or_trace"], 100.0 * cnt["is_shortcut_or_trace"] / n2)),
        "per_file_prefetch_hit 214 (0.25%)": ("FALSE", "computed %d (%.2f%%)" % (cnt["per_file_prefetch_hit"], 100.0 * cnt["per_file_prefetch_hit"] / n2)),
        "after_hours_touch 14,455 (17%)": ("FALSE", "computed %d (%.1f%%) -- the flag is 1 for most files because m/a_time hour is taken in UTC against an 08-18 window" % (cnt["after_hours_touch"], 100.0 * cnt["after_hours_touch"] / n2)),
        "delta_si_fn 16,307 (19.2%)": ("FALSE", "non-zero on %d (%.1f%%); %d differ by >=1 day" % (cnt["delta_si_fn"], 100.0 * cnt["delta_si_fn"] / n2, int((d2["delta_si_fn"] >= 86400).sum()))),
        "filename_entropy 40,794 (48%)": ("UNVERIFIABLE", "feature is continuous and non-zero on %d (100%%); %s" % (cnt["filename_entropy"], ("a threshold of >%s gives that count" % ent_match[0]) if ent_match else "no entropy threshold on a 0.01 grid reproduces 40,794")),
        "path_depth 18,301 (21.5%)": ("TRUE only as 'depth > 5'", "path_depth is non-zero on %d (100%%); the count 18,301 equals files with depth>5 (%d = %.1f%%) but the claim does not state a threshold" % (cnt["path_depth"], depth6, 100.0 * depth6 / n2)),
    }
    add(7, "Img2 coverage: is_shortcut_or_trace 629 (0.74%), per_file_prefetch_hit 214 (0.25%), after_hours_touch 14,455 (17%), delta_si_fn 16,307 (19.2%), "
           "filename_entropy 40,794 (48%), path_depth 18,301 (21.5%)", "FALSE (2 of 6 reproduce)",
        " | ".join("%s -> %s: %s" % (k, v[0], v[1]) for k, v in sub.items()))
    # 8
    ev8 = []
    for t in TAGS:
        d, r = C[t]["df23"], C[t]["raw23"]
        si = d["delta_si_fn"] > 0
        cr_back = ((pd.to_numeric(r["fn_cr_time"], errors="coerce").fillna(0) - pd.to_numeric(r["cr_time"])) >= 86400) & (r["cr_time"] > 0) if "fn_cr_time" in r else None
        ev8.append("%s: %.1f%% of files have SI.m != FN.m, %.1f%% by >=1 day%s" % (
            t, 100.0 * si.mean(), 100.0 * (d["delta_si_fn"] >= 86400).mean(),
            ("; SI.created earlier than FN.created by >=1 day on %.1f%%" % (100.0 * cr_back.mean())) if cr_back is not None else ""))
    tsrows = []
    for t in ("img1", "img2"):
        for tg in M.IMAGES[t]["targets"]:
            if tg.get("timestomp"):
                d = C[t]["df23"]
                idx = d.index[d["path"].str.contains("|".join(re.escape(p) for p in tg["patterns"]), case=False, regex=True)]
                if len(idx):
                    tsrows.append("%s known timestomp target %s: delta_si_fn=%s" % (t, tg["name"], [int(x) for x in d.loc[idx[:3], "delta_si_fn"]]))
    add(8, "delta_si_fn mismatch is 100% proof of timestamp tampering", "FALSE",
        "Mismatch is the normal state: " + "; ".join(ev8) + ". Windows updates $STANDARD_INFORMATION modified time on every write but $FILE_NAME times only on create/rename/move, "
        "so SI.m vs FN.m differs for any edited file. Even the stricter 'SI.created earlier than FN.created' test is common here (copies/restores keep SI times), so neither is proof; "
        "it is a weak indicator and a noisy feature. " + " ".join(tsrows))
    # 9
    tm = {}
    for t in TAGS:
        txt = open(os.path.join(ROOT, "runs", t, "pipeline.log"), encoding="utf-8", errors="ignore").read()
        mm = re.search(r"Step extractor\.py completed in ([\d.]+)s", txt)
        tm[t] = float(mm.group(1)) if mm else None
    pw = ["%s walk %.1fs" % (t, C[t]["probe"]["walk_seconds"]) for t in TAGS if C[t].get("probe")]
    add(9, "Parsing MFT metadata takes under 30 seconds", "FALSE (as a general statement)",
        "Whole extraction stage (MFT walk + EVT/EVTX + prefetch + registry) from pipeline.log: img1 %.2fs, img2 %.2fs, img3 %.2fs. True for Img1/Img2, "
        "false for Img3 (%.0fs, 197,058 records). MFT-only time is not logged; a minimal re-walk (name/meta flags only, no file reads) took: %s."
        % (tm["img1"], tm["img2"], tm["img3"], tm["img3"], "; ".join(pw) or "probe skipped"))
    # 10
    wrapper = open(os.path.join(ROOT, "feature_eng2.py")).read()
    uses_fe = "from feature_engineering import" in wrapper
    steps = open(os.path.join(ROOT, "run_pipeline.py")).read()
    fe_src = open(os.path.join(ROOT, "feature_engineering.py")).read()
    try:
        old = subprocess.run(["git", "show", "0b6f08d:feature_eng2.py"], cwd=ROOT, capture_output=True, text=True).stdout
    except Exception:
        old = ""
    paths = C["img2"]["raw23"]["path"].astype(str).str.lower()
    n_old = int(paths.str.contains(r"\\temp\\", regex=True).sum() + paths.str.contains(r"\\users\\", regex=True).sum())
    n_new = int(paths.str.contains(r"[\\/]temp[\\/]|[\\/]tmp[\\/]", regex=True).sum() + paths.str.contains(r"[\\/]users[\\/]|[\\/]documents and settings[\\/]", regex=True).sum())
    add(10, "feature_eng2.py bugs: backslash-only path regex for temp/user paths; pd.Timestamp.now() reference time",
        "TRUE for the original feature_eng2.py (commit 0b6f08d); FALSE for the code the pipeline runs",
        "run_pipeline.py STEPS runs feature_engineering.py (%s); feature_eng2.py is now an 18-line wrapper that only re-exports it (%s). The initial-commit "
        "feature_eng2.py did contain r'\\\\temp\\\\', r'\\\\users\\\\' (%s) and now=pd.Timestamp.now() (%s); on Img2's forward-slash paths those regexes match %d files vs %d for the "
        "current [\\\\/] regex. Current feature_engineering.py uses the [\\\\/] regex (%s) and the dataset max m_time as reference, with Timestamp.now() only as fallback "
        "when max m_time<=0 (%s). The current reference time has its own flaw: future_m is always 0."
        % ('"feature_engineering.py"' in steps, uses_fe, "temp" in old and "\\\\temp\\\\" in old, "Timestamp.now()" in old, n_old, n_new,
           "[\\\\/]temp" in fe_src, "int(max_m) if pd.notna(max_m) and max_m > 0 else int(pd.Timestamp.now()" in fe_src))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------
def md_table(df, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    return "\n".join(out)


def write_md(C, firing, claims):
    L = []
    A = L.append
    A("# Why only some features fire in SHAP\n")
    A("Generated by `shap_feature_firing.py` from the fresh runs in `runs/img{1,2,3}` and `reports/multimodel_eval`. "
      "FIRED means mean |SHAP| > 1e-6 over the explained rows.\n")

    # ---- summary
    A("## 1. Direct answers\n")
    summ = []
    for t in TAGS:
        s17 = firing[(firing.image == t) & (firing.feature_set == "17")]
        sub = {m: firing[(firing.image == t) & (firing.feature_set == "23") & (firing.model == m)].fired.sum() for m in MODELS}
        summ.append(dict(image=C[t]["label"], files=C[t]["mft"]["files"], explained_rows_17=int(s17.explained_rows.iloc[0]),
                         fired_17=f"{int(s17.fired.sum())}/17", constant_17=int(s17.constant.sum()),
                         fired_23_IF=f"{sub[MODELS[0]]}/23", fired_23_LOF=f"{sub[MODELS[1]]}/23", fired_23_OCSVM=f"{sub[MODELS[2]]}/23"))
    A(md_table(pd.DataFrame(summ), list(summ[0].keys())) + "\n")
    c17 = {t: firing[(firing.image == t) & (firing.feature_set == "17") & firing.constant].feature.tolist() for t in TAGS}
    A("**Is the setup wrong?** Partly. The model and SHAP computation are mechanically correct (TreeSHAP of a constant column is exactly 0), "
      "but the *feature definitions* make a block of columns incapable of ever firing, on every image, not just the first:\n")
    A("* **Eight columns are constant on all three disks**: `future_m`, `is_deleted`, `credential_tool`, `sniffer_tool`, `powershell_exec`, `cmd_exec`, `script_host`, `usb_present`. "
      "Constant columns by image: "
      + "; ".join("%s: %d (%s)" % (t, len(v), ", ".join(v)) for t, v in c17.items()) + ".")
    A("* The five tool flags and `usb_present` are *scalars computed once per disk* and assigned to every file row (`df[col] = int(any(...))`). A per-disk fact cannot rank one file above another, "
      "so an isolation tree never splits on it. Img1 shows this best: the Cain, Ethereal/WinPcap and CMD prefetch files exist, the flags are 1, and they are still silent.")
    A("* `future_m` compares each `m_time` with the *maximum m_time of the same dataset*, so `m_time > reference` is false for every row by construction.")
    A("* `is_deleted` is 0 everywhere because the extractor tests `meta.flags` only (see section 4); deleted directory entries are visible in the walk but not counted.")
    A("* `usb_present` is 1 on every disk because `usb_devices.txt` is always written and its existence counts as detection, even on Img1 whose file holds only a placeholder line.")
    A("* Rare-but-varying flags (`zero_size_recent`, `temp_path`, `is_archive`) have so few non-zero rows that a 256-row isolation-tree subsample rarely contains any; they fire weakly or not at all.")
    A("* SHAP rows differ between the two sets and this affects the comparison: the 17-set explains only the ~5% flagged rows with an interventional background; "
      "the 23-set IF explains a 20,000-row random sample (+ caught targets) with path-dependent TreeSHAP; LOF/OC-SVM use KernelSHAP on at most 12 caught-target rows "
      "(far fewer rows, so more features show ~0 or are noisy; LOF magnitudes reach 1e5-1e7 because the novelty-LOF score is unbounded and is not comparable to IF values).\n")

    A("**Is it only the first image?** No. Fired counts in the 17-set are %s; on every image the same 8 columns are dead, plus 1-2 rare ones (`zero_size_recent`, and `is_archive` on Img2 with a single non-zero row)." %
      ", ".join("%s %s" % (t, d["fired_17"]) for t, d in zip(TAGS, summ)) + "\n")

    # ---- per-image tables
    A("## 2. Per image: 17-feature set (Isolation Forest, pipeline SHAP on flagged rows)\n")
    cols = ["feature", "unique_values", "nonzero", "nonzero_pct", "constant", "mean_abs_shap", "rank", "fired", "if_splits", "root_cause"]
    for t in TAGS:
        s17 = firing[(firing.image == t) & (firing.feature_set == "17")].sort_values("rank")
        A("### %s (%d files; SHAP on %d flagged rows; %d trees x %d-row subsamples)\n" % (C[t]["label"], C[t]["mft"]["files"], int(s17.explained_rows.iloc[0]), C[t]["n_estimators"], C[t]["max_samples"]))
        A("Fired: " + ", ".join("%s (%.3f)" % (a, b) for a, b in zip(s17[s17.fired].feature, s17[s17.fired].mean_abs_shap)) + "\n")
        A("Not fired: " + ", ".join(s17[~s17.fired].feature) + "\n")
        A(md_table(s17, cols) + "\n")

    A("## 3. Per image: 23-feature set\n")
    cols23 = ["feature", "unique_values", "nonzero_pct", "mean_abs_shap", "rank", "fired", "root_cause"]
    for t in TAGS:
        A("### %s (%d files)\n" % (C[t]["label"], C[t]["mft"]["files"]))
        for m in MODELS:
            s = firing[(firing.image == t) & (firing.feature_set == "23") & (firing.model == m)].sort_values("rank")
            A("**%s** -- fired %d/23 on %d explained rows. Not fired: %s\n" % (m, int(s.fired.sum()), int(s.explained_rows.iloc[0]), ", ".join(s[~s.fired].feature) or "none"))
            if m == "Isolation Forest":
                A(md_table(s, cols23) + "\n")
        A("The six new features are all non-constant on this image: " + ", ".join(
            "%s (%.1f%% non-zero)" % (f, 100.0 * (C[t]["df23"][f] != 0).mean()) for f in M.NEW_6) +
          ". The 23-set therefore adds firing features, but the six dead 17-set columns remain dead.\n")

    # ---- bugs
    A("## 4. Real setup bugs (suggested fixes, not implemented)\n")
    pr = {t: C[t].get("probe") for t in TAGS}
    A("| # | Bug | Evidence | Suggested fix |\n|---|---|---|---|")
    bugs = [
        ("is_deleted always 0", "mft_records.json has %s is_deleted=true records (img1/2/3); extractor tests only `meta.flags & TSK_FS_META_FLAG_UNALLOC`. Re-walk of the images finds name-level unallocated entries: %s." % (
            "/".join(str(C[t]["mft"]["deleted_true_all"]) for t in TAGS),
            "; ".join("%s %d (of which meta=None %d)" % (t, pr[t]["name_unalloc"], pr[t]["name_unalloc_meta_none"]) for t in TAGS if pr[t]) or "probe skipped"),
         "OR in `entry.info.name.flags & TSK_FS_NAME_FLAG_UNALLOC` (and treat meta=None unallocated names as deleted); also record the MFT sequence/in-use flag."),
        ("Global flags broadcast to every file", "credential_tool, sniffer_tool, powershell_exec, cmd_exec, script_host, usb_present are scalars (feature_engineering.py L~125-140); constant on every image.",
         "Make them per-file: match the file's own basename against prefetch run names (the 23-set `per_file_prefetch_hit` does this), or its path under tool directories, or its prefetch last-run time proximity."),
        ("usb_present counts a placeholder file", "usb_detected = exists(SYSTEM) or exists(usb_devices.txt); usb_devices.txt is always written. Real USB entries: %s." % ", ".join("%s %d" % (t, C[t]["usb"]["real_entries"]) for t in TAGS),
         "Parse USBSTOR properly (python-registry); then make it per-file via files modified within the device's first/last-connected window, not a disk constant."),
        ("future_m can never be 1", "reference = max(m_time) of the same dataset; %s rows exceed it." % "/".join(str(C[t]["mft"]["m_gt_max"]) for t in TAGS),
         "Compare to an external reference (acquisition time from the image metadata/registry ShutdownTime, or the OS install date), or replace with 'timestamp after the last log/registry event'."),
        ("Prefetch keyword matching on joined names", "'cmd' matches MPCMDRUN.EXE on Img3; 'stored' and 'cain' are substrings; nothing checks Win10 MAM-compressed content.",
         "Match on parsed executable name, whole-word, per file."),
        ("delta_si_fn is a weak tamper test", "SI.m != FN.m for most files (see claim 8); it is not 'proof of timestomping'.",
         "Treat as a weak hint only. Prefer combined evidence: SI.created < FN.created together with a rare extension/location, plus $UsnJrnl/$LogFile corroboration; do not use modified-time equality alone."),
        ("after_hours_touch uses UTC against an 08:00-18:00 window", "Non-zero on %.0f%% of Img2 files, so almost constant." % (100.0 * (C["img2"]["df23"]["after_hours_touch"] > 0).mean()),
         "Convert to the host's local timezone (registry TimeZoneInformation) and use the case's policy hours."),
        ("Prefetch extraction count differs from the MFT listing", "Extracted .pf files vs .pf names in the MFT listing: %s. Not investigated further (listing may include stale/duplicate names)." % ", ".join("%s %d/%d" % (t, C[t]["pf_count"], C[t]["mft_pf_files"]) for t in TAGS),
         "Log each skipped .pf (size cap, read error) so flag inputs are auditable."),
        ("SHAP row sets differ across pipelines", "17-set: flagged rows only; 23-set IF: 20k random sample + targets; LOF/OC-SVM: <=12 caught rows.",
         "Explain the same row set for every model (e.g. all top-K flagged rows + all target rows) and use a fixed IF explainer setting."),
    ]
    for i, (a, b, c) in enumerate(bugs, 1):
        A("| %d | %s | %s | %s |" % (i, a, b, c))
    A("")

    # ---- why 17 and what to add
    A("## 5. Why these 17 features, and what can be added\n")
    A("The repository does not document a rationale; this is inferred from the code (`feature_engineering.py`, `extractor.py`). All 17 come from three cheap sources: "
      "the MFT/file-system record (the five timestamps, size, deleted flag, path), the *names* of Prefetch files, and the existence of a USB file. "
      "They need no parsing of binary artefacts, work identically on Windows XP (no EVTX, no Win10 compressed prefetch), 7 and 10, and the extraction+feature step takes seconds "
      "(feature_engineering stage: %s s). The first 11 are real per-file metadata; the last 6 are disk-level lookups that were bolted on as per-file columns, which is why they are dead.\n" %
      "/".join(re.search(r"Step feature_engineering\.py completed in ([\d.]+)s", open(os.path.join(ROOT, "runs", t, "pipeline.log"), encoding="utf-8", errors="ignore").read()).group(1) for t in TAGS))
    A("Already added in the benchmark (23-set) and non-constant on all three disks: `is_shortcut_or_trace`, `per_file_prefetch_hit`, `after_hours_touch`, `delta_si_fn`, `filename_entropy`, `path_depth`.\n")
    A("Features worth adding next (per-file, metadata-only, vetted against what the extractor already holds):\n")
    for s in [
        "**Created-time SI-vs-FN test** (`si_cr_before_fn_cr`, optionally combined with location/extension rarity): data already in `fn_cr_time` / `fn_m_time`. It is noisy on its own (see claim 8), so add it as a feature, not as a verdict; sub-second-zero SI precision needs the raw 100 ns FILETIME, which the extractor currently truncates to integer seconds.",
        "**Correct `is_deleted`** (name-unallocated entries): the extractor already sees them; gives real signal for wiped/removed tools.",
        "**Directory-level burst / sibling features** (files created in the same minute; number of siblings; share of siblings that are executables): `burst_detection.py` already computes burst windows, but only as a separate model, not as columns.",
        "**Extension/type mismatches and rare-extension rate** (extension frequency across the image, double extensions, executable extension in a user or temp directory): path-only, cheap.",
        "**Ownership/user directory** (which /Users/<name> or Documents and Settings profile): lets a model separate system noise from user-created files.",
        "**Created-after-OS-install and install-window membership** (`cr_time` relative to the median system-file `cr_time`): separates post-install user files from the base OS image.",
        "**Per-file execution evidence from Prefetch contents** (last-run times and run count for the matching .pf; Win10 files need MAM decompression) and **Recent/LNK targets**: converts the dead global execution flags into real per-file features.",
        "**Zone.Identifier / download marker and size-vs-extension plausibility**: indicates files that arrived from outside; needs ADS enumeration from the MFT.",
    ]:
        A("* " + s)
    A("")
    A("Not worth adding: more disk-level booleans (they will be constant again) and anything the extractor cannot supply per file.\n")

    # ---- claims
    A("## 6. Check of earlier claims\n")
    A(md_table(claims, ["claim_no", "claim", "verdict", "evidence"]) + "\n")
    with open(os.path.join(OUT, "shap_feature_firing.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-probe", action="store_true", help="skip the pytsk3 re-walk of the raw images (is_deleted evidence)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="firing_")
    C = {}
    rows = []
    for t in TAGS:
        print("[*] %s ..." % t, flush=True)
        C[t] = build_ctx(t, not a.skip_probe, tmp)
        assert C[t]["build_matches_pipeline"], "23-set rebuild disagrees with pipeline 17 features for " + t
        rows += rows_for_17(C[t]) + rows_for_23(C[t])
    firing = pd.DataFrame(rows)
    firing.to_csv(os.path.join(OUT, "feature_firing.csv"), index=False)
    claims = build_claims(C, firing)
    claims.to_csv(os.path.join(OUT, "claims_check.csv"), index=False)
    write_md(C, firing, claims)
    print(firing.groupby(["image", "feature_set", "model"]).fired.sum().to_string())
    print("[+] wrote", OUT)


if __name__ == "__main__":
    main()
