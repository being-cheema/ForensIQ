"""
Threshold-stability study ("4th ablation"): is the "100% at 5.5%" result a fluke, and what is a
stable review threshold?

Images: img2 (Win7 data leakage, 19 targets) and img3 (Win10 Lone Wolf, 34 targets). img1 is excluded.
Configs: Isolation Forest / LOF / One-Class SVM on all 23 features, plus Isolation Forest on the 17
legacy features.

One run with seed s:
  1. drop a random 10% of NON-target rows (rows belonging to any target are always kept),
     random generator = np.random.RandomState(s)
  2. standardize, refit with seed s (IF random_state=s, OC-SVM subsample seed s with 10,000 rows,
     LOF is deterministic so only the drop varies), rank the remaining rows by suspicion score
  3. for every threshold pct, K = round(pct * N_sub); a target is caught if any of its rows lies
     in the top K. Because the ranking does not depend on K, the model is fitted once per
     (image, config, seed) and all thresholds are read off that single ranking.
Precision = targets caught / K (same convention as the earlier ablation files).

Seeds: R1 = 0-4, R2 = 100-104, R3 = 200-204. Fine sweep and full sweep use R1.

Usage (from repo root):  .venv/bin/python threshold_sweep.py
Per-fit results are cached in .cache/threshold_sweep so an interrupted run resumes.
"""
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import multimodel_eval as M

OUT = os.path.join(M.BASE_DIR, "reports", "threshold_sweep")
CACHE = os.path.join(M.BASE_DIR, ".cache", "threshold_sweep")
OLD = os.path.join(M.BASE_DIR, "reports")

IMAGES = ["img2", "img3"]
CONFIGS = [  # (name, model, feature set)
    ("IF-23", "Isolation Forest", "all"),
    ("LOF-23", "Local Outlier Factor", "all"),
    ("OCSVM-23", "One-Class SVM", "all"),
    ("IF-17", "Isolation Forest", "legacy"),
]
RANDS = {"R1": [0, 1, 2, 3, 4], "R2": [100, 101, 102, 103, 104], "R3": [200, 201, 202, 203, 204]}
FINE = [5, 7, 9, 11, 13, 15]
GRID = list(range(5, 100, 2)) + [100]
THRESHOLDS = sorted(set(GRID) | set(FINE) | {5.5})
SVM_N = 10000
DROP = 0.10


def one_run(df, X, active, all_idx, model, seed):
    """Returns (N_sub, per-target best rank array) for one seeded run."""
    n = len(df)
    non_target = np.array([i for i in range(n) if i not in all_idx])
    rng = np.random.RandomState(seed)
    drop = rng.choice(non_target, size=int(round(DROP * len(non_target))), replace=False)
    keep = np.ones(n, bool)
    keep[drop] = False
    kept_idx = np.where(keep)[0]
    pos = np.full(n, -1)
    pos[kept_idx] = np.arange(len(kept_idx))
    Xs = M.standardize(X[kept_idx])
    score, _ = M.fit_score(model, Xs, seed, SVM_N)
    _, order = M.top_k_mask(score, len(score))
    rank = np.empty(len(score), int)
    rank[order] = np.arange(len(score))
    best = [min(rank[pos[i]] for i in t["idx"]) for t in active]   # best (lowest) rank per target
    return len(kept_idx), np.array(best)


def hits_at(n_sub, best, pct):
    return int((best < int(round(pct / 100 * n_sub))).sum())


def collect():
    """Run (or load from cache) every fit. Returns dict[(img, cfg, seed)] -> (n_sub, best) and totals."""
    os.makedirs(CACHE, exist_ok=True)
    runs, totals, sizes = {}, {}, {}
    for img in IMAGES:
        spec = M.IMAGES[img]
        t0 = time.time()
        df, raw, feats = M.build_features(spec["art_dir"], img)
        tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
        active, all_idx = M.match_targets(df["path"], tg)
        totals[img] = len(active)
        sizes[img] = len(df)
        print(f"[{img}] {len(df)} files, {len(active)} targets, {len(feats)} features "
              f"({time.time()-t0:.0f}s)", flush=True)
        X_all = df[feats].values.astype(float)
        X_leg = df[M.LEGACY_17].values.astype(float)
        for cfg, model, fs in CONFIGS:
            X = X_all if fs == "all" else X_leg
            for seeds in RANDS.values():
                for s in seeds:
                    f = os.path.join(CACHE, f"{img}_{cfg}_{s}.json")
                    if os.path.exists(f):
                        d = json.load(open(f))
                        runs[(img, cfg, s)] = (d["n_sub"], np.array(d["best"]))
                        continue
                    t1 = time.time()
                    n_sub, best = one_run(df, X, active, all_idx, model, s)
                    json.dump({"n_sub": n_sub, "best": best.tolist()}, open(f, "w"))
                    runs[(img, cfg, s)] = (n_sub, best)
                    print(f"[{img}] {cfg} seed {s}: 5%={hits_at(n_sub,best,5)} 5.5%={hits_at(n_sub,best,5.5)} "
                          f"100%={hits_at(n_sub,best,100)} ({time.time()-t1:.0f}s)", flush=True)
    return runs, totals, sizes


