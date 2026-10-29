"""
remediation_v2.py
=================
Evidence-based containment advice for the LIVE environment a disk image came from.

Inputs  : the final feature set (19 features), scored by Isolation Forest (seed 42); indicators are computed from the
          paths and raw times of the flagged files only (trust_eval indicator regexes). Ground truth is never read.
          runs/{img}/artifacts/registry/SOFTWARE  (OS detection), runs/{img}/artifacts/usb/usb_devices.txt (context only)
Operating point: Isolation Forest, 19 features, seed 42, 20% review budget (headline) and 15%.
Outputs : reports/remediation_v2/{img}/playbook.md, per-recommendation .cmd (XP) / .ps1 (Win7, Win10) scripts,
          reports/remediation_v2/AUDIT.md, web/src/data/remediation.json

Nothing here is meant to run against seized evidence (ISO/IEC 27037). Every recommendation is advice for the live
environment, needs human approval, and every system-changing command is commented out by default.
The old remediation.py is untouched; this module only imports its trigger logic to document why it was wrong.
"""
import os
import re
import json
import struct
from collections import OrderedDict

import numpy as np
import pandas as pd

os.environ.setdefault("FORENSIQ_FEATURE_SET", "final")   # 19 features: 17 clean + 2 burst
import multimodel_eval as M            # noqa: E402
import study_v3_common as S            # noqa: E402
import trust_eval as T                 # noqa: E402  (indicator regexes and the timestomp test only)

BASE = os.path.dirname(os.path.abspath(__file__))
TRUST = os.path.join(BASE, "web", "src", "data", "trust")
OUT = os.path.join(BASE, "reports", "remediation_v2")
JSON_OUT = os.path.join(BASE, "web", "src", "data", "remediation.json")
MODEL = "Isolation Forest"
BUDGETS = ["15", "20"]
HEADLINE = "20"
SEED = 42
N_FEATURES = len(M.FEATURES)
IMGS = ["img1", "img2", "img3"]
SCOPE = "live environment the disk came from - never run on the evidence"
STANDARD = "ISO/IEC 27037"
CONF_ORDER = ["low", "medium", "high"]


# ---------------------------------------------------------------------------------------------
# minimal registry-hive reader (regf), enough to read a few values; no third-party dependency
# ---------------------------------------------------------------------------------------------
class Hive:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        if self.d[:4] != b"regf":
            raise ValueError("not a regf hive")
        self.root = struct.unpack_from("<I", self.d, 0x24)[0]

    def _c(self, o):
        return 0x1000 + o

    def _nk(self, o):
        b = self._c(o)
        if self.d[b + 4:b + 6] != b"nk":
            raise ValueError("bad nk")
        flags = struct.unpack_from("<H", self.d, b + 6)[0]
        nsub, = struct.unpack_from("<I", self.d, b + 0x18)
        sublist, = struct.unpack_from("<I", self.d, b + 0x20)
        nval, = struct.unpack_from("<I", self.d, b + 0x28)
        vlist, = struct.unpack_from("<I", self.d, b + 0x2c)
        nl, = struct.unpack_from("<H", self.d, b + 0x4c)
        nm = self.d[b + 0x50:b + 0x50 + nl]
        nm = nm.decode("latin1") if flags & 0x20 else nm.decode("utf-16le", "replace")
        return {"name": nm, "nsub": nsub, "sublist": sublist, "nval": nval, "vlist": vlist}

    def _subs(self, o):
        n = self._nk(o)
        out = []
        if n["nsub"] == 0 or n["sublist"] == 0xFFFFFFFF:
            return out

        def walk(lo):
            b = self._c(lo)
            sig = self.d[b + 4:b + 6]
            cnt, = struct.unpack_from("<H", self.d, b + 6)
            if sig in (b"lf", b"lh"):
                for i in range(cnt):
                    out.append(struct.unpack_from("<I", self.d, b + 8 + i * 8)[0])
            elif sig == b"li":
                for i in range(cnt):
                    out.append(struct.unpack_from("<I", self.d, b + 8 + i * 4)[0])
            elif sig == b"ri":
                for i in range(cnt):
                    walk(struct.unpack_from("<I", self.d, b + 8 + i * 4)[0])
        walk(n["sublist"])
        return out

    def key(self, path):
        o = self.root
        for part in [p for p in path.split("\\") if p]:
            for c in self._subs(o):
                if self._nk(c)["name"].lower() == part.lower():
                    o = c
                    break
            else:
                return None
        return o

    def values(self, o):
        n = self._nk(o)
        res = {}
        if n["nval"] == 0 or n["vlist"] == 0xFFFFFFFF:
            return res
        b = self._c(n["vlist"])
        for i in range(n["nval"]):
            vo, = struct.unpack_from("<I", self.d, b + 4 + i * 4)
            vb = self._c(vo)
            nl, dl, do, ty, fl = struct.unpack_from("<HIIIH", self.d, vb + 6)
            nm = self.d[vb + 0x18:vb + 0x18 + nl]
            nm = nm.decode("latin1") if fl & 1 else nm.decode("utf-16le", "replace")
            if dl & 0x80000000:
                data = struct.pack("<I", do)[:dl & 0x7FFFFFFF]
            else:
                data = self.d[self._c(do) + 4:self._c(do) + 4 + dl]
            if ty in (1, 2):
                data = data.decode("utf-16le", "replace").rstrip("\x00")
            elif ty == 4 and len(data) >= 4:
                data = struct.unpack("<I", data[:4])[0]
            res[nm] = data
        return res


