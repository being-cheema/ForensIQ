"""
robustness_check.py
===================
Sensitivity checks for the 3-model benchmark: LOF neighbour count, One-Class SVM subsample size
and seed, Isolation Forest seed. Writes reports/multimodel_eval/robustness.json.
"""
import os
import json
import warnings

import numpy as np
from sklearn.neighbors import LocalOutlierFactor

import multimodel_eval as M

warnings.filterwarnings("ignore")
out = {}
for tag in ["img1", "img2", "img3"]:
    spec = M.IMAGES[tag]
    if not os.path.exists(os.path.join(spec["art_dir"], "mft", "mft_records.json")):
        continue
    df, raw, feats = M.build_features(spec["art_dir"], tag)
    tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
    act, idx = M.match_targets(df["path"], tg)
    X = M.standardize(df[feats].values.astype(float))
    K = int(round(M.BUDGET_PCT * len(X)))
    hit = lambda s: M.metrics(M.top_k_mask(s, K)[0], act, idx)["targets_hit"]
    r = {"targets": len(act), "unique_rows": int(len(np.unique(X, axis=0))), "rows": len(X), "lof": {}, "ocsvm": {}}
    for k in (20, 50, 100, 300):
        s = -LocalOutlierFactor(n_neighbors=k, n_jobs=-1).fit(X).negative_outlier_factor_
        r["lof"][str(k)] = hit(s)
    for n in (5000, 10000, 20000):
        r["ocsvm"][str(n)] = [hit(M.fit_score("One-Class SVM", X, sd, n)[0]) for sd in (42, 1, 2, 3, 4)]
    r["iforest_seeds"] = [hit(M.fit_score("Isolation Forest", X, sd)[0]) for sd in (42, 1, 2, 3, 4)]
    out[tag] = r
    print(tag, r, flush=True)
with open(os.path.join(M.OUT, "robustness.json"), "w") as f:
    json.dump(out, f, indent=2)
