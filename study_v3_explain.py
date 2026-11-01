"""study_v3_explain.py: explainability ablations B1 (faithfulness), B2 (stability), B3 (planted attacks).
Protocol: reports/study_v3/PROTOCOL.md (+ AMENDMENT.md). Final feature set only (FORENSIQ_FEATURE_SET=final).

    FORENSIQ_FEATURE_SET=final python study_v3_explain.py             # all disks in parallel, then merge
    FORENSIQ_FEATURE_SET=final python study_v3_explain.py --disk img1 # one disk -> results_img1.json
    FORENSIQ_FEATURE_SET=final python study_v3_explain.py --merge     # rebuild summary.md / csv / site.json

Design notes
  * Explainers: Isolation Forest = TreeSHAP; OC-SVM and LOF = KernelSHAP (background 20 rows, nsamples 200, the
    random stream is reseeded per explained row so a row's attribution depends only on model, row and background).
  * A reason = the top-3 features with the largest POSITIVE SHAP value (they push the file towards "suspicious").
  * LOF is transductive: a training row would be its own neighbour. For every explained/edited training row the LOF query
    removes that row from its own neighbour list (exact leave-one-out for the query); ranks are taken against the ordinary
    full-fit LOF scores. Planted rows are not in the data, so they are plain queries.
  * Deletion test replaces features by the column MEDIAN of the standardized matrix (not by permutation).
  * Ground truth is only used to choose which flagged files to explain and for the forensic-sense sanity.
"""
import os, sys, json, time, csv, subprocess, itertools, warnings

import numpy as np
from scipy.stats import wilcoxon
from sklearn.neighbors import LocalOutlierFactor

import multimodel_eval as M
import study_v3_common as C
from trust_eval import top3, jaccard, expected_for

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(C.OUT, "B")
SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OC-SVM"}
MODELS = M.MODELS
KERNEL = ("Local Outlier Factor", "One-Class SVM")
BUDGETS = {"20": 0.20, "15": 0.15}
N_OTHER = {"Isolation Forest": 300, "Local Outlier Factor": 100, "One-Class SVM": 100}
NS, BG_N = 200, 20
N_DRAWS = 5
ONLY = [x for x in os.environ.get("MODELS_ONLY", "").split(",") if x] or None   # e.g. MODELS_ONLY="Isolation Forest": per-file arrays for intervals
NOISE_FRAC = 0.01
PASS_P, PASS_SEED, PASS_NOISE, PASS_ATTR = 0.01, 0.7, 0.6, 0.80
WEAK = {"filename_entropy", "path_depth", "size"}     # not a convincing reason on its own


# --------------------------------------------------------------------------- model wrapper
class Fit:
    def __init__(self, model, X, seed):
        self.model, self.X, self.seed = model, X, seed
        self.ref, self.fm = M.fit_score(model, X, seed)
        self.ref_sorted = np.sort(self.ref)
        self.cache = {}
        if model == "Isolation Forest":
            self.fn = lambda A, exclude=None: -self.fm.score_samples(A)
        elif model == "One-Class SVM":
            self.fn = lambda A, exclude=None: -self.fm.decision_function(A)
        else:
            self.nov = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=-1).fit(X)
            self.fn = self._lof

    def _lof(self, A, exclude=None):
        """LOF of query rows A against the fitted data. `exclude` (row index or array) removes that training row from the
        query's neighbours (exact leave-one-out for the query), so a training row is not its own neighbour."""
        A = np.atleast_2d(A)
        nov, k = self.nov, 20
        if exclude is None:
            dist, ind = nov.kneighbors(A, n_neighbors=k)
        else:
            dist, ind = nov.kneighbors(A, n_neighbors=k + 1)
            e = np.broadcast_to(np.asarray(exclude), (len(A),))[:, None]
            keep = ind != e
            keep[keep.all(1), -1] = False
            dist, ind = dist[keep].reshape(len(A), k), ind[keep].reshape(len(A), k)
        reach = np.maximum(dist, nov._distances_fit_X_[ind, k - 1])
        lrd_q = 1.0 / (reach.mean(1) + 1e-10)
        return nov._lrd[ind].mean(1) / lrd_q

    def rank_vals(self, v):
        """1-based rank of score v among the ordinary scores (count of strictly larger + 1)."""
        return len(self.ref) - np.searchsorted(self.ref_sorted, v, side="right") + 1

    def rank_row(self, i):
        return self.rank_vals(self.ref[i])