# ---------------------------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------------------------
def detect_os(tag):
    art = os.path.join(BASE, "runs", tag, "artifacts")
    idx = os.path.join(BASE, "runs", tag, "features", "file_index.csv")
    paths = pd.read_csv(idx, usecols=["path"])["path"].astype(str) if os.path.exists(idx) else pd.Series([], dtype=str)
    pc = {"Documents and Settings": int(paths.str.startswith("/Documents and Settings/").sum()),
          "Users": int(paths.str.startswith("/Users/").sum()),
          "WINDOWS": int(paths.str.startswith("/WINDOWS/").sum()),
          "Windows": int(paths.str.startswith("/Windows/").sum())}
    path_family = "xp" if pc["Documents and Settings"] > 0 and pc["Users"] == 0 else (
        "vista+" if pc["Users"] > 0 else "unknown")
    info = {"product": None, "version": None, "build": None, "sp": None}
    method = None
    hive = os.path.join(art, "registry", "SOFTWARE")
    try:
        h = Hive(hive)
        k = h.key(r"Microsoft\Windows NT\CurrentVersion")
        v = h.values(k) if k else {}
        info = {"product": v.get("ProductName"), "version": v.get("CurrentVersion"),
                "build": str(v.get("CurrentBuildNumber") or v.get("CurrentBuild") or ""),
                "sp": v.get("CSDVersion")}
        method = ("SOFTWARE hive, Microsoft\\Windows NT\\CurrentVersion: ProductName, CurrentVersion, "
                  "CurrentBuildNumber, CSDVersion")
    except Exception:
        method = None
    ver, build = info["version"], int(re.sub(r"\D", "", info["build"] or "0") or 0)
    if ver:
        if ver.startswith("5."):
            fam = "xp"
        elif ver in ("6.0", "6.1"):
            fam = "win7"
        elif build >= 10240 or ver.startswith("10."):
            fam = "win10"
        else:
            fam = "win7"      # 6.2 / 6.3 (Windows 8 / 8.1): PowerShell 3/4, treated with the conservative Win7 set
    elif path_family == "xp":
        fam, method = "xp", "path heuristic only (SOFTWARE hive not readable)"
    elif path_family == "vista+":
        fam, method = "win7", "path heuristic only: 'Users' profiles imply Vista or later, treated as Win7 (conservative)"
    else:
        fam, method = "win7", "no evidence of version; conservative Win7 command set"
    agree = (path_family == "xp") == (fam == "xp") if path_family != "unknown" else None
    pathnote = ("profiles under 'Documents and Settings' (%d paths), none under 'Users'; system folder 'WINDOWS' (%d)"
                % (pc["Documents and Settings"], pc["WINDOWS"]) if path_family == "xp" else
                "profiles under 'Users' (%d paths); system folder 'Windows' (%d)" % (pc["Users"], pc["Windows"]))
    name = info["product"] or {"xp": "Windows XP", "win7": "Windows (Vista/7)", "win10": "Windows 10"}[fam]
    return {"family": fam, "product": name, "version": info["version"], "build": info["build"],
            "servicePack": info["sp"], "method": method, "pathCheck": pathnote, "pathAgrees": agree,
            "shell": {"xp": "cmd.exe only (no PowerShell on this OS)", "win7": "Windows PowerShell 2.0-compatible cmdlets only",
                      "win10": "Windows PowerShell 5.1"}[fam],
            "scriptExt": "cmd" if fam == "xp" else "ps1"}


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
SKIP_PROFILES = {"default", "public", "all users", "default user", "localservice", "networkservice", "desktop.ini"}
RX_PROFILE = re.compile(r"^/(users|documents and settings)/([^/]+)/", re.I)


def win(p):
    return "C:" + p.replace("/", "\\")


def accounts(files):
    seen = OrderedDict()
    for r, p in files:
        m = RX_PROFILE.match(p)
        if m and m.group(2).lower() not in SKIP_PROFILES:
            seen.setdefault(m.group(2), m.group(1))
    return list(seen.keys())


def uniq(seq):
    return list(OrderedDict.fromkeys(seq))


def usb_devices(tag):
    p = os.path.join(BASE, "runs", tag, "artifacts", "usb", "usb_devices.txt")
    if not os.path.exists(p):
        return []
    L = [l.strip() for l in open(p, errors="replace").read().splitlines()]
    return [l for l in L if l.startswith("USB Device:") or l.startswith("Device Serial Signature:")]


def level_up(c):
    return CONF_ORDER[min(2, CONF_ORDER.index(c) + 1)]


def level_down(c):
    return CONF_ORDER[max(0, CONF_ORDER.index(c) - 1)]


def cmd_of(spec, fam):
    """A command spec has per-OS variants: xp (cmd.exe), w7 and w10 (PowerShell, or native exes).  None = not available."""
    v = spec["xp"] if fam == "xp" else (spec["w7"] if fam == "win7" else (spec["w10"] if spec.get("w10") else spec["w7"]))
    return v


def C(desc, kind, xp=None, w7=None, w10=None, na_xp=None, na_w7=None, note=None):
    return {"desc": desc, "kind": kind, "xp": xp, "w7": w7, "w10": w10, "na_xp": na_xp, "na_w7": na_w7, "note": note}


def realise(specs, fam):
    """-> (commands for this OS, notApplicable list)"""
    cmds, na = [], []
    for s in specs:
        v = cmd_of(s, fam)
        modern = s["w10"] or s["w7"] or s["xp"]
        if v is None:
            reason = s["na_xp"] if fam == "xp" else (s["na_w7"] or s["na_xp"])
            na.append({"desc": s["desc"], "wouldBe": modern, "reason": reason or "not available on this OS"})
            continue
        ps = v.startswith("PS:")
        cmds.append({"desc": s["desc"], "kind": s["kind"], "shell": "powershell" if ps else "cmd",
                     "cmd": v[3:] if ps else v, "note": s["note"],
                     "requiresApproval": s["kind"] == "change"})
    return cmds, na


def pat(names):
    return "|".join(re.escape(n) for n in names)


def words(names):
    return " ".join(n.upper() for n in names)


# ---------------------------------------------------------------------------------------------
# tool / family recognition on supporting paths
# ---------------------------------------------------------------------------------------------
RX_WIPER_NAME = re.compile(r"(eraser|ccleaner|ccsetup|sdelete|cipher|bleachbit|dban|shredder|secure-?delete|"
                           r"evidence-?eliminator|privacy-?(?:eraser|cleaner)|wipe(?:r|file|disk)?|killdisk|file-?shredder)", re.I)
RX_HACK_NAME = re.compile(r"(cain|ethereal|netstumbler|whois|anonymizer|wpcap|nmap|wireshark|l0phtcrack|metasploit|nessus)", re.I)
SNIFFERS = {"cain", "ethereal", "wpcap", "wireshark", "netstumbler"}
CRACKERS = {"cain", "l0phtcrack"}
CLOUD_FAM = [("Google Drive", re.compile(r"/google/drive|/googledrive|/drivefs/|sync_config\.db|snapshot\.db|sync_log\.log|googledrivesync", re.I)),
             ("Dropbox", re.compile(r"/dropbox/|\.dropbox|filecache\.dbx|dropbox", re.I)),
             ("Box Sync", re.compile(r"/box sync/|/box/box sync|boxsync", re.I)),
             ("OneDrive", re.compile(r"/onedrive/|onedrive", re.I)),
             ("iCloud", re.compile(r"/icloud|icloudsetup", re.I))]
RX_GENERIC = re.compile(r"setupapi|usbstor|netsetupapi|/winsxs/|/driverstore/|/installer/|\.mfc|vc90|msvc|mfc90|atl90|msvcr", re.I)


def name_set(rx, files, norm=None):
    out = []
    for r, p in files:
        for m in rx.finditer(p.rsplit("/", 1)[-1] + " " + p):
            n = m.group(1).lower()
            out.append((norm or {}).get(n, n))
    return uniq(out)


def tool_dirs(files, rx):
    """install folders (not Prefetch/Recent) that hold the named tools"""
    out = []
    for r, p in files:
        lp = p.lower()
        if "/prefetch/" in lp or "/recent/" in lp:
            continue
        m = rx.search(lp)
        if not m:
            continue
        parts = p.split("/")
        d = "/".join(parts[:-1])
        if d.lower().startswith(("/program files", "/users", "/documents and settings")):
            # trim to the folder named after the tool where possible
            idx = [i for i, s in enumerate(parts[:-1]) if rx.search(s.lower())]
            if idx:
                d = "/".join(parts[:idx[0] + 1])
            out.append(win(d))
    return uniq(out)[:4]


# ---------------------------------------------------------------------------------------------
# recommendations
# ---------------------------------------------------------------------------------------------
def pick_support(files, generic_first=False):
    sp = [{"rank": int(r), "path": p, "generic": bool(RX_GENERIC.search(p))} for r, p in files]
    spec = [s for s in sp if not s["generic"]]
    gen = [s for s in sp if s["generic"]]
    return (spec + gen)[:10], len(spec), len(gen)


