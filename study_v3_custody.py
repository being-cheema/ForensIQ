"""study_v3_custody.py: evidence-integrity checks for the study (read-only on all evidence).

    .venv/bin/python study_v3_custody.py hash      # source images (SHA-256, MD5) + artefacts (SHA-256), pass 1
    .venv/bin/python study_v3_custody.py verify    # re-hash the artefacts after the analysis and compare

Writes reports/study_v3/final/P/custody.json. Source image files are opened with mode 'rb' only.
Published hashes are used only where they exist in the repository: the per-segment MD5 values in
images/hacking/SCHARDT.LOG. No published hash is held locally for the other images.
"""
import os, re, sys, json, time, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "reports", "study_v3", "final", "P", "custody.json")
IMG = os.path.join(HERE, "images")
SOURCES = {
    "img1": sorted(glob.glob(f"{IMG}/hacking/SCHARDT.00?")) + [f"{IMG}/hacking/SCHARDT.dd"],
    "img2": sorted(glob.glob(f"{IMG}/dataleak/cfreds_2015_data_leakage_pc.7z.00?")) + [f"{IMG}/dataleak/cfreds_2015_data_leakage_pc.dd"],
    "img3": sorted(glob.glob(f"{IMG}/lonewolf/LoneWolf.E0?")),
}
ARTS = {t: os.path.join(HERE, "runs", t, "artifacts") for t in ("img1", "img2", "img3")}


def hash_file(p, md5=True):
    s, m = hashlib.sha256(), hashlib.md5() if md5 else None
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8 << 20), b""):
            s.update(c)
            if m: m.update(c)
    return s.hexdigest(), (m.hexdigest() if m else None)


def published_schardt():
    """Per-segment MD5 values printed in SCHARDT.LOG (four 32-bit words per segment)."""
    pub, seg = {}, None
    for line in open(f"{IMG}/hacking/SCHARDT.LOG", errors="replace"):
        m = re.search(r"(SCHARDT\.\d{3}):.*MD5 Value", line)
        if m: seg = m.group(1); continue
        m = re.search(r"\*\s*\.\.\.([0-9A-F ]+)\.\.\.", line)
        if seg and m:
            pub[seg] = m.group(1).replace(" ", "").lower(); seg = None
    return pub


def hash_tree(root):
    d = {}
    for dp, _, fs in os.walk(root):
        for fn in fs:
            p = os.path.join(dp, fn)
            d[os.path.relpath(p, root)] = hash_file(p, md5=False)[0]
    return d


def main():
    mode = sys.argv[1]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if mode == "hash":
        pub = published_schardt()
        res = {"note": "read-only hashing; published hashes only where present in the repository", "images": {}, "artefacts": {}}
        for tag, files in SOURCES.items():
            for p in files:
                name = os.path.basename(p)
                if not os.path.exists(p):
                    res["images"][name] = {"disk": tag, "status": "missing"}; continue
                t = time.time(); s, m = hash_file(p)
                e = {"disk": tag, "bytes": os.path.getsize(p), "sha256": s, "md5": m, "published_md5": pub.get(name)}
                e["status"] = ("match" if m == pub[name] else "MISMATCH") if name in pub else "published hash not available locally"
                res["images"][name] = e
                print(name, e["status"], f"{time.time()-t:.0f}s", flush=True)
                json.dump(res, open(OUT, "w"), indent=1)
        for tag, root in ARTS.items():
            h = hash_tree(root)
            res["artefacts"][tag] = {"files": len(h), "bytes": sum(os.path.getsize(os.path.join(root, k)) for k in h), "pass1": h}
        json.dump(res, open(OUT, "w"), indent=1)
    else:
        for tag, root in ARTS.items():
            a = res["artefacts"][tag]; h = hash_tree(root); p1 = a["pass1"]
            a["pass2_files"] = len(h)
            a["mismatches"] = sum(1 for k in p1 if h.get(k) != p1[k]) + sum(1 for k in h if k not in p1)
            a["pass1_sha256_of_hashes"] = hashlib.sha256(json.dumps(p1, sort_keys=True).encode()).hexdigest()
            print(tag, a["files"], a["pass2_files"], "mismatches", a["mismatches"])
        json.dump(res, open(OUT, "w"), indent=1)


main()