def stat_rows(runs, totals, sizes, seeds, thresholds):
    rows = []
    for img in IMAGES:
        for cfg, _, _ in CONFIGS:
            for pct in thresholds:
                h = np.array([hits_at(*runs[(img, cfg, s)], pct) for s in seeds], float)
                k = np.mean([int(round(pct / 100 * runs[(img, cfg, s)][0])) for s in seeds])
                T = totals[img]
                rows.append({"image": img, "config": cfg, "threshold_pct": pct, "K_mean": round(k, 1),
                             "targets_total": T, "hits_mean": round(h.mean(), 2), "hits_std": round(h.std(), 2),
                             "recall_pct": round(100 * h.mean() / T, 1), "recall_std_pct": round(100 * h.std() / T, 1),
                             "precision_pct": round(100 * h.mean() / k, 4)})
    return pd.DataFrame(rows)


def stable_points(means, grid, total):
    """means: dict pct -> mean hits over grid. Returns (max_recall_pct, first_at_max, first_ge90, knee_sustained, knee_first)."""
    mx = max(means[g] for g in grid)
    first_max = next(g for g in grid if means[g] >= mx - 1e-9)
    ge90 = next((g for g in grid if means[g] / total >= 0.9), None)
    gains = [means[grid[i + 1]] - means[grid[i]] for i in range(len(grid) - 1)]
    knee_first = next((grid[i] for i, g in enumerate(gains) if g < 1), grid[-1])
    # sustained: every later +2% step adds < 1 target on average
    knee_sust = grid[-1]
    for i in range(len(grid) - 1):
        if all(g < 1 for g in gains[i:]):
            knee_sust = grid[i]
            break
    return mx / total * 100, first_max, ge90, knee_sust, knee_first


