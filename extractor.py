"""
extractor.py
============
ForensIQ Forensic Artifact Extraction Engine
Supports both legacy Windows XP (.evt, MBR) and modern Windows 7/10 (.evtx, GPT).
Extracts MFT filesystem metadata, Windows Event Logs (EVT/EVTX), Prefetch,
and Registry hives (USBSTOR / SYSTEM / SOFTWARE / SAM).
"""

import os
import re
import sys
import json
import struct
import datetime
import traceback
import subprocess

try:
    import pytsk3
except ImportError:
    pytsk3 = None

try:
    import pyewf
except ImportError:
    pyewf = None

try:
    import Evtx.Evtx as evtx_lib
    from lxml import etree
except ImportError:
    evtx_lib = None
    etree = None


class EWFImgInfo(pytsk3.Img_Info if pytsk3 else object):
    """pytsk3 Img_Info adapter for Expert Witness Format (E01) disk images using pyewf."""
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__()

    def close(self):
        try:
            self._ewf_handle.close()
        except Exception:
            pass

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()


from config import (
    IMAGE_PATH,
    PART_OFFSET,
    SECTOR_SIZE,
    OUT_DIR
)

# High-value EVTX channels to prioritize for fast, comprehensive triage
PRIORITY_EVTX_CHANNELS = {
    "security.evtx",
    "system.evtx",
    "application.evtx",
    "microsoft-windows-powershell%4operational.evtx",
    "microsoft-windows-taskscheduler%4operational.evtx",
    "microsoft-windows-terminalservices-localsessionmanager%4operational.evtx",
    "microsoft-windows-codeintegrity%4operational.evtx",
    "microsoft-windows-windows defender%4operational.evtx",
}

SUSPICIOUS_TOOLS = [
    "mimikatz", "pwdump", "cain", "wireshark", "ethereal",
    "tcpdump", "powershell", "cmd", "wscript", "cscript",
    "123wasp", "lookathost", "lookatlan", "netstumbler"
]