def rec_wiper(ctx):
    ind = ctx["ind"]["a_wiper_executed"]
    files = ind["files"]
    sup, nspec, ngen = pick_support(files)
    tools = name_set(RX_WIPER_NAME, files, {"ccsetup": "ccleaner"})
    pf = ind.get("prefetchConfirmed", 0)
    exe = sum(1 for r, p in files if p.lower().endswith((".exe", ".com", ".bat", ".cmd")))
    conf = "high" if pf >= 1 else ("medium" if exe >= 1 else "low")
    why = (f"{ind['count']} flagged files name a wiper/cleaner; {pf} are Prefetch entries, which prove the program ran."
           if pf else f"{ind['count']} flagged files name a wiper/cleaner but none is a Prefetch execution record.")
    names = ", ".join(tools)
    pattern = pat(tools)
    specs = [
        C("List Prefetch records (proof of execution and last run) for the named tools", "read",
          xp=f'dir "%SystemRoot%\\Prefetch" /a /t:w | findstr /i "{words(tools)}"',
          w7=f"PS:Get-ChildItem \"$env:SystemRoot\\Prefetch\" | Where-Object {{ $_.Name -match '{pattern}' }} | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize"),
        C("Look for scheduled wipe tasks", "read", xp=f'schtasks /query /fo LIST /v | findstr /i "{words(tools)} TASKNAME"',
          w7=f'schtasks /query /fo LIST /v | findstr /i "{words(tools)} TASKNAME"'),
        C("Find the installed program entries to learn the exact name and version", "read",
          xp=f'reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall /s | findstr /i "DisplayName" | findstr /i "{words(tools)}"',
          w7=f'reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall /s | findstr /i "DisplayName" | findstr /i "{words(tools)}"'),
        C("Copy the Security event log to external media before anything else changes", "read",
          xp="cscript //nologo %SystemRoot%\\System32\\eventquery.vbs /l security /v /fo csv > Security_events.csv",
          w7="wevtutil epl Security Security.evtx",
          na_xp=None, note="Writes a copy to the current folder: run it from removable media you control, not the host disk. XP: eventquery.vbs ships with XP Professional only; otherwise take a forensic image."),
        C("Remove the installed cleaner (changes the system)", "change",
          xp='wmic product where "name=\'<exact name from the uninstall list>\'" call uninstall',
          w7="PS:(Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like '" + (tools[0] if tools else "x") + "*' }).Uninstall()",
          note="Only after the owner and legal sign off; uninstalling destroys the tool's own logs and schedule."),
    ]
    acts = [
        f"Treat this as evidence of an attempt to destroy data: the flagged files name {names}.",
        "Copy the Prefetch folder, the event logs and the scheduled-task list to write-protected external media before anything else is touched.",
        "From the Prefetch records, establish when the tool last ran and how many times; compare with the incident window.",
        "Ask the account owner and their manager whether the tool was authorised for this machine.",
        "Check the same user's other machines and any file shares for the same tool.",
        "Do not launch the tool. Removal is optional, and only after the logs above are safely copied (approval required)."]
    return dict(id="anti-forensic-cleaner", title="A data-wiping or cleaning tool was installed" + (" and has run" if pf else ""),
                mitre="T1070.004", mitreName="Indicator Removal: File Deletion", conf=conf, why=why,
                trigger={"indicator": "(a) wiper / cleaner executable or Prefetch record", "count": ind["count"],
                         "detail": f"{ind['count']} of the flagged files name a cleaner ({names}); {pf} Prefetch records.",
                         "tools": tools},
                support=sup, specs=specs, actions=acts, accounts=accounts(files))


def rec_docs(ctx):
    ind = ctx["ind"]["b_recent_doc_traces"]
    files = ind["files"]
    sup, nspec, ngen = pick_support(files)
    accs = accounts(files)
    n = ind["count"]
    conf = "medium" if n >= 5 else "low"
    why = (f"{n} flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, "
           "not copying or removal; it is never rated higher than medium.")
    fam = ctx["os"]["family"]
    specs = []
    for u in accs[:3]:
        specs.append(C(f"List the {u} Recent-documents folder, newest first", "read",
                       xp=f'dir /a /o-d /t:w "C:\\Documents and Settings\\{u}\\Recent"',
                       w7=f'PS:Get-ChildItem -Force "C:\\Users\\{u}\\AppData\\Roaming\\Microsoft\\Windows\\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize'))
    if fam != "xp":
        for u in accs[:1]:
            specs.append(C(f"List the {u} Jump List stores", "read", xp=None,
                           w7=f'PS:Get-ChildItem -Force "C:\\Users\\{u}\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize',
                           na_xp="Jump Lists were introduced in Windows 7"))
    specs.append(C("Show account details and last logon for the profiles named in the paths", "read",
                   xp=" & ".join(f'net user "{u}"' for u in accs[:3]) or "net user",
                   w7=("PS:" + "; ".join(f'net user "{u}"' for u in accs[:3])) if accs else "net user"))
    acts = [
        "Copy the Recent folder and Jump List stores of " + (", ".join(accs) if accs else "the listed profiles") + " to external media.",
        "Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.",
        "Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.",
        "No containment is advised from this indicator alone."]
    return dict(id="document-access-traces", title="Recently opened documents are recorded for " + (", ".join(accs[:3]) or "the listed profiles"),
                mitre=None, mitreName=None, conf=conf, why=why,
                trigger={"indicator": "(b) shortcut / jump-list traces of documents", "count": n,
                         "detail": f"{n} flagged .lnk or jump-list files under profile(s) {', '.join(accs) or 'n/a'}."},
                support=sup, specs=specs, actions=acts, accounts=accs)


