"""study_v3_explain_ci.py: 95% bootstrap intervals for B1-B3 of Isolation Forest (20% budget), from the per-file arrays written by
MODELS_ONLY="Isolation Forest" FORENSIQ_FEATURE_SET=final python study_v3_explain.py --disk <img>.
Files are resampled with replacement (10,000 draws, seed 0); for B3 the 60 planted files are resampled and keep their five seeds.
The files of one disk are not independent, so the intervals describe the sampling of files on that disk and are not
population intervals."""
import json, os
import numpy as np
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "study_v3", "final", "B")
rng = np.random.RandomState(0)
NB = 10000
def pct(x): return [round(float(np.percentile(x, 2.5)), 3), round(float(np.percentile(x, 97.5)), 3)]
res = {}
for t in ["img1", "img2", "img3", "img4", "img5"]:
    R = json.load(open(os.path.join(OUT, f"results_{t}_perfile.json")))["models"]["Isolation Forest"]
    a = np.array(R["B1_perfile"]["drop_shap"]); b = np.array(R["B1_perfile"]["drop_random"]); n = len(a)
    idx = rng.randint(0, n, (NB, n))
    ratio = np.median(a[idx], 1) / np.median(b[idx], 1)
    r = {"B1": {"n": n, "ratio": round(float(np.median(a) / np.median(b)), 2), "ci": pct(ratio)}}
    sj = np.array(R["B2"]["seeds"]["20"]["per_file"]); idx = rng.randint(0, len(sj), (NB, len(sj)))
    r["B2_seeds"] = {"n": len(sj), "mean": round(float(sj.mean()), 3), "ci": pct(sj[idx].mean(1))}
    nj = np.array(R["B2"]["noise"]["20"]["per_file"]); idx = rng.randint(0, len(nj), (NB, len(nj)))
    r["B2_noise"] = {"n": len(nj), "mean": round(float(nj.mean()), 3), "ci": pct(nj[idx].mean(1))}
    raw = R["B3"]["raw20"]; seeds = list(raw)
    det = np.array([raw[s]["detected"] for s in seeds]); hit = np.array([raw[s]["named"] for s in seeds])   # seeds x 60
    def stat(ix):
        d = det[:, ix]; h = hit[:, ix]
        dd = d.mean(); nm = (d & h).sum() / d.sum() if d.sum() else np.nan
        return dd, nm
    pt = stat(np.arange(det.shape[1]))
    bs = np.array([stat(rng.randint(0, det.shape[1], det.shape[1])) for _ in range(NB)])
    r["B3_detected"] = {"n_files": int(det.shape[1]), "seeds": len(seeds), "value": round(100 * float(pt[0]), 1), "ci": [round(100 * float(np.nanpercentile(bs[:, 0], 2.5)), 1), round(100 * float(np.nanpercentile(bs[:, 0], 97.5)), 1)]}
    r["B3_named_of_detected"] = {"value": round(100 * float(pt[1]), 1), "ci": [round(100 * float(np.nanpercentile(bs[:, 1], 2.5)), 1), round(100 * float(np.nanpercentile(bs[:, 1], 97.5)), 1)]}
    res[t] = r
    print(t, json.dumps(r))
json.dump(res, open(os.path.join(OUT, "explain_ci_IF.json"), "w"), indent=1)

# B3, share of detected planted files whose top-3 names the cause: the bootstrap above collapses to [100, 100] when every detected
# file is named, which would claim more than 60 files can show. We therefore also give a Wilson interval on distinct planted files:
# a file counts as detected if any seed flagged it, and as named if every seed that flagged it named the cause.
def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(float(100 * (c - h) / d), 1), round(float(100 * (c + h) / d), 1)]
for t in ["img1", "img2", "img3", "img4", "img5"]:
    raw = json.load(open(os.path.join(OUT, f"results_{t}_perfile.json")))["models"]["Isolation Forest"]["B3"]["raw20"]
    det = np.array([raw[s]["detected"] for s in raw]).astype(bool); hit = np.array([raw[s]["named"] for s in raw]).astype(bool)
    any_det = det.any(0); all_named = ((~det) | hit).all(0) & any_det
    k, n = int(all_named.sum()), int(any_det.sum())
    res[t]["B3_named_files_wilson"] = {"detected_files": n, "named_every_time": k, "share": round(100 * k / n, 1), "wilson": wilson(k, n)}
    print(t, res[t]["B3_named_files_wilson"])
json.dump(res, open(os.path.join(OUT, "explain_ci_IF.json"), "w"), indent=1)