class DiskImage:
    """Wraps raw disk image handle and mounted filesystem."""
    def __init__(self, path, offset_sectors=None):
        if not path:
            raise ValueError("No disk image path provided.")

        resolved_path = os.path.abspath(path)
        is_e01 = False

        if os.path.isdir(resolved_path):
            candidates = sorted([
                os.path.join(resolved_path, f) for f in os.listdir(resolved_path)
                if f.lower().endswith((".e01", ".ex01"))
            ])
            if candidates:
                resolved_path = candidates[0]
                is_e01 = True
        elif resolved_path.lower().endswith((".e01", ".ex01")):
            is_e01 = True

        if not os.path.exists(resolved_path):
            raise FileNotFoundError(
                f"Disk image file not found: '{resolved_path}'\n"
                f"    Please pass an existing image path:\n"
                f"      python extractor.py path/to/image.raw\n"
                f"      python run_pipeline.py --image path/to/image.raw\n"
                f"    Or use existing pre-extracted artifacts:\n"
                f"      python run_pipeline.py --skip-extraction"
            )

        if pytsk3 is None:
            raise RuntimeError("pytsk3 is required to open forensic disk images.")

        self.path = resolved_path
        self.ewf_handle = None

        if is_e01:
            if pyewf is None:
                raise RuntimeError(
                    "libewf-python is required to open .E01 disk images directly.\n"
                    "Install via: pip install libewf-python"
                )
            try:
                filenames = pyewf.glob(resolved_path)
            except Exception:
                filenames = [resolved_path]
            if not filenames:
                filenames = [resolved_path]
            print(f"[+] Direct E01 Ingestion: Detected {len(filenames)} segment(s) for '{os.path.basename(resolved_path)}'")
            self.ewf_handle = pyewf.handle()
            self.ewf_handle.open(filenames)
            self.img = EWFImgInfo(self.ewf_handle)
            media_size = self.ewf_handle.get_media_size()
            print(f"[+] Mounted virtual E01 disk: {media_size:,} bytes ({media_size / (1024**3):.2f} GB) — ZERO conversion needed")
        else:
            self.img = pytsk3.Img_Info(resolved_path)

        self.fs = None
        self.offset = None

        # Determine partition offset
        target_offset = PART_OFFSET if offset_sectors is None else offset_sectors

        def _is_os_partition(fs_obj):
            if fs_obj is None:
                return False
            try:
                root_entries = fs_obj.open_dir(path="/")
                for entry in root_entries:
                    ename = entry.info.name.name.decode("utf-8", "ignore").lower()
                    if ename in ["windows", "winnt", "users", "documents and settings"]:
                        return True
            except Exception:
                pass
            return False

        self._is_os_partition = _is_os_partition

        if target_offset and target_offset > 0:
            try:
                candidate_fs = pytsk3.FS_Info(self.img, offset=target_offset * SECTOR_SIZE)
                if _is_os_partition(candidate_fs):
                    self.fs = candidate_fs
                    self.offset = target_offset
                    print(f"[+] Mounted OS partition at specified sector offset {target_offset} ({target_offset * SECTOR_SIZE} bytes)")
                else:
                    print(f"[*] Partition at offset {target_offset} does not contain Windows OS root. Auto-detecting...")
                    self._auto_detect_partition()
            except Exception as e:
                print(f"[!] Failed to mount partition at specified offset {target_offset}: {e}")
                print("[*] Attempting automatic partition detection...")
                self._auto_detect_partition()
        else:
            self._auto_detect_partition()

        if self.fs is None:
            raise RuntimeError(f"Could not open valid NTFS/FAT filesystem in {path}")

        self.root = self.fs.open_dir(path="/")
        print(f"[+] Successfully opened image root: {path}")

    def _auto_detect_partition(self):
        """
        Auto-detect primary OS partition by checking volume info and common candidate offsets:
        - Sector 206848 (Windows 7 / NIST CFReDS Data Leakage PC)
        - Sector 1259520 (Windows 10 GPT / Lone Wolf)
        - Sector 63 (Windows XP MBR)
        - Sector 2048 (Standard MBR partition 1)
        """
        # 1. Try pytsk3 Volume_Info table
        try:
            vol = pytsk3.Volume_Info(self.img)
            for part in vol:
                desc = part.desc.decode("utf-8", "ignore") if isinstance(part.desc, bytes) else str(part.desc)
                # Look for NTFS / Basic Data Partition
                if part.len > 2048 and any(k in desc.lower() for k in ["ntfs", "basic data", "primary"]):
                    try:
                        fs_candidate = pytsk3.FS_Info(self.img, offset=part.start * SECTOR_SIZE)
                        # Verify it has Windows or Users directory
                        test_dir = fs_candidate.open_dir(path="/")
                        for entry in test_dir:
                            ename = entry.info.name.name.decode("utf-8", "ignore").lower()
                            if ename in ["windows", "winnt", "users", "documents and settings"]:
                                self.fs = fs_candidate
                                self.offset = part.start
                                print(f"[+] Auto-detected OS partition: '{desc}' at sector {part.start}")
                                return
                    except Exception:
                        continue
        except Exception:
            pass

        # 2. Try candidate sector list
        candidates = [206848, 1259520, 63, 2048, 0]
        for sec in candidates:
            try:
                fs_candidate = pytsk3.FS_Info(self.img, offset=sec * SECTOR_SIZE)
                test_dir = fs_candidate.open_dir(path="/")
                for entry in test_dir:
                    ename = entry.info.name.name.decode("utf-8", "ignore").lower()
                    if ename in ["windows", "winnt", "users", "documents and settings"]:
                        self.fs = fs_candidate
                        self.offset = sec
                        print(f"[+] Auto-detected valid OS partition at sector offset {sec}")
                        return
            except Exception:
                continue


def ensure_dir(path):
    """Ensure directory exists and return path."""
    os.makedirs(path, exist_ok=True)
    return path


def open_dir_ci(fs, path):
    """
    Open a directory within the filesystem in a case-insensitive manner.
    """
    if not path or path == "/":
        return fs.open_dir(path="/")

    parts = [p for p in path.strip("/").split("/") if p]
    current_dir = fs.open_dir(path="/")

    for part in parts:
        found = False
        target = part.lower()
        for entry in current_dir:
            try:
                name = entry.info.name.name.decode("utf-8", "ignore").lower()
                if name == target and entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR:
                    current_dir = entry.as_directory()
                    found = True
                    break
            except Exception:
                continue
        if not found:
            raise FileNotFoundError(f"Directory not found: {path} (missing component: {part})")

    return current_dir


def extract_file_from_image(disk, img_path):
    """Reads all bytes of a file from the disk image using case-insensitive path resolution."""
    parts = [p for p in img_path.strip("/").split("/") if p]
    if not parts:
        return b""

    # Walk directories down to parent
    parent_dir = open_dir_ci(disk.fs, "/".join(parts[:-1]))
    filename = parts[-1].lower()

    for entry in parent_dir:
        try:
            name = entry.info.name.name.decode("utf-8", "ignore").lower()
            if name == filename and entry.info.meta:
                f = disk.fs.open_meta(entry.info.meta.addr)
                size = f.info.meta.size
                return f.read_random(0, size)
        except Exception:
            continue

    raise FileNotFoundError(f"File not found in disk image: {img_path}")