def rec_cloud(ctx):
    ind = ctx["ind"]["c_removable_or_cloud"]
    files = ind["files"]
    sup, nspec, ngen = pick_support(files)
    fam = ctx["os"]["family"]
    clouds = []
    for r, p in files:
        if RX_GENERIC.search(p):
            continue
        for nm, rx in CLOUD_FAM:
            if rx.search(p):
                clouds.append(nm)
                break
    clouds = uniq(clouds)
    third_party = [c for c in clouds if not (c == "OneDrive" and fam == "win10")]
    usb = ctx["usb"]
    usb_specific = any(re.search(r"usbstor", p, re.I) and not RX_GENERIC.search(p) for r, p in files)
    n = ind["count"]
    if nspec == 0:
        # the disk-level device list is context only: it is not a flagged-file indicator and never raises confidence
        conf = "low"
        why = (f"The {n} flagged file(s) are only Windows' own setupapi / usbstor files, which exist on every install. "
               "They become evidence only if they list removable devices.")
    elif not third_party:
        conf = "low"
        why = f"Only {', '.join(clouds)}, which is built into this Windows version, is flagged."
    else:
        conf = "high" if nspec >= 5 else "medium"
        why = f"{nspec} client-specific files from {', '.join(third_party)} are in the flagged set ({n} flagged files in all)."
    mitre = None
    both = []
    if conf != "low":
        if usb_specific:
            both.append("T1052.001")
        if third_party:
            both.append("T1567.002")
        mitre = both[0] if both else None
    mitre_name = {"T1052.001": "Exfiltration Over Physical Medium: Exfiltration over USB",
                  "T1567.002": "Exfiltration Over Web Service: Exfiltration to Cloud Storage"}.get(mitre)
    accs = accounts([f for f in files if not RX_GENERIC.search(f[1])])
    cdirs = []
    for nm, rx in CLOUD_FAM:
        if nm not in third_party:
            continue
        for r, p in files:
            if rx.search(p) and not RX_GENERIC.search(p) and p.lower().startswith(("/program files", "/users")):
                parts = p.split("/")
                m = [i for i, s in enumerate(parts[:-1]) if rx.search("/" + s.lower() + "/")]
                cdirs.append(win("/".join(parts[:m[0] + 1] if m else parts[:-1])))
                break
    cdirs = uniq(cdirs)[:3]
    specs = [
        C("List every USB storage device the host has seen (vendor, product, serial)", "read",
          xp="reg query HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR /s", w7="reg query HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR /s"),
        C("List the volumes and drive letters Windows mapped to those devices", "read",
          xp="reg query HKLM\\SYSTEM\\MountedDevices", w7="reg query HKLM\\SYSTEM\\MountedDevices"),
        C("Read the device-install log for first-connection times of those serials", "read",
          xp='findstr /i /c:"Disk&Ven" "%SystemRoot%\\setupapi.log"',
          w7="PS:Select-String -Path \"$env:SystemRoot\\inf\\setupapi.dev.log\" -Pattern 'Disk&Ven' | Select-Object -First 100 LineNumber, Line | Format-List",
          note="XP keeps this in %SystemRoot%\\setupapi.log; Vista and later in %SystemRoot%\\inf\\setupapi.dev.log."),
    ]
    for d in cdirs:
        specs.append(C(f"Show the {d.split(chr(92))[-1]} sync client folder and its logs", "read",
                       xp=f'dir /a /s /o-d "{d}" | findstr /i ".log .db"', w7=f'PS:Get-ChildItem -Force -Recurse "{d}" -ErrorAction SilentlyContinue | Where-Object {{ $_.Extension -match "\\.(log|db)$" }} | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime'))
    specs.append(C("List local accounts", "read", xp="net user", w7="net user"))
    if conf != "low":
        if usb_specific:
            specs.append(C("Block new USB storage devices (changes the system)", "change",
                           xp='reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR /v Start /t REG_DWORD /d 4 /f',
                           w7='reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR /v Start /t REG_DWORD /d 4 /f',
                           note="Stops all USB mass storage, including legitimate devices; set Start back to 3 to undo. Needs a policy decision."))
        for u in accs[:2]:
            specs.append(C(f"Reset the password of {u}, whose profile holds the flagged files (changes the system)", "change",
                           xp=f'net user "{u}" *', w7=f'net user "{u}" *', note="Prompts for the new password; do not put it in the script."))
    usbl = ctx["usb"]
    acts = []
    if usbl:
        acts.append("Review the removable-device history. The extracted list names: " + "; ".join(usbl[:6]) + (" ..." if len(usbl) > 6 else "") + ". Match each serial to an owner and to the incident window.")
    else:
        acts.append("Review the removable-device history for any device serials; the extractor found none on this disk, so start from the registry and setup log commands below.")
    if third_party:
        acts.append("A sync client is present: " + ", ".join(third_party) + ". Identify the signed-in account from its config database or logs and ask the provider (or tenant admin) for sharing, link and download audit logs.")
    if conf != "low":
        acts.append("If the device or account is not authorised, sign the cloud account out and revoke its sessions at the provider (not a local command).")
        if accs:
            acts.append("Consider resetting the passwords of " + ", ".join(accs[:2]) + " (approval required).")
    else:
        acts.append("No containment is advised: these are generic OS files. Only act if the setup log lists removable disks.")
    ttl = ("Removable-device and cloud-sync artifacts" if usb_specific or third_party else "Device-install logs are present")
    return dict(id="removable-or-cloud", title=ttl, mitre=mitre, mitreName=mitre_name, mitreAlso=[x for x in both[1:]],
                conf=conf, why=why,
                trigger={"indicator": "(c) removable-device or cloud-sync artifacts", "count": n,
                         "detail": f"{n} flagged files; {nspec} client-specific, {ngen} generic OS files among the {len(files)} listed.",
                         "clients": third_party, "usbDevices": usbl[:12]},
                support=sup, specs=specs, actions=acts, accounts=accs)


def rec_hack(ctx):
    ind = ctx["ind"]["d_hacking_tools"]
    files = ind["files"]
    sup, nspec, ngen = pick_support(files)
    tools = name_set(RX_HACK_NAME, files)
    pf = sum(1 for r, p in files if p.lower().endswith(".pf"))
    exe = sum(1 for r, p in files if p.lower().endswith(".exe") and "/prefetch/" not in p.lower())
    n = ind["count"]
    conf = "high" if pf >= 1 and n >= 5 else ("medium" if n >= 2 else "low")
    why = f"{n} flagged files name {', '.join(tools)}; {pf} Prefetch records and {exe} executables are among the listed ones."
    sniff = bool(set(tools) & SNIFFERS)
    crack = bool(set(tools) & CRACKERS)
    mitre = "T1588.002"
    also = (["T1040"] if sniff else []) + (["T1110.002"] if crack else [])
    dirs = tool_dirs(files, RX_HACK_NAME)
    accs = accounts(files)
    names = pat(tools)
    specs = []
    for d in dirs:
        specs.append(C(f"List the install folder {d}", "read", xp=f'dir /a /s "{d}"', w7=f'PS:Get-ChildItem -Force -Recurse "{d}" | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize'))
    specs.append(C("List Prefetch records (proof of execution) for the named tools", "read",
                   xp=f'dir "%SystemRoot%\\Prefetch" /a /t:w | findstr /i "{words(tools)}"',
                   w7=f"PS:Get-ChildItem \"$env:SystemRoot\\Prefetch\" | Where-Object {{ $_.Name -match '{names}' }} | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize"))
    if sniff:
        specs.append(C("Check whether the WinPcap capture driver service is installed", "read", xp="sc query npf", w7="sc query npf"))
    specs.append(C("Show running processes that match the tool names", "read",
                   xp=f'tasklist /v | findstr /i "{words(tools)}"', w7=f"PS:Get-Process | Where-Object {{ $_.ProcessName -match '{names}' }} | Select-Object ProcessName, Id, Path",
                   note="XP: tasklist is in XP Professional only."))
    specs.append(C("Show open network connections and owning process IDs", "read", xp="netstat -ano", w7="netstat -ano"))
    specs.append(C("List administrators on the host", "read", xp="net localgroup administrators", w7="net localgroup administrators"))
    if conf != "low":
        if sniff:
            specs.append(C("Stop and disable the capture driver (changes the system)", "change",
                           xp="sc stop npf & sc config npf start= disabled", w7="sc stop npf; sc config npf start= disabled",
                           note="Only if the driver exists and the tool is confirmed unauthorised."))
        for d in dirs[:2]:
            specs.append(C(f"Move {d} to a quarantine folder instead of deleting it (changes the system)", "change",
                           xp=f'move "{d}" "D:\\quarantine\\{d.split(chr(92))[-1]}"', w7=f'PS:Move-Item "{d}" "D:\\quarantine\\{d.split(chr(92))[-1]}"',
                           note="Keep the files: they are exhibits."))
        for u in accs[:2]:
            specs.append(C(f"Reset the password of {u}, the profile that holds the tools (changes the system)", "change",
                           xp=f'net user "{u}" *', w7=f'net user "{u}" *', note="Prompts for the new password."))
    acts = [f"Confirm with security staff whether {', '.join(tools)} are authorised on this machine; if a security team did not install them, treat as unauthorised.",
            "Copy the tool folders, the Prefetch records and the event logs to external media before removing anything."]
    if sniff:
        acts.append("Packet-capture or sniffing tools can read passwords crossing the network segment: list the accounts that logged in on that segment after the install date and reset their passwords (approval required).")
    if crack:
        acts.append("Password-cracking tools were present: assume the local account hashes (SAM) are exposed and reset the local passwords.")
    acts += ["Review firewall and intrusion-detection logs for this host's address from the first Prefetch run time onward.",
             "Quarantine rather than delete the tools once the copies are safe (approval required)."]
    return dict(id="hacking-tools", title="Network-attack or password tools present: " + ", ".join(tools),
                mitre=mitre, mitreName="Obtain Capabilities: Tool", mitreAlso=also, conf=conf, why=why,
                trigger={"indicator": "(d) hacking-tool names", "count": n,
                         "detail": f"{n} flagged files name {', '.join(tools)}.", "tools": tools},
                support=sup, specs=specs, actions=acts, accounts=accs)