def explain(fit, rows, bg, bg_idx=None):
    """SHAP matrix (len(rows) x F) of suspicion, cached per row."""
    import shap
    rows = [int(r) for r in rows]
    miss = [r for r in dict.fromkeys(rows) if r not in fit.cache]
    planted = getattr(fit, "planted", False)
    if miss:
        if fit.model == "Isolation Forest":
            sv = -np.asarray(shap.TreeExplainer(fit.fm).shap_values(fit.X[miss]))
            for r, v in zip(miss, sv):
                fit.cache[r] = v
        else:
            for r in miss:
                ex_r = None if (planted or fit.model != "Local Outlier Factor") else r

                def f(A, ex_r=ex_r):
                    if ex_r is not None and A.shape == bg.shape and np.array_equal(A, bg):
                        return fit.fn(A, bg_idx)       # background rows: each excludes itself
                    return fit.fn(A, ex_r)
                ex = shap.KernelExplainer(f, bg)
                np.random.seed(0)
                fit.cache[r] = np.asarray(ex.shap_values(fit.X[r:r + 1], nsamples=NS, silent=True)).reshape(-1)
    return np.array([fit.cache[r] for r in rows])


def tops(sv, feats):
    return [top3(v, feats) for v in sv]


def jac_mean(a, b):
    return float(np.mean([jaccard(x, y) for x, y in zip(a, b)])) if len(a) else None


def wil(a, b):
    try:
        return float(wilcoxon(a, b, alternative="greater").pvalue)
    except Exception:
        return 1.0


