"""study_v3_reliability_a.py: ablations A2 (threshold + seeds), A4 (models vs plain rules), A6 (cross-disk transfer).
Protocol: reports/study_v3/PROTOCOL.md. Ground truth is used only to score rankings."""
import os, json, time, csv
import numpy as np
import study_v3_common as C
import multimodel_eval as M

T0 = time.time()
CACHE = os.path.join(M.BASE_DIR, ".cache", "study_v3")
os.makedirs(CACHE, exist_ok=True)
DIRS = {k: os.path.join(C.OUT, k) for k in ("A2", "A4", "A6")}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)
SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OC-SVM"}
MODELS = M.MODELS
STEP2 = list(range(0, 201, 2))          # 1 % steps for json
BUD1 = [C.BUDGETS[i] for i in STEP2]


def get_score(D, model, seed):
    sd = 0 if model == "Local Outlier Factor" else seed     # LOF deterministic: one run
    f = os.path.join(CACHE, f"{D['tag']}_{SHORT[model]}_{sd}.npy")
    if os.path.exists(f):
        return np.load(f)
    s = C.score(D, model, D["feats"], seed)
    np.save(f, s)
    return s


def stable_rank_score(D, keys):
    """Rank by keys (list, primary first, bigger = earlier); ties by path order. Returns score for C helpers."""
    n = D["N"]
    pr = np.argsort(np.argsort(D["df"]["path"].astype(str).values, kind="stable"), kind="stable")
    order = np.lexsort(tuple([pr] + [-np.nan_to_num(np.asarray(k, float)) for k in keys[::-1]]))
    s = np.empty(n); s[order] = np.arange(n, 0, -1)
    return s


def fp_at(D, s, b):
    K = int(round(b / 100 * D["N"]))
    top = np.argsort(-s, kind="stable")[:K]
    hit = len(set(top.tolist()) & set(D["all_idx"]))
    return K - hit, K


def f2(x): return round(float(x), 2)


# ---------------- scores + curves ----------------
disks = {t: C.load(t) for t in C.DISKS}
S, CUR, SUM = {}, {}, {}
for t, D in disks.items():
    for m in MODELS:
        for sd in C.SEEDS:
            s = get_score(D, m, sd)
            S[t, m, sd] = s
            CUR[t, m, sd] = C.curve(D, s)
            SUM[t, m, sd] = C.summary(D, s)
            SUM[t, m, sd]["fa15"] = fp_at(D, s, 15)[0]
            SUM[t, m, sd]["fa20"] = fp_at(D, s, 20)[0]
    print(t, "scored", round(time.time() - T0), "s", flush=True)
TG = {t: len(disks[t]["active"]) for t in disks}
need = {t: int(np.ceil(0.9 * TG[t])) for t in disks}

