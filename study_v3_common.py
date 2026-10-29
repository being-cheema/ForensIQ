"""
study_v3_common.py
==================
Shared loading and scoring for the study v3 ablations, so every ablation measures the same way
(reports/study_v3/PROTOCOL.md). Ground truth is used only to score rankings.

    D = load("img2")                       # features, targets, cached per disk and feature set
    s = score(D, "Isolation Forest", cols, seed)
    curve(D, s)                            # targets caught at every protocol budget
    summary(D, s)                          # headline numbers, knee, plateau
"""

import os
import functools

import numpy as np

import multimodel_eval as M

DISKS = ["img1", "img2", "img3"]
SEEDS = [42, 1337, 9999, 7, 2024]
BUDGETS = [round(x * 0.5, 1) for x in range(0, 201)]   # 0-100 % in 0.5 % steps
HEADLINE = [15.0, 20.0]
OUT = os.path.join(M.BASE_DIR, "reports", "study_v3", *([] if M.FEATURE_SET == "clean" else [M.FEATURE_SET]))


@functools.lru_cache(maxsize=None)
def load(tag, with_burst=True):
    """Feature table for one disk under the active FEATURE_SET, plus target indices.
    Burst candidate columns are added (not part of the default column list)."""
    spec = M.IMAGES[tag]
    df, raw, feats = M.build_features(spec["art_dir"], tag)
    if with_burst:
        M.add_burst_features(df, raw)
    tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
    active, all_idx = M.match_targets(df["path"], tg)
    return {"tag": tag, "df": df, "raw": raw, "feats": list(feats), "active": active,
            "all_idx": all_idx, "N": len(df), "label": spec["label"], "scenario": spec["scenario"]}


def matrix(D, cols):
    return M.standardize(D["df"][list(cols)].values.astype(float))


def score(D, model, cols, seed=42, X=None):
    """Suspicion score per file (higher = more suspicious)."""
    s, _ = M.fit_score(model, matrix(D, cols) if X is None else X, seed)
    return s


def first_rank(D, s):
    """Best (1-based) rank of each target: a target is caught once any of its files is reached."""
    order = np.argsort(-s, kind="stable")
    pos = np.empty(len(s), dtype=np.int64)
    pos[order] = np.arange(1, len(s) + 1)
    return np.array([pos[t["idx"]].min() for t in D["active"]])


def curve(D, s, budgets=BUDGETS):
    """Targets caught at each budget (% of disk)."""
    fr = first_rank(D, s)
    return [int((fr <= int(round(b / 100 * D["N"]))).sum()) for b in budgets]


def summary(D, s):
    """Headline catches, knee (first budget with >= 90 % of targets) and plateau (last target found)."""
    fr = np.sort(first_rank(D, s))
    T, N = len(fr), D["N"]
    pct = lambda r: round(100.0 * float(r) / N, 2)
    out = {"targets": T}
    for b in HEADLINE:
        out[f"at{int(b)}"] = int((fr <= int(round(b / 100 * N))).sum())
    out["knee_pct"] = pct(fr[int(np.ceil(0.9 * T)) - 1])
    out["plateau_pct"] = pct(fr[-1])
    return out
