"""study_v3_img4_demo.py: what the examiner sees on Images 4 and 5 (seed 42, 20% budget): target ranks, TreeSHAP reasons, top of the list."""
import os, sys, json
import numpy as np, shap
import study_v3_common as C
import multimodel_eval as M
assert M.FEATURE_SET == "final"
out = []
def reasons(v, feats, k=3):
    idx = [j for j in np.argsort(-v) if v[j] > 0][:k]
    return ", ".join(f"{feats[j]} (+{v[j]:.2f})" for j in idx)
for tag in ("img4", "img5"):
    D = C.load(tag); N = D["N"]; feats = D["feats"]; paths = D["df"]["path"].astype(str).values
    Xs = C.matrix(D, feats); s, fm = M.fit_score("Isolation Forest", Xs, 42)
    order = np.argsort(-s, kind="stable"); rank = np.empty(N, dtype=int); rank[order] = np.arange(1, N + 1)
    K = int(round(0.2 * N)); ex = shap.TreeExplainer(fm)
    tf = sorted({i for t in D["active"] for i in t["idx"]}, key=lambda i: rank[i])
    out += [f"## {M.IMAGES[tag]['label']}", "", f"{N:,} files; 20% review budget = {K:,} files; seed 42.", "", "### Target files", "", "| rank | % of list | inside 20% budget | file | top reasons (TreeSHAP) |", "|---|---|---|---|---|"]
    sv = -np.asarray(ex.shap_values(Xs[tf]))
    for i, v in zip(tf, sv):
        out.append(f"| {rank[i]:,} | {100*rank[i]/N:.2f}% | {'yes' if rank[i] <= K else 'no'} | `{paths[i]}` | {reasons(v, feats)} |")
    top = order[:10]; sv = -np.asarray(ex.shap_values(Xs[top]))
    out += ["", "### Top 10 of the ranked list", "", "| rank | file | top reasons |", "|---|---|---|"]
    for r, (i, v) in enumerate(zip(top, sv), 1):
        out.append(f"| {r} | `{paths[i]}` | {reasons(v, feats)} |")
    out.append("")
open("reports/study_v3/final/IMG4_demo.md", "w").write("\n".join(out)); print("\n".join(out))
