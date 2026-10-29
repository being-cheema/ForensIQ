"""
trust_eval.py
=============
Trust evaluation for the ForensIQ results site (full disk, models fit with seed 42, as in
export_site_data.py).

  1. toolOutput : what the examiner sees (ranked top-N list per model, SHAP reason, path category,
                  noise-vs-user summary per 5/10/15/20 % budget)
  2. verdicts   : evidence-based (NON-circular) indicators computed only from the flagged set, with
                  disk base rates / enrichment, evaluated afterwards against the known scenario
  3. xai        : faithfulness (deletion test), stability (seeds), forensic sense, constant-feature mass

Usage:
  python trust_eval.py --images img1          # one image (run the three in parallel)
  python trust_eval.py --md-only              # rebuild reports/trust_eval/trust_eval.md from the JSONs

Outputs: web/src/data/trust/{img1,img2,img3}.json, reports/trust_eval/trust_eval.md
"""
import os
import re
import sys
import json
import time
import pickle
import argparse
import itertools
import warnings

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, fisher_exact
from sklearn.neighbors import LocalOutlierFactor

import multimodel_eval as M

warnings.filterwarnings("ignore")
BASE = M.BASE_DIR
TRUST_DIR = os.path.join(BASE, "web", "src", "data", "trust")
REPORT_DIR = os.path.join(BASE, "reports", "trust_eval")
CACHE = os.path.join(BASE, ".cache", "trust_eval")
BUDGET_PCTS = [5, 10, 15, 20]
MAX_ROWS = 3000
SEEDS = [42, 1337, 9999, 7, 2024]
SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OCSVM"}
N_NONTARGET = 200            # IF: random non-target flagged files for the deletion test
N_NONTARGET_KERNEL = 60      # LOF / OC-SVM (KernelSHAP is slow): fewer
MAX_TARGETS_KERNEL = 40      # caught targets explained with KernelSHAP
MAX_STAB_KERNEL = 20         # KernelSHAP stability targets
KSHAP_N_FAITH, KSHAP_N_STAB, KSHAP_BG = 300, 200, 50
TS_HOURS = 1
TS_ENRICH_MIN = 1.5          # "indicated" needs enrichment >= this (and >= 1 file)
SUPPORT_CAP = 25

# ----------------------------------------------------------------------------
# Hand-written forensic expectation: which features SHOULD explain a target of this type
# (first regex that matches the target name wins)
# ----------------------------------------------------------------------------
TIME = ["delta_mc", "delta_mb", "delta_ab", "delta_si_fn", "after_hours_touch", "future_m"]
EXPECTED_RULES = [
    (r"NMEM|NGETTIME|timestomp", set(TIME)),
    (r"wiped via eraser", set(TIME + ["size"])),
    (r"eraser|ccleaner|ccsetup", set(["per_file_prefetch_hit", "is_exe"] + TIME)),
    (r"\(lnk\)|\.lnk$|^box sync|^dropbox|^google drive", {"is_shortcut_or_trace"}),
    (r"sync_log|sync_config|snapshot\.db|setupapi|system\.evtx", {"is_shortcut_or_trace", "usb_present"}),
    (r"masqueraded|\.zip", {"size", "is_archive", "filename_entropy"}),
    (r"wordlist", {"size", "is_archive", "filename_entropy"}),
    (r"cain|ethereal|winpcap|netstumbler|123wasp|defrag|anonymizer",
     {"credential_tool", "sniffer_tool", "is_exe", "per_file_prefetch_hit"}),
    (r"login data", {"user_path", "path_depth", "size", "is_shortcut_or_trace"}),
    (r"\.(jpg|png|docx?|pptx?|xlsx?|pdf|xps|csv|gdoc|url)\b|resignation|decoy|confidential",
     {"user_path", "path_depth", "size", "filename_entropy", "after_hours_touch"}),
]


def expected_for(name):
    for pat, s in EXPECTED_RULES:
        if re.search(pat, name, re.I):
            return sorted(s)
    return []


# ----------------------------------------------------------------------------
# Path categories (heuristic)
# ----------------------------------------------------------------------------
DOC_EXT = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".rtf", ".odt", ".csv", ".jpg", ".jpeg",
           ".png", ".gif", ".bmp", ".zip", ".rar", ".7z", ".xps", ".gdoc", ".gsheet", ".url", ".mp3", ".mp4", ".avi",
           ".mov", ".wav", ".wmv", ".pst", ".msg", ".eml"}
EXE_EXT = {".exe", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".msi", ".scr", ".jar"}
LOG_EXT = {".log", ".evtx", ".evt", ".etl", ".tmp"}


