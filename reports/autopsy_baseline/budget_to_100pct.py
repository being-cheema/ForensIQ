"""Expected share of the disk an examiner must read before the last target is found, with Autopsy but no ranking.
Favourable to Autopsy: the examiner first reads every file that has any Autopsy artefact (random order inside the group),
then the remaining files in random order. A target is found with the first of its files. 20,000 repetitions, seed 0.
usage: FORENSIQ_FEATURE_SET=final python budget_to_100pct.py   (needs the three Autopsy case databases)"""
import sys, os, json, sqlite3, glob
sys.path.insert(0, "/Users/cheema/ForensIQ/reports/autopsy_baseline"); sys.path.insert(0, "/Users/cheema/ForensIQ")
import numpy as np
import analyze as A
M = A.M
REPS = 20000; rng = np.random.default_rng(0); out = {}
for tag, i in (("img1", 1), ("img2", 2), ("img3", 3)):
    case = glob.glob(f"/Users/cheema/ForensIQ/tools/autopsy/autopsy_cases/img{i}_*")[0]
    con = sqlite3.connect(f"file:{case}/autopsy.db?mode=ro", uri=True)
    rows = con.execute("select f.parent_path, f.name from blackboard_artifacts b join tsk_files f on f.obj_id=b.obj_id").fetchall()
    flagged = set(A.strip((a or "") + (b or "")).strip().lower() for a, b in rows)
    fp = A.fiq_paths(tag); N = len(fp)
    tg = M.IMAGES[tag]["targets"]; tg = tg(fp) if callable(tg) else tg
    active, _ = M.match_targets(fp, tg)
    isf = np.array([p.lower() in flagged for p in fp]); F = int(isf.sum())
    tfiles = [np.array(t["idx"]) for t in active]
    allt = np.unique(np.concatenate(tfiles))
    res = np.empty(REPS)
    for r in range(REPS):
        key = rng.random(N) + (~isf)            # flagged files sort first, random inside each group
        pos = np.empty(N, dtype=np.int64); pos[np.argsort(key, kind="stable")] = np.arange(1, N + 1)
        res[r] = max(pos[ix].min() for ix in tfiles) / N * 100
    out[tag] = {"N": N, "flagged_first": F, "uncaught_targets": int(sum(1 for ix in tfiles if not isf[ix].any())),
                "mean_pct": round(float(res.mean()), 1), "p5": round(float(np.percentile(res, 5)), 1), "p95": round(float(np.percentile(res, 95)), 1)}
    print(tag, out[tag], flush=True)
json.dump(out, open("/Users/cheema/ForensIQ/reports/autopsy_baseline/mac/budget_to_100pct.json", "w"), indent=1)
