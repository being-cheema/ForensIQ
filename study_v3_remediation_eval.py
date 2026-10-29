"""
study_v3_remediation_eval.py  (study v3, experiment C1)
=======================================================
Does the evidence-based remediation (remediation_v2.py) name the right indicators, and the old template
stage (remediation.py) not?  Final feature set (19 features), Isolation Forest, seed 42; flagged = top 20 % (headline)
and 15 %.  Ground truth is the PUBLIC case description of each disk, written down as a table before any comparison.

    FORENSIQ_FEATURE_SET=final .venv/bin/python study_v3_remediation_eval.py

Writes reports/study_v3/final/C1/{summary.md, results.csv, site.json}.  Nothing generated here is ever executed.
"""
import os

os.environ.setdefault("FORENSIQ_FEATURE_SET", "final")

import re                       # noqa: E402
import csv                      # noqa: E402
import json                     # noqa: E402
import itertools                # noqa: E402

import numpy as np              # noqa: E402

import multimodel_eval as M     # noqa: E402
import study_v3_common as S     # noqa: E402
import remediation_v2 as R      # noqa: E402

OUT = os.path.join(S.OUT, "C1")
SEEDS = [42, 1337, 9999, 7, 2024]
BUDS = ["20", "15"]

# ---------------------------------------------------------------------------------------------
# 1. reference: expected indicators per disk, from the public case descriptions.  Fixed before comparison.
# ---------------------------------------------------------------------------------------------
INDICATORS = [
    ("timestomp", "Timestamp tampering (timestomping)"),
    ("wiper", "Anti-forensic wiping / cleaning tool"),
    ("usb", "Removable-media use"),
    ("cloud", "Cloud-sync use"),
    ("hacking_tools", "Hacking / password / sniffer tools"),
    ("doc_access", "Document access traces"),
    ("browser", "Browser activity"),
    ("log_clearing", "Event-log clearing"),
    ("malware_misc", "Malware, ransomware, PowerShell or persistence"),
]
IDS = [k for k, _ in INDICATORS]
EXPECTED = {   # yes = 1
    "img1": dict(timestomp=1, wiper=0, usb=0, cloud=0, hacking_tools=1, doc_access=0, browser=0, log_clearing=0, malware_misc=0),
    "img2": dict(timestomp=0, wiper=1, usb=1, cloud=1, hacking_tools=0, doc_access=0, browser=0, log_clearing=0, malware_misc=0),
    "img3": dict(timestomp=0, wiper=0, usb=0, cloud=1, hacking_tools=0, doc_access=1, browser=1, log_clearing=0, malware_misc=0),
}
CASE = {
    "img1": "external hacking: hacking, password-cracking and sniffer tools; Novell tools timestomped",
    "img2": "insider data leakage via removable media and cloud, with anti-forensic wiping (Eraser, CCleaner)",
    "img3": "insider (Lone Wolf) planning and exfiltration via documents, cloud and browser",
}
# Sensitivity only (not the reference): the repo's target list marks Eraser.exe on img2 as timestomped.
EXPECTED_SENS = {"img2": dict(EXPECTED["img2"], timestomp=1)}

V1_MAP = {"timestamp_backdating": "timestomp", "log_clearing": "log_clearing", "usb_exfiltration": "usb",
          "credential_dumping": "hacking_tools", "network_beaconing": "hacking_tools",
          "powershell_attack": "malware_misc", "malware_detected": "malware_misc", "ransomware": "malware_misc",
          "persistence": "malware_misc"}
RX_USB = re.compile(r"usbstor|setupapi", re.I)


