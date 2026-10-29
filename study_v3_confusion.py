"""study_v3_confusion.py: file-level confusion matrices, Isolation Forest, final feature set, 20 % review budget.

    FORENSIQ_FEATURE_SET=final .venv/bin/python study_v3_confusion.py

Positive = target file (every file matching a ground-truth pattern, D["all_idx"]); flagged = top K = round(0.20 N)
files by suspicion score. TP = target files flagged, FP = non-target files flagged, FN = target files not flagged,
TN = the rest. Seed 42 and the mean over seeds 42, 1337, 9999, 7, 2024; per disk and pooled (sum of counts).
Ground truth is used only to score the ranking. Writes reports/study_v3/final/P/confusion.json.
"""
import os, json
import numpy as np
import multimodel_eval as M
import study_v3_common as C

assert M.FEATURE_SET == "final", "run with FORENSIQ_FEATURE_SET=final"
MODEL, BUDGET = "Isolation Forest", 20.0
OUTF = os.path.join(C.OUT, "P", "confusion.json")


def rates(tp, fp, fn, tn):
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": tp / (tp + fp), "recall_file": tp / (tp + fn),
            "specificity": tn / (tn + fp), "fpr": fp / (fp + tn)}


res = {"model": MODEL, "feature_set": M.FEATURE_SET, "budget_pct": BUDGET, "seeds": C.SEEDS, "disks": {}}
pool = {"seed42": np.zeros(4), "mean": np.zeros(4)}
for tag in C.DISKS:
    D = C.load(tag)
    N, K = D["N"], int(round(BUDGET / 100 * D["N"]))
    y = np.zeros(N, bool); y[list(D["all_idx"])] = True
    cm = {}
    for s in C.SEEDS:
        sc = C.score(D, MODEL, D["feats"], s)
        top = np.argsort(-sc, kind="stable")[:K]
        f = np.zeros(N, bool); f[top] = True
        tp = int((f & y).sum()); fp = int((f & ~y).sum()); fn = int((~f & y).sum()); tn = int((~f & ~y).sum())
        cm[s] = (tp, fp, fn, tn)
        fr = C.first_rank(D, sc)
        cm[s] += (int((fr <= K).sum()),)           # targets caught (target-level)
    m42 = np.array(cm[42][:4], float)
    mm = np.mean([cm[s][:4] for s in C.SEEDS], axis=0)
    res["disks"][tag] = {"N": N, "K": K, "target_files": int(y.sum()), "targets": len(D["active"]),
                         "seed42": {**rates(*map(float, m42)), "targets_caught": cm[42][4]},
                         "seed_mean": {**rates(*map(float, mm)), "targets_caught": float(np.mean([cm[s][4] for s in C.SEEDS]))},
                         "per_seed_TP": {str(s): cm[s][0] for s in C.SEEDS}}
    pool["seed42"] += m42; pool["mean"] += mm
    print(tag, N, K, cm[42], flush=True)
res["pooled"] = {k: rates(*map(float, v)) for k, v in pool.items()}
res["pooled"]["targets"] = sum(d["targets"] for d in res["disks"].values())
os.makedirs(os.path.dirname(OUTF), exist_ok=True)
json.dump(res, open(OUTF, "w"), indent=1)
print(json.dumps(res["pooled"], indent=1))
