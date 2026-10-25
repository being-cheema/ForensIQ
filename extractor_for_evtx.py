
import os
import json

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
    def __init__(self, path, offset_sectors):
        self.img = pytsk3.Img_Info(path)

        self.fs = pytsk3.FS_Info(
            self.img,
            offset=offset_sectors * SECTOR_SIZE
        )

        self.root = self.fs.open_dir(path="/")

        print(f"[+] Opened {path}")



# Top-level disk initialization removed for import safety (Milestone 1, §11.1)



def extract_file_from_image(disk, img_path):
    f = disk.fs.open(img_path)
    size = f.info.meta.size
    return f.read_random(0, size)


def extract_evtx(disk, out_dir=OUT_DIR):
    evtx_dir = "/WINDOWS/system32/winevt/Logs"
    events = []

    out_raw = os.path.join(out_dir, "evtx")
    os.makedirs(out_raw, exist_ok=True)

    try:
        log_dir = disk.fs.open_dir(path=evtx_dir)
    except Exception:
        print("[!] Event log dir not found — check path case")
        return []

    for entry in log_dir:
        name = entry.info.name.name

        if not name.endswith(b".evtx"):
            continue

        fname = name.decode("utf-8")

        raw = extract_file_from_image(
            disk,
            f"{evtx_dir}/{fname}"
        )

        raw_path = os.path.join(out_raw, fname)

        with open(raw_path, "wb") as fh:
            fh.write(raw)

        with evtx_lib.Evtx(raw_path) as log:
            for record in log.records():
                try:
                    xml = etree.fromstring(record.xml())
                    ns = "http://schemas.microsoft.com/win/2004/08/events/event"

                    time_node = xml.find(f".//{{{ns}}}TimeCreated")
                    timestamp = (
                        time_node.get("SystemTime")
                        if time_node is not None
                        else ""
                    )

                    events.append({
                        "source": fname,
                        "event_id": xml.findtext(
                            f".//{{{ns}}}EventID"
                        ),
                        "timestamp": timestamp,
                        "computer": xml.findtext(
                            f".//{{{ns}}}Computer"
                        ),
                    })

                except Exception:
                    pass

    with open(
        os.path.join(out_raw, "parsed_events.json"),
        "w"
    ) as f:
        json.dump(events, f, indent=2)

    print(f"[+] EVTX: {len(events)} events")

    return events




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
    print(f"[*] Starting modern EVTX extraction from {IMAGE_PATH}")
    disk = DiskImage(IMAGE_PATH, PART_OFFSET)
    extract_evtx(disk)
    extract_mft(disk)
    extract_prefetch(disk)
    extract_usb_history(disk)
    print("[+] EVTX extraction complete.")


if __name__ == "__main__":
    main()