def v2_indicators(tag, op, seed, bud):
    """Indicator keys named by each v2 recommendation (all emitted, and medium-or-high only)."""
    D, order, rank_of, ind = R._CACHE[(tag, seed)]
    K = int(round(int(bud) / 100 * D["N"]))
    fl = np.zeros(D["N"], dtype=bool)
    fl[order[:K]] = True
    paths = D["df"]["path"].values
    usb_any = any(RX_USB.search(paths[i]) for i in np.where(fl & ind["removable_cloud"])[0])
    allk, medk = set(), set()
    for r in op["recs"]:
        ks = set()
        if r["id"] == "anti-forensic-cleaner":
            ks.add("wiper")
        elif r["id"] == "hacking-tools":
            ks.add("hacking_tools")
        elif r["id"] == "timestamp-inconsistency":
            ks.add("timestomp")
        elif r["id"] == "document-access-traces":
            ks.add("doc_access")
        elif r["id"] == "removable-or-cloud":
            if r["trigger"].get("clients"):
                ks.add("cloud")
            if usb_any:
                ks.add("usb")
        allk |= ks
        if r["confidence"] in ("medium", "high"):
            # medium+: removable media only if the recommendation itself claims it (client-specific USBSTOR evidence)
            medk |= {k for k in ks if k != "usb"} | ({"usb"} if "T1052.001" in ([r["mitre"]] + list(r.get("mitreAlso") or [])) else set())
    return allk, medk


def prf(trig, exp):
    e = {k for k in IDS if exp[k]}
    tp = len(trig & e)
    p = tp / len(trig) if trig else None
    rc = tp / len(e) if e else None
    return {"triggered_n": len(trig), "expected_n": len(e), "tp": tp, "fp": len(trig - e), "fn": len(e - trig),
            "precision": p, "recall": rc}


def jac(a, b):
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


# ---------------------------------------------------------------------------------------------
# 2. checks on v2 output
# ---------------------------------------------------------------------------------------------
EVIDENCE_RX = re.compile(r"(\.e01\b|\.001\b|\.dd\b|\.raw\b|\.aff\b|\.vmdk\b|\.vhd\b|/dev/|physicaldrive|\\\\\.\\|schardt|"
                         r"\bimages[\\/]|\bruns[\\/]|lonewolf|\bdd\s+if=|\bdcfldd\b|\bewfmount\b|\bmount\s+-o)", re.I)
BAN = {
    "xp": [(r"get-[a-z]+|select-[a-z]+|where-object|format-[a-z]+|powershell|\$env:", "PowerShell syntax (XP has no PowerShell)"),
           (r"\bauditpol\b", "auditpol (not on XP)"), (r"\bwevtutil\b", "wevtutil (Vista+)"),
           (r"netsh\s+advfirewall", "netsh advfirewall (Vista+)"), (r"vssadmin\s+create\s+shadow", "vssadmin create shadow (Server only)"),
           (r"set-processmitigation|start-mpscan|update-mpsignature", "Defender / mitigation cmdlets"),
           (r"\bicacls\b|\bwinrm\b|\bbcdedit\b", "tool not on XP")],
    "win7": [(r"get-ciminstance|get-nettcpconnection|get-filehash|convertfrom-json|get-smb|get-netfirewall|get-mp[a-z]+|"
              r"start-mpscan|set-processmitigation|get-defender|invoke-webrequest|expand-archive|compress-archive|"
              r"-file\b|-directory\b", "cmdlet or parameter newer than PowerShell 2.0"),
             (r"\|\s*where\s+[a-z]+\s+-|\|\s*\?\s+[a-z]+\s+-", "simplified Where-Object syntax (PowerShell 3+)"),
             (r"vssadmin\s+create\s+shadow", "vssadmin create shadow (Server only)")],
    "win10": [(r"vssadmin\s+create\s+shadow", "vssadmin create shadow (Server only)")],
}