def rec_ts(ctx):
    t = ctx["ts"]
    files = t["files"]
    sup, nspec, ngen = pick_support(files)
    enr, n = t["enrichment"], t["count"]
    p = t["fisherP"]
    if enr is None:
        conf, why = "low", "No enrichment could be computed (no disk-wide baseline)."
    elif enr < 1:
        conf, why = "low", f"Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment {enr:.2f})."
    elif not t["indicated"]:
        conf, why = "low", f"Low: weak enrichment ({enr:.2f}, below the {1.5} needed). Gaps like this occur on ordinary disks."
    elif n >= 50 and p is not None and p < 0.01:
        conf, why = "high", f"{n} files with creation earlier than the filename-record time by over 1 h; enrichment {enr:.2f} over the disk rate (Fisher p {p:.1e})."
    else:
        conf, why = "medium", f"{n} files show the pattern; enrichment {enr:.2f}" + (f" (Fisher p {p:.1e})." if p is not None else ".")
    accs = accounts(files)
    ex = [p for r, p in files if not p.lower().startswith(("/windows/system32/config", "/$"))][:3]
    specs = [C("Show the journal state of the system volume", "read", xp="fsutil usn queryjournal C:", w7="fsutil usn queryjournal C:",
               note="Needs an elevated prompt.")]
    for p_ in ex:
        specs.append(C(f"Read the visible timestamps of {p_.rsplit('/', 1)[-1]}", "read",
                       xp=f'dir /a /t:c "{win(p_)}" & dir /a /t:w "{win(p_)}"',
                       w7=f'PS:Get-Item -Force "{win(p_)}" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List'))
    specs.append(C("Show the current file-system audit policy", "read", xp=None,
                   w7='auditpol /get /category:"Object Access"', na_xp="auditpol.exe is not part of Windows XP (Resource Kit only); use Local Security Policy > Audit object access"))
    if conf != "low":
        specs.append(C("Turn on file-system auditing (changes the system)", "change", xp=None,
                       w7='auditpol /set /subcategory:"File System" /success:enable /failure:enable',
                       na_xp="auditpol.exe is not part of Windows XP; enable 'Audit object access' in Local Security Policy",
                       note="Records nothing until audit entries (SACLs) are set on the folders you care about."))
    if conf == "low":
        acts = [f"No containment. {why}",
                "Visible timestamps cannot show this; only an offline comparison of the two time sets in the MFT can. The MFT export keeps whole seconds, so the sub-second test cannot run.",
                "Do not act on this indicator unless another recommendation here also fires."]
    else:
        acts = ["Copy $MFT, $LogFile and $UsnJrnl:$J from an image of the volume, not from the live disk.",
                "Offline, compare standard-information and filename-record times for the listed files with an MFT parser; a creation time earlier than the filename-record time is the pattern to confirm.",
                "Cross-check against the $UsnJrnl and $LogFile: a file whose visible times predate its first journal entry was probably altered.",
                "Turn on file-system auditing going forward if the audit policy shows it is off (approval required)."]
    mitre = "T1070.006"
    return dict(id="timestamp-inconsistency", title="File creation times earlier than their filename-record time",
                mitre=mitre, mitreName="Indicator Removal: Timestomp", conf=conf, why=why,
                trigger={"indicator": "timestomp (creation < filename-record creation - 1 h)", "count": n,
                         "detail": f"{n} flagged files; enrichment {('%.2f' % enr) if enr is not None else 'n/a'} over the disk rate "
                                   f"({t['flaggedRate']*100:.2f}% of flagged against {t['diskRate']*100:.2f}% of the disk).",
                         "enrichment": enr, "fisherP": p, "flaggedRate": t["flaggedRate"], "diskRate": t["diskRate"],
                         "indicated": t["indicated"]},
                support=sup, specs=specs, actions=acts, accounts=accs)


# ---------------------------------------------------------------------------------------------
INDICATORS = [("a_wiper_executed", "Wiper or cleaner executed", "(a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files", rec_wiper),
              ("b_recent_doc_traces", "Document access traces", "(b) no shortcut or jump-list trace of a document among the flagged files", rec_docs),
              ("c_removable_or_cloud", "Removable-device or cloud-sync artifacts", "(c) no setupapi, USBSTOR or cloud-sync artifact among the flagged files", rec_cloud),
              ("d_hacking_tools", "Hacking tools", "(d) no hacking-tool name among the flagged files", rec_hack)]


_CACHE = {}


def flagged_verdicts(tag, seed=SEED, budgets=BUDGETS):
    """Isolation Forest on the final features -> {bud: (K, verdict)} from the flagged files only.
    Also returns the ranked order (best first) so callers can reuse the same flagged set."""
    key = (tag, seed)
    if key not in _CACHE:
        D = S.load(tag)
        sc = S.score(D, MODEL, M.FEATURES, seed)
        order = np.argsort(-sc, kind="stable")
        rank_of = np.empty(len(sc), dtype=np.int64)
        rank_of[order] = np.arange(1, len(sc) + 1)
        ind = T.indicator_arrays(D["df"], D["raw"])
        _CACHE[key] = (D, order, rank_of, ind)
    D, order, rank_of, ind = _CACHE[key]
    N = D["N"]
    out = {}
    for b in budgets:
        K = int(round(int(b) / 100 * N))
        out[b] = (K, T.evidence_verdict(order[:K], ind, D["df"], rank_of, N))
    return out