def main():
    os.makedirs(OUT, exist_ok=True)
    runs, totals, sizes = collect()

    fine = stat_rows(runs, totals, sizes, RANDS["R1"], FINE)
    fine.to_csv(os.path.join(OUT, "fine_sweep.csv"), index=False)
    full = stat_rows(runs, totals, sizes, RANDS["R1"], GRID)
    full.to_csv(os.path.join(OUT, "full_sweep.csv"), index=False)
    at55 = stat_rows(runs, totals, sizes, RANDS["R1"], [5.0, 5.5])

    # --- three randomizations ------------------------------------------------
    rrows, stable, agree = [], {}, {}
    for img in IMAGES:
        T = totals[img]
        for cfg, _, _ in CONFIGS:
            means = {}
            for r, seeds in RANDS.items():
                means[r] = {p: np.mean([hits_at(*runs[(img, cfg, s)], p) for s in seeds]) for p in GRID}
            for p in GRID:
                v = [means[r][p] for r in RANDS]
                rrows.append({"image": img, "config": cfg, "threshold_pct": p, "targets_total": T,
                              **{f"{r}_hits_mean": round(means[r][p], 2) for r in RANDS},
                              **{f"{r}_recall_pct": round(100 * means[r][p] / T, 1) for r in RANDS},
                              "spread": round(max(v) - min(v), 2), "agree_within_0.5": bool(max(v) - min(v) <= 0.5)})
            sp = {r: stable_points(means[r], GRID, T) for r in RANDS}
            sub = [x for x in rrows if x["image"] == img and x["config"] == cfg]
            rate = float(np.mean([x["agree_within_0.5"] for x in sub]))
            names = ["max_recall_pct", "first_at_max_recall", "first_recall_ge_90", "knee_sustained", "knee_first_gain_lt_1"]
            stable[f"{img}/{cfg}"] = {
                "targets_total": T,
                "per_randomization": {r: dict(zip(names, sp[r])) for r in RANDS},
                "agree": {n: len({sp[r][i] for r in RANDS}) == 1 for i, n in enumerate(names)},
                "per_threshold_agreement_rate": round(rate, 3),
                "per_threshold_agree_count": f"{sum(x['agree_within_0.5'] for x in sub)}/{len(sub)}",
                "pooled_15_seed_first_at_max": None, "pooled_15_seed_first_ge_90": None, "pooled_15_seed_knee_sustained": None,
            }
            pooled = {p: np.mean([hits_at(*runs[(img, cfg, s)], p) for ss in RANDS.values() for s in ss]) for p in GRID}
            pm = stable_points(pooled, GRID, T)
            stable[f"{img}/{cfg}"].update(pooled_15_seed_first_at_max=pm[1], pooled_15_seed_first_ge_90=pm[2],
                                          pooled_15_seed_knee_sustained=pm[3])
    rdf = pd.DataFrame(rrows)
    rdf.to_csv(os.path.join(OUT, "randomizations.csv"), index=False)

    # --- compare with earlier claims (IF-17 on img2) --------------------------
    old = pd.read_csv(os.path.join(OLD, "ablation_4_full_sweep_5_to_100.csv"))
    oldr = pd.read_csv(os.path.join(OLD, "ablation_4_three_randomizations.csv"))
    f2 = full[(full.image == "img2") & (full.config == "IF-17")].set_index("threshold_pct")
    claims = []
    for pct, claim in [(5, 7), (11, 10.4), (15, 12), (25, 18), (43, 19)]:
        got = f2.loc[pct]
        claims.append({"threshold_pct": pct, "claimed_hits": claim, "fresh_hits_mean": got.hits_mean,
                       "fresh_hits_std": got.hits_std, "reproduces(|diff|<=0.5)": bool(abs(got.hits_mean - claim) <= 0.5)})
    oldmerge = old.set_index("Threshold_Pct")["Hits_Mean"]
    common = [p for p in GRID if p in oldmerge.index]
    close = sum(abs(f2.loc[p].hits_mean - oldmerge[p]) <= 0.5 for p in common)
    old_ident = int((oldr["Identical"] == "YES").sum())
    comparison = {"claims": claims, "full_sweep_points_within_0.5": f"{close}/{len(common)}",
                  "old_randomizations_identical_rows": f"{old_ident}/{len(oldr)}",
                  "fresh_img2_IF-17_agree_rate": stable["img2/IF-17"]["per_threshold_agree_count"]}
    json.dump({"thresholds_grid": GRID, "stable_thresholds": stable, "comparison_with_earlier_claims": comparison},
              open(os.path.join(OUT, "stable_thresholds.json"), "w"), indent=2, default=float)

    write_md(full, fine, at55, rdf, stable, comparison, totals, sizes)
    print("done", flush=True)


