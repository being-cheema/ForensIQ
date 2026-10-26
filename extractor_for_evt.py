
import os
import json
import re
import subprocess

try:
    import pytsk3
except ImportError:
    pytsk3 = None

try:
    import Evtx.Evtx as evtx_lib
    from lxml import etree
except ImportError:
    evtx_lib = None
    etree = None

from config import (
    IMAGE_PATH,
    PART_OFFSET,
    SECTOR_SIZE,
    OUT_DIR
)


class DiskImage:
    def __init__(self, path, offset_sectors=None):
        if pytsk3 is None:
            raise RuntimeError("pytsk3 is required to open disk images.")
        self.img = pytsk3.Img_Info(path)
        self.fs = None
        self.offset = None

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

        if target_offset and target_offset > 0:
            try:
                candidate_fs = pytsk3.FS_Info(self.img, offset=target_offset * SECTOR_SIZE)
                if _is_os_partition(candidate_fs):
                    self.fs = candidate_fs
                    self.offset = target_offset
            except Exception:
                pass

        if self.fs is None:
            candidates = [63, 206848, 1259520, 2048, 0]
            try:
                vol = pytsk3.Volume_Info(self.img)
                for part in vol:
                    if part.len > 2048:
                        try:
                            c_fs = pytsk3.FS_Info(self.img, offset=part.start * SECTOR_SIZE)
                            if _is_os_partition(c_fs):
                                self.fs = c_fs
                                self.offset = part.start
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            if self.fs is None:
                for sec in candidates:
                    try:
                        c_fs = pytsk3.FS_Info(self.img, offset=sec * SECTOR_SIZE)
                        if _is_os_partition(c_fs):
                            self.fs = c_fs
                            self.offset = sec
                            break
                    except Exception:
                        continue

        if self.fs is None:
            raise RuntimeError(f"Could not open valid OS filesystem in {path}")

        self.root = self.fs.open_dir(path="/")
        print(f"[+] Opened {path} at sector offset {self.offset}")



# Top-level disk initialization removed for import safety (Milestone 1, §11.1)



def extract_file_from_image(disk, img_path):
    f = disk.fs.open(img_path)
    size = f.info.meta.size
    return f.read_random(0, size)



def extract_evtx(disk, out_dir=OUT_DIR):
    evtx_dir = "/WINDOWS/system32/config"
    events = []

    out_raw = os.path.join(out_dir, "evtx")
    os.makedirs(out_raw, exist_ok=True)

    try:
        log_dir = disk.fs.open_dir(path=evtx_dir)
    
    except Exception as e:
        import traceback
        print(f"[!] Failed opening {evtx_dir}: {e}")
        traceback.print_exc()

    for entry in log_dir:
        try:
            name = entry.info.name.name

            if not name.lower().endswith(b".evt"):
                continue

            fname = name.decode("utf-8")

            raw = extract_file_from_image(
                disk,
                f"{evtx_dir}/{fname}"
            )

            raw_path = os.path.join(out_raw, fname)

            with open(raw_path, "wb") as fh:
                fh.write(raw)

            events.append({
                "source": fname,
                "path": raw_path
            })

        except Exception as e:
            print(f"[!] Error processing entry: {e}")

    with open(
        os.path.join(out_raw, "parsed_events.json"),
        "w"
    ) as f:
        json.dump(events, f, indent=2)

    print(f"[+] EVT files extracted: {len(events)}")

    return events



def parse_evt_files():
    evt_dir = os.path.join(OUT_DIR, "evtx")
    parsed_events = []

    for filename in os.listdir(evt_dir):

        if not filename.lower().endswith(".evt"):
            continue

        filepath = os.path.join(evt_dir, filename)

        try:
            print(f"[+] Parsing {filename}")

            result = subprocess.run(
                ["evtexport", filepath],
                capture_output=True,
                text=True
            )

            output = result.stdout

            records = re.split(
                r"\nEvent number\s+:\s+",
                output
            )

            for record in records[1:]:

                event = {}

                event_num_match = re.match(
                    r"(\d+)",
                    record
                )

                if event_num_match:
                    event["event_number"] = int(
                        event_num_match.group(1)
                    )

                creation_match = re.search(
                    r"Creation time\s+:\s+(.*)",
                    record
                )

                if creation_match:
                    event["timestamp"] = (
                        creation_match.group(1).strip()
                    )

                source_match = re.search(
                    r"Source name\s+:\s+(.*)",
                    record
                )

                if source_match:
                    event["source"] = (
                        source_match.group(1).strip()
                    )

                computer_match = re.search(
                    r"Computer name\s+:\s+(.*)",
                    record
                )

                if computer_match:
                    event["computer"] = (
                        computer_match.group(1).strip()
                    )

                eventid_match = re.search(
                    r"Event identifier\s+:\s+.*\((\d+)\)",
                    record
                )

                if eventid_match:
                    event["event_id"] = int(
                        eventid_match.group(1)
                    )

                type_match = re.search(
                    r"Event type\s+:\s+(.*)",
                    record
                )

                if type_match:
                    event["event_type"] = (
                        type_match.group(1).strip()
                    )

                event["file"] = filename

                if "timestamp" in event:
                    parsed_events.append(event)

        except Exception as e:
            print(f"[!] Failed: {filename}: {e}")

    out_path = os.path.join(
        evt_dir,
        "parsed_events.json"
    )

    with open(out_path, "w") as f:
        json.dump(parsed_events, f, indent=2)

    print(
        f"[+] Parsed {len(parsed_events)} events"
    )

    return parsed_events