def build_op(tag, osinfo, bud, seed=SEED):
    K, v = flagged_verdicts(tag, seed)[bud]
    ctx = {"ind": v["indicators"], "ts": v["timestomp"], "os": osinfo, "usb": usb_devices(tag)}
    recs, nt = [], []
    fam = osinfo["family"]
    order = [("a_wiper_executed", rec_wiper), ("d_hacking_tools", rec_hack), ("c_removable_or_cloud", rec_cloud),
             ("b_recent_doc_traces", rec_docs)]
    for key, fn in order:
        if v["indicators"][key]["fired"]:
            recs.append(fn(ctx))
    if v["timestomp"]["count"] >= 1:
        recs.append(rec_ts(ctx))
    else:
        nt.append({"id": "timestamp-inconsistency", "title": "Timestomp indicator",
                   "reason": f"0 of the {K:,} flagged files have a creation time over 1 h earlier than the filename-record time."})
    for key, title, why0, fn in INDICATORS:
        if not v["indicators"][key]["fired"]:
            nt.append({"id": key, "title": title, "reason": f"0 of the {K:,} flagged files matched: {why0}."})
    out = []
    for i, r in enumerate(recs, 1):
        cmds, na = realise(r["specs"], fam)
        approval = any(c["requiresApproval"] for c in cmds)
        out.append(OrderedDict([
            ("id", r["id"]), ("title", r["title"]), ("mitre", r["mitre"]), ("mitreName", r.get("mitreName")),
            ("mitreAlso", r.get("mitreAlso") or []),
            ("trigger", OrderedDict([("indicator", r["trigger"]["indicator"]), ("detail", r["trigger"]["detail"]),
                                     ("count", r["trigger"]["count"]), ("operatingPoint", f"{MODEL}, {N_FEATURES} features, seed {seed}, {bud}% budget ({K:,} files)"),
                                     ("files", [OrderedDict([("path", s["path"]), ("rank", s["rank"]), ("generic", s["generic"])]) for s in r["support"]])] +
                                    [(k, r["trigger"][k]) for k in ("tools", "clients", "usbDevices", "enrichment", "fisherP", "flaggedRate", "diskRate", "indicated") if k in r["trigger"]])),
            ("confidence", r["conf"]), ("confidenceWhy", r["why"]),
            ("scope", SCOPE), ("actions", r["actions"]), ("commands", cmds), ("notApplicable", na),
            ("requiresApproval", approval), ("accounts", r["accounts"])]))
    return {"K": K, "recs": out, "notTriggered": nt}


# ---------------------------------------------------------------------------------------------
# the old module, re-run on each run directory to document what it did and why it was wrong
# ---------------------------------------------------------------------------------------------
OLD_FAULTS = {
    "timestamp_backdating": ("remediate_timestamp.ps1", "delta_mb < 60 on more than 50 flagged files",
                             "A small modify-to-birth gap is the normal state of installed or copied files; it says nothing about $SI vs $FN, and it fires on any large flagged set."),
    "log_clearing": ("remediate_log_clearing.ps1", "more than 3 hours with no log events (log_gap)",
                     "Hours with no events are the norm on a workstation that is switched off or idle; it is not an event-log clearing record (event 1102)."),
    "usb_exfiltration": ("remediate_usb.ps1", "usb_devices.txt exists, or any flagged row has usb_present",
                         "The extractor always writes usb_devices.txt and usb_present is set for every flagged row, so this fired on every disk whether or not a device was ever connected."),
    "credential_dumping": ("remediate_credentials.ps1", "any flagged row has credential_tool",
                           "credential_tool is a per-disk constant: either every flagged row has it or none does. It names no file."),
    "powershell_attack": ("remediate_powershell.ps1", "any flagged row has powershell_exec", "No file is named; never fired on these disks."),
    "network_beaconing": ("remediate_network.ps1", "any flagged row has sniffer_tool",
                          "sniffer_tool is a per-disk constant, like credential_tool; no beaconing was measured."),
    "malware_detected": ("remediate_malware.ps1", "at least one flagged .exe in a temp path",
                         "One executable in a temp folder is routine (installers, updaters); this fires on every disk."),
    "ransomware": ("remediate_ransomware.ps1", "more than 20 flagged archives",
                   "Archives are not encryption. It fires on the XP hacking case, which contains no ransomware."),
    "persistence": ("remediate_persistence.ps1", "any flagged row has script_host", "No file is named; never fired on these disks."),
}
REPLACED_BY = {"timestamp_backdating": "timestamp-inconsistency", "usb_exfiltration": "removable-or-cloud",
               "credential_dumping": "hacking-tools", "network_beaconing": "hacking-tools"}

CLAIMS = [
    {"script": "remediate_credentials.ps1", "claimed": "Kills LSASS credential dumpers",
     "actual": "Two `reg add` lines: LSA RunAsPPL=1 and WDigest UseLogonCredential=0. No process is listed or killed.",
     "problem": "RunAsPPL needs Windows 8.1 or later and does nothing on XP; the WDigest value only matters on Win7/8 with KB2871997. XP cannot open a .ps1 file at all."},
    {"script": "remediate_credentials.ps1", "claimed": "Resets passwords",
     "actual": "No password is read or changed in any generated script. (A separate hand-kept remediate_account.ps1 that disables a hard-coded account is not produced by remediation.py.)",
     "problem": "Claim has no code behind it."},
    {"script": "remediate_credentials.ps1", "claimed": "Purges Kerberos tickets",
     "actual": "No `klist purge` or equivalent anywhere.", "problem": "Claim has no code behind it."},
    {"script": "remediate_network.ps1", "claimed": "Disables promiscuous mode",
     "actual": "`netsh advfirewall set allprofiles state on`, then a firewall rule blocking outbound TCP 4444, 1337, 8888.",
     "problem": "Promiscuous mode is never touched. `netsh advfirewall` does not exist on XP (it uses `netsh firewall`). The three ports are a guess, not taken from any file."},
    {"script": "remediate_network.ps1", "claimed": "Stops the npf (WinPcap) service",
     "actual": "No `sc` or `Stop-Service` call.", "problem": "Claim has no code behind it."},
    {"script": "remediate_timestamp.ps1", "claimed": "Extracts $SI vs $FN timestamps",
     "actual": "One line: `auditpol /set /subcategory:\"File System\" /success:enable /failure:enable`.",
     "problem": "Extracts nothing. auditpol is not on XP, and the setting records nothing until audit entries are put on folders."},
    {"script": "remediate_usb.ps1", "claimed": "USB storage disabled across the system",
     "actual": "Sets USBSTOR Start=4 with Set-ItemProperty, runs gpupdate /force, exports USBSTOR names.",
     "problem": "It changes the live system with no approval step and blocks legitimate devices. PowerShell does not exist on XP."},
    {"script": "remediate_log_clearing.ps1", "claimed": "Audit policy reinforced for log-tampering protection",
     "actual": "Reads event 1102 with Get-WinEvent and enables the 'Security System Extension' audit subcategory.",
     "problem": "That subcategory logs security-package loading, not log clearing, and protects nothing. Get-WinEvent and auditpol do not exist on XP."},
    {"script": "remediate_ransomware.ps1", "claimed": "VSS snapshot created and process mitigations enforced",
     "actual": "`vssadmin create shadow /for=C:` and `Set-ProcessMitigation -System -Enable DEP`.",
     "problem": "`vssadmin create shadow` works on Windows Server only; Set-ProcessMitigation needs Windows 10 and DEP is already on."},
    {"script": "remediate_malware.ps1", "claimed": "Defender signatures updated and scan triggered",
     "actual": "`Start-MpScan` and `Update-MpSignature`.",
     "problem": "The Defender cmdlets are Windows 8+ only; XP and Win7 do not have them."},
]