def check_checks(tag, d, ops, seed=42):
    D, order, rank_of, ind = R._CACHE[(tag, seed)]
    paths = D["df"]["path"].values
    res = {"cite": [], "evidence_cmd": [], "changes_commented": [], "os": []}
    fam = d["os"]["family"]
    for bud in BUDS:
        K = int(round(int(bud) / 100 * D["N"]))
        flagged_paths = {paths[i] for i in order[:K]}
        for r in ops[bud]["recs"]:
            fs = r["trigger"]["files"]
            ok = len(fs) >= 1 and all(f["path"] in flagged_paths and f["rank"] <= K for f in fs)
            res["cite"].append({"budget": bud, "rec": r["id"], "files": len(fs), "pass": bool(ok)})
            for c in r["commands"] + r["notApplicable"]:
                txt = c.get("cmd") or c.get("wouldBe") or ""
                hit = EVIDENCE_RX.search(txt)
                res["evidence_cmd"].append({"budget": bud, "rec": r["id"], "cmd": txt[:90], "pass": hit is None,
                                            "match": hit.group(0) if hit else None})
            for c in r["commands"]:
                shell_ok = not (fam == "xp" and c["shell"] == "powershell")
                bad = [why for rx, why in BAN[fam] if re.search(rx, c["cmd"], re.I)]
                if not shell_ok:
                    bad.append("PowerShell command on an OS without PowerShell")
                res["os"].append({"budget": bud, "rec": r["id"], "cmd": c["cmd"][:90], "violations": bad})
    # change commands must be commented out in every generated script
    base = os.path.join(R.OUT, tag)
    for sub in ("", "budget15"):
        dd = os.path.join(base, sub) if sub else base
        for fn in sorted(os.listdir(dd)):
            if not fn.endswith((".cmd", ".ps1")):
                continue
            lines = open(os.path.join(dd, fn), errors="replace").read().splitlines()
            live_change, inblock = 0, False
            for ln in lines:
                if not ln.strip():
                    inblock = False
                    continue
                iscom = ln.lstrip().upper().startswith(("REM ", "#"))
                if "CHANGES SYSTEM (requires approval)" in ln:
                    inblock = True
                elif inblock and not iscom:
                    live_change += 1
                if "[CHANGES SYSTEM]" in ln and not iscom:
                    live_change += 1
            res["changes_commented"].append({"file": f"{tag}/{sub + '/' if sub else ''}{fn}", "pass": live_change == 0})
    return res