def save_binary(path, data):
    """Write binary data to file, creating parent directories if needed."""
    ensure_dir(os.path.dirname(path))
    with open(path, "wb") as fh:
        fh.write(data)


def normalize_timestamp(value):
    """
    Robust timestamp normalizer (H-1):
    Handles Windows FILETIME (100ns since 1601), millisecond epochs,
    Unix seconds, datetime objects, and ISO strings, returning ISO-8601 UTC string.
    """
    if value is None or value == "" or value == 0:
        return ""

    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc).isoformat()

    # Attempt numeric conversion
    num_val = None
    if isinstance(value, (int, float)):
        num_val = value
    elif isinstance(value, str):
        try:
            num_val = float(value) if "." in value else int(value)
        except ValueError:
            # Already a datetime string? Try parsing
            try:
                dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.isoformat()
            except Exception:
                return value

    if num_val is not None:
        try:
            # 1. Windows FILETIME (100ns intervals since 1601-01-01)
            # Range: 116444736000000000 (1970) to 200000000000000000 (~2234)
            if 116444736000000000 <= num_val <= 200000000000000000:
                unix_ts = (num_val - 116444736000000000) / 10000000.0
                dt = datetime.datetime.fromtimestamp(unix_ts, tz=datetime.timezone.utc)
                return dt.isoformat()

            # 2. Millisecond epoch (10^12 <= ts < 10^14)
            if 1000000000000 <= num_val < 100000000000000:
                unix_ts = num_val / 1000.0
                dt = datetime.datetime.fromtimestamp(unix_ts, tz=datetime.timezone.utc)
                return dt.isoformat()

            # 3. Standard Unix seconds (10^8 <= ts < 10^12)
            if 100000000 <= num_val < 1000000000000:
                dt = datetime.datetime.fromtimestamp(num_val, tz=datetime.timezone.utc)
                return dt.isoformat()

        except Exception:
            return ""

    return str(value)


def _filetime_to_unix(ft):
    """Convert a Windows FILETIME (100 ns ticks since 1601) to Unix seconds."""
    return int(ft / 10_000_000 - 11644473600) if ft else 0


def _read_fn_times(entry):
    """
    Reads the kernel-maintained $FILE_NAME (0x30) timestamps of an NTFS entry.
    Returns {} when the attribute is unavailable so callers can skip the
    delta_si_fn feature rather than fabricate it.
    """
    try:
        f = entry.as_file()
        for attr in f:
            if attr.info.type != pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME:
                continue
            raw = attr.read_random(0, 48)
            if len(raw) < 48:
                continue
            # $FILE_NAME layout: parent ref (8) | crtime | mtime | ctime | atime (8 each)
            cr, mt = struct.unpack_from("<QQ", raw, 8)
            return {"fn_cr_time": _filetime_to_unix(cr), "fn_m_time": _filetime_to_unix(mt)}
    except Exception:
        pass
    return {}


def extract_mft(disk, out_dir=OUT_DIR):
    """
    Recursively walk filesystem tree and dump MFT records.
    Logs skipped unreadable entries (M-1).
    """
    records = []
    skipped_count = 0
    out_path = os.path.join(out_dir, "mft", "mft_records.json")
    ensure_dir(os.path.dirname(out_path))

    def walk(directory, current_path="/"):
        nonlocal skipped_count
        for entry in directory:
            try:
                name_bytes = entry.info.name.name
                if name_bytes in (b".", b".."):
                    continue

                name_str = name_bytes.decode("utf-8", "replace")
                full_path = current_path + name_str
                meta = entry.info.meta

                rec = {
                    "path": full_path,
                    "inode": int(meta.addr) if meta else -1,
                    "size": int(meta.size) if meta else 0,
                    "type": "dir" if entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR else "file",
                    "m_time": int(meta.mtime) if meta else 0,
                    "a_time": int(meta.atime) if meta else 0,
                    "c_time": int(meta.ctime) if meta else 0,
                    "cr_time": int(meta.crtime) if meta else 0,
                    "is_deleted": bool(meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC) if meta else False
                }
                if meta and rec["type"] == "file":
                    rec.update(_read_fn_times(entry))
                records.append(rec)
                if len(records) % 10000 == 0:
                    print(f"[*] Indexed {len(records):,} MFT filesystem records...", flush=True)

                if rec["type"] == "dir":
                    try:
                        walk(entry.as_directory(), full_path + "/")
                    except Exception:
                        skipped_count += 1
            except Exception:
                skipped_count += 1

    print("[*] Walking MFT filesystem structure...")
    walk(disk.root)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"[+] MFT records extracted: {len(records):,}")
    if skipped_count > 0:
        print(f"[i] Skipped {skipped_count:,} unreadable or inaccessible directory entries (expected on raw images)")

    return records


