"""Fit sklearn IF(200, rs=42) and LOF(k=20) on the SAME sample rows the Lab uses; dump scores to .cache/lab_validate_{img}.json"""
import json, os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
B = os.path.dirname(os.path.abspath(__file__))
for img in ("img1", "img2", "img3"):
    D = json.load(open(f"{B}/web/src/data/lab/{img}.json"))
    X = np.array([r["x"] for r in D["rows"]])
    sif = -IsolationForest(n_estimators=200, random_state=42).fit(X).score_samples(X)
    slof = -LocalOutlierFactor(n_neighbors=20).fit(X).negative_outlier_factor_
    json.dump({"if": sif.tolist(), "lof": slof.tolist()}, open(f"{B}/.cache/lab_validate_{img}.json", "w"))
    print(img, "ok")
