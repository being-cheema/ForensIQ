"""time_e2e_mac.py: one end-to-end ForensIQ run in a fresh process, timed per stage.
usage: FORENSIQ_FEATURE_SET=final python time_e2e_mac.py TAG IMAGE_PATH RUN
raw image -> extractor -> 19 final features -> Isolation Forest (seed 42, 200 trees) -> rank, top 20% -> TreeSHAP on every flagged file.
Artefacts go to a scratch directory, not to runs/. Appends one JSON line to reports/autopsy_baseline/mac/timing.jsonl."""
import os, sys, json, time, shutil, resource
tag, image, run = sys.argv[1], sys.argv[2], int(sys.argv[3])
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
scratch = f"/private/tmp/forensiq_timing/{tag}_{run}"
shutil.rmtree(scratch, ignore_errors=True); os.makedirs(scratch)
os.environ["FORENSIQ_OUT_DIR"] = os.path.join(scratch, "artifacts")
import numpy as np, shap
import multimodel_eval as M
import extractor
T = {}; t0 = time.perf_counter()
extractor.run_all(image_path=image, out_dir=os.environ["FORENSIQ_OUT_DIR"]); T["extraction"] = time.perf_counter() - t0
t = time.perf_counter()
ck = f"timing_{tag}_{run}"
df, raw, feats = M.build_features(os.environ["FORENSIQ_OUT_DIR"], ck); feats = list(feats); N = len(df)
Xs = M.standardize(df[feats].values.astype(float)); T["features"] = time.perf_counter() - t
t = time.perf_counter(); s, fm = M.fit_score("Isolation Forest", Xs, 42); T["if_fit_score"] = time.perf_counter() - t
t = time.perf_counter(); K = int(round(0.20 * N)); order = np.argsort(-s, kind="stable"); flagged = order[:K]; T["rank_top20"] = time.perf_counter() - t
t = time.perf_counter(); expl = shap.TreeExplainer(fm)
for a in range(0, K, 4000): expl.shap_values(Xs[flagged[a:a + 4000]])
T["treeshap"] = time.perf_counter() - t
T["total"] = time.perf_counter() - t0
spec = M.IMAGES[tag]; tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
active, _ = M.match_targets(df["path"], tg)
pos = np.empty(N, dtype=np.int64); pos[order] = np.arange(1, N + 1)
caught = int(sum(1 for x in active if pos[x["idx"]].min() <= K))
rec = {"tag": tag, "run": run, "files": N, "n_features": len(feats), "flagged": K, "targets": len(active), "targets_caught_20pct": caught,
       "seconds": {k: round(v, 3) for k, v in T.items()}, "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 1)}
with open(os.path.join(ROOT, "reports", "autopsy_baseline", "mac", "timing.jsonl"), "a") as f: f.write(json.dumps(rec) + "\n")
shutil.rmtree(scratch, ignore_errors=True); shutil.rmtree(os.path.join(M.CACHE, f"{ck}_feat"), ignore_errors=True)
print(json.dumps(rec))
