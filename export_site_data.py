"""
export_site_data.py
===================
Exports what the results site needs into site/data.json: per-image stats, exact target ranks under each
model (so the browser can compute recall at any review budget), SHAP drivers per caught target, verdicts and
pipeline stage timings. (The old 2-D sample, single-seed ablation and robustness tables are gone: the Lab and
study v3 replace them.)

Run after multimodel_eval.py and robustness_check.py:  python export_site_data.py
"""

import os
import re
import json
import warnings

import numpy as np
import pandas as pd

import multimodel_eval as M
from run_pipeline import STEPS

warnings.filterwarnings("ignore")
SITE = os.path.join(M.BASE_DIR, "site")
SAMPLE_N = 1800
PCTS = [round(x, 3) for x in np.concatenate([np.arange(0.002, 0.02, 0.002), np.arange(0.02, 0.201, 0.005)])]


def stage_times(tag):
    p = os.path.join(M.BASE_DIR, "runs", tag, "pipeline.log")
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r"│\s+(\S+\.py)\s+│.*│\s+(?:PASS|FAIL)\s+│\s+([\d.]+)\s+│", line)
            if m:
                out[m.group(1)] = float(m.group(2))
    return out


def pca2(X):
    Xc = X - X.mean(0)
    _, _, vt = np.linalg.svd(Xc[np.random.RandomState(0).choice(len(Xc), min(len(Xc), 20000), replace=False)],
                             full_matrices=False)
    return Xc @ vt[:2].T


def top_features(row, n=4):
    items = sorted(((k, float(v)) for k, v in row.items() if k not in ("path", "dominant_feature")),
                   key=lambda a: -abs(a[1]))[:n]
    return [[k, round(v, 3)] for k, v in items]


def strip_sample(sample, n_rest=220, n_tgt=40):
    """The header's scrolling path strip only needs a few real paths and which are evidence (path, target name)."""
    tg = [q for q in sample if q["t"]][:n_tgt]
    rest = [q for q in sample if not q["t"]][:n_rest]
    return [{"p": q["p"], "t": q["t"]} for q in rest + tg]


def main():
    os.makedirs(SITE, exist_ok=True)
    results = json.load(open(os.path.join(M.OUT, "results.json")))["results"]
    main_df = pd.read_csv(os.path.join(M.OUT, "results_main.csv"))
    try:   # the site no longer shows the old single-seed ablation; study v3 A1/A3 replace it
        abl = pd.read_csv(os.path.join(M.OUT, "results_ablation.csv"))
    except pd.errors.EmptyDataError:
        abl = pd.DataFrame(columns=["image", "config", "n_features", "model", "targets"])
    rob_p = os.path.join(M.OUT, "robustness.json")
    rob = json.load(open(rob_p)) if os.path.exists(rob_p) else {}

    data = {"models": M.MODELS, "pcts": PCTS, "images": {}, "pipeline": [
        {"script": s, "title": t, "desc": d} for s, t, d in STEPS]}
    rng = np.random.RandomState(7)

    for tag, res in results.items():
        spec = M.IMAGES[tag]
        df, raw, feats = M.build_features(spec["art_dir"], tag)
        N = len(df)
        tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
        active, all_idx = M.match_targets(df["path"], tg)
        Xs = M.standardize(df[feats].values.astype(float))
        K5 = int(round(M.BUDGET_PCT * N))

        ranks, order_of = {}, {}
        for model in M.MODELS:
            s, _ = M.fit_score(model, Xs, 42, 10000)
            order = np.argsort(-s, kind="stable")
            r = np.empty(N, dtype=np.int64)
            r[order] = np.arange(1, N + 1)
            ranks[model], order_of[model] = r, order
            print(f"[{tag}] {model} scored", flush=True)

        shap_rows = {}
        for model in M.MODELS:
            p = os.path.join(M.SHAP_DIR, f"{tag}_{model.replace(' ', '_')}_shap.csv")
            if os.path.exists(p):
                shap_rows[model] = {r["path"]: top_features(r) for r in pd.read_csv(p).to_dict("records")}

        targets = []
        for t in active:
            idx = np.array(t["idx"])
            entry = {"name": t["name"], "copies": len(idx), "ranks": {}, "path": "", "shap": {}}
            for model in M.MODELS:
                best = idx[np.argmin(ranks[model][idx])]
                entry["ranks"][model] = int(ranks[model][best])
                pth = df["path"].values[best]
                if pth in shap_rows.get(model, {}):
                    entry["shap"][model] = shap_rows[model][pth]
                entry["path"] = entry["path"] or pth
            if not entry["shap"]:
                entry["path"] = df["path"].values[idx[0]]
            targets.append(entry)

        # 2-D sample: random files + every target copy's best-IF file
        coords = pca2(Xs)
        keep = set(rng.choice(N, min(N, SAMPLE_N), replace=False).tolist())
        for t in active:
            keep.add(int(t["idx"][np.argmin(ranks["Isolation Forest"][np.array(t["idx"])])]))
        keep = sorted(keep)
        tgt_names = {}
        for t in active:
            for i in t["idx"]:
                tgt_names.setdefault(int(i), t["name"])
        sample = [{
            "x": round(float(coords[i, 0]), 3), "y": round(float(coords[i, 1]), 3),
            "r": [int(ranks[m][i]) for m in M.MODELS],
            "t": tgt_names.get(i, ""),
            "p": df["path"].values[i][-70:],
        } for i in keep]

        # score curves: recall of targets vs budget, for each model
        curves = {}
        for model in M.MODELS:
            tr = np.array([e["ranks"][model] for e in targets])
            curves[model] = [round(float((tr <= int(round(p * N))).mean()), 4) for p in PCTS]

        a = abl[abl["image"] == res["label"]]
        ablation = [{"config": c, "n": int(a[a["config"] == c]["n_features"].iloc[0]),
                     **{m: a[(a["config"] == c) & (a["model"] == m)]["targets"].iloc[0] for m in M.MODELS}}
                    for c in dict.fromkeys(a["config"])]
        mrows = main_df[main_df["image"] == res["label"]].to_dict("records")
        const = []
        fp = os.path.join(M.BASE_DIR, "runs", tag, "features", "macb_features.csv")
        if os.path.exists(fp):
            fdf = pd.read_csv(fp)
            const = [c for c in fdf.columns if c != "path" and fdf[c].nunique() <= 1]

        data["images"][tag] = {
            "label": res["label"], "files": N, "K5": K5, "features": feats,
            "targets": targets, "curves": curves, "sample": strip_sample(sample),
            "metrics": {r["model"]: {k: r[k] for k in ("targets", "target_recall", "file_recall", "accuracy",
                                                       "precision", "f1", "timestomping", "insider",
                                                       "recall_at_5.5pct", "recall_at_10pct")} for r in mrows},
            "verdicts": {m: res["models"][m]["verdicts"] for m in M.MODELS},
            "shap_global": {m: (res["models"][m]["shap"] or {}).get("mean_abs", {}) for m in M.MODELS},
            "stage_times": stage_times(tag),
            "scenario": spec["scenario"],
        }

    with open(os.path.join(SITE, "data.json"), "w") as f:
        json.dump(data, f, separators=(",", ":"), default=str)
    print("[+] wrote", os.path.join(SITE, "data.json"), os.path.getsize(os.path.join(SITE, "data.json")) // 1024, "KB")


if __name__ == "__main__":
    main()
