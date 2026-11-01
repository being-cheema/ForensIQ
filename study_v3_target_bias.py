"""study_v3_target_bias.py: how far could the choice of targets bias recall? (final 19 features, IF, five seeds)
(a) share of targets that sit in a user-profile folder, and IF / plain-rule R3 recall for profile vs other targets;
(b) IF recall without the two location features (user_path, temp_path);
(c) leave-one-target-out range of the pooled recall at 15%.
Ground truth is used only to score rankings. Usage: FORENSIQ_FEATURE_SET=final python study_v3_target_bias.py"""
import os, json
import numpy as np
import study_v3_common as C
import study_v3_reliability_a as A
import multimodel_eval as M
assert M.FEATURE_SET == "final"
OUT = os.path.join(C.OUT, "TARGET_BIAS"); os.makedirs(OUT, exist_ok=True)
PROFILE = ("/users/", "/documents and settings/")
res = {}; pooled_hits = {15: [], 20: []}
for tag in C.DISKS:
    D = C.load(tag); N = D["N"]; paths = D["df"]["path"].astype(str).str.lower().values
    tg = D["active"]; T = len(tg)
    prof = np.array([all(paths[i].startswith(PROFILE) for i in t["idx"]) for t in tg])
    K = {b: int(round(b / 100 * N)) for b in (15, 20)}
    R3 = A.stable_rank_score(D, [sum(D["df"][c].astype(float) for c in ["temp_path", "user_path", "is_exe", "is_script", "is_archive"])])
    r3 = C.first_rank(D, R3)
    cols_noloc = [f for f in D["feats"] if f not in ("user_path", "temp_path")]
    fr_all, fr_noloc = [], []
    for sd in C.SEEDS:
        fr_all.append(C.first_rank(D, C.score(D, "Isolation Forest", D["feats"], sd)))
        fr_noloc.append(C.first_rank(D, C.score(D, "Isolation Forest", cols_noloc, sd)))
    fr_all, fr_noloc = np.array(fr_all), np.array(fr_noloc)           # seeds x targets
    r = {"N": N, "targets": T, "targets_in_profile": int(prof.sum())}
    for b in (15, 20):
        hit = (fr_all <= K[b])                                          # seeds x targets
        pooled_hits[b].append(hit)
        r[f"IF_at{b}_all"] = round(float(hit.sum(1).mean()), 1)
        r[f"IF_at{b}_noloc"] = round(float((fr_noloc <= K[b]).sum(1).mean()), 1)
        r[f"IF_at{b}_profile"] = round(float(hit[:, prof].sum(1).mean()), 1) if prof.any() else None
        r[f"IF_at{b}_other"] = round(float(hit[:, ~prof].sum(1).mean()), 1) if (~prof).any() else None
        r[f"R3_at{b}_profile"] = int((r3[prof] <= K[b]).sum()); r[f"R3_at{b}_other"] = int((r3[~prof] <= K[b]).sum())
    res[tag] = r; print(tag, r, flush=True)
# leave-one-target-out, pooled over the three disks (seed means)
out = {"per_disk": res, "leave_one_out": {}}
for b in (15, 20):
    H = np.concatenate(pooled_hits[b], axis=1)                          # seeds x 60
    tot = H.sum(1).mean(); lo = [(H.sum(1) - H[:, j]).mean() / (H.shape[1] - 1) * 100 for j in range(H.shape[1])]
    out["leave_one_out"][str(b)] = {"pooled_recall_pct": round(tot / H.shape[1] * 100, 1), "loo_min": round(min(lo), 1), "loo_max": round(max(lo), 1)}
json.dump(out, open(os.path.join(OUT, "results.json"), "w"), indent=1); print(json.dumps(out["leave_one_out"]))