def categorize(p):
    lp = p.lower()
    name = lp.rsplit("/", 1)[-1]
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if (name in ("ntuser.dat", "usrclass.dat") or name.startswith("ntuser.dat") or "/config/" in lp and
            re.search(r"/config/(system|software|sam|security|default|components)", lp) or ext in (".hiv", ".regtrans-ms")
            or name.endswith(".dat.log1") or name.endswith(".dat.log2")):
        return "registry"
    if ext == ".pf" or "/prefetch/" in lp or ext == ".lnk" or "destinations-ms" in name:
        return "prefetch-or-lnk"
    if ext in LOG_EXT or "/logs/" in lp or "/logfiles/" in lp:
        return "log"
    if re.search(r"/(google/chrome|mozilla|firefox|internet explorer|microsoft/edge|temporary internet files|inetcache|"
                 r"content\.ie5|webcache|opera|cookies)/", lp):
        return "browser"
    in_user = lp.startswith("/users/") or lp.startswith("/documents and settings/")
    if in_user and ext in DOC_EXT and "/appdata/" not in lp and "/application data/" not in lp:
        return "user-document"
    in_sys = lp.startswith(("/windows/", "/winnt/", "/program files", "/programdata/", "/$", "/system volume information",
                            "/recovery", "/boot", "/perflogs"))
    if ext in EXE_EXT and not lp.startswith(("/windows/", "/winnt/")):
        return "executable"
    if in_sys or ext in (".dll", ".sys", ".mui", ".cat", ".manifest", ".mum", ".inf", ".nls", ".drv", ".ocx", ".cpl",
                         ".ttf", ".fon", ".ico", ".bin", ".dat", ".cab", ".ini", ".gpd", ".chm", ".hlp", ".xml"):
        return "system-noise"
    return "other"


# ----------------------------------------------------------------------------
# Evidence-based indicator regexes (applied to lower-cased full path)
# ----------------------------------------------------------------------------
RX_WIPER = re.compile(r"(^|[^a-z0-9])(eraser|ccleaner|ccsetup|sdelete|cipher|bleachbit|dban|shredder|secure-?delete|"
                      r"evidence-?eliminator|privacy-?(eraser|cleaner)|wipe(r|file|disk)?|killdisk|file-?shredder)"
                      r"([^a-z]|$)")
RX_CLOUD_USB = re.compile(r"setupapi|usbstor|/google/drive|/googledrive|/drivefs/|sync_config\.db|snapshot\.db|"
                          r"sync_log\.log|/dropbox/|\.dropbox|filecache\.dbx|/onedrive/|/box sync/|/icloud")
RX_HACK = re.compile(r"(^|[^a-z0-9])(cain|ethereal|netstumbler|whois|anonymizer|wpcap|nmap|wireshark|l0phtcrack|"
                     r"metasploit|nessus)([^a-z]|$)")
RX_DOCNAME = re.compile(r"\.(docx?|xlsx?|pptx?|pdf|rtf|odt|txt|xps|csv)(\.lnk)?$")


def indicator_arrays(df, raw):
    lp = df["path"].astype(str).str.lower()
    name = lp.str.rsplit("/", n=1).str[-1]
    ext = name.str.extract(r"(\.[^.]+)$")[0].fillna("")
    exe_or_pf = ext.isin([".exe", ".pf", ".com", ".bat", ".cmd"])
    a = (lp.map(lambda s: bool(RX_WIPER.search(s))) & exe_or_pf).values
    a_pf = a & (ext == ".pf").values
    lnk = (ext == ".lnk").values
    jl = name.str.contains("destinations-ms", regex=False).values
    docname = name.map(lambda s: bool(RX_DOCNAME.search(s))).values
    recent = lp.str.contains("/recent/", regex=False).values
    b = ((lnk & docname) | (lnk & recent) | jl)
    b_strict = (lnk & docname) | jl
    c = lp.map(lambda s: bool(RX_CLOUD_USB.search(s))).values
    d = lp.map(lambda s: bool(RX_HACK.search(s))).values
    fn_cr = pd.to_numeric(raw.get("fn_cr_time", 0), errors="coerce").fillna(0).values
    cr = raw["cr_time"].values
    valid = (fn_cr > 0) & (cr > 0)
    ts = valid & (cr < fn_cr - TS_HOURS * 3600)
    return {"wiper": a, "wiper_prefetch": a_pf, "recent_doc_trace": b, "recent_doc_trace_strict": b_strict,
            "removable_cloud": c, "hacking_tools": d, "ts": ts, "ts_valid": valid}


