"""study_v3_img45_rerun.py: clean end-to-end rerun on Images 4 and 5, from the raw E01 files, nothing changed.
(1) extract again into a scratch folder and compare every artefact with the first extraction (SHA-256);
(2) score again (final 19 features, IF, five seeds, original and amended target lists) and compare with the saved results;
(3) write the hashed explanation records twice and compare byte for byte; (4) hash the artefacts again after all analyses.
Usage: FORENSIQ_FEATURE_SET=final python study_v3_img45_rerun.py"""
import os, sys, json, glob, hashlib, shutil, subprocess, time
import numpy as np
import multimodel_eval as M
import study_v3_common as C
import study_v3_explanation_record as ER
assert M.FEATURE_SET == "final"
IMG = {"img4": "images/szechuan/desktop/20200918_0417_DESKTOP-SDN1RPT.E01", "img5": "images/szechuan/dc/E01-DC01/20200918_0347_CDrive.E01"}
SCR = "/private/tmp/forensiq_img45_rerun"; OUT = os.path.join(C.OUT, "IMG45_RERUN"); os.makedirs(OUT, exist_ok=True)
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def manifest(d): return {os.path.relpath(p, d): sha(p) for p in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)) if os.path.isfile(p) and not p.endswith("artifact_summary.json")}
res = {}
shutil.rmtree(SCR, ignore_errors=True)
for tag, img in IMG.items():
    art = os.path.join(SCR, tag, "artifacts"); os.makedirs(art)
    t0 = time.time(); env = dict(os.environ, FORENSIQ_OUT_DIR=art, FORENSIQ_IMAGE_PATH=os.path.abspath(img))
    subprocess.run([sys.executable, "extractor.py", os.path.abspath(img)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    t_ex = time.time() - t0
    m_new = manifest(art); m_old = manifest(os.path.join(M.BASE_DIR, "runs", tag, "artifacts"))
    same = {k: m_new.get(k) == v for k, v in m_old.items()}
    r = {"extraction_seconds": round(t_ex, 1), "artefacts": len(m_new), "artefacts_identical_to_first_extraction": int(sum(same.values())), "artefacts_first_extraction": len(m_old),
         "differing": [k for k, v in same.items() if not v][:10]}
    for t in (tag, tag + "_am"):
        M.IMAGES[t]["art_dir"] = art
    for f in glob.glob(os.path.join(M.CACHE, f"{tag}*_feat")): shutil.rmtree(f, ignore_errors=True)
    for t in (tag, tag + "_am"):
        D = C.load(t); N = D["N"]
        runs = [C.summary(D, C.score(D, "Isolation Forest", D["feats"], sd)) for sd in C.SEEDS]
        ranks = [[int(x) for x in C.first_rank(D, C.score(D, "Isolation Forest", D["feats"], sd))] for sd in C.SEEDS]
        saved = json.load(open(os.path.join(C.OUT, f"IMG4_{t}", "results.json")))
        r[t] = {"files": N, "targets": len(D["active"]), "at15": [x["at15"] for x in runs], "at20": [x["at20"] for x in runs],
                "best_rank_identical_to_saved": ranks == [x["best_rank"] for x in saved["IF"]]}
    d1, d2 = os.path.join(SCR, tag, "rec1"), os.path.join(SCR, tag, "rec2")
    m1 = ER.generate(tag, d1); m2 = ER.generate(tag, d2)
    r["records"] = {"n": m1["n_records"], "byte_identical_two_passes": open(os.path.join(d1, m1["file"]), "rb").read() == open(os.path.join(d2, m2["file"]), "rb").read(),
                    "sha256": m1["sha256_records_file"], "feature_table_sha256": m1["feature_table_sha256"]}
    r["artefacts_unchanged_after_analysis"] = manifest(art) == m_new
    res[tag] = r; print(tag, json.dumps(r), flush=True)
json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1)