def v1_triggers(tag, idx=None, seed=SEED, budget=20):
    """The trigger conditions of remediation.py (detect_breach_types), evaluated without writing any script.
    The flagged rows are the top `budget` % of the final-feature Isolation Forest; the columns the old rules read
    (credential_tool, sniffer_tool, usb_present ...) come from the legacy 23-feature table of the same disk, joined by path,
    because the final set no longer carries them.  Returns (fired list, values dict)."""
    D = S.load(tag)
    if idx is None:
        flagged_verdicts(tag, seed, [str(budget)])
        _, order, _, _ = _CACHE[(tag, seed)]
        idx = order[:int(round(budget / 100 * D["N"]))]
    leg_key = ("legacy", tag)
    if leg_key not in _CACHE:
        L, _, _ = M.build_features_legacy23(M.IMAGES[tag]["art_dir"], tag)
        _CACHE[leg_key] = L.drop_duplicates("path").set_index("path")
    L = _CACHE[leg_key]
    fl = D["df"].iloc[idx]
    col = lambda c: fl["path"].map(L[c]).fillna(0).astype(float) if c in L.columns else pd.Series(0.0, index=fl.index)
    fd = D["df"].iloc[idx]
    art = M.IMAGES[tag]["art_dir"]
    lgp = os.path.join(BASE, "runs", tag, "features", "log_gap_features.csv")
    lg = pd.read_csv(lgp) if os.path.exists(lgp) else pd.DataFrame()
    cnt = lambda m: int(m.sum())
    dmb = fd["delta_mb"] if "delta_mb" in fd.columns else col("delta_mb")
    vals = OrderedDict()
    fired = []
    rules = [
        ("timestamp_backdating", cnt(dmb < 60) > 50, f"{cnt(dmb < 60):,} of {len(fd):,} flagged rows have delta_mb < 60"),
        ("log_clearing", (lg["gap"] == 1).sum() > 3 if "gap" in lg.columns else False, f"{int((lg['gap'] == 1).sum()) if 'gap' in lg.columns else 0:,} no-event hours"),
        ("usb_exfiltration", cnt(col("usb_present")) > 0 or os.path.exists(os.path.join(art, "usb", "usb_devices.txt")),
         f"usb_devices.txt present; usb_present set on {cnt(col('usb_present')):,} of {len(fd):,} flagged rows"),
        ("credential_dumping", cnt(col("credential_tool")) > 0, f"credential_tool set on {cnt(col('credential_tool')):,} of {len(fd):,} flagged rows"),
        ("powershell_attack", cnt(col("powershell_exec")) > 0, f"powershell_exec set on {cnt(col('powershell_exec')):,} of {len(fd):,} flagged rows"),
        ("network_beaconing", cnt(col("sniffer_tool")) > 0, f"sniffer_tool set on {cnt(col('sniffer_tool')):,} of {len(fd):,} flagged rows"),
        ("malware_detected", cnt((fd["temp_path"] == 1) & (fd["is_exe"] == 1)) > 0, f"{cnt((fd['temp_path'] == 1) & (fd['is_exe'] == 1))} flagged executable(s) in temp paths"),
        ("ransomware", cnt(fd["is_archive"]) > 20, f"{cnt(fd['is_archive'])} flagged archives"),
        ("persistence", cnt(col("script_host")) > 0, f"script_host set on {cnt(col('script_host')):,} of {len(fd):,} flagged rows"),
    ]
    for b, f, v in rules:
        vals[b] = v
        if f:
            fired.append(b)
    return fired, vals


def old_run(tag):
    fired, vals = v1_triggers(tag)
    out = []
    for b in fired:
        s, rule, fault = OLD_FAULTS[b]
        out.append(OrderedDict([("breach", b), ("script", s), ("rule", rule), ("value", vals.get(b, "")), ("fault", fault),
                                ("generated", True), ("replacedBy", REPLACED_BY.get(b))]))
    return out


# ---------------------------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------------------------
HEADER = ["ForensIQ remediation v2 - advice for the LIVE environment this disk came from.",
          "NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.",
          "Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default."]


def script_text(r, osinfo, tag, label, bud, K):
    fam = osinfo["family"]
    cm = "REM " if fam == "xp" else "# "
    L = []
    if fam == "xp":
        L.append("@echo off")
    for h in HEADER:
        L.append(cm + h)
    L.append(cm + f"Recommendation: {r['title']}  [confidence: {r['confidence']}]")
    L.append(cm + f"Source disk: {label}; detected OS: {osinfo['product']} ({osinfo['version']}, build {osinfo['build']})")
    L.append(cm + f"Trigger: {r['trigger']['indicator']} at {MODEL} {N_FEATURES} features, {bud}% budget ({K:,} files)")
    L.append(cm + f"Why this confidence: {r['confidenceWhy']}")
    L.append(cm + "Supporting flagged files (rank  path):")
    for f in r["trigger"]["files"]:
        L.append(cm + f"   {f['rank']:>6}  {f['path']}")
    L.append("")
    if fam == "xp":
        L += ['if /i not "%FORENSIQ_LIVE_OK%"=="YES" (', "  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.", "  exit /b 1", ")", ""]
    else:
        L += ["if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }", ""]
    for c in r["commands"]:
        L.append(cm + c["desc"] + ("" if c["kind"] == "read" else "  -- CHANGES SYSTEM (requires approval)"))
        if c["note"]:
            L.append(cm + "Note: " + c["note"])
        lines = c["cmd"].split("\n")
        if c["kind"] == "read":
            L += lines
        else:
            L += [cm + "[CHANGES SYSTEM] " + x for x in lines]
        L.append("")
    if r["notApplicable"]:
        L.append(cm + "Omitted because this OS lacks them:")
        for n in r["notApplicable"]:
            L.append(cm + f"  - {n['desc']}: {n['reason']}")
    return ("\r\n" if fam == "xp" else "\n").join(L) + ("\r\n" if fam == "xp" else "\n")


