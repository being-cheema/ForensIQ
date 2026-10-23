"""
image_utils.py
==============
Utilities for handling, detecting, verifying, and concatenating
split forensic disk images (e.g. .001, .002, ... or split raw chunks).
Supports NIST CFReDS Data Leakage PC images (.001-.004) and Schardt (.001-.008).
"""

import os
import re
import sys
import glob
import hashlib
import argparse


def find_split_segments(first_segment_path):
    """
    Given the first segment of a split image (e.g., 'image.001' or 'image.raw.001'),
    find all matching sequential parts in order.
    Returns a sorted list of absolute paths.
    """
    first_path = os.path.abspath(first_segment_path)
    if not os.path.exists(first_path):
        return []

    dirname = os.path.dirname(first_path)
    basename = os.path.basename(first_path)

    # Match common split formats: .001, .raw.001, .dd.001, etc.
    match = re.search(r"^(.*?)(?:\.)(\d{3,4})$", basename, re.IGNORECASE)
    if not match:
        return [first_path]

    prefix = match.group(1)
    digits = len(match.group(2))

    # Look for all prefix.NNN files
    candidates = []
    index = 1
    while True:
        num_str = str(index).zfill(digits)
        candidate_name = f"{prefix}.{num_str}"
        candidate_path = os.path.join(dirname, candidate_name)

        if not os.path.exists(candidate_path):
            # Try uppercase/lowercase match
            found = False
            for f in os.listdir(dirname):
                if f.lower() == candidate_name.lower():
                    candidates.append(os.path.join(dirname, f))
                    found = True
                    break
            if not found:
                break
        else:
            candidates.append(candidate_path)
        index += 1

    return candidates


def hash_file(file_path, algorithm="sha256", buffer_size=1048576):
    """Compute cryptographic hash of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(buffer_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def merge_split_images(first_segment_path, output_path=None, buffer_size=4194304):
    """
    Concatenates split raw segments into a single raw disk image (.dd / .raw).
    
    Parameters:
        first_segment_path: Path to the first split chunk (e.g. images/SCHARDT.001)
        output_path: Path for the merged output. Defaults to prefix + '_COMPLETE.dd'
        buffer_size: Read/write buffer size in bytes (default 4MB)
    
    Returns:
        output_path on success, or None on failure.
    """
    segments = find_split_segments(first_segment_path)
    if not segments:
        print(f"[!] No split image segments found for: {first_segment_path}")
        return None

    if len(segments) == 1 and not re.search(r"\.\d{3}$", segments[0]):
        print(f"[i] Single non-split image detected: {segments[0]}")
        return segments[0]

    if not output_path:
        base_dir = os.path.dirname(segments[0])
        match = re.search(r"^(.*?)(?:\.)(\d{3,4})$", os.path.basename(segments[0]))
        prefix = match.group(1) if match else "merged"
        output_path = os.path.join(base_dir, f"{prefix}_COMPLETE.dd")

    if os.path.exists(output_path):
        print(f"[+] Merged image already exists: {output_path}")
        return output_path

    print(f"[+] Found {len(segments)} split segment(s):")
    total_size = sum(os.path.getsize(s) for s in segments)
    for s in segments:
        print(f"    - {os.path.basename(s)} ({os.path.getsize(s):,} bytes)")
    print(f"[+] Assembling into: {output_path} (Expected size: {total_size:,} bytes)")

    written_bytes = 0
    with open(output_path, "wb") as out_f:
        for seg in segments:
            seg_name = os.path.basename(seg)
            with open(seg, "rb") as in_f:
                while chunk := in_f.read(buffer_size):
                    out_f.write(chunk)
                    written_bytes += len(chunk)
                    progress = (written_bytes / total_size) * 100
                    sys.stdout.write(f"\r[+] Progress: {progress:.1f}% ({written_bytes:,} / {total_size:,} bytes)")
                    sys.stdout.flush()

    print(f"\n[✓] Successfully assembled {len(segments)} segments into {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="ForensIQ Split Image Assembly Tool")
    parser.add_argument("--input", "-i", required=True, help="Path to first split segment (e.g. data_leakage_pc.001)")
    parser.add_argument("--output", "-o", default=None, help="Output path for assembled raw image")
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 hash of assembled image")
    
    args = parser.parse_args()
    result = merge_split_images(args.input, args.output)
    if result and args.hash:
        print(f"[+] Computing SHA-256 for {result}...")
        sha = hash_file(result)
        print(f"[+] SHA-256: {sha}")


if __name__ == "__main__":
    main()
