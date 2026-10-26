"""
chain_of_custody.py
===================
ForensIQ Cryptographic Chain of Custody & Evidence Verification
Computes SHA-256 hashes of all extracted forensic artifacts at extraction time
and verifies manifest integrity across the full analysis lifecycle.
"""

import os
import json
import hashlib
import datetime
from config import OUT_DIR, IMAGE_PATH, REPORT_DIR


def sha256_file(path):
    """Compute SHA-256 hash in 64KB stream chunks."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def build_manifest(out_dir=OUT_DIR, report_dir=REPORT_DIR, source_image=IMAGE_PATH):
    """Walks the artifacts directory and hashes every extracted file."""
    manifest = {
        "tool": "ForensIQ v1.0",
        "examiner": "Automated Digital Forensics Pipeline",
        "source_image": source_image,
        "extraction_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "artefacts": [],
    }

    if not os.path.exists(out_dir):
        print(f"[!] Artifacts directory {out_dir} does not exist.")
        return manifest

    for root, _, files in os.walk(out_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                stat = os.stat(fpath)
                manifest["artefacts"].append({
                    "path": fpath,
                    "size_b": stat.st_size,
                    "sha256": sha256_file(fpath),
                    "mtime": datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat(),
                })
            except Exception:
                continue

    os.makedirs(report_dir, exist_ok=True)
    manifest_path = os.path.join(report_dir, "chain_of_custody.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] CoC manifest generated: {len(manifest['artefacts'])} artifacts hashed -> {manifest_path}")
    return manifest


def verify_manifest(manifest_path=None):
    """Verifies that extracted artifacts have not been modified or corrupted."""
    if manifest_path is None:
        manifest_path = os.path.join(REPORT_DIR, "chain_of_custody.json")

    if not os.path.exists(manifest_path):
        print(f"[!] Manifest not found at {manifest_path}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    passed = 0
    failed = []

    for entry in manifest.get("artefacts", []):
        fpath = entry.get("path", "")
        expected_hash = entry.get("sha256", "")

        if not os.path.exists(fpath):
            failed.append(("MISSING", fpath))
            continue

        actual_hash = sha256_file(fpath)
        if actual_hash == expected_hash:
            passed += 1
        else:
            failed.append(("TAMPERED", fpath))

    print("\n[+] Chain of Custody Integrity Verification:")
    print(f"    - Passed: {passed}")
    print(f"    - Failed: {len(failed)}")

    if not failed:
        print("    [+] All artifacts intact - cryptographic integrity verified.")
    else:
        for reason, path in failed:
            print(f"    [!] {reason}: {path}")

    return len(failed) == 0


def main():
    manifest = build_manifest()
    manifest_path = os.path.join(REPORT_DIR, "chain_of_custody.json")
    verify_manifest(manifest_path)


if __name__ == "__main__":
    main()