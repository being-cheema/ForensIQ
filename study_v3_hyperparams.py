"""study_v3_hyperparams.py: hyperparameter sensitivity on the final 19 features (protocol rule A5).
IF: n_estimators x max_samples, 5 seeds. LOF: k. OC-SVM: nu (gamma=scale, 10,000-row fit sample), 5 seeds.
Rule: headline recall (targets caught at 15% and 20%, seed mean) changes by <= 1 target across the tested IF settings.
Ground truth is used only to score rankings. Usage: FORENSIQ_FEATURE_SET=final python study_v3_hyperparams.py"""
import os, json, time
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
import study_v3_common as C
import multimodel_eval as M

assert M.FEATURE_SET == "final", "run with FORENSIQ_FEATURE_SET=final"
OUT = os.path.join(C.OUT, "A5_hyper"); os.makedirs(OUT, exist_ok=True)
NS, MS = [50, 100, 200, 500], [256, 512, 1024]
KS, NUS = [10, 20, 35, 50], [0.01, 0.05, 0.1]
t0 = time.time(); res = {}
for tag in C.DISKS:
    D = C.load(tag); X = C.matrix(D, D["feats"]); r = {"targets": len(D["active"]), "N": D["N"], "rows": []}
    def run(name, fn, seeds):
        runs = [C.summary(D, fn(sd)) for sd in seeds]
        r["rows"].append({"setting": name, "seeds": len(seeds),
            "at15": float(np.mean([x["at15"] for x in runs])), "at20": float(np.mean([x["at20"] for x in runs])),
            "min15": min(x["at15"] for x in runs), "min20": min(x["at20"] for x in runs),
            "knee": float(np.mean([x["knee_pct"] for x in runs]))})
    for n in NS:
        for m in MS:
            run(f"IF n={n}, max_samples={m}", lambda sd: -IsolationForest(n_estimators=n, max_samples=m, random_state=sd, n_jobs=-1).fit(X).score_samples(X), C.SEEDS)
    for k in KS:
        run(f"LOF k={k}", lambda sd: -LocalOutlierFactor(n_neighbors=k, n_jobs=-1).fit(X).negative_outlier_factor_, [0])
    for nu in NUS:
        def f(sd):
            idx = np.random.RandomState(sd).choice(len(X), size=min(len(X), 10000), replace=False)
            return -OneClassSVM(kernel="rbf", nu=nu, gamma="scale").fit(X[idx]).decision_function(X)
        run(f"OC-SVM nu={nu}", f, C.SEEDS)
    res[tag] = r; print(tag, "done", round(time.time() - t0), "s", flush=True)
rule = {}
for tag, r in res.items():
    IF = [x for x in r["rows"] if x["setting"].startswith("IF")]
    d = next(x for x in IF if x["setting"] == "IF n=200, max_samples=256")
    rule[tag] = {"default_at15": d["at15"], "default_at20": d["at20"],
        "range15": [min(x["at15"] for x in IF), max(x["at15"] for x in IF)],
        "range20": [min(x["at20"] for x in IF), max(x["at20"] for x in IF)],
        "max_change15": max(abs(x["at15"] - d["at15"]) for x in IF), "max_change20": max(abs(x["at20"] - d["at20"]) for x in IF)}
rule["pass_20"] = all(v["max_change20"] <= 1 for k, v in rule.items() if k in C.DISKS)
rule["pass_15"] = all(v["max_change15"] <= 1 for k, v in rule.items() if k in C.DISKS)
json.dump({"results": res, "rule": rule}, open(os.path.join(OUT, "results.json"), "w"), indent=1)
L = ["# Hyperparameter sensitivity (final 19 features)", "", "Cells: targets caught at 15% / 20% (seed mean). Default IF n=200, max_samples=256.", ""]
for tag, r in res.items():
    L += [f"## {tag} ({r['targets']} targets)", "", "| setting | at15 | at20 | knee % |", "|---|---|---|---|"]
    L += [f"| {x['setting']} | {x['at15']:.1f} | {x['at20']:.1f} | {x['knee']:.1f} |" for x in r["rows"]] + [""]
L += ["## Rule", "```", json.dumps(rule, indent=1), "```"]
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L))
print(json.dumps(rule, indent=1))