def extract_mft(disk, out_dir=OUT_DIR):
    records = []

    out_path = os.path.join(
        out_dir,
        "mft",
        "mft_records.json"
    )

    def walk_dir(directory, path="/"):
        for entry in directory:
            name = entry.info.name.name

            if name in [b".", b".."]:
                continue

            try:
                meta = entry.info.meta

                record = {
                    "path": path + name.decode(
                        "utf-8",
                        errors="replace"
                    ),
                    "inode": int(meta.addr) if meta else -1,
                    "size": int(meta.size) if meta else 0,
                    "type": (
                        "dir"
                        if entry.info.name.type
                        == pytsk3.TSK_FS_NAME_TYPE_DIR
                        else "file"
                    ),
                    "m_time": int(meta.mtime) if meta else 0,
                    "a_time": int(meta.atime) if meta else 0,
                    "c_time": int(meta.ctime) if meta else 0,
                    "cr_time": int(meta.crtime) if meta else 0,
                    "is_deleted": (
                        bool(meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC)
                        if meta else False
                    ),
                }

                records.append(record)

                if record["type"] == "dir":
                    walk_dir(
                        entry.as_directory(),
                        path
                        + name.decode(
                            "utf-8",
                            errors="replace"
                        )
                        + "/"
                    )

            except Exception:
                pass

    walk_dir(disk.root)

    os.makedirs(
        os.path.dirname(out_path),
        exist_ok=True
    )

    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"[+] MFT: {len(records)} records")

    return records




def extract_prefetch(disk, out_dir=OUT_DIR):
    pf_dir = "/WINDOWS/Prefetch"
    results = []

    out_raw = os.path.join(out_dir, "prefetch")
    os.makedirs(out_raw, exist_ok=True)

    try:
        pf_folder = disk.fs.open_dir(path=pf_dir)

    except Exception:
        print("[!] Prefetch directory not found")
        return []

    for entry in pf_folder:
        name = entry.info.name.name

        if not name.endswith(b".pf"):
            continue

        fname = name.decode("utf-8")

        raw = extract_file_from_image(
            disk,
            f"{pf_dir}/{fname}"
        )

        path = os.path.join(out_raw, fname)

        with open(path, "wb") as fh:
            fh.write(raw)

        meta = entry.info.meta

        results.append({
            "name": fname,
            "size": int(meta.size),
            "m_time": int(meta.mtime),
            "path": path
        })

    with open(
        os.path.join(out_raw, "prefetch_list.json"),
        "w"
    ) as f:
        json.dump(results, f, indent=2)

    print(f"[+] Prefetch: {len(results)} files")

    return results


def extract_usb_history(disk, out_dir=OUT_DIR):
    hive = "/WINDOWS/system32/config/SYSTEM"

    dest = os.path.join(
        out_dir,
        "usb",
        "SYSTEM"
    )

    os.makedirs(
        os.path.dirname(dest),
        exist_ok=True
    )

    raw = extract_file_from_image(
        disk,
        hive
    )

    with open(dest, "wb") as fh:
        fh.write(raw)

    print(f"[+] SYSTEM hive extracted to {dest}")
    print(
        "[+] Next: regripper -r artifacts/usb/SYSTEM "
        "-p usbstor > usb.txt"
    )

    return dest


def main():
    print(f"[*] Starting legacy EVT extraction from {IMAGE_PATH}")
    disk = DiskImage(IMAGE_PATH, PART_OFFSET)
    extract_evtx(disk)
    parse_evt_files()
    extract_mft(disk)
    extract_prefetch(disk)
    extract_usb_history(disk)
    print("[+] EVT extraction complete.")


if __name__ == "__main__":
    main()

