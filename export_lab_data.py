"""export_lab_data.py - sample + full-data ranks for the in-browser Lab -> web/src/data/lab/{img}.json"""
import os, json, sys, warnings
import numpy as np
import multimodel_eval as M

warnings.filterwarnings("ignore")
OUT = os.path.join(M.BASE_DIR, "web", "src", "data", "lab")
SAMPLE_N, TARGET_CAP, DAY = 2000, 300, 86400

INFO = {
    "delta_mc": "Seconds between the file's content-modified time and its MFT-record change time; large gaps hint at timestamp tampering.",
    "delta_mb": "Seconds between the file's modified time and its birth (creation) time; negative or odd gaps mean it was modified before it existed.",
    "delta_ab": "Seconds between last-access time and birth time, showing how long after creation the file was last touched.",
    "future_m": "1 if the modified time lies in the future relative to the rest of the disk, a classic timestomping sign.",
    "zero_size_recent": "1 if the file is empty yet recently modified, often a wiped or truncated file.",
    "size": "File size in bytes.",
    "is_deleted": "1 if the MFT record is marked deleted but still recoverable.",
    "is_exe": "1 if the file is an executable or library (.exe, .dll, .sys ...).",
    "is_archive": "1 if the file is a compressed archive (.zip, .rar, .7z ...), a typical staging container for exfiltration.",
    "temp_path": "1 if the file lives in a temp or cache directory where malware and tools often drop.",
    "user_path": "1 if the file lives inside a user profile folder rather than the system area.",
    "credential_tool": "1 if the file name matches a known password-cracking or credential-dumping tool.",
    "sniffer_tool": "1 if the file name matches a network sniffing or scanning tool.",
    "powershell_exec": "1 if the file is associated with PowerShell execution.",
    "cmd_exec": "1 if the file is associated with command-prompt execution.",
    "script_host": "1 if the file is a script or script-host artifact (.vbs, .js, .bat ...).",
    "usb_present": "1 if the file's timing coincides with a USB device being attached.",
    "is_shortcut_or_trace": "1 if the file is a shortcut or trace artifact (.lnk, .pf, .evtx, .log, .db) showing someone used something.",
    "per_file_prefetch_hit": "1 if Windows Prefetch shows this exact program was executed.",
    "after_hours_touch": "1 if the file was modified or accessed outside normal working hours.",
    "delta_si_fn": "Seconds of disagreement between the two MFT timestamp sets ($STANDARD_INFORMATION vs $FILE_NAME); nonzero is strong timestomping evidence.",
    "filename_entropy": "Shannon entropy of the file name; random-looking names score high.",
    "path_depth": "How many folders deep the file sits.",
    "m_before_cr": "1 if the file's modified time is earlier than its creation time (0 < modified < created), a classic backdating or copy signature.",
    "log_burst_count": "How many files on the disk share this file's exact modified second (log scale); a bulk copy or wipe stamps many files at once.",
    "log_burst_60s": "How many files on the disk share this file's modified minute (log scale); a wider version of the burst count.",
    "is_script": "1 if the file extension is a script type (.ps1, .bat, .cmd, .vbs, .js, .wsf, .hta).",
}


def rank_arr(s):
    o = np.argsort(-s, kind="stable"); r = np.empty(len(s), dtype=np.int64); r[o] = np.arange(1, len(s) + 1); return r


def main(tags):
    os.makedirs(OUT, exist_ok=True)
    for tag in tags:
        spec = M.IMAGES[tag]
        df, raw, feats = M.build_features(spec["art_dir"], tag)
        N = len(df)
        tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
        active, all_idx = M.match_targets(df["path"], tg)
        Xraw = df[feats].values.astype(float)
        mu = Xraw.mean(0); sd = Xraw.std(0); sd[sd == 0] = 1.0
        Xs = (Xraw - mu) / sd
        assert np.allclose(Xs, M.standardize(Xraw))
        rk = {}
        for key, model in (("if", "Isolation Forest"), ("lof", "Local Outlier Factor"), ("svm", "One-Class SVM")):
            s, _ = M.fit_score(model, Xs, 42, 10000); rk[key] = rank_arr(s); print(tag, key, flush=True)
        tname = {}
        for t in active:
            for i in t["idx"]:
                tname.setdefault(int(i), t["name"])
        rng = np.random.RandomState(7)
        tidx = np.array(sorted(tname))
        if len(tidx) > TARGET_CAP:
            tidx = np.sort(rng.choice(tidx, TARGET_CAP, replace=False))
        rest = np.setdiff1d(np.arange(N), np.array(sorted(tname)))
        rest = rng.choice(rest, min(len(rest), SAMPLE_N - len(tidx)), replace=False)
        keep = np.sort(np.concatenate([tidx, rest]))
        def tsv(col, i):
            v = float(raw[col].values[i]); return int(v) if v > 0 else None
        rows = [{"p": df["path"].values[i], "t": tname.get(int(i), ""),
                 "x": [round(float(v), 3) for v in Xs[i]],
                 "ts": {"m": tsv("m_time", i), "a": tsv("a_time", i), "c": tsv("c_time", i), "b": tsv("cr_time", i)},
                 "rk": {k: int(rk[k][i]) for k in rk}} for i in keep]
        # timeline
        m = raw["m_time"].values.astype(float); valid = m > 0
        lo, hi = np.percentile(m[valid], [0.5, 99.5])
        start = int(lo // DAY * DAY); nb = int((hi - start) // DAY) + 1
        def hist(mask):
            v = m[mask & valid]; v = v[(v >= start) & (v < start + nb * DAY)]
            return np.bincount(((v - start) // DAY).astype(int), minlength=nb).tolist()
        tmask = np.zeros(N, dtype=bool); tmask[list(all_idx)] = True
        tl = {"start": start, "binSec": DAY, "counts": hist(np.ones(N, dtype=bool)),
              "targets": {"start": start, "binSec": DAY, "counts": hist(tmask)}}
        pct = {f: [round(float(v), 3) for v in np.percentile(Xraw[:, j], [1, 50, 99])] for j, f in enumerate(feats)}
        out = {"features": feats, "label": spec["label"], "N": N, "K5": int(round(M.BUDGET_PCT * N)),
               "targets": [t["name"] for t in active], "tsKinds": ["m", "a", "c", "b"],
               "tsNote": "m=$SI modified, a=accessed, c=MFT record changed, b=birth/created; null where the MFT value is 0/missing.",
               "rows": rows, "mean": [round(float(v), 6) for v in mu], "std": [round(float(v), 6) for v in sd],
               "rawRanges": pct, "featureInfo": {f: INFO.get(f, f) for f in feats}, "timeline": tl}
        p = os.path.join(OUT, f"{tag}.json")
        json.dump(out, open(p, "w"), separators=(",", ":"))
        print(tag, "rows", len(rows), "targets", len(tidx), os.path.getsize(p) // 1024, "KB", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or ["img1", "img2", "img3"])
