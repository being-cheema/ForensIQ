"""study_v3_img4.py: frozen pipeline on Image 4 (blind check). Nothing is tuned: final 19 features, IF 200 trees / subsample 256,
seeds 42, 1337, 9999, 7, 2024, budgets 15% and 20%, plain rules R3 and R4 as in A3. Targets: IMG4_TARGETS (pre-registered)."""
import os, json, time
import numpy as np
import study_v3_common as C
import multimodel_eval as M
assert M.FEATURE_SET == "final"
t0 = time.time()
D = C.load(os.environ.get("TAG", "img4")); N = D["N"]
out = {"N": N, "features": len(D["feats"]), "targets_defined": len(M.IMAGES[D["tag"]]["targets"]), "targets_on_disk": len(D["active"]),
       "target_files": len(D["all_idx"]), "target_names": [t["name"] for t in D["active"]]}
rows = []
for sd in C.SEEDS:
    s = C.score(D, "Isolation Forest", D["feats"], sd); fr = C.first_rank(D, s)
    rows.append({"seed": sd, "best_rank": [int(x) for x in fr], "best_rank_pct": [round(100 * x / N, 3) for x in fr], **C.summary(D, s)})
out["IF"] = rows
def rule(keys):
    return C.summary(D, __import__("study_v3_reliability_a").stable_rank_score(D, keys)) if False else None
import study_v3_reliability_a as A
R3 = A.stable_rank_score(D, [sum(D["df"][c].astype(float) for c in ["temp_path", "user_path", "is_exe", "is_script", "is_archive"])])
R4 = A.stable_rank_score(D, [D["raw"]["m_time"].astype(float)])
out["R3"] = {**C.summary(D, R3), "best_rank_pct": [round(100 * x / N, 3) for x in C.first_rank(D, R3)]}
out["R4"] = {**C.summary(D, R4), "best_rank_pct": [round(100 * x / N, 3) for x in C.first_rank(D, R4)]}
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(100 * (c - h) / d, 1), round(100 * (c + h) / d, 1)
T = len(D["active"])
for b in (15, 20):
    k = np.mean([r[f"at{b}"] for r in rows]); out[f"IF_at{b}"] = {"mean": k, "worst": min(r[f"at{b}"] for r in rows), "wilson": wilson(round(k), T)}
out["seconds"] = round(time.time() - t0, 1)
os.makedirs(os.path.join(C.OUT, "IMG4_" + D["tag"]), exist_ok=True)
json.dump(out, open(os.path.join(C.OUT, "IMG4_" + D["tag"], "results.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