def playbook_text(tag, label, osinfo, ops):
    box = ["ADVICE FOR THE LIVE ENVIRONMENT THIS DISK CAME FROM",
           "Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).",
           "Commands that change the system are commented out in the scripts and marked below."]
    L = ["+" + "-" * 98 + "+"] + [f"| {t:<96} |" for t in box] + ["+" + "-" * 98 + "+", "", f"# Containment playbook: {label}", "",
         f"- Detected OS: **{osinfo['product']}** (version {osinfo['version']}, build {osinfo['build']}"
         + (f", {osinfo['servicePack']}" if osinfo.get('servicePack') else "") + ")",
         f"- Detected by: {osinfo['method']}. Path check: {osinfo['pathCheck']}.",
         f"- Shell for the scripts: {osinfo['shell']}",
         f"- Operating point: {MODEL}, {N_FEATURES} features, seed {SEED}; the 20% budget is the headline, the 15% budget is shown for comparison.", ""]
    for bud in BUDGETS:
        op = ops[bud]
        L += [f"## {bud}% budget ({op['K']:,} flagged files)" + (" - headline" if bud == HEADLINE else ""), ""]
        if not op["recs"]:
            L += ["No indicator fired. No recommendation.", ""]
        for i, r in enumerate(op["recs"], 1):
            L += [f"### {i}. {r['title']}", "",
                  f"- Technique: {r['mitre'] + ' ' + (r['mitreName'] or '') if r['mitre'] else 'none claimed'}",
                  f"- Confidence: **{r['confidence']}**. {r['confidenceWhy']}",
                  f"- Scope: {r['scope']}",
                  f"- Requires approval: {'yes, it contains system-changing commands' if r['requiresApproval'] else 'no system-changing command is offered'}",
                  f"- Trigger: {r['trigger']['detail']}", "", "Supporting flagged files (rank, path):", ""]
            L += [f"- {f['rank']:,}  `{f['path']}`" + ("  (generic OS file)" if f["generic"] else "") for f in r["trigger"]["files"]]
            L += ["", "Actions:", ""] + [f"{j}. {a}" for j, a in enumerate(r["actions"], 1)]
            L += ["", "Commands:", ""]
            for c in r["commands"]:
                tag_ = "READ-ONLY" if c["kind"] == "read" else "CHANGES SYSTEM - requires approval"
                L += [f"- {c['desc']} [{tag_}]", "", "  ```" + ("powershell" if c["shell"] == "powershell" else "bat"), "  " + c["cmd"], "  ```"]
                if c["note"]:
                    L += ["", f"  Note: {c['note']}"]
                L.append("")
            if r["notApplicable"]:
                L += ["Not applicable on this OS:", ""] + [f"- {n['desc']} - {n['reason']}" for n in r["notApplicable"]] + [""]
        L += ["Not triggered:", ""]
        L += [f"- {n['title']}: {n['reason']}" for n in op["notTriggered"]] or ["- (every indicator fired)"]
        L.append("")
    return "\n".join(L)


def audit_md(old):
    L = ["# Audit of the old remediation stage", "",
         "Scope: `remediation.py` (unchanged, still used by `run_pipeline.py`) against what an earlier description said its scripts do, "
         "and against the three source operating systems. Checked by reading the code and re-running its trigger logic on `runs/img1`, `runs/img2`, `runs/img3`.", "",
         "## 1. Claimed behaviour against actual code", "",
         "| Script | The earlier description said | What the code does | Problem |", "|---|---|---|---|"]
    for c in CLAIMS:
        L.append(f"| `{c['script']}` | {c['claimed']} | {c['actual']} | {c['problem']} |")
    L += ["", "## 2. Trigger faults", "",
          "| Breach type | Rule in the code | Fault | Fired on |", "|---|---|---|---|"]
    for b, (s, rule, fault) in OLD_FAULTS.items():
        on = [f"Image {t[-1]} ({v})" for t in IMGS for e in old[t] if e["breach"] == b for v in [e["value"]]]
        L.append(f"| `{b}` | {rule} | {fault} | {'; '.join(on) or 'none of the three disks'} |")
    L += ["", "## 3. The scripts cannot run on the source OS", "",
          "- Image 1 is Windows XP (5.1, build 2600). XP has no PowerShell: every old script is a `.ps1` file.",
          "- Cmdlets and tools used by the old scripts that XP lacks: `Get-WinEvent`, `Set-ItemProperty` (PowerShell), `auditpol`, `netsh advfirewall`, `Start-MpScan`.",
          "- Win10-only or Server-only features: `Set-ProcessMitigation` (Windows 10), `vssadmin create shadow` (Windows Server), RunAsPPL (Windows 8.1+).",
          "- Nothing in any old script is tied to a specific file. The new version cites the flagged files and their ranks for every recommendation.", "",
          "## 4. What replaced it", "",
          "`remediation_v2.py` takes only the fair indicators from `trust_eval.py` (Isolation Forest, 19 features, 20% (headline) and 15% budgets), detects the Windows version from the SOFTWARE hive, "
          "and writes advice that is read-only by default, OS-specific, tied to named files, and marked for human approval. See `reports/remediation_v2/<img>/playbook.md`.", ""]
    return "\n".join(L)


def write_all():
    os.makedirs(OUT, exist_ok=True)
    data = OrderedDict()
    oldall = {}
    for tag in IMGS:
        D = S.load(tag)
        d = {"label": D["label"], "files": int(D["N"])}
        osinfo = detect_os(tag)
        ops = {b: build_op(tag, osinfo, b) for b in BUDGETS}
        old = old_run(tag)
        oldall[tag] = old
        idir = os.path.join(OUT, tag)
        os.makedirs(idir, exist_ok=True)
        for fn in os.listdir(idir):
            fp = os.path.join(idir, fn)
            if os.path.isfile(fp):
                os.remove(fp)
            elif fn.startswith("budget"):
                import shutil
                shutil.rmtree(fp)
        with open(os.path.join(idir, "playbook.md"), "w") as f:
            f.write(playbook_text(tag, d["label"], osinfo, ops))
        for bud in BUDGETS:
            sub = idir if bud == HEADLINE else os.path.join(idir, "budget" + bud)
            os.makedirs(sub, exist_ok=True)
            for i, r in enumerate(ops[bud]["recs"], 1):
                p = os.path.join(sub, f"{i:02d}_{r['id']}.{osinfo['scriptExt']}")
                with open(p, "w", newline="") as f:
                    f.write(script_text(r, osinfo, tag, d["label"], bud, ops[bud]["K"]))
        new15 = [{"id": r["id"], "title": r["title"], "confidence": r["confidence"]} for r in ops["15"]["recs"]]
        new20 = [{"id": r["id"], "title": r["title"], "confidence": r["confidence"]} for r in ops["20"]["recs"]]
        data[tag] = OrderedDict([
            ("label", d["label"]), ("files", d["files"]), ("os", osinfo), ("ops", ops),
            ("oldVsNew", OrderedDict([("old", old), ("new15", new15), ("new20", new20),
                                      ("dropped", [e["breach"] for e in old if e["replacedBy"] is None or e["replacedBy"] not in [n["id"] for n in new20]])]))])
    with open(os.path.join(OUT, "AUDIT.md"), "w") as f:
        f.write(audit_md(oldall))
    meta = OrderedDict([
        ("operatingPoint", {"model": MODEL, "features": N_FEATURES, "featureSet": "final (17 clean + 2 burst)", "seed": SEED, "budgets": [15, 20], "recommended": 20}),
        ("scope", SCOPE), ("standard", STANDARD),
        ("warning", "Advice for the live environment the disk came from. Every step needs human approval. Never run against seized evidence (ISO/IEC 27037)."),
        ("claims", CLAIMS)])
    with open(JSON_OUT, "w") as f:
        json.dump(OrderedDict([("meta", meta), ("images", data)]), f, separators=(",", ":"))
    print("[+] wrote", OUT, "and", JSON_OUT, f"({os.path.getsize(JSON_OUT)/1024:.0f} KB)")
    for tag in IMGS:
        x = data[tag]
        print(tag, x["os"]["product"], x["os"]["family"], "|", {b: [(r["id"], r["confidence"]) for r in x["ops"][b]["recs"]] for b in BUDGETS})


if __name__ == "__main__":
    write_all()