def md_table(df, cols, heads):
    out = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def write_md(full, fine, at55, rdf, stable, comp, totals, sizes):
    L = ["# Threshold stability study (4th ablation, fresh runs)", "",
         "Question: is the 'everything caught at 5.5%' result a fluke, and what review threshold is stable?", "",
         "Method: images img2 (%d files, %d targets) and img3 (%d files, %d targets); IF, LOF, OC-SVM on 23 features plus IF on the 17 legacy features. "
         "Each run drops a random 10%% of non-target rows, refits with the seed, and ranks all remaining rows; every threshold is read off that one ranking "
         "(K = round(pct x rows kept)). A target is caught if any of its rows is in the top K. Precision = targets caught / K. "
         "Seeds: R1 = 0-4, R2 = 100-104, R3 = 200-204; sections 1, 2 and 4 use R1. Reproduce with `.venv/bin/python threshold_sweep.py`."
         % (sizes["img2"], totals["img2"], sizes["img3"], totals["img3"]), ""]
    L += ["## 1. Fine sweep (seeds 0-4, mean +/- std over 5 runs)", ""]
    for img in IMAGES:
        for cfg, _, _ in CONFIGS:
            s = fine[(fine.image == img) & (fine.config == cfg)].copy()
            s["hits"] = s.apply(lambda r: f"{r.hits_mean:.1f} +/- {r.hits_std:.2f}", axis=1)
            s["rec"] = s.apply(lambda r: f"{r.recall_pct:.1f} +/- {r.recall_std_pct:.1f}", axis=1)
            L += [f"### {img} / {cfg} ({totals[img]} targets)", "",
                  md_table(s, ["threshold_pct", "K_mean", "hits", "rec", "precision_pct"],
                           ["Threshold %", "K (files)", "Targets caught", "Recall %", "Precision %"]), ""]
    L += ["## 2. Targets caught at exactly 5.0% and 5.5% (seeds 0-4)", ""]
    t = at55.copy()
    t["hits"] = t.apply(lambda r: f"{r.hits_mean:.1f} +/- {r.hits_std:.2f}", axis=1)
    t["rec"] = t.apply(lambda r: f"{r.recall_pct:.1f}", axis=1)
    L += [md_table(t, ["image", "config", "threshold_pct", "K_mean", "hits", "rec"],
                   ["Image", "Config", "Threshold %", "K", "Targets caught", "Recall %"]), ""]
    L += ["## 3. Full sweep 5-100% (seeds 0-4; mean targets caught, std in brackets)", "",
          "Full per-threshold data (recall, precision) is in `full_sweep.csv`.", ""]
    hdr = ["Threshold %"] + [f"{i}/{c}" for i in IMAGES for c, _, _ in CONFIGS]
    L += ["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
    for p in GRID:
        cells = [str(p)]
        for img in IMAGES:
            for cfg, _, _ in CONFIGS:
                r = full[(full.image == img) & (full.config == cfg) & (full.threshold_pct == p)].iloc[0]
                cells.append(f"{r.hits_mean:.1f} ({r.hits_std:.2f})")
        L.append("| " + " | ".join(cells) + " |")
    L += ["", "## 4. Three independent randomizations: do stable thresholds agree?", "",
          "Stable-threshold definitions (on the 5,7,...,99,100 grid, using the mean over the 5 seeds of each randomization): "
          "(i) smallest threshold where mean recall reaches its maximum; (ii) smallest threshold with mean recall >= 90%; "
          "(iii) knee = smallest threshold after which every further +2% step adds < 1 target on average ('sustained'); "
          "the first-step variant (first +2% step adding < 1 target) is in the JSON. 'Agree rate' = share of thresholds where the three "
          "randomization means lie within 0.5 targets of each other.", ""]
    rows = []
    for k, v in stable.items():
        pr = v["per_randomization"]
        f = lambda n: " / ".join(str(pr[r][n]) for r in RANDS)
        ag = lambda n: "yes" if v["agree"][n] else "NO"
        rows.append(f"| {k} | {f('first_at_max_recall')} ({ag('first_at_max_recall')}) | {f('first_recall_ge_90')} ({ag('first_recall_ge_90')}) | "
                    f"{f('knee_sustained')} ({ag('knee_sustained')}) | {v['per_threshold_agree_count']} ({100*v['per_threshold_agreement_rate']:.0f}%) | "
                    f"{v['pooled_15_seed_first_ge_90']} / {v['pooled_15_seed_knee_sustained']} |")
    L += ["| Image/Config | (i) first at max recall R1/R2/R3 | (ii) first recall>=90% R1/R2/R3 | (iii) knee R1/R2/R3 | Agree rate | Pooled 15 seeds: >=90% / knee |",
          "|---|---|---|---|---|---|"] + rows + [""]
    L += ["## 5. Comparison with the earlier claims (IF on 17 features, img2)", "",
          "No script that produced `reports/ablation_4_threshold_sweep.md/.json`, `ablation_4_full_sweep_5_to_100.csv` or "
          "`ablation_4_three_randomizations.csv` exists in the repository, so those numbers cannot be traced to code; this study re-derives them from scratch.", "",
          md_table(pd.DataFrame(comp["claims"]), ["threshold_pct", "claimed_hits", "fresh_hits_mean", "fresh_hits_std", "reproduces(|diff|<=0.5)"],
                   ["Threshold %", "Claimed targets", "Fresh mean", "Fresh std", "Reproduces (within 0.5)"]), "",
          f"- Full-sweep points where fresh IF-17 mean is within 0.5 of the earlier file: {comp['full_sweep_points_within_0.5']}.",
          f"- Earlier three-randomization file: {comp['old_randomizations_identical_rows']} rows marked identical (it covers 5-43% only, seeds 42/1337/9999). "
          f"Fresh IF-17 img2 agreement within 0.5 targets: {comp['fresh_img2_IF-17_agree_rate']} thresholds.", ""]
    open(os.path.join(OUT, "threshold_sweep.md"), "w").write("\n".join(L) + "\n")
    # findings are appended by hand-written section generated below
    open(os.path.join(OUT, "findings_placeholder.txt"), "w").write("")
    os.remove(os.path.join(OUT, "findings_placeholder.txt"))


if __name__ == "__main__":
    main()