def evidence_verdict(idx, ind, df, rank_of, N):
    """idx = flagged row indices (ordered by rank). Uses only what the tool can see in the flagged set."""
    paths = df["path"].values
    res = {}
    fl = np.zeros(N, dtype=bool)
    fl[idx] = True

    def lst(mask):
        ii = [i for i in idx if mask[i]]
        return {"count": len(ii), "files": [[int(rank_of[i]), paths[i]] for i in ii[:SUPPORT_CAP]]}

    ts_f, valid_f = int((fl & ind["ts"]).sum()), int((fl & ind["ts_valid"]).sum())
    ts_d, valid_d = int(ind["ts"].sum()), int(ind["ts_valid"].sum())
    fr = ts_f / valid_f if valid_f else 0.0
    dr = ts_d / valid_d if valid_d else 0.0
    enrich = fr / dr if dr > 0 else None
    p = None
    if valid_f:
        try:
            p = float(fisher_exact([[ts_f, valid_f - ts_f], [ts_d - ts_f, (valid_d - valid_f) - (ts_d - ts_f)]],
                                   alternative="greater")[1])
        except Exception:
            p = None
    ts = lst(ind["ts"] & fl)
    ts.update({"flaggedWithFn": valid_f, "flaggedRate": round(fr, 5), "diskCount": ts_d, "diskWithFn": valid_d,
               "diskRate": round(dr, 5), "enrichment": None if enrich is None else round(enrich, 3),
               "fisherP": p,
               "subSecondCheck": "unavailable: MFT export stores whole-second epoch times, so the zero-sub-second "
                                 "rule cannot be evaluated",
               "indicated": bool(ts["count"] >= 1 and enrich is not None and enrich >= TS_ENRICH_MIN)})
    res["timestomp"] = ts

    inds = {
        "a_wiper_executed": lst(ind["wiper"] & fl),
        "b_recent_doc_traces": lst(ind["recent_doc_trace"] & fl),
        "c_removable_or_cloud": lst(ind["removable_cloud"] & fl),
        "d_hacking_tools": lst(ind["hacking_tools"] & fl),
    }
    inds["a_wiper_executed"]["prefetchConfirmed"] = int((ind["wiper_prefetch"] & fl).sum())
    for k, v in inds.items():
        v["fired"] = v["count"] > 0
    res["indicators"] = inds
    insider = [k for k in ("a_wiper_executed", "b_recent_doc_traces", "c_removable_or_cloud") if inds[k]["fired"]]
    res["insiderAntiForensic"] = {"indicated": len(insider) >= 2, "fired": insider}
    res["hackerTools"] = {"indicated": inds["d_hacking_tools"]["fired"], "fired": ["d_hacking_tools"] if inds["d_hacking_tools"]["fired"] else []}
    return res


EXPECTED_TRUTH = {  # scenario ground truth (from the task statement / repo case notes)
    "img1": {"insider": False, "hacker_tools": True, "timestomp": True,
             "note": "hacker; repo case notes mark NMEM/NGETTIME as timestomped"},
    "img2": {"insider": True, "hacker_tools": False, "timestomp": True, "note": "insider, Eraser timestomping"},
    "img3": {"insider": True, "hacker_tools": False, "timestomp": False, "note": "lone-wolf planner, no timestomp known"},
}


