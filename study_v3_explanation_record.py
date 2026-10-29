"""study_v3_explanation_record.py: the explanation record R(f) for every flagged file, with a custody manifest.

    FORENSIQ_FEATURE_SET=final .venv/bin/python study_v3_explanation_record.py

For Isolation Forest, seed 42, final feature set (19 features), top 20% of each disk flagged:

    R(f) = (path, score, rank, top-k SHAP attributions, model config hash, feature-set hash, seed)

One JSON line per flagged file, in rank order, written to reports/study_v3/final/P/records/imgN_records.jsonl
(gzipped when larger than 20 MB). Fields
  path               file path in the image
  score              suspicion score = -IsolationForest.score_samples (higher = more suspicious)
  rank               1-based rank over all files of the disk (stable sort, ties by row order)
  top_k_shap         the k = 3 features with the largest |SHAP| (TreeSHAP on the suspicion score), [feature, value]
  model_config_hash  SHA-256 of the canonical JSON of the model class and its get_params()
  feature_set_hash   SHA-256 of the canonical JSON of the ordered feature-name list
  seed               model seed
Ground truth is not used and not stored. manifest.json holds SHA-256 of every records file, of the feature table
(path column + float64 feature matrix bytes), of the code files, library versions, and a re-run check: the whole
generation (feature build, fit, score, SHAP, serialisation) is executed twice and the records compared byte for byte.
"""
import os, sys, io, json, gzip, time, hashlib, shutil, platform, warnings

import numpy as np

import multimodel_eval as M

warnings.filterwarnings("ignore")
assert M.FEATURE_SET == "final", "run with FORENSIQ_FEATURE_SET=final"
import shap, sklearn

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "reports", "study_v3", "final", "P")
DISKS = ["img1", "img2", "img3"]
SEED, BUDGET_PCT, TOPK = 42, 20, 3
GZ_OVER = 20 * 2 ** 20
TOTAL_CAP = 60 * 2 ** 20
CODE = ["multimodel_eval.py", "study_v3_common.py", "study_v3_explanation_record.py"]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()


def table_hash(df, feats):
    h = hashlib.sha256()
    h.update("\n".join(df["path"].astype(str)).encode("utf-8", "surrogateescape"))
    h.update(json.dumps(list(feats)).encode())
    h.update(np.ascontiguousarray(df[list(feats)].values.astype("float64")).tobytes())
    return h.hexdigest()


def generate(tag, outdir, limit_top=None):
    """Build the table, fit IF (seed 42), score, TreeSHAP on flagged files, write records. Returns metadata."""
    t0 = time.perf_counter()
    spec = M.IMAGES[tag]
    df, raw, feats = M.build_features(spec["art_dir"], tag)
    feats = list(feats)
    N = len(df)
    Xs = M.standardize(df[feats].values.astype(float))
    s, fm = M.fit_score("Isolation Forest", Xs, SEED)
    K = int(round(BUDGET_PCT / 100 * N))
    order = np.argsort(-s, kind="stable")
    flagged = order[:K] if limit_top is None else order[:limit_top]
    t1 = time.perf_counter()
    expl = shap.TreeExplainer(fm)
    sv = np.empty((len(flagged), len(feats)))
    for a in range(0, len(flagged), 4000):
        sv[a:a + 4000] = -np.asarray(expl.shap_values(Xs[flagged[a:a + 4000]]))
    t2 = time.perf_counter()
    mh = sha_bytes(canon({"class": "sklearn.ensemble.IsolationForest", "params": fm.get_params()}))
    fh = sha_bytes(canon(feats))
    paths = df["path"].astype(str).values
    buf = io.BytesIO()
    for r, (i, v) in enumerate(zip(flagged, sv), 1):
        top = sorted(range(len(feats)), key=lambda j: (-abs(v[j]), feats[j]))[:TOPK]
        rec = {"path": paths[i], "score": round(float(s[i]), 8), "rank": r,
               "top_k_shap": [[feats[j], round(float(v[j]), 6)] for j in top],
               "model_config_hash": mh, "feature_set_hash": fh, "seed": SEED}
        buf.write(json.dumps(rec, separators=(",", ":")).encode("ascii") + b"\n")
    data = buf.getvalue()
    name = f"{tag}_records.jsonl"
    if len(data) > GZ_OVER:
        name += ".gz"
        z = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=z, mtime=0, compresslevel=9) as g:
            g.write(data)
        payload = z.getvalue()
    else:
        payload = data
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, name), "wb") as f:
        f.write(payload)
    return {"file": name, "n_records": int(len(flagged)), "files_in_disk": int(N), "K_flagged_20pct": K,
            "bytes_raw": len(data), "bytes_written": len(payload), "features": feats,
            "model_config_hash": mh, "feature_set_hash": fh, "feature_table_sha256": table_hash(df, feats),
            "model_params": fm.get_params(),
            "sha256_records_file": sha_file(os.path.join(outdir, name)),
            "seconds_build_fit_score": round(t1 - t0, 2), "seconds_treeshap": round(t2 - t1, 2)}