# --------------------------------------------------------------------------- per disk
def run_disk(tag):
    t0 = time.time()
    D = C.load(tag)
    feats, N = D["feats"], D["N"]
    X = D["df"][feats].values.astype(float)
    Xs = M.standardize(X)
    F = len(feats)
    K = {k: int(round(p * N)) for k, p in BUDGETS.items()}
    nonconst = np.where(Xs.std(0) > 0)[0]
    med = np.median(Xs, axis=0)
    bg_idx = np.random.RandomState(0).choice(N, BG_N, replace=False)
    bg = Xs[bg_idx]
    tgt_all = set(int(i) for i in D["all_idx"])
    res = {"tag": tag, "N": N, "K": K, "features": feats, "targets": len(D["active"]), "models": {}}
    log = lambda m: print(f"[{tag}] {m} ({time.time() - t0:.0f}s)", flush=True)

    # ---- base fits (seed 42)
    base = {m: Fit(m, Xs, 42) for m in MODELS}
    log("base fits done")

    # ---- planted data (B3), shared by all models
    rngp = np.random.RandomState(2026)
    cand = np.array([i for i in range(N) if i not in tgt_all and base["Isolation Forest"].rank_row(i) > K["20"]])
    pick = rngp.choice(cand, 60, replace=False)
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    col = {f: j for j, f in enumerate(feats)}
    q = lambda f, p: float(np.percentile(X[:, col[f]], p))
    types = {
        "P1 timestamp forgery": ({"delta_si_fn": q("delta_si_fn", 99.5), "m_before_cr": 1.0},
                                 ["delta_si_fn", "m_before_cr", "delta_mb", "delta_mc"]),
        "P2 hidden executable in temp": ({"is_exe": 1.0, "temp_path": 1.0, "path_depth": q("path_depth", 95)},
                                         ["is_exe", "temp_path", "path_depth"]),
        "P3 bulk-wipe burst": ({"log_burst_count": float(X[:, col["log_burst_count"]].max()),
                                "log_burst_60s": float(X[:, col["log_burst_60s"]].max())},
                               ["log_burst_count", "log_burst_60s"]),
    }
    Xp_raw, ptype = [], []
    for ti, (tn, (mods, _)) in enumerate(types.items()):
        for b in pick[ti * 20:(ti + 1) * 20]:
            r = X[b].copy()
            for f, v in mods.items():
                r[col[f]] = v
            Xp_raw.append(r)
            ptype.append(tn)
    Xp = (np.array(Xp_raw) - mu) / sd
    ptype = np.array(ptype)
    cause = {tn: {col[f] for f in c} for tn, (_, c) in types.items()}
    res["planted_spec"] = {tn: {"set": m, "cause": c} for tn, (m, c) in types.items()}

    for mo in [m_ for m_ in MODELS if ONLY is None or m_ in ONLY]:
        fit = base[mo]
        R = {"model": mo}
        # ---- flagged sets, sample
        order = np.argsort(-fit.ref, kind="stable")
        pos = np.empty(N, np.int64)
        pos[order] = np.arange(1, N + 1)
        caught = []
        for t in D["active"]:
            ii = np.array(t["idx"])
            b = int(ii[np.argmin(pos[ii])])
            if pos[b] <= K["20"]:
                caught.append((t["name"], b))
        pool = [int(i) for i in order[:K["20"]] if int(i) not in tgt_all]
        rs = np.random.RandomState(11)
        others = [int(i) for i in rs.choice(pool, min(N_OTHER[mo], len(pool)), replace=False)]
        rows = [b for _, b in caught] + others
        is_t = np.array([True] * len(caught) + [False] * len(others))
        R["n_targets_caught20"] = len(caught)
        R["n_targets_caught15"] = int(sum(pos[b] <= K["15"] for _, b in caught))
        sv = explain(fit, rows, bg, bg_idx)
        T3 = tops(sv, feats)
        log(f"{SHORT[mo]} base SHAP on {len(rows)} rows")

        # ---- B1 faithfulness
        rr = np.random.RandomState(1)
        Q = []
        for i, t3 in zip(rows, T3):
            xm = Xs[i].copy(); xm[t3] = med[t3]; Q.append(xm)
            for _ in range(N_DRAWS):
                xr = Xs[i].copy(); j = rr.choice(nonconst, 3, replace=False); xr[j] = med[j]; Q.append(xr)
        sc = fit.fn(np.array(Q), np.repeat(rows, 1 + N_DRAWS)).reshape(len(rows), 1 + N_DRAWS)
        q0 = fit.fn(Xs[rows], np.array(rows))
        rank_excl = lambda v, i: fit.rank_vals(v) - (1 if fit.ref[i] > v else 0)
        old = np.array([rank_excl(q0[k], i) for k, i in enumerate(rows)])
        new = np.array([rank_excl(sc[k, 0], i) for k, i in enumerate(rows)])
        rnd = np.array([[rank_excl(sc[k, d], i) for d in range(1, 1 + N_DRAWS)] for k, i in enumerate(rows)])
        d_shap = (new - old).astype(float)
        d_rand = (rnd - old[:, None]).mean(1)
        pos_rows = np.array([pos[i] for i in rows])
        b1 = {}
        for bk in BUDGETS:
            m_ = pos_rows <= K[bk]
            a, b = d_shap[m_], d_rand[m_]
            ms, mr = float(np.median(a)), float(np.median(b))
            tt = m_ & is_t
            b1[bk] = {"n": int(m_.sum()), "n_targets": int(tt.sum()), "median_drop_shap": ms,
                      "median_drop_random": mr, "ratio": (ms / mr if mr > 0 else None),
                      "mean_drop_shap": float(a.mean()), "mean_drop_random": float(b.mean()),
                      "share_shap_beats_random": float((a > b).mean()), "wilcoxon_p": wil(a, b),
                      "pass": bool(wil(a, b) < PASS_P),
                      "targets_median_shap": float(np.median(d_shap[tt])) if tt.any() else None,
                      "targets_median_random": float(np.median(d_rand[tt])) if tt.any() else None}
        R["B1"] = b1
        m20 = pos_rows <= K["20"]
        R["B1_perfile"] = {"drop_shap": [float(x) for x in d_shap[m20]], "drop_random": [float(x) for x in d_rand[m20]]}
        log(f"{SHORT[mo]} B1 done")

        # ---- forensic sense (descriptive)
        sense = []
        for k, (name, b) in enumerate(caught):
            exp = expected_for(name)
            t3n = [feats[j] for j in T3[k]]
            sense.append({"target": name, "rank": int(pos[b]), "top3": t3n, "expected": exp,
                          "top1_sensible": bool(t3n and t3n[0] not in WEAK),
                          "match_expected": bool(set(t3n) & set(exp))})
        R["sense"] = sense
        R["sense_summary"] = {"n": len(sense),
                              "top1_sensible": float(np.mean([s["top1_sensible"] for s in sense])) if sense else None,
                              "match_expected": float(np.mean([s["match_expected"] for s in sense])) if sense else None}

        # ---- B2 stability
        b2 = {}
        # (i) seeds
        if mo != "Local Outlier Factor":
            fits = {sd_: (fit if sd_ == 42 else Fit(mo, Xs, sd_)) for sd_ in C.SEEDS}
            rk = {sd_: np.array([f.rank_row(i) for i in rows]) for sd_, f in fits.items()}
            seeds_res = {}
            for bk in BUDGETS:
                common = [k for k in range(len(rows))
                          if all(rk[s_][k] <= K[bk] for s_ in C.SEEDS) and pos_rows[k] <= K[bk]]
                cr = [rows[k] for k in common]
                tp = {s_: tops(explain(f, cr, bg, bg_idx), feats) for s_, f in fits.items()}
                js = []
                for k in range(len(cr)):
                    js.append(np.mean([jaccard(tp[a][k], tp[b][k]) for a, b in itertools.combinations(C.SEEDS, 2)]))
                seeds_res[bk] = {"per_file": [float(x) for x in js], "n_common": len(cr), "n_sample_flagged": int((pos_rows <= K[bk]).sum()),
                                 "mean_jaccard": float(np.mean(js)) if js else None}
            b2["seeds"] = seeds_res
            log(f"{SHORT[mo]} B2 seeds done")
        else:
            b2["seeds"] = None      # LOF has no random component
        # (ii) 1 % input noise
        rn = np.random.RandomState(5)
        Xn = Xs + rn.normal(size=Xs.shape) * NOISE_FRAC * Xs.std(0)
        fn_ = Fit(mo, Xn, 42)
        bgn = Xn[bg_idx]
        svn = explain(fn_, rows, bgn, bg_idx)
        Tn = tops(svn, feats)
        noise_res = {}
        for bk in BUDGETS:
            m_ = np.where(pos_rows <= K[bk])[0]
            noise_res[bk] = {"per_file": [jaccard(T3[k], Tn[k]) for k in m_], "n": int(len(m_)),
                             "mean_jaccard": jac_mean([T3[k] for k in m_], [Tn[k] for k in m_]),
                             "top1_same": float(np.mean([T3[k][0] == Tn[k][0] for k in m_])) if len(m_) else None}
        b2["noise"] = noise_res
        R["B2"] = b2
        log(f"{SHORT[mo]} B2 noise done")

        # ---- B3 planted attacks
        b3 = {}
        seeds_p = C.SEEDS if mo == "Isolation Forest" else [42]
        per_seed = []
        for s_ in seeds_p:
            f = fit if s_ == 42 else Fit(mo, Xs, s_)
            psc = f.fn(Xp)
            prank = f.rank_vals(psc)
            psv = explain(_PlantedView(f, Xp), list(range(len(Xp))), bg, bg_idx)
            ptop = tops(psv, feats)
            recs = {}
            for tn in types:
                idx = np.where(ptype == tn)[0]
                for bk in BUDGETS:
                    det = np.array([prank[k] <= K[bk] for k in idx])
                    hit = np.array([bool(set(ptop[k]) & cause[tn]) for k in idx])
                    recs[(tn, bk)] = (det, hit)
            per_seed.append((s_, recs, prank, ptop))
        b3["raw20"] = {str(s_): {"detected": np.concatenate([recs[(k_, "20")][0] for k_ in types]).astype(int).tolist(),
                                 "named": np.concatenate([recs[(k_, "20")][1] for k_ in types]).astype(int).tolist()}
                       for s_, recs, _, _ in per_seed}
        for tn in list(types) + ["ALL"]:
            for bk in BUDGETS:
                vals = []
                for s_, recs, _, _ in per_seed:
                    keys = list(types) if tn == "ALL" else [tn]
                    det = np.concatenate([recs[(k_, bk)][0] for k_ in keys])
                    hit = np.concatenate([recs[(k_, bk)][1] for k_ in keys])
                    vals.append((len(det), det.sum(), (det & hit).sum(), hit.sum()))
                n_ = vals[0][0]
                det_r = [v[1] / n_ for v in vals]
                att_det = [v[2] / v[1] if v[1] else float("nan") for v in vals]
                att_all = [v[3] / n_ for v in vals]
                b3.setdefault(tn, {})[bk] = {
                    "n": int(n_), "detect_pct": 100 * float(np.mean(det_r)),
                    "attr_hit_detected_pct": 100 * float(np.nanmean(att_det)) if not all(np.isnan(att_det)) else None,
                    "attr_hit_all_pct": 100 * float(np.mean(att_all)),
                    "seeds": [int(s_) for s_ in seeds_p],
                    "attr_hit_detected_pct_by_seed": [None if np.isnan(a) else 100 * float(a) for a in att_det],
                    "detect_pct_by_seed": [100 * float(a) for a in det_r]}
        # example: top-3 of the first planted row per type (seed 42)
        s42 = [p for p in per_seed if p[0] == 42][0]
        b3["examples"] = {tn: {"rank": int(s42[2][np.where(ptype == tn)[0][0]]),
                               "top3": [feats[j] for j in s42[3][np.where(ptype == tn)[0][0]]]} for tn in types}
        R["B3"] = b3
        log(f"{SHORT[mo]} B3 done")
        res["models"][mo] = R

    res["runtime_s"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"results_{tag}" + ("_perfile" if ONLY else "") + ".json"), "w"), indent=1, default=float)
    log("written")