def evaluate_verdict(tag, v):
    t = EXPECTED_TRUTH[tag]
    out = {"truth": t}
    out["timestomp"] = {"verdict": v["timestomp"]["indicated"], "correct": v["timestomp"]["indicated"] == t["timestomp"]}
    out["insider"] = {"verdict": v["insiderAntiForensic"]["indicated"], "correct": v["insiderAntiForensic"]["indicated"] == t["insider"]}
    out["hacker_tools"] = {"verdict": v["hackerTools"]["indicated"], "correct": v["hackerTools"]["indicated"] == t["hacker_tools"]}
    return out


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def load_ctx(tag):
    p = os.path.join(CACHE, f"{tag}.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    os.makedirs(CACHE, exist_ok=True)
    spec = M.IMAGES[tag]
    out = M.build_features(spec["art_dir"], tag)
    pickle.dump(out, open(p, "wb"))
    return out


def top3(sv_row, feats, positive=True):
    """Top-3 feature indices of one SHAP row: strongest positive (suspicion-raising) contributors, padded by |value|."""
    order_abs = np.argsort(-np.abs(sv_row))
    if not positive:
        return [int(j) for j in order_abs[:3]]
    pos = [int(j) for j in np.argsort(-sv_row) if sv_row[j] > 1e-9][:3]
    for j in order_abs:
        if len(pos) >= 3:
            break
        if int(j) not in pos and abs(sv_row[j]) > 1e-9:
            pos.append(int(j))
    return pos


def kernel_shap(fn, bg, X, nsamples, seed):
    import shap
    np.random.seed(seed)
    return np.asarray(shap.KernelExplainer(fn, bg).shap_values(X, nsamples=nsamples, silent=True)).reshape(len(X), -1)


def tree_shap(fitted, X):
    import shap
    return -np.asarray(shap.TreeExplainer(fitted).shap_values(X))


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def stab_summary(tops):
    """tops: {seed: top3 list} -> mean pairwise Jaccard, pairwise top-1 agreement, all-agree top-1."""
    ks = list(tops)
    pairs = list(itertools.combinations(ks, 2))
    jac = np.mean([jaccard(tops[a], tops[b]) for a, b in pairs])
    t1 = np.mean([tops[a][0] == tops[b][0] for a, b in pairs])
    allsame = len({tops[k][0] for k in ks}) == 1
    return float(jac), float(t1), bool(allsame)


# ----------------------------------------------------------------------------
def run_image(tag):
    t0 = time.time()
    spec = M.IMAGES[tag]
    df, raw, feats = load_ctx(tag)
    N = len(df)
    paths = df["path"].values
    tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
    active, all_idx = M.match_targets(df["path"], tg)
    tgt_name = {}
    for t in active:
        for i in t["idx"]:
            tgt_name.setdefault(int(i), t["name"])
    X = df[feats].values.astype(float)
    Xs = M.standardize(X)
    nonconst = np.where(X.std(0) > 0)[0]
    const_idx = np.where(X.std(0) == 0)[0]
    near_idx = []
    for j in range(X.shape[1]):
        vals, cnt = np.unique(X[:, j], return_counts=True)
        if (N - cnt.max()) / N <= 0.001:
            near_idx.append(j)
    near_idx = np.array(near_idx, dtype=int)
    K = {p: int(round(p / 100 * N)) for p in BUDGET_PCTS}
    NR = min(K[20], MAX_ROWS)
    print(f"[{tag}] {N:,} files, {len(active)} targets, K={K}, const={len(const_idx)} near={len(near_idx)}", flush=True)

    # ---- fit models seed 42 (as export_site_data) --------------------------------
    scores, fitted, order, rank_of = {}, {}, {}, {}
    for mo in M.MODELS:
        s, fm = M.fit_score(mo, Xs, 42, 10000)
        scores[mo], fitted[mo] = s, fm
        order[mo] = np.argsort(-s, kind="stable")
        r = np.empty(N, dtype=np.int64)
        r[order[mo]] = np.arange(1, N + 1)
        rank_of[mo] = r
        print(f"[{tag}] {mo} fitted {time.time()-t0:.0f}s", flush=True)

    # scoring functions for the deletion test (SAME fitted model; LOF = novelty refit as in run_shap)
    nov = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=-1).fit(Xs)
    fns = {"Isolation Forest": lambda A: -fitted["Isolation Forest"].score_samples(A),
           "Local Outlier Factor": lambda A: -nov.score_samples(A),
           "One-Class SVM": lambda A: -fitted["One-Class SVM"].decision_function(A)}
    base = {mo: fns[mo](Xs) for mo in M.MODELS}
    # LOF: the novelty model counts a training point as its own neighbour, so for the deletion test the row is
    # held out (novelty LOF refit without it) and ranked against the ordinary training LOF scores
    base["Local Outlier Factor"] = scores["Local Outlier Factor"].copy()
    print(f"[{tag}] base scores {time.time()-t0:.0f}s", flush=True)

    # ---- caught targets (best copy within the 20% budget) and non-target flagged sample ------
    caught = {}   # model -> list of (target name, row idx)
    for mo in M.MODELS:
        lst = []
        for t in active:
            ii = np.array(t["idx"])
            b = int(ii[np.argmin(rank_of[mo][ii])])
            if rank_of[mo][b] <= K[20]:
                lst.append((t["name"], b))
        caught[mo] = lst
    rng = np.random.RandomState(0)
    nontarget = {}
    for mo in M.MODELS:
        pool = [int(i) for i in order[mo][:K[20]] if int(i) not in tgt_name]
        n = N_NONTARGET if mo == "Isolation Forest" else N_NONTARGET_KERNEL
        nontarget[mo] = [int(i) for i in rng.choice(pool, min(n, len(pool)), replace=False)]

    # ---- SHAP at seed 42 --------------------------------------------------------------
    import shap  # noqa
    sv = {}   # model -> {row idx: shap vector}
    bg_rng = np.random.RandomState(0)
    bg = Xs[bg_rng.choice(N, KSHAP_BG, replace=False)]
    # IF: top-300 (tool reasons) + all caught + nontarget
    need = set(int(i) for i in order["Isolation Forest"][:300]) | {b for _, b in caught["Isolation Forest"]} | set(nontarget["Isolation Forest"])
    need = sorted(need)
    sh = tree_shap(fitted["Isolation Forest"], Xs[need])
    sv["Isolation Forest"] = {i: sh[k] for k, i in enumerate(need)}
    print(f"[{tag}] IF TreeSHAP on {len(need)} rows {time.time()-t0:.0f}s", flush=True)
    for mo in ["Local Outlier Factor", "One-Class SVM"]:
        sel = [b for _, b in caught[mo]][:MAX_TARGETS_KERNEL] + nontarget[mo]
        sel = list(dict.fromkeys(sel))
        sh = kernel_shap(fns[mo], bg, Xs[sel], KSHAP_N_FAITH, 0)
        sv[mo] = {i: sh[k] for k, i in enumerate(sel)}
        print(f"[{tag}] {mo} KernelSHAP on {len(sel)} rows {time.time()-t0:.0f}s", flush=True)

    # existing SHAP CSVs: reasons for tool-output rows (positive top contributor)
    csv_reason = {}
    for mo in M.MODELS:
        p = os.path.join(M.SHAP_DIR, f"{tag}_{mo.replace(' ', '_')}_shap.csv")
        d = {}
        if os.path.exists(p):
            c = pd.read_csv(p)
            vals = c[feats].values
            for k, pth in enumerate(c["path"].values):
                if pth not in d:
                    d[pth] = feats[top3(vals[k], feats)[0]]
        csv_reason[mo] = d

    # ======================= 1. tool output ===========================================
    tool = {}
    for mo in M.MODELS:
        o = order[mo]
        catK = {}
        rows = []
        cats_all = {}
        for k in range(K[20]):
            i = int(o[k])
            cats_all[i] = categorize(paths[i])
        for r in range(NR):
            i = int(o[r])
            reason = ""
            if mo == "Isolation Forest" and i in sv[mo]:
                reason = feats[top3(sv[mo][i], feats)[0]]
            elif paths[i] in csv_reason[mo]:
                reason = csv_reason[mo][paths[i]]
            elif i in sv.get(mo, {}):
                reason = feats[top3(sv[mo][i], feats)[0]]
            rows.append([r + 1, round(float(scores[mo][i]), 4), paths[i], tgt_name.get(i, ""), reason, cats_all[i]])
        summ = {}
        first_t = min((int(rank_of[mo][i]) for i in tgt_name), default=None)
        for p in BUDGET_PCTS:
            ids = [int(i) for i in o[:K[p]]]
            cc = {}
            for i in ids:
                cc[cats_all[i]] = cc.get(cats_all[i], 0) + 1
            hit_t = {t["name"] for t in active if any(rank_of[mo][i] <= K[p] for i in t["idx"])}
            summ[str(p)] = {"K": K[p], "systemNoise": cc.get("system-noise", 0),
                            "userFiles": cc.get("user-document", 0),
                            "systemNoiseShare": round(cc.get("system-noise", 0) / K[p], 4),
                            "userShare": round(cc.get("user-document", 0) / K[p], 4),
                            "categories": cc, "targetsHit": len(hit_t), "targetsTotal": len(active),
                            "targetFilesInTopK": int(sum(1 for i in tgt_name if rank_of[mo][i] <= K[p]))}
        tool[mo] = {"rows": rows, "N": NR, "budgets": {str(p): K[p] for p in BUDGET_PCTS},
                    "firstTargetRank": first_t, "summary": summ,
                    "reasonCoverage": round(sum(1 for r in rows if r[4]) / len(rows), 4)}

    # ======================= 2. verdicts =============================================
    ind = indicator_arrays(df, raw)
    ver = {"method": {
        "timestomp": f"flagged files with $SI creation < $FN creation - {TS_HOURS}h (both present); sub-second rule "
                     f"unavailable (whole-second times). 'indicated' = >=1 flagged and enrichment >= {TS_ENRICH_MIN}.",
        "insider": "indicated when >=2 of: (a) wiper/cleaner exe or prefetch, (b) LNK/jumplist traces of doc files, "
                   "(c) setupapi/usbstor/cloud-sync artifacts",
        "hacker": "(d) hacking-tool names (cain, ethereal, netstumbler, whois, anonymizer, ...) in the flagged set"},
        "diskTimestomp": {"count": int(ind["ts"].sum()), "withFn": int(ind["ts_valid"].sum()),
                          "rate": round(float(ind["ts"].sum() / max(1, ind["ts_valid"].sum())), 5)},
        "diskIndicatorCounts": {k: int(v.sum()) for k, v in ind.items() if k != "ts_valid"},
        "perModel": {}, "evaluation": {}}
    for mo in M.MODELS:
        ver["perModel"][mo], ver["evaluation"][mo] = {}, {}
        for p in BUDGET_PCTS:
            v = evidence_verdict(order[mo][:K[p]], ind, df, rank_of[mo], N)
            ver["perModel"][mo][str(p)] = v
            ver["evaluation"][mo][str(p)] = evaluate_verdict(tag, v)

    # ======================= 3. explainability =======================================
    xai = {"faithfulness": {}, "stability": {}, "sense": [], "summary": {}}
    ranks_of_score = lambda mo, i, new: int((base[mo] > new).sum() - (base[mo][i] > new)) + 1
    nc = nonconst
    for mo in M.MODELS:
        is_t = {i for _, i in caught[mo]}
        rows_sel = [i for i in sv[mo] if i in is_t or i in set(nontarget[mo])]
        recs, rng2 = [], np.random.RandomState(1)
        for i in rows_sel:
            t3 = top3(sv[mo][i], feats)
            f_i = fns[mo]
            if mo == "Local Outlier Factor":
                keep = np.ones(N, dtype=bool)
                keep[i] = False
                nov_i = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=-1).fit(Xs[keep])
                f_i = lambda A, nv=nov_i: -nv.score_samples(A)
            old = ranks_of_score(mo, i, base[mo][i])
            xm = Xs[i].copy()
            xm[t3] = 0.0
            new = ranks_of_score(mo, i, float(f_i(xm[None, :])[0]))
            Rm = np.repeat(Xs[i][None, :], 10, axis=0)
            for d in range(10):
                Rm[d, rng2.choice(nc, 3, replace=False)] = 0.0
            rs = f_i(Rm)
            rnd = np.mean([ranks_of_score(mo, i, float(x)) - old for x in rs])
            recs.append((i, i in is_t, new - old, float(rnd), old))
        a = np.array([r[2] for r in recs], float)
        b = np.array([r[3] for r in recs], float)
        try:
            pw = float(wilcoxon(a, b, alternative="greater").pvalue)
        except Exception:
            pw = None
        grp = lambda f: [r for r in recs if f(r)]
        xai["faithfulness"][mo] = {
            "n": len(recs), "nTargets": sum(r[1] for r in recs), "nNonTarget": sum(not r[1] for r in recs),
            "medianRankChangeShapTop3": float(np.median(a)), "medianRankChangeRandom3": float(np.median(b)),
            "meanRankChangeShapTop3": float(a.mean()), "meanRankChangeRandom3": float(b.mean()),
            "shareShapBeatsRandom": float((a > b).mean()), "wilcoxonP": pw,
            "targetsOnly": {"n": len(grp(lambda r: r[1])),
                            "medianShap": float(np.median([r[2] for r in grp(lambda r: r[1])])) if grp(lambda r: r[1]) else None,
                            "medianRandom": float(np.median([r[3] for r in grp(lambda r: r[1])])) if grp(lambda r: r[1]) else None},
            "samples": [[paths[r[0]][-80:], r[4], r[2], round(r[3], 1)] for r in recs if r[1]][:25]}
        print(f"[{tag}] {mo} faithfulness done {time.time()-t0:.0f}s", flush=True)

        # constant-feature SHAP mass
        S = np.abs(np.array([sv[mo][i] for i in rows_sel]))
        tot = S.sum()
        xai["summary"].setdefault(mo, {})["shapMassConstant"] = float(S[:, const_idx].sum() / tot) if tot else 0.0
        xai["summary"][mo]["shapMassNearConstant"] = float(S[:, near_idx].sum() / tot) if tot else 0.0

        # forensic sense
        sense_all = []
        for name, i in caught[mo]:
            if i not in sv[mo]:
                continue
            t3 = [feats[j] for j in top3(sv[mo][i], feats)]
            exp = expected_for(name)
            sense_all.append({"target": name, "model": mo, "top3": t3, "expected": exp,
                              "match": bool(set(t3) & set(exp)), "rank": int(rank_of[mo][i])})
        xai["sense"].extend(sense_all)
        xai["summary"][mo]["senseMatch"] = (float(np.mean([s["match"] for s in sense_all])) if sense_all else None)
        xai["summary"][mo]["senseN"] = len(sense_all)
        xai["summary"][mo]["targetsCaught20"] = len(caught[mo])

    # ---- stability ---------------------------------------------------------------------
    # IF: five refits, TreeSHAP of each caught target
    tgt_rows = [b for _, b in caught["Isolation Forest"]]
    stab = {}
    if tgt_rows:
        per_seed = {}
        for sd in SEEDS:
            fm = fitted["Isolation Forest"] if sd == 42 else M.fit_score("Isolation Forest", Xs, sd, 10000)[1]
            sh = tree_shap(fm, Xs[tgt_rows])
            per_seed[sd] = [top3(sh[k], feats) for k in range(len(tgt_rows))]
        js, t1, al = [], [], []
        for k in range(len(tgt_rows)):
            j, a_, s_ = stab_summary({sd: per_seed[sd][k] for sd in SEEDS})
            js.append(j); t1.append(a_); al.append(s_)
        stab["Isolation Forest"] = {"n": len(tgt_rows), "meanJaccardTop3": float(np.mean(js)),
                                    "top1AgreementPairwise": float(np.mean(t1)), "top1AllSeedsSame": float(np.mean(al)),
                                    "nsamples": "exact TreeSHAP"}
    print(f"[{tag}] IF stability done {time.time()-t0:.0f}s", flush=True)
    for mo in ["Local Outlier Factor", "One-Class SVM"]:
        tr = [b for _, b in caught[mo]][:MAX_STAB_KERNEL]
        if not tr:
            continue
        per_seed = {}
        for sd in SEEDS:
            if mo == "One-Class SVM" and sd != 42:
                f_sd = (lambda m_: (lambda A: -m_.decision_function(A)))(M.fit_score(mo, Xs, sd, 10000)[1])
            else:
                f_sd = fns[mo]
            bg_s = Xs[np.random.RandomState(sd).choice(N, KSHAP_BG, replace=False)]
            sh = kernel_shap(f_sd, bg_s, Xs[tr], KSHAP_N_STAB, sd)
            per_seed[sd] = [top3(sh[k], feats) for k in range(len(tr))]
        js, t1, al = [], [], []
        for k in range(len(tr)):
            j, a_, s_ = stab_summary({sd: per_seed[sd][k] for sd in SEEDS})
            js.append(j); t1.append(a_); al.append(s_)
        stab[mo] = {"n": len(tr), "meanJaccardTop3": float(np.mean(js)), "top1AgreementPairwise": float(np.mean(t1)),
                    "top1AllSeedsSame": float(np.mean(al)),
                    "nsamples": f"KernelSHAP nsamples={KSHAP_N_STAB}, bg={KSHAP_BG}, <= {MAX_STAB_KERNEL} targets"}
        print(f"[{tag}] {mo} stability done {time.time()-t0:.0f}s", flush=True)
    xai["stability"] = stab
    xai["notes"] = {"top3": "top-3 strongest suspicion-raising SHAP contributors (padded by |SHAP|)",
                    "kernelCaps": f"KernelSHAP models: <= {MAX_TARGETS_KERNEL} caught targets and {N_NONTARGET_KERNEL} "
                                  f"non-target flagged files per model (IF: all caught targets + {N_NONTARGET}); caught = within the top-20% budget",
                    "lofNote": "LOF rescoring uses a novelty=True refit with the tested row held out (else a training point is its own neighbour), ranked against the ordinary training LOF scores"}

    out = {"tag": tag, "label": spec["label"], "scenario": spec["scenario"], "files": N, "features": feats,
           "constantFeatures": [feats[j] for j in const_idx], "nearConstantFeatures": [feats[j] for j in near_idx],
           "budgets": {str(p): K[p] for p in BUDGET_PCTS}, "targets": len(active),
           "toolOutput": tool, "verdicts": ver, "xai": xai, "seconds": round(time.time() - t0, 1)}
    os.makedirs(TRUST_DIR, exist_ok=True)
    pth = os.path.join(TRUST_DIR, f"{tag}.json")
    with open(pth, "w") as f:
        json.dump(out, f, separators=(",", ":"), default=str)
    print(f"[{tag}] wrote {pth} {os.path.getsize(pth)/1024:.0f} KB in {time.time()-t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------
def fmt_p(p):
    return "n/a" if p is None else (f"{p:.2e}" if p < 1e-3 else f"{p:.3f}")


def write_md():
    os.makedirs(REPORT_DIR, exist_ok=True)
    L = ["# ForensIQ trust evaluation", "",
         "Generated by `trust_eval.py`. Full disk, models fit with seed 42 (as `export_site_data.py`). "
         "Caught = best copy of a target inside the top-20% budget. Top-3 reasons = strongest suspicion-raising SHAP "
         "features. KernelSHAP (LOF, OC-SVM) uses nsamples=300 (faithfulness) / 200 (stability), 50 background rows, "
         "capped at 40 caught targets + 60 non-target flagged files (faithfulness) and 20 targets (stability).", ""]
    for tag in ["img1", "img2", "img3"]:
        p = os.path.join(TRUST_DIR, f"{tag}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        L += [f"## {d['label']} ({d['files']:,} files, {d['targets']} targets)", "",
              f"Constant features: {', '.join(d['constantFeatures'])}", "", "### Tool output (noise vs user files)", "",
              "| model | budget | K | system-noise | user-doc | first target rank | targets hit |", "|---|---|---|---|---|---|---|"]
        for mo in M.MODELS:
            t = d["toolOutput"][mo]
            for b in ["5", "10", "15", "20"]:
                s = t["summary"][b]
                L.append(f"| {SHORT[mo]} | {b}% | {s['K']} | {s['systemNoise']} ({s['systemNoiseShare']*100:.1f}%) | "
                         f"{s['userFiles']} ({s['userShare']*100:.1f}%) | {t['firstTargetRank']} | {s['targetsHit']}/{s['targetsTotal']} |")
        v = d["verdicts"]
        L += ["", "### Evidence-based verdicts", "",
              f"Disk-wide timestomp indicator rate: {v['diskTimestomp']['count']:,}/{v['diskTimestomp']['withFn']:,} "
              f"= {v['diskTimestomp']['rate']*100:.2f}%. Sub-second rule not computable (whole-second times).", "",
              "| model | budget | ts flagged | ts rate | enrichment | Fisher p | ts verdict | (a) wiper | (b) doc traces | (c) USB/cloud | (d) hack tools | insider verdict | hacker verdict |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for mo in M.MODELS:
            for b in ["5", "10", "15", "20"]:
                x = v["perModel"][mo][b]
                t = x["timestomp"]
                i = x["indicators"]
                L.append(f"| {SHORT[mo]} | {b}% | {t['count']} | {t['flaggedRate']*100:.2f}% | {t['enrichment']} | {fmt_p(t['fisherP'])} | "
                         f"{'yes' if t['indicated'] else 'no'} | {i['a_wiper_executed']['count']} | {i['b_recent_doc_traces']['count']} | "
                         f"{i['c_removable_or_cloud']['count']} | {i['d_hacking_tools']['count']} | "
                         f"{'indicated' if x['insiderAntiForensic']['indicated'] else 'no'} | {'indicated' if x['hackerTools']['indicated'] else 'no'} |")
        L += ["", f"Scenario truth: {v['evaluation'][M.MODELS[0]]['20']['truth']}", "",
              "| model | budget | timestomp correct | insider correct | hacker-tools correct |", "|---|---|---|---|---|"]
        for mo in M.MODELS:
            for b in ["5", "10", "15", "20"]:
                e = v["evaluation"][mo][b]
                L.append(f"| {SHORT[mo]} | {b}% | {e['timestomp']['correct']} | {e['insider']['correct']} | {e['hacker_tools']['correct']} |")
        x = d["xai"]
        L += ["", "### Explainability", "",
              "| model | n | median rank change SHAP-top3 | random-3 | SHAP>random share | Wilcoxon p | Jaccard top3 | top-1 pairwise | top-1 all seeds | sense match | SHAP mass on constant |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for mo in M.MODELS:
            f = x["faithfulness"].get(mo, {})
            s = x["stability"].get(mo, {})
            sm = x["summary"].get(mo, {})
            L.append(f"| {SHORT[mo]} | {f.get('n')} | {f.get('medianRankChangeShapTop3', float('nan')):.0f} | "
                     f"{f.get('medianRankChangeRandom3', float('nan')):.0f} | {f.get('shareShapBeatsRandom', float('nan')):.2f} | "
                     f"{fmt_p(f.get('wilcoxonP'))} | {s.get('meanJaccardTop3', float('nan')):.2f} | "
                     f"{s.get('top1AgreementPairwise', float('nan')):.2f} | {s.get('top1AllSeedsSame', float('nan')):.2f} | "
                     f"{(sm.get('senseMatch') if sm.get('senseMatch') is not None else float('nan')):.2f} ({sm.get('senseN')}/{sm.get('targetsCaught20')}) | "
                     f"{sm.get('shapMassConstant', 0):.4f} / near {sm.get('shapMassNearConstant', 0):.4f} |")
        L.append("")
    with open(os.path.join(REPORT_DIR, "trust_eval.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("[+] wrote", os.path.join(REPORT_DIR, "trust_eval.md"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", nargs="+", default=[])
    ap.add_argument("--md-only", action="store_true")
    a = ap.parse_args()
    for t in a.images:
        run_image(t)
    if a.md_only or not a.images:
        write_md()
