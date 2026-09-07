# Hash every extracted artefact at time of extraction

import hashlib
import json
import os
import datetime

from config import OUT_DIR, IMAGE_PATH, REPORT_DIR


def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)

    return h.hexdigest()


def build_manifest():
    manifest = {
        "tool": "ForensIQ v1.0",
        "examiner": "[Student Name]",
        "source_image": IMAGE_PATH,
        "extraction_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "artefacts": [],
    }

    for root, _, files in os.walk(OUT_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            stat = os.stat(fpath)

            manifest["artefacts"].append(
                {
                    "path": fpath,
                    "size_b": stat.st_size,
                    "sha256": sha256_file(fpath),
                    "mtime": datetime.datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=datetime.timezone.utc,
                    ).isoformat(),
                }
            )

    out = os.path.join(REPORT_DIR, "chain_of_custody.json")

    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)

    print(
        f"[+] CoC manifest: {len(manifest['artefacts'])} files -> {out}"
    )

    return manifest


manifest = build_manifest()


# Verify the manifest at pipeline completion

def verify_manifest(manifest_path):
    with open(manifest_path) as f:
        manifest = json.load(f)

    passed = 0
    failed = []

    for entry in manifest["artefacts"]:
        if not os.path.exists(entry["path"]):
            failed.append(("MISSING", entry["path"]))
            continue

        if sha256_file(entry["path"]) == entry["sha256"]:
            passed += 1
        else:
            failed.append(("TAMPERED", entry["path"]))

    print("\n[+] Chain of Custody Verification")
    print(f" Passed : {passed}")
    print(f" Failed : {len(failed)}")

    if not failed:
        print(" [✓] All artefacts intact — chain of custody maintained.")
    else:
        for reason, path in failed:
            print(f" [!] {reason}: {path}")

    return len(failed) == 0


verify_manifest(f"{REPORT_DIR}/chain_of_custody.json")