class _PlantedView:
    """Minimal Fit-like view so explain() can explain planted rows (matrix Xp) with the fitted model of f."""
    def __init__(self, f, Xp):
        self.model, self.fm, self.fn, self.X, self.cache, self.planted = f.model, getattr(f, 'fm', None), f.fn, Xp, {}, True


# --------------------------------------------------------------------------- merge / report
def fmt(x, nd=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def pf(b):
    return "PASS" if b else "FAIL"


def merge():
    P = {t: json.load(open(os.path.join(OUT, f"results_{t}.json"))) for t in C.DISKS if
         os.path.exists(os.path.join(OUT, f"results_{t}.json"))}
    tags = list(P)
    L = []
    w = L.append
    verdict = {"B1": {}, "B2": {}, "B3": {}}
    rows_b1, rows_b2, rows_b3, rows_sense = [], [], [], []
    for t in tags:
        for mo in MODELS:
            R = P[t]["models"][mo]
            sm = SHORT[mo]
            for bk in BUDGETS:
                b = R["B1"][bk]
                rows_b1.append([t, sm, bk, b["n"], b["n_targets"], b["median_drop_shap"], b["median_drop_random"],
                                b["ratio"], b["share_shap_beats_random"], b["wilcoxon_p"], pf(b["pass"])])
            for bk in BUDGETS:
                s = R["B2"]["seeds"][bk] if R["B2"]["seeds"] else None
                n_ = R["B2"]["noise"][bk]
                sj = s["mean_jaccard"] if s else None
                ok_s = True if s is None else (sj is not None and sj >= PASS_SEED)
                ok_n = n_["mean_jaccard"] is not None and n_["mean_jaccard"] >= PASS_NOISE
                rows_b2.append([t, sm, bk, s["n_common"] if s else None, sj, n_["n"], n_["mean_jaccard"],
                                n_["top1_same"], pf(ok_s and ok_n)])
            for tn in list(P[t]["planted_spec"]) + ["ALL"]:
                for bk in BUDGETS:
                    b = R["B3"][tn][bk]
                    ok = b["attr_hit_detected_pct"] is not None and b["attr_hit_detected_pct"] >= 100 * PASS_ATTR
                    rows_b3.append([t, sm, tn, bk, b["n"], b["detect_pct"], b["attr_hit_detected_pct"],
                                    b["attr_hit_all_pct"], pf(ok) if tn == "ALL" else ""])
            ss = R["sense_summary"]
            rows_sense.append([t, sm, ss["n"], ss["top1_sensible"], ss["match_expected"]])
    # csvs
    def wcsv(name, head, rows):
        with open(os.path.join(OUT, name), "w", newline="") as f:
            cw = csv.writer(f); cw.writerow(head); cw.writerows(rows)
    wcsv("b1_faithfulness.csv", ["disk", "model", "budget_pct", "n_files", "n_targets", "median_rank_drop_shap_top3",
                                 "median_rank_drop_random3", "ratio", "share_shap_beats_random", "wilcoxon_p", "result"], rows_b1)
    wcsv("b2_stability.csv", ["disk", "model", "budget_pct", "n_files_seeds", "jaccard_seeds", "n_files_noise",
                              "jaccard_noise_1pct", "top1_same_noise", "result"], rows_b2)
    wcsv("b3_planted.csv", ["disk", "model", "attack", "budget_pct", "n", "detected_pct", "attr_hit_of_detected_pct",
                            "attr_hit_of_all_pct", "result_all_types"], rows_b3)
    wcsv("forensic_sense.csv", ["disk", "model", "targets_caught_at_20", "top1_not_weak_share", "match_expected_share"], rows_sense)
    json.dump(P, open(os.path.join(OUT, "results.json"), "w"), default=float)

    # verdicts (headline 20 %)
    b1c = {(r[0], r[1]): r[10] for r in rows_b1 if r[2] == "20"}
    b2c = {(r[0], r[1]): r[8] for r in rows_b2 if r[2] == "20"}
    b3c = {(r[0], r[1]): r[8] for r in rows_b3 if r[2] == "ALL" and r[3] == "20"}
    rule = lambda d: ("PASS" if all(v == "PASS" for v in d.values()) else "FAIL") + f" ({sum(v == 'PASS' for v in d.values())}/{len(d)} disk x model cells pass)"

    w("# Study v3, explainability ablations B1-B3 (final feature set)")
    w("")
    w("Feature set: 19 features (17 clean + log_burst_count, log_burst_60s). Headline flagging budget: top 20% of the disk by "
      "suspicion score (15% reported alongside). Models are fitted once per seed on the standardized matrix; every number below "
      "comes from `study_v3_explain.py`. Pass rules are the ones fixed in PROTOCOL.md; a rule passes only if **every** disk x model "
      "cell passes.")
    w("")
    w("## Verdict")
    w("")
    w("| Rule | What it asks | Result at 20% |")
    w("|---|---|---|")
    w(f"| B1 faithfulness | removing the SHAP top-3 moves a flagged file down the ranking more than removing 3 random features (one-sided Wilcoxon p < 0.01) | **{rule(b1c)}** |")
    w(f"| B2 stability | top-3 reasons agree across seeds (Jaccard >= 0.7) and under 1% noise (>= 0.6) | **{rule(b2c)}** |")
    w(f"| B3 planted attacks | SHAP top-3 names the planted cause in >= 80% of detected planted files | **{rule(b3c)}** |")
    w("")
    fails = lambda d: ", ".join(f"{k[0]} {k[1]}" for k, v in d.items() if v != "PASS") or "none"
    w("Cells that fail at 20% (disk model):")
    w("")
    w(f"- B1: {fails(b1c)}")
    w(f"- B2: {fails(b2c)}")
    w(f"- B3: {fails(b3c)}")
    w("")
    w("Cells are listed in the tables below. Failures are reported as failures; nothing was re-tuned. "
      "Counting only Isolation Forest (TreeSHAP) and OC-SVM, the pattern in the tables is that their reasons are faithful and stable, "
      "while LOF's KernelSHAP reasons are not: LOF is a local density method, so editing a few features can move a file to another sparse "
      "region instead of a dense one (the ranking does not fall), and a 1% jitter reshuffles its nearest neighbours.")
    w("")
    w("## How each test works (plain English)")
    w("")
    w("- **Reason** = the three features that push a file's suspicion score up the most (largest positive SHAP values). "
      "Isolation Forest uses TreeSHAP; One-Class SVM and LOF use KernelSHAP (20 background rows, 200 samples per file).")
    w("- **B1 deletion test.** For flagged files (every target caught, plus a seeded random sample of other flagged files: "
      "300 for Isolation Forest, 100 for OC-SVM and LOF) we overwrite the three reason features with the disk's **median** value "
      "(not a permutation), score the file again with the **same fitted model**, and see how far it falls in the ranking. "
      "The control overwrites 3 random features of the same file the same way (5 draws, averaged). A faithful explanation "
      "should cause a bigger drop than the random control.")
    w("- **B2 stability.** (i) Seeds: Isolation Forest and OC-SVM are refitted with the 5 study seeds; for files flagged under all 5 seeds "
      "we take the mean pairwise Jaccard overlap of their top-3 reasons. LOF has no random component, so only the noise test applies. "
      "(ii) Noise: Gaussian noise with sd = 1% of each column's std is added to the standardized matrix, the model is refitted "
      "(seed 42) and the top-3 reasons are compared with the clean ones. KernelSHAP's own sampling noise is removed by reusing the "
      "same random stream, so differences come from the model, not the explainer's dice.")
    w("- **B3 planted attacks.** Per disk, 60 random ordinary files (non-target, not flagged by Isolation Forest seed 42) are copied and "
      "one cause is planted in each copy, 20 per attack type: P1 timestamp forgery (delta_si_fn at the disk's 99.5th percentile, m_before_cr = 1; "
      "cause features delta_si_fn, m_before_cr, delta_mb, delta_mc), P2 hidden executable in temp (is_exe = 1, temp_path = 1, path_depth at the 95th "
      "percentile), P3 bulk-wipe burst (both burst features at the disk maximum). Planted rows are standardized with the original disk mean/std, "
      "scored by models fitted on the original rows only, and explained. *Detected* = lands in the flagged top 20%; "
      "*attribution hit* = top-3 reasons include at least one cause feature. Isolation Forest is repeated over all 5 seeds (values are 5-seed means).")
    w("- **LOF caveat.** LOF is transductive: a row in its own training set counts as its own neighbour. Every explained or edited training row is therefore "
      "queried with itself removed from its neighbour list (the original and the edited version alike), and ranked against the ordinary LOF scores. "
      "The other points' densities still include the row, a second-order effect that is the same for the SHAP and control arms.")
    w("")

    w("## B1 Faithfulness (deletion test)")
    w("")
    for bk in BUDGETS:
        w(f"### Flagged = top {bk}%")
        w("")
        w("| Disk | Model | Files (targets) | Median rank drop, SHAP top-3 | Median rank drop, random 3 | Ratio | SHAP > random share | Wilcoxon p | Result |")
        w("|---|---|---|---|---|---|---|---|---|")
        for r in rows_b1:
            if r[2] == bk:
                p = r[9]
                w(f"| {r[0]} | {r[1]} | {r[3]} ({r[4]}) | {fmt(r[5], 0)} | {fmt(r[6], 1)} | {fmt(r[7], 1)} | {fmt(r[8])} | "
                  f"{'<1e-4' if p < 1e-4 else f'{p:.4f}'} | {pf(r[10] == 'PASS')} |")
        w("")
    w("Rank drop = how many places lower the file ranks after the edit (higher means the removed features mattered more).")
    w("")

    w("## B2 Stability of reasons")
    w("")
    for bk in BUDGETS:
        w(f"### Flagged = top {bk}%")
        w("")
        w("| Disk | Model | Files in all 5 seeds | Jaccard across seeds (>= 0.7) | Files (noise) | Jaccard under 1% noise (>= 0.6) | Same top reason under noise | Result |")
        w("|---|---|---|---|---|---|---|---|")
        for r in rows_b2:
            if r[2] == bk:
                w(f"| {r[0]} | {r[1]} | {r[3] if r[3] is not None else 'n/a (deterministic)'} | {fmt(r[4])} | {r[5]} | {fmt(r[6])} | {fmt(r[7])} | {pf(r[8] == 'PASS')} |")
        w("")
    w("For LOF the seed test does not exist, so its result rests on the noise test alone.")
    w("")

    w("## B3 Planted attacks (known cause)")
    w("")
    for bk in BUDGETS:
        w(f"### Detection and attribution, flagged = top {bk}%")
        w("")
        w("| Disk | Model | Attack | Detected (%) | Attribution hit, of detected (%) | Attribution hit, of all planted (%) | Result (all types, of detected >= 80) |")
        w("|---|---|---|---|---|---|---|")
        for r in rows_b3:
            if r[3] == bk:
                w(f"| {r[0]} | {r[1]} | {r[2]} | {fmt(r[5], 1)} | {fmt(r[6], 1)} | {fmt(r[7], 1)} | {r[8]} |")
        w("")
    w("Planted values for Isolation Forest are means over the 5 seeds (per-seed values are in results.json).")
    w("")

    w("## Forensic sense (descriptive, no pass rule)")
    w("")
    w("Among the real targets caught in the top 20% (best copy of each target), the share whose single strongest reason is not "
      "filename_entropy, path_depth or size alone, and the share whose top-3 includes a feature a forensic examiner would expect for "
      "that kind of target (hand-written list carried over from the earlier trust study).")
    w("")
    w("| Disk | Model | Targets caught | Top reason is a forensic feature | Top-3 includes an expected feature |")
    w("|---|---|---|---|---|")
    for r in rows_sense:
        w(f"| {r[0]} | {r[1]} | {r[2]} | {fmt(r[3])} | {fmt(r[4])} |")
    w("")
    w("_Reading it honestly: see the per-target detail in site.json; a high share here does not prove the reason is right, only that it is not an obvious artefact._")
    w("")
    w("## Runtime")
    w("")
    w("Per-disk seconds: " + ", ".join(f"{t} {P[t]['runtime_s']}" for t in tags) + " (disks ran in parallel).")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")

    # compact site.json
    site = {"featureSet": "final", "headline": "top 20%", "rules": {"B1": rule(b1c), "B2": rule(b2c), "B3": rule(b3c)},
            "thresholds": {"B1_p": PASS_P, "B2_seed": PASS_SEED, "B2_noise": PASS_NOISE, "B3_attr": PASS_ATTR}, "disks": {}}
    for t in tags:
        site["disks"][t] = {}
        for mo in MODELS:
            R = P[t]["models"][mo]
            d = {"B1": R["B1"], "B2": R["B2"], "sense": R["sense_summary"],
                 "B3": {tn: {bk: {k: v for k, v in R["B3"][tn][bk].items() if not k.endswith("by_seed")} for bk in BUDGETS}
                        for tn in list(P[t]["planted_spec"]) + ["ALL"]},
                 "B3examples": R["B3"]["examples"],
                 "targets": [[s["target"], s["rank"], s["top3"], s["match_expected"]] for s in R["sense"]]}
            site["disks"][t][SHORT[mo]] = d
    s = json.dumps(site, separators=(",", ":"), default=float)
    assert len(s) < 400_000, len(s)
    open(os.path.join(OUT, "site.json"), "w").write(s)
    print(f"merged: summary.md, csvs, results.json, site.json ({len(s)/1024:.0f} KB)")


if __name__ == "__main__":
    if M.FEATURE_SET != "final":
        sys.exit("run with FORENSIQ_FEATURE_SET=final")
    os.makedirs(OUT, exist_ok=True)
    a = sys.argv[1:]
    if "--disk" in a:
        run_disk(a[a.index("--disk") + 1])
    elif "--merge" in a:
        merge()
    else:
        t0 = time.time()
        ps = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "--disk", t]) for t in C.DISKS]
        rc = [p.wait() for p in ps]
        if any(rc):
            sys.exit(f"disk job failed: {rc}")
        merge()
        print(f"total {time.time() - t0:.0f}s")
