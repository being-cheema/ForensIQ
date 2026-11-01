"""study_v3_location_classes.py: which targets does each method catch, split by where the target's files lie?
Classes: user folder (all files under a profile folder), system folder (any file under /Windows/System32 or /WINDOWS/system32), other (e.g. Program Files).
Methods: IF (final 19 features, five seeds), plain rules R1..R4 (deterministic). Images 1 to 5, full target lists.
Usage: FORENSIQ_FEATURE_SET=final python study_v3_location_classes.py"""
import os, json, sys
import numpy as np
import study_v3_common as C
def srs(D, keys):
    n = D["N"]
    pr = np.argsort(np.argsort(D["df"]["path"].astype(str).values, kind="stable"), kind="stable")
    order = np.lexsort(tuple([pr] + [-np.nan_to_num(np.asarray(k, float)) for k in keys[::-1]]))
    s = np.empty(n); s[order] = np.arange(n, 0, -1); return s
PROFILE = ("/users/", "/documents and settings/")
out = {}; rows = []
for tag in ("img1", "img2", "img3", "img4", "img5"):
    D = C.load(tag); df = D["df"]; N = D["N"]; paths = df["path"].astype(str).str.lower().values; K = {b: int(round(b / 100 * N)) for b in (15, 20)}
    cls = []
    for t in D["active"]:
        ps = [paths[i] for i in t["idx"]]
        if any("/windows/system32/" in p or "/winnt/system32/" in p for p in ps): cls.append("system folder")
        elif all(p.startswith(PROFILE) for p in ps): cls.append("user folder")
        else: cls.append("other")
    rules = {"R1": [df["delta_si_fn"].astype(float)], "R3": [sum(df[c].astype(float) for c in ["temp_path", "user_path", "is_exe", "is_script", "is_archive"])], "R4": [D["raw"]["m_time"].astype(float)]}
    fr = {k: C.first_rank(D, srs(D, v)) for k, v in rules.items()}
    fr["IF"] = np.array([C.first_rank(D, C.score(D, "Isolation Forest", D["feats"], sd)) for sd in C.SEEDS])   # seeds x targets
    for ci in sorted(set(cls)):
        idx = [i for i, c in enumerate(cls) if c == ci]
        for b in (15, 20):
            r = {"image": tag, "class": ci, "targets": len(idx), "budget": b,
                 "IF": round(float((fr["IF"][:, idx] <= K[b]).sum(1).mean()), 1)}
            for k in ("R1", "R3", "R4"): r[k] = int((fr[k][idx] <= K[b]).sum())
            rows.append(r)
    out[tag] = {"names": [(t["name"], c) for t, c in zip(D["active"], cls)]}
json.dump({"rows": rows, "targets": out}, open("reports/study_v3/final/IMG4_img5/location_classes.json", "w"), indent=1)
agg = {}
for r in rows:
    a = agg.setdefault((r["class"], r["budget"]), {"targets": 0, "IF": 0, "R1": 0, "R3": 0, "R4": 0})
    for k in ("targets", "IF", "R1", "R3", "R4"): a[k] += r[k]
for (c, b), a in sorted(agg.items()): print(c, b, {k: round(v, 1) for k, v in a.items()})
print()
for r in rows:
    if r["budget"] == 20: print(r)
