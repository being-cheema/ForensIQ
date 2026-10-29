"""
study_v3_reliability_b.py
=========================
Study v3 reliability ablations A1 (feature groups), A3 (feature sets), A5 (hyperparameters) and
A7 (robustness). Judged against the pass rules in reports/study_v3/PROTOCOL.md.

Isolation Forest uses all five protocol seeds; LOF and One-Class SVM use seed 42 only for A1/A3.
Scores are cached in .cache/study_v3b/.

    python study_v3_reliability_b.py
"""

import os
import json
import time
import hashlib

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

import multimodel_eval as M
import study_v3_common as C

DISKS, SEEDS, BUDGETS, HEADLINE = C.DISKS, C.SEEDS, C.BUDGETS, C.HEADLINE
MODELS = M.MODELS
IF_, LOF_, SVM_ = MODELS
SHORT = {IF_: "IF", LOF_: "LOF", SVM_: "OCSVM"}
CACHE = os.path.join(M.BASE_DIR, ".cache", "study_v3b")
os.makedirs(CACHE, exist_ok=True)
OUT = C.OUT
T0 = time.time()


# ----------------------------------------------------------------------------- helpers
def cached(key, fn):
    h = hashlib.sha1(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()[:24]
    p = os.path.join(CACHE, h + ".npy")
    if os.path.exists(p):
        return np.load(p)
    s = np.asarray(fn(), dtype=np.float32)
    np.save(p, s)
    return s


def S(D, model, cols, seed, variant="clean"):
    """Cached suspicion scores (float32 so cached and fresh runs rank identically)."""
    cols = list(cols)
    return cached([variant, D["tag"], model, cols, seed], lambda: C.score(D, model, cols, seed))


def seeds_for(model):
    return SEEDS if model == IF_ else [42]


def agg(summs):
    out = {"n_seeds": len(summs), "targets": summs[0]["targets"]}
    for k in ("at15", "at20", "knee_pct", "plateau_pct"):
        v = np.array([s[k] for s in summs], dtype=float)
        out[k] = round(float(v.mean()), 3)
        out[k + "_sd"] = round(float(v.std(ddof=1)) if len(v) > 1 else 0.0, 3)
    return out


def ev(D, model, cols, variant="clean"):
    summs = [C.summary(D, S(D, model, cols, sd, variant)) for sd in seeds_for(model)]
    return agg(summs)


def ev_all(cols, variant="clean", models=MODELS, Dmap=None):
    """{disk: {model: agg}}"""
    r = {}
    for t in DISKS:
        D = (Dmap or DATA)[t]
        r[t] = {m: ev(D, m, cols, variant) for m in models}
    return r


def pm(a, k, d=1):
    return f"{a[k]:.{d}f}±{a[k + '_sd']:.{d}f}" if a["n_seeds"] > 1 else f"{a[k]:.{d}f}"


def table(header, rows):
    L = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    L += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(L)


def write(folder, name, text):
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


def write_site(folder, obj):
    s = json.dumps(obj, separators=(",", ":"))
    assert len(s) < 400_000, (folder, len(s))
    write(folder, "site.json", s)
    print(f"  site.json {folder}: {len(s) / 1000:.1f} KB")


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def verdict(ok):
    return "PASS" if ok else "FAIL"


# ----------------------------------------------------------------------------- data
log("loading disks (clean + legacy tables)")
DATA, LEG = {}, {}
for t in DISKS:
    D = C.load(t)
    spec = M.IMAGES[t]
    ldf, lraw, lfeats = M.build_features_legacy23(spec["art_dir"], t)
    M.add_burst_features(ldf, lraw)
    assert len(ldf) == D["N"] and (ldf["path"].values == D["df"]["path"].values).all(), "row mismatch"
    assert (lraw["path"].values == D["raw"]["path"].values).all()
    DATA[t] = D
    LEG[t] = dict(D, df=ldf, feats=list(lfeats))
CLEAN = DATA["img1"]["feats"]
GROUPS = M.GROUPS_CLEAN
assert sorted(sum(GROUPS.values(), [])) == sorted(CLEAN)
BURST = M.BURST
TG = {t: DATA[t]["N"] for t in DISKS}
NT = {t: len(DATA[t]["active"]) for t in DISKS}
log(f"disks: {TG}  targets: {NT}  clean features: {len(CLEAN)}")

CLEAN_EV = ev_all(CLEAN)  # reference results used by several ablations


def deltas(a, b):
    """{disk: (d15, d20)} of IF seed means, b minus a (dict {disk: {model: agg}})."""
    return {t: (round(b[t][IF_]["at15"] - a[t][IF_]["at15"], 3), round(b[t][IF_]["at20"] - a[t][IF_]["at20"], 3))
            for t in DISKS}


# ============================================================================= A1
def run_A1():
    log("A1 feature groups")
    sets = {"full clean set": CLEAN}
    for g, cols in GROUPS.items():
        sets[f"only {g}"] = list(cols)
        sets[f"all except {g}"] = [c for c in CLEAN if c not in cols]
    res = {name: ev_all(cols) for name, cols in sets.items()}
    full = res["full clean set"]

    # rule (a): removing a group lowers IF mean recall at 15% or 20% on >=1 disk
    rule_a, rule_b = {}, {}
    for g in GROUPS:
        d = deltas(full, res[f"all except {g}"])
        rule_a[g] = {"lowers_on": [t for t in DISKS if d[t][0] < 0 or d[t][1] < 0], "deltas": d}
        o = res[f"only {g}"]
        matches = all(o[t][IF_]["at15"] >= full[t][IF_]["at15"] - 1e-9 and o[t][IF_]["at20"] >= full[t][IF_]["at20"] - 1e-9
                      for t in DISKS)
        rule_b[g] = {"alone_matches_full_on_all_disks": matches}
    pass_a = all(len(v["lowers_on"]) >= 1 for v in rule_a.values())
    pass_b = not any(v["alone_matches_full_on_all_disks"] for v in rule_b.values())
    ok = pass_a and pass_b

    L = ["# A1: feature-group ablation", "",
         "Which of the three feature groups of the clean set do the results depend on? Each group is tested "
         "alone (only that group) and removed (everything except that group), on all three disks.", "",
         "Settings: Isolation Forest (200 trees, sample 256) with all five seeds, reported as mean±sd over seeds "
         "(sd with n-1). **LOF and One-Class SVM were run with seed 42 only** (single value, no sd). "
         "Budgets 15% and 20% of the disk; knee = smallest budget (% of disk) reaching >=90% of targets; "
         "plateau = budget at which the last target is reached. Targets: "
         + ", ".join(f"{t} = {NT[t]}" for t in DISKS) + ".", "",
         "Groups (clean set): " + "; ".join(f"{g} = {len(c)} feature(s) ({', '.join(c)})" for g, c in GROUPS.items()) + ".", ""]
    for t in DISKS:
        L += [f"## {DATA[t]['label']} ({NT[t]} targets, {TG[t]:,} files)", ""]
        rows = []
        for name in sets:
            a = res[name][t]
            rows.append([name, len(sets[name]), pm(a[IF_], "at15"), pm(a[IF_], "at20"), pm(a[IF_], "knee_pct"),
                         pm(a[IF_], "plateau_pct"), a[LOF_]["at15"], a[LOF_]["at20"], a[SVM_]["at15"], a[SVM_]["at20"]])
        L += [table(["feature set", "#feat", "IF at15", "IF at20", "IF knee %", "IF plateau %", "LOF at15", "LOF at20",
                     "OCSVM at15", "OCSVM at20"], rows), ""]
    L += ["## Pass rules (PROTOCOL A1)", "",
          "Evaluated on IF seed means. \"Lowers recall\" = removing the group gives a lower mean at 15% or at 20% on at least one disk.", ""]
    rows = [[g, ", ".join(rule_a[g]["lowers_on"]) or "none", " / ".join(f"{t}: {rule_a[g]['deltas'][t][0]:+.1f},{rule_a[g]['deltas'][t][1]:+.1f}" for t in DISKS),
             "yes" if rule_b[g]["alone_matches_full_on_all_disks"] else "no"] for g in GROUPS]
    L += [table(["group", "removal lowers recall on", "change at15,at20 when removed (targets)", "group alone matches full set on all disks"], rows), "",
          f"- Rule 1 (every group's removal lowers recall on >=1 disk): **{verdict(pass_a)}**",
          f"- Rule 2 (no single group alone matches the full set on all disks): **{verdict(pass_b)}**",
          f"- A1 overall: **{verdict(ok)}**", ""]
    write("A1", "summary.md", "\n".join(L))
    write_site("A1", {"groups": GROUPS, "budgets": HEADLINE, "targets": NT, "n": TG,
                      "if_seeds": SEEDS, "other_models_seed": 42,
                      "results": {n: {t: {SHORT[m]: res[n][t][m] for m in MODELS} for t in DISKS} for n in res},
                      "rule1": {g: v["lowers_on"] for g, v in rule_a.items()},
                      "rule2": {g: v["alone_matches_full_on_all_disks"] for g, v in rule_b.items()},
                      "pass": {"rule1": pass_a, "rule2": pass_b, "overall": ok}})
    return ok


# ============================================================================= A3
def curve_mean(D, model, cols, variant="clean"):
    cs = np.array([C.curve(D, S(D, model, cols, sd, variant)) for sd in seeds_for(model)], dtype=float)
    return [round(float(x), 2) for x in cs.mean(0)]


def flagged_mask(s, N, pct):
    k = int(round(pct / 100 * N))
    order = np.argsort(-s, kind="stable")
    m = np.zeros(N, bool)
    m[order[:k]] = True
    return m


def run_A3():
    log("A3 feature sets")
    L = ["# A3: feature-set ablations", "",
         "Settings: Isolation Forest with all five seeds (mean±sd over seeds, sd with n-1). **LOF and One-Class SVM "
         "were run with seed 42 only** (single value). Budgets 15%/20% of the disk. Targets: "
         + ", ".join(f"{t} = {NT[t]}" for t in DISKS) + ".", ""]
    site = {"targets": NT, "n": TG, "if_seeds": SEEDS, "other_models_seed": 42}

    def tbl_sets(named):
        out = []
        for t in DISKS:
            rows = []
            for name, r in named.items():
                a = r[t]
                rows.append([name] + [x for m in MODELS for x in (pm(a[m], "at15"), pm(a[m], "at20"), pm(a[m], "knee_pct"), pm(a[m], "plateau_pct"))])
            out += [f"**{DATA[t]['label']}** ({NT[t]} targets)", "",
                    table(["set"] + [f"{SHORT[m]} {k}" for m in MODELS for k in ("at15", "at20", "knee %", "plateau %")], rows), ""]
        return out

    # (a) legacy23 vs clean
    leg_feats = {t: LEG[t]["feats"] for t in DISKS}
    LEG_EV = {t: {m: ev(LEG[t], m, leg_feats[t], "legacy23") for m in MODELS} for t in DISKS}
    L += ["## (a) legacy23 vs clean", "",
          f"legacy23 = the 23 features used up to study v2 ({len(leg_feats['img1'])} columns found); clean = {len(CLEAN)} features. "
          "The legacy table was rebuilt with the same builder and checked to have identical file paths and row order as the clean table.", ""]
    L += tbl_sets({"legacy23": LEG_EV, "clean": CLEAN_EV})
    site["a_legacy_vs_clean"] = {"legacy23": LEG_EV, "clean": CLEAN_EV}
    site["curves"] = {t: {"legacy23": curve_mean(LEG[t], IF_, leg_feats[t], "legacy23"),
                          "clean": curve_mean(DATA[t], IF_, CLEAN)} for t in DISKS}

    # (b) drop one
    log("A3(b) drop-one")
    drop = {f: ev_all([c for c in CLEAN if c != f]) for f in CLEAN}
    rows, raise_set, drop_site = [], {}, {}
    for f in CLEAN:
        d = deltas(CLEAN_EV, drop[f])
        raisers = [t for t in DISKS if d[t][0] > 1e-9 or d[t][1] > 1e-9]
        raise_set[f] = {"raises_on": raisers, "deltas": d}
        o = {m: {t: (round(drop[f][t][m]["at15"] - CLEAN_EV[t][m]["at15"], 3), round(drop[f][t][m]["at20"] - CLEAN_EV[t][m]["at20"], 3))
                 for t in DISKS} for m in (LOF_, SVM_)}
        drop_site[f] = {"IF_delta": d, "LOF_delta": o[LOF_], "OCSVM_delta": o[SVM_], "raises_on": raisers}
        rows.append([f] + [f"{d[t][0]:+.1f}/{d[t][1]:+.1f}" for t in DISKS] +
                    [f"{o[LOF_][t][0]:+.0f}/{o[LOF_][t][1]:+.0f}" for t in DISKS] +
                    [f"{o[SVM_][t][0]:+.0f}/{o[SVM_][t][1]:+.0f}" for t in DISKS] + [", ".join(raisers) or "-"])
    L += ["## (b) drop-one: clean minus a single feature", "",
          "Cells are the change in targets caught (removed minus full clean) at 15% / 20%. IF = seed mean over 5 seeds; LOF and OCSVM = seed 42. "
          "Last column lists disks where IF recall goes UP when the feature is removed (the protocol's drop criterion).", "",
          table(["feature removed"] + [f"IF {t}" for t in DISKS] + [f"LOF {t}" for t in DISKS] + [f"OCSVM {t}" for t in DISKS] + ["IF raises on"], rows), ""]
    site["b_drop_one"] = drop_site

    # (c) burst
    log("A3(c) burst")
    CB = CLEAN + BURST
    BURST_EV = ev_all(CB, "burst")
    L += ["## (c) clean vs clean + burst", "",
          f"Burst candidates {BURST} (counts of files sharing the same modified second / minute) added to the clean set; same models, same seeds.", ""]
    L += tbl_sets({"clean": CLEAN_EV, "clean+burst": BURST_EV})
    bd = deltas(CLEAN_EV, BURST_EV)
    b_raise = [t for t in DISKS if bd[t][0] > 1e-9 or bd[t][1] > 1e-9]
    b_lower = [t for t in DISKS if bd[t][0] < -1e-9 or bd[t][1] < -1e-9]
    burst_pass = bool(b_raise) and not b_lower
    L += ["IF change with burst (targets at 15% / 20%): " + "; ".join(f"{t} {bd[t][0]:+.1f}/{bd[t][1]:+.1f}" for t in DISKS) + ".",
          f"Raises on: {', '.join(b_raise) or 'none'}. Lowers on: {', '.join(b_lower) or 'none'}. "
          f"Protocol rule (raise on >=1 disk and lower on none; a disk that goes up at one budget and down at the other counts as lowering): **{verdict(burst_pass)}**.", ""]
    site["c_burst"] = {"clean": CLEAN_EV, "clean_plus_burst": BURST_EV, "delta": bd, "passes": burst_pass}
    site["curves"] = {t: dict(site["curves"][t], burst=curve_mean(DATA[t], IF_, CB, "burst")) for t in DISKS}

    # (d) Gemini's v1 vs v2 as defined
    log("A3(d)/(e) v1 vs v2 and Anonymizer check")
    V2COLS = ["delta_mc", "delta_mb", "delta_ab", "future_m", "zero_size_recent", "size"] + BURST
    V2COLS = ["delta_mc", "delta_mb", "delta_ab", "future_m", "zero_size_recent", "size", "log_burst_count", "log_burst_60s"]
    v1, v2 = {}, {}
    for t in DISKS:
        v1[t] = C.summary(LEG[t], S(LEG[t], IF_, leg_feats[t], 42, "legacy23"))
        v2[t] = C.summary(LEG[t], S(LEG[t], IF_, V2COLS, 42, "legacy23+burst"))
        for r, s in ((v1[t], S(LEG[t], IF_, leg_feats[t], 42, "legacy23")), (v2[t], S(LEG[t], IF_, V2COLS, 42, "legacy23+burst"))):
            r["at5"] = int((C.first_rank(LEG[t], s) <= int(round(0.05 * TG[t]))).sum())
    L += ["## (d) v1 vs v2 as originally defined (for the record)", "",
          "v1 = Isolation Forest, 200 trees, seed 42, on the legacy 23 features. v2 = Isolation Forest, 200 trees, seed 42, on exactly "
          f"{V2COLS} taken from the legacy table plus the burst columns. Single seed, one model.", "",
          "**This is not a fair comparison**: the two arms differ in feature count (23 vs 8), in the features' content and "
          "in the burst information, v2's feature list was chosen with knowledge of the outcome on these disks, only one seed was run, "
          "and no other model or disk-level repeat exists. The fair tests are (a), (b) and (c) above.", ""]
    rows = []
    for t in DISKS:
        for name, r in (("v1", v1[t]), ("v2", v2[t])):
            rows.append([DATA[t]["label"], name, r["targets"], r["at5"], r["at15"], r["at20"], r["knee_pct"], r["plateau_pct"]])
    L += [table(["disk", "arm", "targets", "at5", "at15", "at20", "knee %", "plateau %"], rows), ""]
    site["d_v1_v2"] = {"v1": v1, "v2": v2, "v2_features": V2COLS}

    # (e) Anonymizer fact check
    ARMS = {"v1 (legacy23 IF)": (LEG, leg_feats, "legacy23"), "v2 (8 feat + burst IF)": (LEG, {t: V2COLS for t in DISKS}, "legacy23+burst"),
            "clean IF": (DATA, {t: CLEAN for t in DISKS}, "clean"), "clean+burst IF": (DATA, {t: CB for t in DISKS}, "burst")}
    anon = {}
    for t in DISKS:
        N = TG[t]
        mask_a = DATA[t]["df"]["path"].str.contains("anonymizer", case=False, na=False).values
        anon[t] = {"n_files": int(mask_a.sum()), "arms": {}}
        for arm, (dm, fm, var) in ARMS.items():
            per = {}
            for b in (5.0, 15.0, 20.0):
                cnt = []
                for sd in SEEDS:
                    cnt.append(int((flagged_mask(S(dm[t], IF_, fm[t], sd, var), N, b) & mask_a).sum()))
                per[f"{int(b)}%"] = {"seed42": cnt[0], "mean5": round(float(np.mean(cnt)), 2)}
            anon[t]["arms"][arm] = per
        # v1-missed vs v2-caught at seed 42
        miss = {}
        for b in (5.0, 15.0, 20.0):
            f1 = flagged_mask(S(LEG[t], IF_, leg_feats[t], 42, "legacy23"), N, b)
            f2 = flagged_mask(S(LEG[t], IF_, V2COLS, 42, "legacy23+burst"), N, b)
            miss[f"{int(b)}%"] = {"v1_missed": int((mask_a & ~f1).sum()), "v2_caught_of_those": int((mask_a & ~f1 & f2).sum())}
        anon[t]["v1_missed_v2_caught_seed42"] = miss
    L += ["## (e) Fact-check: \"v2 caught 65 of 70 Anonymizer files that v1 missed\"", "",
          "Method: files whose path contains \"anonymizer\" (case-insensitive), counted on each disk; a file is flagged if it is in the top K "
          "files of the arm's ranking (K = budget % of the disk). Isolation Forest, seed 42 and mean over 5 seeds.", ""]
    for t in DISKS:
        L += [f"**{DATA[t]['label']}**: {anon[t]['n_files']} files with \"anonymizer\" in the path.", ""]
        if anon[t]["n_files"]:
            rows = []
            for arm in ARMS:
                p = anon[t]["arms"][arm]
                rows.append([arm] + [f"{p[b]['seed42']} ({p[b]['mean5']:.1f})" for b in ("5%", "15%", "20%")])
            L += [table(["arm", "flagged at 5% seed42 (5-seed mean)", "at 15%", "at 20%"], rows), "",
                  "v1-missed / v2-caught (seed 42): " + "; ".join(f"{b}: v1 missed {v['v1_missed']}, of which v2 caught {v['v2_caught_of_those']}"
                                                                for b, v in anon[t]["v1_missed_v2_caught_seed42"].items()) + ".", ""]
    site["e_anonymizer"] = anon

    # (f) apply protocol rules
    log("A3(f) protocol rules and FINAL set")
    failing = [f for f in CLEAN if raise_set[f]["raises_on"]]
    final_cols = [c for c in CLEAN if c not in failing] + (BURST if burst_pass else [])
    FINAL_EV = ev_all(final_cols, "final")
    L += ["## (f) Protocol rules and the final feature set", "",
          "Rule: a feature is kept only if removing it does not raise IF seed-mean recall at 15% or 20% on any disk. "
          "Burst enters only if it raises recall on at least one disk and lowers it on none.", ""]
    rows = [[f, "DROP" if f in failing else "keep", ", ".join(raise_set[f]["raises_on"]) or "-",
             "; ".join(f"{t} {raise_set[f]['deltas'][t][0]:+.1f}/{raise_set[f]['deltas'][t][1]:+.1f}" for t in DISKS)] for f in CLEAN]
    L += [table(["feature", "decision", "removal raises recall on", "change when removed (at15/at20)"], rows), "",
          f"Features failing the rule (candidates to drop): {failing or 'none'}. Burst: {'included' if burst_pass else 'not included'}.", "",
          f"**FINAL set ({len(final_cols)} features)**: {', '.join(final_cols)}.", "",
          "Note: each feature was tested by removing it alone from the full clean set; all failing features are dropped together, "
          "so the combined effect is checked directly by scoring the FINAL set below rather than assumed.", ""]
    L += tbl_sets({"clean": CLEAN_EV, "FINAL": FINAL_EV})
    fd = deltas(CLEAN_EV, FINAL_EV)
    L += ["FINAL minus clean, IF targets at 15%/20%: " + "; ".join(f"{t} {fd[t][0]:+.1f}/{fd[t][1]:+.1f}" for t in DISKS) + ".", ""]
    L += ["Caveat, reported as found: the rule counts any increase of the seed mean (even +0.2 of a target) on any disk as a raise, and on img3 "
          "removing almost any single feature raises recall (the 17-feature model is diluted there). Applied mechanically, the rule therefore keeps only "
          f"{len(final_cols) - (len(BURST) if burst_pass else 0)} of {len(CLEAN)} clean features. The FINAL set is not uniformly better: see the img1 and the LOF/OCSVM columns above. "
          "Nothing was re-tuned after seeing this.", ""]
    site["f_final"] = {"features": final_cols, "dropped": failing, "burst_included": burst_pass, "results": FINAL_EV, "delta_vs_clean": fd}
    site["curves"] = {t: dict(site["curves"][t], final=curve_mean(DATA[t], IF_, final_cols, "final")) for t in DISKS}
    reasons = {f: {"decision": "dropped" if f in failing else "kept",
                   "if_mean_change_when_removed_at15_at20": {t: list(raise_set[f]["deltas"][t]) for t in DISKS}} for f in CLEAN}
    reasons["burst"] = {"decision": "included" if burst_pass else "not included",
                        "if_mean_change_when_added_at15_at20": {t: list(bd[t]) for t in DISKS}, "raises_on": b_raise, "lowers_on": b_lower}
    with open(os.path.join(OUT, "A3", "final_features.json"), "w") as f:
        json.dump({"final": final_cols, "dropped": failing, "burst_included": burst_pass, "reason": reasons}, f, indent=1)
    write("A3", "summary.md", "\n".join(L))
    write_site("A3", site)
    return failing, final_cols, burst_pass, anon, (v1, v2)


# ============================================================================= A5
def sk_scores(D, model, X, seed, **kw):
    N = len(X)
    if model == IF_:
        m = IsolationForest(n_estimators=kw["n_estimators"], max_samples=kw["max_samples"], contamination=M.BUDGET_PCT,
                            random_state=seed, n_jobs=-1).fit(X)
        return -m.score_samples(X)
    if model == LOF_:
        m = LocalOutlierFactor(n_neighbors=kw["k"], contamination=M.BUDGET_PCT, n_jobs=-1).fit(X)
        return -m.negative_outlier_factor_
    rng = np.random.RandomState(seed)
    idx = rng.choice(N, size=min(N, 10000), replace=False)
    m = OneClassSVM(kernel="rbf", nu=kw["nu"], gamma="scale").fit(X[idx])
    return -m.decision_function(X)


def run_A5():
    log("A5 hyperparameters")
    Xs = {t: C.matrix(DATA[t], CLEAN) for t in DISKS}

    def go(model, params, seeds):
        out = {}
        for t in DISKS:
            summs = []
            for sd in seeds:
                s = cached(["A5", t, model, params, sd], lambda: sk_scores(DATA[t], model, Xs[t], sd, **params))
                summs.append(C.summary(DATA[t], s))
            out[t] = agg(summs)
        return out

    ifres = {}
    for ne in (50, 100, 200, 500):
        for ms in (256, 512, 1024, "auto"):
            ifres[(ne, ms)] = go(IF_, {"n_estimators": ne, "max_samples": ms}, SEEDS)
            log(f"  IF n={ne} ms={ms}")
    lofres = {k: go(LOF_, {"k": k}, [42]) for k in (10, 20, 35, 50)}
    svmres = {nu: go(SVM_, {"nu": nu}, [42]) for nu in (0.01, 0.05, 0.1)}

    # sanity: our default equals the pipeline's clean result
    for t in DISKS:
        assert abs(ifres[(200, 256)][t]["at15"] - CLEAN_EV[t][IF_]["at15"]) < 1e-9, "IF default differs from pipeline"
        assert abs(ifres[(200, 256)][t]["at20"] - CLEAN_EV[t][IF_]["at20"]) < 1e-9
        assert lofres[20][t]["at15"] == CLEAN_EV[t][LOF_]["at15"] and svmres[0.05][t]["at20"] == CLEAN_EV[t][SVM_]["at20"]

    def maxchg(res, default):
        o = {}
        for t in DISKS:
            o[t] = {b: round(max(abs(r[t][b] - res[default][t][b]) for r in res.values()), 3) for b in ("at15", "at20")}
            o[t]["range15"] = round(max(r[t]["at15"] for r in res.values()) - min(r[t]["at15"] for r in res.values()), 3)
            o[t]["range20"] = round(max(r[t]["at20"] for r in res.values()) - min(r[t]["at20"] for r in res.values()), 3)
        return o

    mc = {"IF": maxchg(ifres, (200, 256)), "LOF": maxchg(lofres, 20), "OCSVM": maxchg(svmres, 0.05)}
    fam_ok = {f: all(mc[f][t][b] <= 1.0 + 1e-9 for t in DISKS for b in ("at15", "at20")) for f in mc}
    ok = all(fam_ok.values())

    L = ["# A5: hyperparameter sensitivity", "",
         "Clean features. Isolation Forest (sklearn IsolationForest called directly; 5 seeds, mean±sd) over n_estimators x max_samples; "
         "LOF over k; One-Class SVM over nu with gamma=\"scale\" (10,000-row fit sample). **LOF and One-Class SVM: seed 42 only.** "
         "Default = IF (200 trees, sample 256), LOF k=20, OCSVM nu=0.05; the defaults were checked to reproduce the pipeline's clean results exactly. "
         "max_samples \"auto\" equals min(256, n) = 256 in sklearn, so it is expected to match the 256 column.", "",
         "Cells are targets caught at 15% / 20% of the disk. Targets: " + ", ".join(f"{t} = {NT[t]}" for t in DISKS) + ".", ""]
    for t in DISKS:
        L += [f"## {DATA[t]['label']}", ""]
        rows = [[f"IF n={ne}, max_samples={ms}", pm(r[t], "at15"), pm(r[t], "at20"), pm(r[t], "knee_pct"), pm(r[t], "plateau_pct")]
                for (ne, ms), r in ifres.items()]
        rows += [[f"LOF k={k}", r[t]["at15"], r[t]["at20"], r[t]["knee_pct"], r[t]["plateau_pct"]] for k, r in lofres.items()]
        rows += [[f"OCSVM nu={nu}", r[t]["at15"], r[t]["at20"], r[t]["knee_pct"], r[t]["plateau_pct"]] for nu, r in svmres.items()]
        L += [table(["setting", "at15", "at20", "knee %", "plateau %"], rows), ""]
    L += ["## Pass rule (PROTOCOL A5): headline recall changes by <= 1 target across the tested settings", "",
          "Measured as the largest absolute difference of targets caught (IF: seed mean) between any tested setting and the default, "
          "at 15% and at 20%, per disk. The spread (max minus min over settings) is also given.", ""]
    rows = []
    for f in mc:
        for t in DISKS:
            v = mc[f][t]
            rows.append([f, t, v["at15"], v["at20"], v["range15"], v["range20"]])
    L += [table(["model", "disk", "max change at15", "max change at20", "spread at15", "spread at20"], rows), ""]
    L += [f"- {f}: **{verdict(fam_ok[f])}**" for f in fam_ok]
    L += [f"- A5 overall (all three families within 1 target on every disk): **{verdict(ok)}**", ""]
    write("A5", "summary.md", "\n".join(L))
    ser = lambda res: {str(k): {t: v[t] for t in DISKS} for k, v in res.items()}
    write_site("A5", {"targets": NT, "n": TG, "budgets": HEADLINE, "IF": {f"{k[0]}|{k[1]}": {t: v[t] for t in DISKS} for k, v in ifres.items()},
                      "LOF": ser(lofres), "OCSVM": ser(svmres), "max_change": mc, "family_pass": fam_ok, "pass": ok,
                      "if_seeds": SEEDS, "other_models_seed": 42})
    return ok, fam_ok, mc


# ============================================================================= A7
TIME_COLS = ["delta_mc", "delta_mb", "delta_ab", "zero_size_recent", "delta_si_fn", "m_before_cr", "after_hours_touch"]


def time_features(D, sd_noise, seed):
    """Recompute every clean time feature from raw timestamps after adding Gaussian noise (sd seconds) independently to each
    positive timestamp of m, a, c, cr and the $FILE_NAME modified time. Same formulas as feature_engineering / multimodel_eval."""
    raw, df = D["raw"], D["df"]
    rng = np.random.RandomState(seed)

    def get(col):
        t = pd.to_numeric(raw[col], errors="coerce").fillna(0).values.astype(float)
        if sd_noise > 0:
            t = np.where(t > 0, np.round(t + rng.normal(0, sd_noise, len(t))), t)
        return t
    m, a, c, cr = get("m_time"), get("a_time"), get("c_time"), get("cr_time")
    fn = get("fn_m_time") if "fn_m_time" in raw.columns else None
    out = {}
    out["delta_mc"] = np.where((m > 0) & (c > 0), np.abs(m - c), 0.0)
    out["delta_mb"] = np.where((m > 0) & (cr > 0), np.abs(m - cr), 0.0)
    out["delta_ab"] = np.where((a > 0) & (cr > 0), np.abs(a - cr), 0.0)
    now_ts = int(m.max()) if m.max() > 0 else 0
    size = df["size"].values
    out["zero_size_recent"] = ((size == 0) & ((now_ts - m) < 86400) & (m > 0)).astype(int)
    if fn is not None:
        out["delta_si_fn"] = np.where((fn > 0) & (m > 0), np.abs(m - fn), 0.0)
    out["m_before_cr"] = ((m > 0) & (m < cr)).astype(int)
    bias = df.attrs["tz_bias_minutes"]

    def off(t):
        h = pd.to_datetime(t - bias * 60, unit="s", utc=True, errors="coerce").hour
        return (t > 0) & ((h < M.WORK_HOURS_START) | (h >= M.WORK_HOURS_END))
    out["after_hours_touch"] = (off(m) | off(a)).astype(int)
    return out


def recall_after(D, keep, s_sub, pos):
    """targets caught at each headline budget when only rows `keep` (bool) were scored; budgets as % of the reduced disk."""
    Nn = int(keep.sum())
    order = np.argsort(-s_sub, kind="stable")
    rank = np.empty(Nn, dtype=np.int64)
    rank[order] = np.arange(1, Nn + 1)
    fr = []
    for t in D["active"]:
        ii = pos[np.asarray(t["idx"])]
        ii = ii[ii >= 0]
        fr.append(rank[ii].min() if len(ii) else 10 ** 12)
    fr = np.array(fr)
    return {f"at{int(b)}": int((fr <= int(round(b / 100 * Nn))).sum()) for b in HEADLINE}, Nn


def run_A7():
    log("A7 robustness")
    base = {t: [C.summary(DATA[t], S(DATA[t], IF_, CLEAN, sd)) for sd in SEEDS] for t in DISKS}
    runs = {"baseline": {t: [{k: s[k] for k in ("at15", "at20")} for s in base[t]] for t in DISKS}}

    # verify the time-feature rebuild at zero noise reproduces the stored columns
    for t in DISKS:
        z = time_features(DATA[t], 0, 0)
        for c in z:
            assert np.allclose(z[c], DATA[t]["df"][c].values.astype(float)), (t, c, "zero-noise rebuild differs")
    log("  zero-noise time-feature rebuild matches the stored columns on all disks")

    for variant in ("drop10_nontarget", "drop10_all", "noise3600"):
        runs[variant] = {}
        for t in DISKS:
            D = DATA[t]
            N = D["N"]
            tgt = np.zeros(N, bool)
            tgt[list(D["all_idx"])] = True
            res = []
            for sd in SEEDS:
                if variant.startswith("drop10"):
                    rng = np.random.RandomState(sd)
                    cand = np.where(~tgt)[0] if variant == "drop10_nontarget" else np.arange(N)
                    drop = rng.choice(cand, size=int(round(0.1 * len(cand))) if variant == "drop10_nontarget" else int(round(0.1 * N)), replace=False)
                    keep = np.ones(N, bool)
                    keep[drop] = False
                    pos = np.full(N, -1, dtype=np.int64)
                    pos[keep] = np.arange(int(keep.sum()))
                    X = M.standardize(D["df"][CLEAN].values.astype(float)[keep])
                    s = cached(["A7", variant, t, sd], lambda: M.fit_score(IF_, X, sd)[0])
                    r, Nn = recall_after(D, keep, s, pos)
                else:
                    tf = time_features(D, 3600, sd)
                    dfn = D["df"][CLEAN].copy()
                    for c, v in tf.items():
                        dfn[c] = v
                    X = M.standardize(dfn.values.astype(float))
                    s = cached(["A7", variant, t, sd], lambda: M.fit_score(IF_, X, sd)[0])
                    r = {k: v for k, v in C.summary(D, s).items() if k in ("at15", "at20")}
                res.append(r)
            runs[variant][t] = res
            log(f"  {variant} {t}: " + str([(r['at15'], r['at20']) for r in res]))

    # verdicts: relative drop of seed-mean recall (targets caught / targets)
    out, verd = {}, {}
    for v in ("drop10_nontarget", "drop10_all", "noise3600"):
        ok_v = True
        out[v] = {}
        for t in DISKS:
            row = {}
            for b in ("at15", "at20"):
                b0 = np.mean([r[b] for r in runs["baseline"][t]])
                b1 = np.mean([r[b] for r in runs[v][t]])
                rel = (b0 - b1) / b0 if b0 > 0 else 0.0
                pp = 100 * (b0 - b1) / NT[t]
                row[b] = {"base_mean": round(float(b0), 3), "pert_mean": round(float(b1), 3), "rel_drop_pct": round(100 * float(rel), 2),
                          "abs_drop_pp": round(float(pp), 2), "pert_per_seed": [r[b] for r in runs[v][t]]}
                if rel > 0.10 + 1e-12:
                    ok_v = False
            out[v][t] = row
        verd[v] = ok_v
    overall = verd["drop10_nontarget"] and verd["noise3600"]

    names = {"drop10_nontarget": "(i) drop a random 10% of non-target files (all target files kept)",
             "drop10_all": "(i-b) drop a random 10% of ALL files, including target files (reported separately)",
             "noise3600": "(ii) Gaussian noise, sd 3600 s, on timestamps"}
    L = ["# A7: robustness", "",
         "Isolation Forest, clean features, 200 trees, all five seeds (mean over seeds). Baseline = the unperturbed clean run with the same seeds. "
         "Budgets 15% and 20% of the (possibly reduced) disk. Targets: " + ", ".join(f"{t} = {NT[t]}" for t in DISKS) + ".", "",
         "What was done exactly:", "",
         "- Drop variants: for each seed, a random 10% of the non-target files (variant i) or of all files (variant i-b) is removed before the model "
         "is fitted; features are recomputed over the remaining rows (standardisation on the remaining rows); the budget is a percentage of the remaining file count. "
         "\"Target files\" are all files matching any target pattern. In variant i-b a target whose files are all removed counts as missed.",
         "- Noise variant: no deltas were patched. Instead every clean time feature (delta_mc, delta_mb, delta_ab, zero_size_recent, delta_si_fn, m_before_cr, after_hours_touch) "
         "was recomputed from the raw timestamps after adding independent Gaussian noise (sd 3600 s, rounded to whole seconds) to each positive m, a, c and cr time and the $FILE_NAME modified time "
         "(zero = missing timestamps stay zero). Noise seed = model seed. The rebuild was verified to reproduce the stored columns exactly at zero noise on all three disks.",
         "- Pass rule: headline recall (targets caught / targets) falls by <= 10% relative to the baseline seed mean, at both 15% and 20%, on every disk. "
         "Absolute drop in percentage points is shown too. Verdict (overall) uses variants (i) and (ii); (i-b) is judged separately.", ""]
    for v in ("drop10_nontarget", "drop10_all", "noise3600"):
        L += [f"## {names[v]}", ""]
        rows = []
        for t in DISKS:
            for b in ("at15", "at20"):
                r = out[v][t][b]
                rows.append([DATA[t]["label"], b, NT[t], r["base_mean"], r["pert_mean"], r["rel_drop_pct"], r["abs_drop_pp"], r["pert_per_seed"]])
        L += [table(["disk", "budget", "targets", "baseline mean caught", "perturbed mean caught", "relative drop %", "drop (pp)", "perturbed per seed"], rows), "",
              f"Verdict: **{verdict(verd[v])}**", ""]
    L += ["## Overall (PROTOCOL A7)", "", f"- Drop 10% of non-target files: **{verdict(verd['drop10_nontarget'])}**",
          f"- Timestamp noise 1 h: **{verdict(verd['noise3600'])}**",
          f"- Drop 10% of all files (separate): **{verdict(verd['drop10_all'])}**",
          f"- A7 overall (variants i and ii): **{verdict(overall)}**", ""]
    write("A7", "summary.md", "\n".join(L))
    write_site("A7", {"targets": NT, "n": TG, "seeds": SEEDS, "results": out, "verdict": verd, "pass": overall})
    return verd, overall, out


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "A3"), exist_ok=True)
    a1 = run_A1()
    a3 = run_A3()
    a5 = run_A5()
    a7 = run_A7()
    log(f"DONE  A1={a1} A5={a5[0]} A7={a7[1]}  A3 dropped={a3[0]} burst={a3[2]}")
    print("FINAL", a3[1])
    print("ANON", json.dumps({t: {"n": v["n_files"], "miss": v["v1_missed_v2_caught_seed42"]} for t, v in a3[3].items()}))
    print("V1V2", a3[4])
    print("A5 maxchg", json.dumps(a5[2]))
    print("A7", a7[0], json.dumps({v: {t: {b: o[t][b]["rel_drop_pct"] for b in o[t]} for t in o} for v, o in a7[2].items()}))