# ---------------- A2 ----------------
with open(os.path.join(DIRS["A2"], "curves.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["disk", "model", "seed", "budget_pct", "caught", "targets"])
    for (t, m, sd), c in CUR.items():
        for b, v in zip(C.BUDGETS, c):
            w.writerow([t, SHORT[m], sd, b, v, TG[t]])

def agg(vals):
    v = np.array(vals, float); return dict(mean=f2(v.mean()), std=f2(v.std()), min=f2(v.min()), max=f2(v.max()))

A2 = {}
rows = []
for t in disks:
    for m in MODELS:
        ss = [SUM[t, m, sd] for sd in C.SEEDS]
        r = {"disk": t, "model": SHORT[m], "targets": TG[t], "need90": need[t]}
        for k in ("at15", "at20", "knee_pct", "plateau_pct", "fa15", "fa20"):
            a = agg([x[k] for x in ss])
            for kk, v in a.items(): r[f"{k}_{kk}"] = v
        kn = np.array([x["knee_pct"] for x in ss])
        r["knee_seeds_within_0.5pp_of_median"] = int((np.abs(kn - np.median(kn)) <= 0.5).sum())
        r["knee_spread_pp"] = f2(kn.max() - kn.min())
        r["dead_zone_pct"] = f2(100 - r["plateau_pct_mean"])
        r["min_at15_all_seeds"] = int(min(x["at15"] for x in ss)); r["min_at20_all_seeds"] = int(min(x["at20"] for x in ss))
        rows.append(r)
        A2[t, m] = r
with open(os.path.join(DIRS["A2"], "summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

a2_pass = {}
for m in MODELS:
    for h in (15, 20):
        spread_ok = all(A2[t, m]["knee_spread_pp"] <= 2 for t in disks)
        hit_ok = all(A2[t, m][f"min_at{h}_all_seeds"] >= need[t] for t in disks)
        a2_pass[m, h] = (spread_ok, hit_ok, spread_ok and hit_ok)

# ---------------- A4 rules ----------------
RULES = {"R1 timestamp mismatch (delta_si_fn)": lambda D: stable_rank_score(D, [D["df"]["delta_si_fn"]]),
         "R2 modified before created": lambda D: stable_rank_score(D, [D["df"]["m_before_cr"], D["df"]["delta_mb"]]),
         "R3 location (temp+user+exe+script+archive)": lambda D: stable_rank_score(D, [sum(D["df"][c].astype(float) for c in ["temp_path", "user_path", "is_exe", "is_script", "is_archive"])]),
         "R4 recency (latest m_time first)": lambda D: stable_rank_score(D, [D["raw"]["m_time"].astype(float)])}
A4 = {}   # (disk, name) -> dict
A4cur = {}
for t, D in disks.items():
    for name, fn in RULES.items():
        s = fn(D); sm = C.summary(D, s); A4cur[t, name] = C.curve(D, s)
        A4[t, name] = {"at15": sm["at15"], "at20": sm["at20"], "knee_pct": sm["knee_pct"], "plateau_pct": sm["plateau_pct"]}
    sums, curs = [], []
    for sd in C.SEEDS:
        rng = np.random.RandomState(sd); s = rng.permutation(D["N"]).astype(float)
        sums.append(C.summary(D, s)); curs.append(C.curve(D, s))
    name = "R5 random order (mean of 5 seeds)"
    A4cur[t, name] = list(np.mean(curs, 0))
    A4[t, name] = {k: f2(np.mean([x[k] for x in sums])) for k in ("at15", "at20", "knee_pct", "plateau_pct")}
    for m in MODELS:
        A4[t, SHORT[m]] = {k: A2[t, m][f"{k}_mean"] for k in ("at15", "at20", "knee_pct", "plateau_pct")}
        A4cur[t, SHORT[m]] = list(np.mean([CUR[t, m, sd] for sd in C.SEEDS], 0))
names = list(RULES) + ["R5 random order (mean of 5 seeds)"]
with open(os.path.join(DIRS["A4"], "comparison.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["disk", "method", "kind", "targets", "at15", "at20", "knee_pct", "plateau_pct"])
    for t in disks:
        for n in [SHORT[m] for m in MODELS] + names:
            a = A4[t, n]; w.writerow([t, n, "model" if n in SHORT.values() else "rule", TG[t], a["at15"], a["at20"], a["knee_pct"], a["plateau_pct"]])
a4_pass = {}
for m in MODELS:
    for h in (15, 20):
        wins = {}
        for t in disks:
            best = max(names, key=lambda n: A4[t, n][f"at{h}"])
            wins[t] = (A4[t, SHORT[m]][f"at{h}"] > A4[t, best][f"at{h}"], best, A4[t, best][f"at{h}"])
        a4_pass[m, h] = (sum(v[0] for v in wins.values()) >= 2, wins)

# ---------------- A6 ----------------
A6 = {}
for m in MODELS:
    for X in disks:
        kn = A2[X, m]["knee_pct_mean"]
        for Y in disks:
            if X == Y: continue
            K = int(round(kn / 100 * disks[Y]["N"]))
            fr = [(np.array(CUR[Y, m, sd]) if False else None) for sd in C.SEEDS]
            ca = []
            for sd in C.SEEDS:
                ca.append(int((C.first_rank(disks[Y], S[Y, m, sd]) <= K).sum()))
            A6[m, X, Y] = {"knee_from": kn, "K": K, "caught_mean": f2(np.mean(ca)), "pct": f2(100 * np.mean(ca) / TG[Y]),
                           "pct_min_seed": f2(100 * min(ca) / TG[Y])}
a6_pass = {m: all(v["pct"] >= 90 for (mm, X, Y), v in A6.items() if mm == m) for m in MODELS}
fixed = {}
for m in MODELS:
    for h in (15, 20):
        fixed[m, h] = {t: f2(100 * A2[t, m][f"at{h}_mean"] / TG[t]) for t in disks}
with open(os.path.join(DIRS["A6"], "transfer.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "knee_learned_on", "applied_to", "knee_pct", "budget_files", "targets_caught_mean", "pct_targets_caught", "pct_worst_seed"])
    for (m, X, Y), v in A6.items():
        w.writerow([SHORT[m], X, Y, v["knee_from"], v["K"], v["caught_mean"], v["pct"], v["pct_min_seed"]])

# ---------------- site.json ----------------
def dump(name, obj):
    p = os.path.join(DIRS[name], "site.json")
    json.dump(obj, open(p, "w"), separators=(",", ":"))
    print(name, "site.json", os.path.getsize(p) // 1024, "KB")

dump("A2", {"budgets": BUD1, "disks": {t: {"targets": TG[t], "N": disks[t]["N"], "models": {SHORT[m]: {
    "seeds": {str(sd): [CUR[t, m, sd][i] for i in STEP2] for sd in C.SEEDS},
    "summary": A2[t, m]} for m in MODELS}} for t in disks},
    "pass": {f"{SHORT[m]}@{h}": {"knee_spread_ok": a2_pass[m, h][0], "recall_ok": a2_pass[m, h][1], "pass": a2_pass[m, h][2]} for m in MODELS for h in (15, 20)}})
dump("A4", {"budgets": BUD1, "disks": {t: {"targets": TG[t], "rows": [{"method": n, **A4[t, n]} for n in [SHORT[m] for m in MODELS] + names],
    "curves": {n: [round(float(A4cur[t, n][i]), 2) for i in STEP2] for n in [SHORT[m] for m in MODELS] + names}} for t in disks},
    "pass": {f"{SHORT[m]}@{h}": a4_pass[m, h][0] for m in MODELS for h in (15, 20)}})
dump("A6", {"disks": list(disks), "targets": TG, "matrix": [{"model": SHORT[m], "learned_on": X, "applied_to": Y, **v} for (m, X, Y), v in A6.items()],
    "fixed_budget_pct": {f"{SHORT[m]}@{h}": fixed[m, h] for m in MODELS for h in (15, 20)}, "pass": {SHORT[m]: a6_pass[m] for m in MODELS}})

# ---------------- summaries ----------------
PF = lambda b: "PASS" if b else "FAIL"
def table(hdr, rws):
    return "\n".join(["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rws]) + "\n"

L = ["# A2: threshold and seed stability", "",
     "Clean feature set. 5 seeds (42, 1337, 9999, 7, 2024). LOF is deterministic, so its 5 seeds are identical by construction.",
     "Full per-seed curves: `curves.csv`; per disk and model statistics: `summary.csv`. Targets are counted as in the protocol (a target is caught if any of its files is in the top K).", ""]
for t in disks:
    L += [f"## {t} ({disks[t]['label']}): {TG[t]} targets, {disks[t]['N']:,} files, 90% = {need[t]} targets", ""]
    L.append(table(["model", "at15 mean (sd, min-max)", "at20 mean (sd, min-max)", "knee % mean (sd, min-max)", "plateau % mean", "seeds within 0.5pp of median knee", "dead zone % (100-plateau)", "false alarms@15 / @20 (mean)"],
        [[SHORT[m], *[f"{A2[t,m][k+'_mean']} ({A2[t,m][k+'_std']}, {A2[t,m][k+'_min']}-{A2[t,m][k+'_max']})" for k in ("at15", "at20", "knee_pct")],
          A2[t, m]["plateau_pct_mean"], f"{A2[t,m]['knee_seeds_within_0.5pp_of_median']}/5", A2[t, m]["dead_zone_pct"],
          f"{A2[t,m]['fa15_mean']} / {A2[t,m]['fa20_mean']}"] for m in MODELS]))
L += ["## Pass rule (knee spread <= 2pp on every disk, and headline budget catches >= 90% of targets in every seed on every disk)", ""]
L.append(table(["model", "headline", "knee spread ok", "min catch >= 90% every seed/disk", "result"],
               [[SHORT[m], f"{h}%", PF(a2_pass[m, h][0]), PF(a2_pass[m, h][1]), PF(a2_pass[m, h][2])] for m in MODELS for h in (15, 20)]))
L += ["False alarms at the headline budget = files reviewed (K) minus ground-truth files among them (all target files, not just first hits).", ""]
open(os.path.join(DIRS["A2"], "summary.md"), "w").write("\n".join(L))

L = ["# A4: models versus plain rules", "",
     "Rules use no ground truth and no learning; each gives a score per file, ranked the same way as the models (ties by path order). Models are seed means.",
     "R1 delta_si_fn; R2 m_before_cr then delta_mb; R3 temp_path+user_path+is_exe+is_script+is_archive; R4 most recent m_time first; R5 random order (mean of 5 seeds).", ""]
for t in disks:
    L += [f"## {t}: {TG[t]} targets", ""]
    L.append(table(["method", "at15", "at20", "knee %", "plateau %"], [[n, *[A4[t, n][k] for k in ("at15", "at20", "knee_pct", "plateau_pct")]] for n in [SHORT[m] for m in MODELS] + names]))
L += ["## Pass rule (model beats the best rule, strictly, at the headline budget on >= 2 of 3 disks)", ""]
rws = []
for m in MODELS:
    for h in (15, 20):
        p, wins = a4_pass[m, h]
        rws.append([SHORT[m], f"{h}%", "; ".join(f"{t}: {'win' if v[0] else 'no'} (best rule {v[1].split()[0]} = {v[2]})" for t, v in wins.items()), PF(p)])
L.append(table(["model", "headline", "per disk", "result"], rws))
open(os.path.join(DIRS["A4"], "summary.md"), "w").write("\n".join(L))

L = ["# A6: cross-disk transfer", "",
     "For each model, the knee budget (seed-mean % of disk needed for 90% of targets) is learned on one disk and applied to each other disk. Reported: % of targets caught there (mean over seeds).", ""]
L.append(table(["model", "learned on", "applied to", "knee %", "files reviewed", "targets caught (mean)", "% caught", "% caught, worst seed"],
               [[SHORT[m], X, Y, v["knee_from"], v["K"], v["caught_mean"], v["pct"], v["pct_min_seed"]] for (m, X, Y), v in A6.items()]))
L += ["## Pass rule (a budget tuned on any one disk catches >= 90% on the other two)", ""]
L.append(table(["model", "result"], [[SHORT[m], PF(a6_pass[m])] for m in MODELS]))
L += ["## Fixed budget view: % of targets caught (seed mean)", ""]
L.append(table(["model", "budget", *disks, ">= 90% on all 3"], [[SHORT[m], f"{h}%", *[fixed[m, h][t] for t in disks], PF(all(fixed[m, h][t] >= 90 for t in disks))] for m in MODELS for h in (15, 20)]))
open(os.path.join(DIRS["A6"], "summary.md"), "w").write("\n".join(L))
print("done", round(time.time() - T0), "s")