def main():
    t_all = time.time()
    rec_dir = os.path.join(OUT, "records")
    shutil.rmtree(rec_dir, ignore_errors=True)
    meta = {t: generate(t, rec_dir) for t in DISKS}
    total = sum(m["bytes_written"] for m in meta.values())
    limited = None
    if total > TOTAL_CAP:     # fall back: top 2,000 per disk (all targets are inside the top 20%, but not necessarily the top 2,000)
        limited = 2000
        shutil.rmtree(rec_dir)
        meta = {t: generate(t, rec_dir, limit_top=limited) for t in DISKS}
        total = sum(m["bytes_written"] for m in meta.values())
    for t in DISKS:
        print(t, meta[t]["file"], meta[t]["n_records"], "records", meta[t]["bytes_written"], "bytes",
              f"treeshap {meta[t]['seconds_treeshap']}s", flush=True)

    # re-run check: generate everything again from scratch into a scratch folder and compare byte for byte
    chk_dir = os.path.join(os.environ.get("TMPDIR", "/tmp"), "forensiq_record_recheck")
    shutil.rmtree(chk_dir, ignore_errors=True)
    meta2 = {t: generate(t, chk_dir, limit_top=limited) for t in DISKS}
    ident = {t: (open(os.path.join(rec_dir, meta[t]["file"]), "rb").read() ==
                 open(os.path.join(chk_dir, meta2[t]["file"]), "rb").read()) for t in DISKS}
    shutil.rmtree(chk_dir, ignore_errors=True)
    repro = {"passes": 2, "byte_identical": ident, "all_identical": bool(all(ident.values())),
             "sha256_run1": {t: meta[t]["sha256_records_file"] for t in DISKS},
             "sha256_run2": {t: meta2[t]["sha256_records_file"] for t in DISKS},
             "feature_table_sha256_equal": {t: meta[t]["feature_table_sha256"] == meta2[t]["feature_table_sha256"] for t in DISKS},
             "scope": "second pass repeats feature build, scaling, IF fit, scoring, TreeSHAP and serialisation in a fresh call"}

    manifest = {
        "record_definition": "R(f) = (path, score, rank, top-k SHAP attributions, model config hash, feature-set hash, seed)",
        "model": "Isolation Forest (200 trees, max_samples auto = 256, contamination 0.05 [unused for ranking], n_jobs=-1)",
        "seed": SEED, "budget_pct": BUDGET_PCT, "top_k": TOPK, "feature_set": M.FEATURE_SET,
        "explainer": "shap.TreeExplainer on the suspicion score (-score_samples), all flagged files",
        "restricted_to_top": limited,
        "records": {t: {k: v for k, v in meta[t].items() if k not in ("seconds_build_fit_score", "seconds_treeshap")} for t in DISKS},
        "total_bytes_records": total,
        "code_sha256": {c: sha_file(os.path.join(HERE, c)) for c in CODE},
        "libraries": {"python": sys.version.split()[0], "numpy": np.__version__, "scikit-learn": sklearn.__version__,
                      "shap": shap.__version__, "platform": platform.platform()},
        "rerun_check": repro,
        "timing_seconds": {t: {"build_fit_score": meta[t]["seconds_build_fit_score"], "treeshap_all_flagged": meta[t]["seconds_treeshap"]} for t in DISKS},
        "total_seconds_both_passes": round(time.time() - t_all, 1),
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1, sort_keys=True)
    print("byte-identical on re-run:", repro["byte_identical"], "total bytes", total)


if __name__ == "__main__":
    main()