def extract_evt_files(disk, out_dir=OUT_DIR):
    """Extract legacy Windows XP .Evt files from /WINDOWS/system32/config/"""
    evt_dir = "/WINDOWS/system32/config"
    out_evt = ensure_dir(os.path.join(out_dir, "evtx"))
    inventory = []

    try:
        directory = open_dir_ci(disk.fs, evt_dir)
    except Exception:
        return []

    for entry in directory:
        try:
            name = entry.info.name.name
            if not name.lower().endswith(b".evt"):
                continue

            fname = name.decode("utf-8", "ignore")
            raw = extract_file_from_image(disk, f"{evt_dir}/{fname}")
            outfile = os.path.join(out_evt, fname)
            save_binary(outfile, raw)
            inventory.append({"source": fname, "path": outfile})
        except Exception as e:
            print(f"[!] Could not extract EVT {entry.info.name.name}: {e}")

    with open(os.path.join(out_evt, "evt_inventory.json"), "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    if inventory:
        print(f"[+] Extracted {len(inventory)} legacy EVT files")
    return inventory


def parse_evt_files(out_dir=OUT_DIR):
    """Parse extracted legacy .evt files into structured events."""
    evt_dir = os.path.join(out_dir, "evtx")
    if not os.path.exists(evt_dir):
        return []

    parsed_events = []
    evt_files = [f for f in os.listdir(evt_dir) if f.lower().endswith(".evt")]

    for filename in evt_files:
        filepath = os.path.join(evt_dir, filename)
        try:
            # Try evtexport CLI if installed
            result = subprocess.run(["evtexport", filepath], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                records = re.split(r"\nEvent number\s+:\s+", result.stdout)
                for record in records[1:]:
                    event = {"file": filename, "source_log": filename}
                    m = re.search(r"Creation time\s+:\s+(.*)", record)
                    if m:
                        event["timestamp"] = normalize_timestamp(m.group(1).strip())
                    m = re.search(r"Source name\s+:\s+(.*)", record)
                    if m:
                        event["source"] = m.group(1).strip()
                    m = re.search(r"Event identifier\s+:\s+.*\((\d+)\)", record)
                    if m:
                        event["event_id"] = int(m.group(1))
                    m = re.search(r"Event type\s+:\s+(.*)", record)
                    if m:
                        event["event_type"] = m.group(1).strip()

                    if "timestamp" in event:
                        parsed_events.append(event)
        except Exception:
            pass

    out_file = os.path.join(evt_dir, "parsed_events.json")
    # Save if parsed or if no parsed_events exists yet
    if parsed_events or not os.path.exists(out_file):
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed_events, f, indent=2)

    print(f"[+] Parsed {len(parsed_events)} EVT events")
    return parsed_events


def extract_evtx(disk, out_dir=OUT_DIR):
    """
    Extract and parse modern Windows 7 / 10 .evtx binary XML event logs.
    Includes case-insensitive path lookup and selective priority channel triage.
    """
    evtx_dirs = [
        "/Windows/System32/winevt/Logs",
        "/WINDOWS/system32/winevt/Logs",
        "/Windows/system32/winevt/logs"
    ]
    out_raw = ensure_dir(os.path.join(out_dir, "evtx"))
    parsed_events = []
    log_dir = None

    for d in evtx_dirs:
        try:
            log_dir = open_dir_ci(disk.fs, d)
            break
        except Exception:
            continue

    if log_dir is None:
        return []

    print("[+] Detected modern Windows Event Logs (winevt/Logs)")
    for entry in log_dir:
        try:
            name_bytes = entry.info.name.name
            if not name_bytes.lower().endswith(b".evtx"):
                continue

            fname = name_bytes.decode("utf-8", "ignore")
            lower_fname = fname.lower()

            # Filter by priority triage list if hundreds of channels exist
            if lower_fname not in PRIORITY_EVTX_CHANNELS and not any(p in lower_fname for p in ["security", "system", "powershell"]):
                continue

            raw = extract_file_from_image(disk, f"/Windows/System32/winevt/Logs/{fname}")
            raw_path = os.path.join(out_raw, fname)
            save_binary(raw_path, raw)

            if evtx_lib is not None:
                try:
                    with evtx_lib.Evtx(raw_path) as log:
                        for record in log.records():
                            try:
                                xml_str = record.xml()
                                xml = etree.fromstring(xml_str.encode("utf-8"))
                                ns = "http://schemas.microsoft.com/win/2004/08/events/event"

                                time_node = xml.find(f".//{{{ns}}}TimeCreated")
                                raw_ts = time_node.get("SystemTime") if time_node is not None else ""
                                ts = normalize_timestamp(raw_ts)

                                eid = xml.findtext(f".//{{{ns}}}EventID")
                                computer = xml.findtext(f".//{{{ns}}}Computer")
                                provider_node = xml.find(f".//{{{ns}}}Provider")
                                provider = provider_node.get("Name") if provider_node is not None else ""

                                # Extract EventData key-value pairs
                                data_items = []
                                for dnode in xml.findall(f".//{{{ns}}}EventData/{{{ns}}}Data"):
                                    dname = dnode.get("Name", "")
                                    dval = dnode.text or ""
                                    if dval.strip():
                                        data_items.append(f"{dname}={dval}" if dname else dval)
                                message = "; ".join(data_items[:5])

                                parsed_events.append({
                                    "source": fname,
                                    "source_log": fname,
                                    "event_id": int(eid) if eid and eid.isdigit() else eid,
                                    "timestamp": ts,
                                    "computer": computer or "",
                                    "provider": provider or "",
                                    "message": message
                                })
                            except Exception:
                                continue
                except Exception as e:
                    print(f"[!] Error parsing EVTX {fname}: {e}")

        except Exception:
            continue

    if parsed_events:
        out_file = os.path.join(out_raw, "parsed_events.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed_events, f, indent=2)
        print(f"[+] Extracted and parsed {len(parsed_events):,} EVTX event records")

    return parsed_events


def extract_prefetch(disk, out_dir=OUT_DIR):
    """
    Extracts Prefetch files (.pf) from /WINDOWS/Prefetch.
    Detects Windows 10 MAM compressed format and flags suspicious tools.
    """
    pf_dirs = ["/WINDOWS/Prefetch", "/Windows/Prefetch"]
    out_pf = ensure_dir(os.path.join(out_dir, "prefetch"))
    findings = []
    folder = None

    for d in pf_dirs:
        try:
            folder = open_dir_ci(disk.fs, d)
            break
        except Exception:
            continue

    if folder is None:
        print("[!] Prefetch directory not found on disk")
        return []

    for entry in folder:
        try:
            name = entry.info.name.name
            if not name.lower().endswith(b".pf"):
                continue

            fname = name.decode("utf-8", "ignore")
            # Prefetch files are never >10MB; skip corrupt cluster runs
            if entry.info.meta and entry.info.meta.size > 10 * 1024 * 1024:
                continue

            raw = extract_file_from_image(disk, f"/WINDOWS/Prefetch/{fname}")
            outfile = os.path.join(out_pf, fname)
            save_binary(outfile, raw)

            lower = fname.lower()
            is_mam = raw[:4] == b"MAM\x04"

            findings.append({
                "name": fname,
                "path": outfile,
                "size": int(entry.info.meta.size) if entry.info.meta else len(raw),
                "m_time": int(entry.info.meta.mtime) if entry.info.meta else 0,
                "is_compressed_mam": is_mam,
                "is_suspicious": any(t in lower for t in SUSPICIOUS_TOOLS),
                "matched_tools": [t for t in SUSPICIOUS_TOOLS if t in lower]
            })
        except Exception:
            continue

    with open(os.path.join(out_pf, "prefetch_list.json"), "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print(f"[+] Prefetch files extracted: {len(findings)}")
    return findings


def extract_usb_and_registry(disk, out_dir=OUT_DIR):
    """
    Extracts core registry hives (SYSTEM, SOFTWARE, SAM, SECURITY, DEFAULT)
    and extracts USB connection evidence (USBSTOR).
    """
    hive_dirs = ["/WINDOWS/system32/config", "/Windows/System32/config"]
    reg_dir = ensure_dir(os.path.join(out_dir, "registry"))
    usb_dir = ensure_dir(os.path.join(out_dir, "usb"))

    hives = ["SYSTEM", "SOFTWARE", "SAM", "SECURITY", "DEFAULT"]
    extracted = []

    for hive in hives:
        for hd in hive_dirs:
            try:
                raw = extract_file_from_image(disk, f"{hd}/{hive}")
                dest = os.path.join(reg_dir, hive)
                save_binary(dest, raw)
                extracted.append(dest)

                # Keep a direct copy of SYSTEM in usb/ for USBSTOR analysis
                if hive == "SYSTEM":
                    save_binary(os.path.join(usb_dir, "SYSTEM"), raw)
                break
            except Exception:
                continue

    # Search for USB device footprints inside SYSTEM hive
    usb_info_path = os.path.join(usb_dir, "usb_devices.txt")
    system_hive_path = os.path.join(usb_dir, "SYSTEM")
    usb_entries = []

    if os.path.exists(system_hive_path):
        try:
            with open(system_hive_path, "rb") as f:
                content = f.read()
                # Carve USBSTOR string signatures (Disk&Ven_, Removable, etc.)
                matches = re.findall(rb"Disk&Ven_([a-zA-Z0-9_\-\.\&]+)", content)
                for m in set(matches):
                    dev_name = m.decode("utf-8", "ignore")
                    usb_entries.append(f"USB Device: Disk&Ven_{dev_name}")

                serials = re.findall(rb"([A-Za-z0-9]{12,24})&[0-9]", content)
                for s in set(serials[:5]):
                    usb_entries.append(f"Device Serial Signature: {s.decode('utf-8', 'ignore')}")
        except Exception:
            pass

    with open(usb_info_path, "w", encoding="utf-8") as f:
        if usb_entries:
            f.write("\n".join(usb_entries) + "\n")
        else:
            f.write("SYSTEM hive extracted. Query USBSTOR via python-registry or regripper.\n")

    print(f"[+] Registry hives extracted: {len(extracted)} (USB evidence in {usb_dir})")
    return extracted


def export_summary(out_dir=OUT_DIR):
    """Write overall extraction summary."""
    summary = {
        "mft_records": os.path.exists(os.path.join(out_dir, "mft", "mft_records.json")),
        "events_evt": os.path.exists(os.path.join(out_dir, "evtx", "parsed_events.json")),
        "prefetch": os.path.exists(os.path.join(out_dir, "prefetch", "prefetch_list.json")),
        "registry": os.path.exists(os.path.join(out_dir, "registry")),
        "usb": os.path.exists(os.path.join(out_dir, "usb", "SYSTEM"))
    }
    with open(os.path.join(out_dir, "artifact_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("[+] Artifact summary written to artifacts/artifact_summary.json")


def run_all(image_path=IMAGE_PATH, offset=PART_OFFSET, out_dir=OUT_DIR):
    """Full extraction workflow."""
    print("=" * 65)
    print("      ForensIQ Artifact Extraction Engine")
    print("=" * 65)
    print(f"[*] Target Image : {image_path}")
    print(f"[*] Target Offset: {offset}")

    if not os.path.exists(image_path):
        print(f"\n[!] Error: Disk image file does not exist at:")
        print(f"    '{image_path}'")
        print("\n[*] Options to proceed:")
        print("    1. Direct zero-conversion ingestion (supported for .E01, .dd, .raw, .001):")
        print('       python extractor.py "Lone Wolf/LoneWolf.E01"')
        print('       python run_pipeline.py --image "Lone Wolf/LoneWolf.E01"')
        print("    2. If you already have extracted artifacts in artifacts/:")
        print("       python run_pipeline.py --skip-extraction")
        print("=" * 65)
        return False

    disk = DiskImage(image_path, offset)

    extract_mft(disk, out_dir=out_dir)

    # Try modern EVTX first; if none found, fallback to legacy EVT
    evtx_events = extract_evtx(disk, out_dir=out_dir)
    if not evtx_events:
        extract_evt_files(disk, out_dir=out_dir)
        parse_evt_files(out_dir=out_dir)

    extract_prefetch(disk, out_dir=out_dir)
    extract_usb_and_registry(disk, out_dir=out_dir)
    export_summary(out_dir=out_dir)

    print("=" * 65)
    print("      Artifact Extraction Complete")
    print("=" * 65)
    return True


if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else IMAGE_PATH
    target_off = PART_OFFSET
    if len(sys.argv) > 2:
        try:
            target_off = int(sys.argv[2])
        except ValueError:
            target_off = 0
    run_all(target_img, target_off)