# ---------------------------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    rows, site = [], {"reference": {"indicators": INDICATORS, "case": CASE, "expected": EXPECTED}, "disks": {}}
    stab_rows = []
    per = {}
    for tag in S.DISKS:
        osinfo = R.detect_os(tag)
        ops = {b: R.build_op(tag, osinfo, b) for b in BUDS}
        d = {"os": osinfo, "ops": ops}
        v1 = {}
        for b in BUDS:
            fired, vals = R.v1_triggers(tag, budget=int(b))
            v1[b] = ({V1_MAP[x] for x in fired}, fired, vals)
        v2 = {b: v2_indicators(tag, ops[b], 42, b) for b in BUDS}
        chk = check_checks(tag, d, ops)
        per[tag] = {"d": d, "v1": v1, "v2": v2, "chk": chk}
        for b in BUDS:
            for sysname, trig in (("v1", v1[b][0]), ("v2_all", v2[b][0]), ("v2_medium+", v2[b][1])):
                m = prf(trig, EXPECTED[tag])
                rows.append(dict(disk=tag, system=sysname, budget=b, triggered="|".join(sorted(trig)),
                                 expected="|".join(k for k in IDS if EXPECTED[tag][k]), **m))
        # budget / seed stability of v2 indicator sets (all emitted, and medium+)
        sets = {}
        for sd in SEEDS:
            for b in BUDS:
                op = ops[b] if sd == 42 else R.build_op(tag, osinfo, b, seed=sd)
                if sd != 42 or True:
                    sets[(sd, b)] = v2_indicators(tag, op, sd, b)
        per[tag]["sets"] = sets
        recs_by = {k: sorted(r["id"] for r in (ops[k[1]]["recs"] if k[0] == 42 else R.build_op(tag, osinfo, k[1], seed=k[0])["recs"]))
                   for k in sets}
        per[tag]["recs_by"] = recs_by
    # ---------------- summary text ----------------
    L = ["# C1: remediation evaluation on the final features", "",
         "Final feature set (19 features: 17 clean + 2 burst), Isolation Forest. Playbook seed 42; flagged = top 20 % (headline) "
         "and top 15 %. v1 = the trigger logic of `remediation.py`, evaluated without writing or running any script. "
         "v2 = `remediation_v2.py`, whose indicators come only from the paths and raw times of the flagged files.", "",
         "## 1. Reference: expected indicators per disk (written before any comparison)", "",
         "Source: the public case description of each disk (scenario and target names in `multimodel_eval.IMAGES`). "
         "yes = the case description says this behaviour happened.", ""]
    for t in S.DISKS:
        L.append(f"- **{M.IMAGES[t]['label']}**: {CASE[t]}.")
    L += ["", "| Indicator | " + " | ".join(S.DISKS) + " |", "|---|" + "---|" * len(S.DISKS)]
    for k, name in INDICATORS:
        L.append(f"| {name} | " + " | ".join("yes" if EXPECTED[t][k] else "no" for t in S.DISKS) + " |")
    L += ["", "Notes. (1) Neither v1 nor v2 has a browser indicator, so img3's browser item can only count against recall for both; "
          "it is kept because it is in the case description. (2) img2 timestomping and img2 document access are marked no because the "
          "description lists wiping, removable media and cloud, not those; a sensitivity row below marks img2 timestomp yes "
          "(the repo's target list flags Eraser.exe as timestomped). (3) Indicator mapping: v1 credential_dumping and network_beaconing "
          "-> hacking tools; v1 usb_exfiltration -> removable media; v1 powershell, malware, ransomware, persistence -> the last row. "
          "v2 removable-or-cloud -> cloud if a sync client is named; removable media if a flagged file is a setupapi / USBSTOR file (all recs) or, for medium+, only if the recommendation claims T1052.001 (client-specific USBSTOR evidence).", ""]

    def table(bud):
        out = [f"| Disk | System | Triggered | Expected | Precision | Recall |", "|---|---|---|---|---|---|"]
        tot = {}
        for t in S.DISKS:
            for sysname, trig in (("v1 (old)", per[t]["v1"][bud][0]), ("v2 (new), all recs", per[t]["v2"][bud][0]),
                                  ("v2 (new), medium+ only", per[t]["v2"][bud][1])):
                m = prf(trig, EXPECTED[t])
                a = tot.setdefault(sysname, [0, 0, 0])
                a[0] += m["tp"]
                a[1] += m["triggered_n"]
                a[2] += m["expected_n"]
                out.append(f"| {t} | {sysname} | {', '.join(sorted(trig)) or '-'} | {m['tp']}/{m['triggered_n']} true of {m['expected_n']} expected | "
                           f"{fmt(m['precision'])} | {fmt(m['recall'])} |")
        for sysname, (tp, tr, ex) in tot.items():
            out.append(f"| all | {sysname} | | {tp}/{tr} | {fmt(tp / tr if tr else None)} | {fmt(tp / ex)} |")
        return out

    L += ["## 2. Old against new", "", "Precision = triggered indicators that are expected / triggered. Recall = expected indicators that "
          "are triggered / expected. `all` rows pool the three disks (micro average). 'medium+ only' drops the low-confidence "
          "entries, which v2 itself labels as no-containment.", "", "### Top 20 % (headline)", ""] + table("20")
    L += ["", "### Top 15 %", ""] + table("15")
    L += ["", "### What v1 fired, with the rule values (top 20 %)", ""]
    for t in S.DISKS:
        L.append(f"- {t}: " + "; ".join(f"`{b}` ({per[t]['v1']['20'][2][b]})" for b in per[t]["v1"]["20"][1]))
    sens = []
    for t, e in EXPECTED_SENS.items():
        for sysname, trig in (("v1", per[t]["v1"]["20"][0]), ("v2 medium+", per[t]["v2"]["20"][1]), ("v2 all", per[t]["v2"]["20"][0])):
            m = prf(trig, e)
            sens.append(f"{t} {sysname}: precision {fmt(m['precision'])}, recall {fmt(m['recall'])}")
    L += ["", "Sensitivity (img2 timestomp marked yes, 20 %): " + "; ".join(sens) + ".", ""]

    # evidence
    L += ["## 3. Evidence checks on v2", ""]
    allc = [c for t in S.DISKS for c in per[t]["chk"]["cite"]]
    L += [f"**Every recommendation cites at least one flagged file (and every cited file is inside the flagged top-K at its stated rank): "
          f"{'PASS' if all(c['pass'] for c in allc) else 'FAIL'}** ({sum(c['pass'] for c in allc)}/{len(allc)} recommendations, both budgets).", "",
          "| Disk | Budget | Recommendation | Cited flagged files | Result |", "|---|---|---|---|---|"]
    for t in S.DISKS:
        for c in per[t]["chk"]["cite"]:
            L.append(f"| {t} | {c['budget']}% | {c['rec']} | {c['files']} | {'PASS' if c['pass'] else 'FAIL'} |")
    ev = [c for t in S.DISKS for c in per[t]["chk"]["evidence_cmd"]]
    L += ["", f"**No command targets the evidence image: {'PASS' if all(c['pass'] for c in ev) else 'FAIL'}** "
          f"({sum(c['pass'] for c in ev)}/{len(ev)} commands, including the ones left out for the OS). A command fails if it names a disk-image "
          "file or extension (.E01, .001, .dd, .raw ...), a raw device, the `images/` or `runs/` folders, or an imaging or mount tool. "
          "All commands point at live-system paths (C:\\..., registry, event logs).", ""]
    for c in ev:
        if not c["pass"]:
            L.append(f"- FAIL {c['rec']}: `{c['cmd']}` matched `{c['match']}`")
    cc = [c for t in S.DISKS for c in per[t]["chk"]["changes_commented"]]
    L += [f"**Every system-changing command is commented out in the generated scripts: {'PASS' if all(c['pass'] for c in cc) else 'FAIL'}** "
          f"({sum(c['pass'] for c in cc)}/{len(cc)} script files).", ""]

    # budget / seed
    L += ["## 4. Budget and seed consistency of the v2 indicator sets", "",
          "Indicator set = the mapped indicators named by the recommendations; recommendation set = the recommendation ids. "
          "Jaccard 1.00 means identical sets.", "", "| Disk | 15 vs 20 % (seed 42): indicators, all | 15 vs 20 %: medium+ | 15 vs 20 %: rec ids | "
          "Across 5 seeds, 20 %: min pairwise, rec ids | Across 5 seeds, 15 %: min pairwise, rec ids | Across seeds, 20 %: min pairwise, medium+ indicators |",
          "|---|---|---|---|---|---|---|"]
    bj = {}
    for t in S.DISKS:
        s, rb = per[t]["sets"], per[t]["recs_by"]
        a = jac(s[(42, "15")][0], s[(42, "20")][0])
        m = jac(s[(42, "15")][1], s[(42, "20")][1])
        r_ = jac(set(rb[(42, "15")]), set(rb[(42, "20")]))
        mins = {}
        for b in BUDS:
            mins[b] = min(jac(set(rb[(x, b)]), set(rb[(y, b)])) for x, y in itertools.combinations(SEEDS, 2))
        minm = min(jac(s[(x, "20")][1], s[(y, "20")][1]) for x, y in itertools.combinations(SEEDS, 2))
        bj[t] = dict(budget_all=a, budget_medplus=m, budget_recs=r_, seeds20=mins["20"], seeds15=mins["15"], seeds_med20=minm)
        L.append(f"| {t} | {a:.2f} | {m:.2f} | {r_:.2f} | {mins['20']:.2f} | {mins['15']:.2f} | {minm:.2f} |")
    L += ["", "Recommendation ids by seed at 20 %:", ""]
    for t in S.DISKS:
        for sd in SEEDS:
            L.append(f"- {t} seed {sd}: " + ", ".join(per[t]["recs_by"][(sd, "20")]))
    # confidence drift
    L += ["", "Confidence of each recommendation at seed 42, 15 % then 20 %:", ""]
    for t in S.DISKS:
        c15 = {r["id"]: r["confidence"] for r in per[t]["d"]["ops"]["15"]["recs"]}
        c20 = {r["id"]: r["confidence"] for r in per[t]["d"]["ops"]["20"]["recs"]}
        L.append(f"- {t}: " + "; ".join(f"{k}: {c15.get(k, '-')} -> {c20.get(k, '-')}" for k in sorted(set(c15) | set(c20))))

    # OS
    L += ["", "## 5. OS availability check (static)", "",
          "Each command emitted for a disk is scanned for tools and syntax the detected OS lacks: XP = cmd.exe only (no PowerShell, no auditpol, "
          "no wevtutil, no netsh advfirewall); Win7 = PowerShell 2.0 (no later cmdlets or parameters, no simplified Where-Object syntax); "
          "Win10 = PowerShell 5.1. Commands the generator already left out for an OS are listed in the playbook and not counted.", "",
          "| Disk | OS detected | Commands checked | Violations |", "|---|---|---|---|"]
    osv = []
    for t in S.DISKS:
        o = per[t]["d"]["os"]["family"]
        cs = per[t]["chk"]["os"]
        v = [c for c in cs if c["violations"]]
        osv += [(t, c) for c in v]
        L.append(f"| {t} | {per[t]['d']['os']['product']} ({o}) | {len(cs)} | {len(v)} |")
    L.append("")
    if osv:
        for t, c in osv:
            L.append(f"- VIOLATION {t} {c['rec']} ({c['budget']}%): `{c['cmd']}` -> {'; '.join(c['violations'])}")
    else:
        L.append("No violations found.")
    L += ["", "Scope of the check: it is a pattern scan, not an execution; it cannot prove a command works, only that it uses nothing "
          "known to be missing on that OS. Two XP commands carry edition notes in the playbook (`tasklist` and `eventquery.vbs` need XP Professional).", ""]
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L))

    cols = ["disk", "system", "budget", "triggered", "expected", "triggered_n", "expected_n", "tp", "fp", "fn", "precision", "recall"]
    with open(os.path.join(OUT, "results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r["disk"], r["system"], r["budget"], r["triggered"], r["expected"], r["triggered_n"], r["expected_n"], r["tp"], r["fp"], r["fn"],
                        "" if r["precision"] is None else round(r["precision"], 4), "" if r["recall"] is None else round(r["recall"], 4)])
    for t in S.DISKS:
        site["disks"][t] = {"os": per[t]["d"]["os"]["product"], "rows": [r for r in rows if r["disk"] == t],
                            "stability": bj[t],
                            "checks": {"cite": per[t]["chk"]["cite"],
                                       "evidenceCmdFails": [c for c in per[t]["chk"]["evidence_cmd"] if not c["pass"]],
                                       "changesCommented": per[t]["chk"]["changes_commented"],
                                       "osViolations": [c for c in per[t]["chk"]["os"] if c["violations"]]}}
    json.dump(site, open(os.path.join(OUT, "site.json"), "w"), indent=1, default=str)
    print("[+] wrote", OUT)
    print("\n".join(L[L.index("### Top 20 % (headline)"):L.index("### Top 15 %")]))


if __name__ == "__main__":
    main()
