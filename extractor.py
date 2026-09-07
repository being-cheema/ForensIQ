
"""
extractor_for_evt.py
SECTION 1 of 3
Imports, configuration, DiskImage class, helper utilities,
EVT extraction and parsing.
"""

import os
import json
import re
import subprocess
import traceback

import pytsk3
from lxml import etree
import Evtx.Evtx as evtx_lib

from config import (
    IMAGE_PATH,
    PART_OFFSET,
    SECTOR_SIZE,
    OUT_DIR
)


class DiskImage:
    def __init__(self, path, offset_sectors):
        self.img = pytsk3.Img_Info(path)
        self.fs = pytsk3.FS_Info(
            self.img,
            offset=offset_sectors * SECTOR_SIZE
        )
        self.root = self.fs.open_dir(path="/")
        print(f"[+] Opened image: {path}")


disk = DiskImage(IMAGE_PATH, PART_OFFSET)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def extract_file_from_image(disk, img_path):
    f = disk.fs.open(img_path)
    size = f.info.meta.size
    return f.read_random(0, size)


def save_binary(path, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "wb") as fh:
        fh.write(data)


def extract_evt_files(disk, out_dir=OUT_DIR):
    evt_dir = "/WINDOWS/system32/config"
    out_evt = ensure_dir(os.path.join(out_dir, "evtx"))
    events = []

    try:
        directory = disk.fs.open_dir(path=evt_dir)
    except Exception:
        traceback.print_exc()
        return []

    for entry in directory:
        try:
            name = entry.info.name.name

            if not name.lower().endswith(b".evt"):
                continue

            fname = name.decode(errors="ignore")

            raw = extract_file_from_image(
                disk,
                f"{evt_dir}/{fname}"
            )

            outfile = os.path.join(out_evt, fname)
            save_binary(outfile, raw)

            events.append({
                "source": fname,
                "path": outfile
            })

        except Exception as e:
            print(f"[!] {e}")

    with open(
        os.path.join(out_evt, "evt_inventory.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(events, f, indent=2)

    print(f"[+] Extracted {len(events)} EVT files")
    return events


def parse_evt_files():
    evt_dir = os.path.join(OUT_DIR, "evtx")
    parsed_events = []

    for filename in os.listdir(evt_dir):

        if not filename.lower().endswith(".evt"):
            continue

        filepath = os.path.join(evt_dir, filename)

        print(f"[+] Parsing {filename}")

        try:
            result = subprocess.run(
                ["evtexport", filepath],
                capture_output=True,
                text=True
            )

            records = re.split(
                r"\nEvent number\s+:\s+",
                result.stdout
            )

            for record in records[1:]:

                event = {"file": filename}

                m = re.search(
                    r"Creation time\s+:\s+(.*)",
                    record
                )
                if m:
                    event["timestamp"] = m.group(1).strip()

                m = re.search(
                    r"Source name\s+:\s+(.*)",
                    record
                )
                if m:
                    event["source"] = m.group(1).strip()

                m = re.search(
                    r"Event identifier\s+:\s+.*\((\d+)\)",
                    record
                )
                if m:
                    event["event_id"] = int(m.group(1))

                m = re.search(
                    r"Event type\s+:\s+(.*)",
                    record
                )
                if m:
                    event["event_type"] = m.group(1).strip()

                if "timestamp" in event:
                    parsed_events.append(event)

        except Exception as e:
            print(f"[!] Failed {filename}: {e}")

    with open(
        os.path.join(evt_dir, "parsed_events.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(parsed_events, f, indent=2)

    print(f"[+] Parsed {len(parsed_events)} events")

    return parsed_events


if __name__ == "__main__":
    extract_evt_files(disk)
    parse_evt_files()


"""
extractor_for_evt.py
SECTION 2 of 3
Recursive MFT extraction and Prefetch extraction.
"""

import os,json,pytsk3
from config import OUT_DIR

def extract_mft(disk,out_dir=OUT_DIR):
    records=[]
    out_path=os.path.join(out_dir,"mft","mft_records.json")
    os.makedirs(os.path.dirname(out_path),exist_ok=True)

    def walk(directory,path="/"):
        for entry in directory:
            name=entry.info.name.name
            if name in (b".",b".."):
                continue
            try:
                meta=entry.info.meta
                rec={
                    "path":path+name.decode("utf-8","replace"),
                    "inode":int(meta.addr) if meta else -1,
                    "size":int(meta.size) if meta else 0,
                    "type":"dir" if entry.info.name.type==pytsk3.TSK_FS_NAME_TYPE_DIR else "file",
                    "m_time":int(meta.mtime) if meta else 0,
                    "a_time":int(meta.atime) if meta else 0,
                    "c_time":int(meta.ctime) if meta else 0,
                    "cr_time":int(meta.crtime) if meta else 0,
                    "is_deleted":bool(meta.flags==pytsk3.TSK_FS_META_FLAG_UNALLOC) if meta else False
                }
                records.append(rec)
                if rec["type"]=="dir":
                    walk(entry.as_directory(),rec["path"]+"/")
            except Exception:
                pass
    walk(disk.root)
    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(records,f,indent=2)
    print(f"[+] MFT records: {len(records)}")
    return records

SUSPICIOUS_TOOLS=[
"mimikatz","pwdump","cain","wireshark","ethereal",
"tcpdump","powershell","cmd","wscript","cscript"
]

def extract_prefetch(disk,out_dir=OUT_DIR):
    pf_dir="/WINDOWS/Prefetch"
    out_pf=os.path.join(out_dir,"prefetch")
    os.makedirs(out_pf,exist_ok=True)
    findings=[]
    try:
        folder=disk.fs.open_dir(path=pf_dir)
    except Exception:
        print("[!] Prefetch directory missing")
        return []
    for entry in folder:
        name=entry.info.name.name
        if not name.endswith(b".pf"):
            continue
        fname=name.decode("utf-8","ignore")
        raw=extract_file_from_image(disk,f"{pf_dir}/{fname}")
        outfile=os.path.join(out_pf,fname)
        with open(outfile,"wb") as f:
            f.write(raw)
        lower=fname.lower()
        findings.append({
            "name":fname,
            "path":outfile,
            "size":int(entry.info.meta.size),
            "m_time":int(entry.info.meta.mtime),
            "is_suspicious":any(t in lower for t in SUSPICIOUS_TOOLS),
            "matched_tools":[t for t in SUSPICIOUS_TOOLS if t in lower]
        })
    with open(os.path.join(out_pf,"prefetch_list.json"),"w",encoding="utf-8") as f:
        json.dump(findings,f,indent=2)
    print(f"[+] Prefetch files: {len(findings)}")
    return findings


"""
extractor_for_evt.py
SECTION 3 of 3
USB extraction, registry hive extraction, helper parsers,
and orchestration.
"""

import os
import json
import subprocess
from config import OUT_DIR


def extract_usb_history(disk, out_dir=OUT_DIR):
    """
    Extract SYSTEM hive for USB analysis.
    """
    hive = "/WINDOWS/system32/config/SYSTEM"

    usb_dir = os.path.join(out_dir, "usb")
    os.makedirs(usb_dir, exist_ok=True)

    dest = os.path.join(usb_dir, "SYSTEM")

    try:
        raw = extract_file_from_image(disk, hive)

        with open(dest, "wb") as fh:
            fh.write(raw)

        print(f"[+] SYSTEM hive saved to {dest}")

    except Exception as e:
        print(f"[!] Failed extracting SYSTEM hive: {e}")

    return dest


def extract_registry_hives(disk, out_dir=OUT_DIR):
    """
    Extract important registry hives for later parsing.
    """

    hive_names = [
        "SYSTEM",
        "SOFTWARE",
        "SAM",
        "SECURITY",
        "DEFAULT"
    ]

    reg_dir = os.path.join(out_dir, "registry")
    os.makedirs(reg_dir, exist_ok=True)

    extracted = []

    for hive in hive_names:

        image_path = f"/WINDOWS/system32/config/{hive}"

        try:
            raw = extract_file_from_image(
                disk,
                image_path
            )

            outfile = os.path.join(reg_dir, hive)

            with open(outfile, "wb") as fh:
                fh.write(raw)

            extracted.append(outfile)

            print(f"[+] Extracted {hive}")

        except Exception:
            print(f"[!] Could not extract {hive}")

    return extracted


def generate_registry_report(out_dir=OUT_DIR):
    """
    Optional helper using RegRipper if installed.
    """

    reg_dir = os.path.join(out_dir, "registry")

    if not os.path.exists(reg_dir):
        return

    plugins = {
        "SYSTEM": ["services", "usb", "timezone"],
        "SOFTWARE": ["run", "uninstall"],
        "SAM": ["samparse"]
    }

    for hive, plist in plugins.items():

        hive_path = os.path.join(reg_dir, hive)

        if not os.path.exists(hive_path):
            continue

        for plugin in plist:

            output = os.path.join(
                reg_dir,
                f"{hive}_{plugin}.txt"
            )

            try:

                subprocess.run(
                    [
                        "rip.exe",
                        "-r",
                        hive_path,
                        "-p",
                        plugin
                    ],
                    stdout=open(output, "w"),
                    stderr=subprocess.DEVNULL
                )

                print(f"[+] {plugin} parsed")

            except Exception:
                pass


def export_summary():

    summary = {
        "mft_records":
            os.path.exists(
                os.path.join(
                    OUT_DIR,
                    "mft",
                    "mft_records.json"
                )
            ),
        "events":
            os.path.exists(
                os.path.join(
                    OUT_DIR,
                    "evtx",
                    "parsed_events.json"
                )
            ),
        "prefetch":
            os.path.exists(
                os.path.join(
                    OUT_DIR,
                    "prefetch",
                    "prefetch_list.json"
                )
            ),
        "registry":
            os.path.exists(
                os.path.join(
                    OUT_DIR,
                    "registry"
                )
            ),
        "usb":
            os.path.exists(
                os.path.join(
                    OUT_DIR,
                    "usb",
                    "SYSTEM"
                )
            )
    }

    with open(
        os.path.join(
            OUT_DIR,
            "artifact_summary.json"
        ),
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(summary, f, indent=2)

    print("[+] Artifact summary written")


def run_all():

    print("=" * 60)
    print(" ForensIQ Extraction Pipeline ")
    print("=" * 60)

    extract_evt_files(disk)

    parse_evt_files()

    extract_mft(disk)

    extract_prefetch(disk)

    extract_usb_history(disk)

    extract_registry_hives(disk)

    generate_registry_report()

    export_summary()

    print("=" * 60)
    print(" Extraction Complete ")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
