# C1: remediation evaluation on the final features

Final feature set (19 features: 17 clean + 2 burst), Isolation Forest. Playbook seed 42; flagged = top 20 % (headline) and top 15 %. v1 = the trigger logic of `remediation.py`, evaluated without writing or running any script. v2 = `remediation_v2.py`, whose indicators come only from the paths and raw times of the flagged files.

## 1. Reference: expected indicators per disk (written before any comparison)

Source: the public case description of each disk (scenario and target names in `multimodel_eval.IMAGES`). yes = the case description says this behaviour happened.

- **Image 1: XP Hacking (SCHARDT.001)**: external hacking: hacking, password-cracking and sniffer tools; Novell tools timestomped.
- **Image 2: Win7 Data Leakage**: insider data leakage via removable media and cloud, with anti-forensic wiping (Eraser, CCleaner).
- **Image 3: Win10 Lone Wolf**: insider (Lone Wolf) planning and exfiltration via documents, cloud and browser.

| Indicator | img1 | img2 | img3 |
|---|---|---|---|
| Timestamp tampering (timestomping) | yes | no | no |
| Anti-forensic wiping / cleaning tool | no | yes | no |
| Removable-media use | no | yes | no |
| Cloud-sync use | no | yes | yes |
| Hacking / password / sniffer tools | yes | no | no |
| Document access traces | no | no | yes |
| Browser activity | no | no | yes |
| Event-log clearing | no | no | no |
| Malware, ransomware, PowerShell or persistence | no | no | no |

Notes. (1) Neither v1 nor v2 has a browser indicator, so img3's browser item can only count against recall for both; it is kept because it is in the case description. (2) img2 timestomping and img2 document access are marked no because the description lists wiping, removable media and cloud, not those; a sensitivity row below marks img2 timestomp yes (the repo's target list flags Eraser.exe as timestomped). (3) Indicator mapping: v1 credential_dumping and network_beaconing -> hacking tools; v1 usb_exfiltration -> removable media; v1 powershell, malware, ransomware, persistence -> the last row. v2 removable-or-cloud -> cloud if a sync client is named; removable media if a flagged file is a setupapi / USBSTOR file (all recs) or, for medium+, only if the recommendation claims T1052.001 (client-specific USBSTOR evidence).

## 2. Old against new

Precision = triggered indicators that are expected / triggered. Recall = expected indicators that are triggered / expected. `all` rows pool the three disks (micro average). 'medium+ only' drops the low-confidence entries, which v2 itself labels as no-containment.

### Top 20 % (headline)

| Disk | System | Triggered | Expected | Precision | Recall |
|---|---|---|---|---|---|
| img1 | v1 (old) | hacking_tools, malware_misc, timestomp, usb | 2/4 true of 2 expected | 0.50 | 1.00 |
| img1 | v2 (new), all recs | doc_access, hacking_tools, timestomp, usb | 2/4 true of 2 expected | 0.50 | 1.00 |
| img1 | v2 (new), medium+ only | doc_access, hacking_tools, timestomp | 2/3 true of 2 expected | 0.67 | 1.00 |
| img2 | v1 (old) | log_clearing, malware_misc, timestomp, usb | 1/4 true of 3 expected | 0.25 | 0.33 |
| img2 | v2 (new), all recs | cloud, doc_access, timestomp, usb, wiper | 3/5 true of 3 expected | 0.60 | 1.00 |
| img2 | v2 (new), medium+ only | cloud, doc_access, wiper | 2/3 true of 3 expected | 0.67 | 0.67 |
| img3 | v1 (old) | log_clearing, malware_misc, timestomp, usb | 0/4 true of 3 expected | 0.00 | 0.00 |
| img3 | v2 (new), all recs | cloud, doc_access, timestomp, usb | 2/4 true of 3 expected | 0.50 | 0.67 |
| img3 | v2 (new), medium+ only | cloud, doc_access | 2/2 true of 3 expected | 1.00 | 0.67 |
| all | v1 (old) | | 3/12 | 0.25 | 0.38 |
| all | v2 (new), all recs | | 7/13 | 0.54 | 0.88 |
| all | v2 (new), medium+ only | | 6/8 | 0.75 | 0.75 |

### Top 15 %

| Disk | System | Triggered | Expected | Precision | Recall |
|---|---|---|---|---|---|
| img1 | v1 (old) | hacking_tools, malware_misc, timestomp, usb | 2/4 true of 2 expected | 0.50 | 1.00 |
| img1 | v2 (new), all recs | doc_access, hacking_tools, timestomp, usb | 2/4 true of 2 expected | 0.50 | 1.00 |
| img1 | v2 (new), medium+ only | doc_access, hacking_tools, timestomp | 2/3 true of 2 expected | 0.67 | 1.00 |
| img2 | v1 (old) | log_clearing, malware_misc, timestomp, usb | 1/4 true of 3 expected | 0.25 | 0.33 |
| img2 | v2 (new), all recs | cloud, doc_access, timestomp, usb, wiper | 3/5 true of 3 expected | 0.60 | 1.00 |
| img2 | v2 (new), medium+ only | cloud, doc_access, wiper | 2/3 true of 3 expected | 0.67 | 0.67 |
| img3 | v1 (old) | log_clearing, malware_misc, timestomp, usb | 0/4 true of 3 expected | 0.00 | 0.00 |
| img3 | v2 (new), all recs | cloud, doc_access, timestomp, usb | 2/4 true of 3 expected | 0.50 | 0.67 |
| img3 | v2 (new), medium+ only | cloud, doc_access | 2/2 true of 3 expected | 1.00 | 0.67 |
| all | v1 (old) | | 3/12 | 0.25 | 0.38 |
| all | v2 (new), all recs | | 7/13 | 0.54 | 0.88 |
| all | v2 (new), medium+ only | | 6/8 | 0.75 | 0.75 |

### What v1 fired, with the rule values (top 20 %)

- img1: `timestamp_backdating` (1,059 of 2,355 flagged rows have delta_mb < 60); `usb_exfiltration` (usb_devices.txt present; usb_present set on 2,355 of 2,355 flagged rows); `credential_dumping` (credential_tool set on 2,355 of 2,355 flagged rows); `network_beaconing` (sniffer_tool set on 2,355 of 2,355 flagged rows); `malware_detected` (1 flagged executable(s) in temp paths); `ransomware` (48 flagged archives)
- img2: `timestamp_backdating` (11,504 of 17,003 flagged rows have delta_mb < 60); `log_clearing` (17,428 no-event hours); `usb_exfiltration` (usb_devices.txt present; usb_present set on 17,003 of 17,003 flagged rows); `malware_detected` (45 flagged executable(s) in temp paths)
- img3: `timestamp_backdating` (16,696 of 33,222 flagged rows have delta_mb < 60); `log_clearing` (80 no-event hours); `usb_exfiltration` (usb_devices.txt present; usb_present set on 33,222 of 33,222 flagged rows); `malware_detected` (157 flagged executable(s) in temp paths); `ransomware` (26 flagged archives)

Sensitivity (img2 timestomp marked yes, 20 %): img2 v1: precision 0.50, recall 0.50; img2 v2 medium+: precision 0.67, recall 0.50; img2 v2 all: precision 0.80, recall 1.00.

## 3. Evidence checks on v2

**Every recommendation cites at least one flagged file (and every cited file is inside the flagged top-K at its stated rank): PASS** (22/22 recommendations, both budgets).

| Disk | Budget | Recommendation | Cited flagged files | Result |
|---|---|---|---|---|
| img1 | 20% | hacking-tools | 10 | PASS |
| img1 | 20% | removable-or-cloud | 1 | PASS |
| img1 | 20% | document-access-traces | 10 | PASS |
| img1 | 20% | timestamp-inconsistency | 10 | PASS |
| img1 | 15% | hacking-tools | 10 | PASS |
| img1 | 15% | removable-or-cloud | 1 | PASS |
| img1 | 15% | document-access-traces | 10 | PASS |
| img1 | 15% | timestamp-inconsistency | 10 | PASS |
| img2 | 20% | anti-forensic-cleaner | 8 | PASS |
| img2 | 20% | removable-or-cloud | 10 | PASS |
| img2 | 20% | document-access-traces | 10 | PASS |
| img2 | 20% | timestamp-inconsistency | 10 | PASS |
| img2 | 15% | anti-forensic-cleaner | 8 | PASS |
| img2 | 15% | removable-or-cloud | 10 | PASS |
| img2 | 15% | document-access-traces | 10 | PASS |
| img2 | 15% | timestamp-inconsistency | 10 | PASS |
| img3 | 20% | removable-or-cloud | 10 | PASS |
| img3 | 20% | document-access-traces | 10 | PASS |
| img3 | 20% | timestamp-inconsistency | 10 | PASS |
| img3 | 15% | removable-or-cloud | 10 | PASS |
| img3 | 15% | document-access-traces | 10 | PASS |
| img3 | 15% | timestamp-inconsistency | 10 | PASS |

**No command targets the evidence image: PASS** (122/122 commands, including the ones left out for the OS). A command fails if it names a disk-image file or extension (.E01, .001, .dd, .raw ...), a raw device, the `images/` or `runs/` folders, or an imaging or mount tool. All commands point at live-system paths (C:\..., registry, event logs).

**Every system-changing command is commented out in the generated scripts: PASS** (22/22 script files).

## 4. Budget and seed consistency of the v2 indicator sets

Indicator set = the mapped indicators named by the recommendations; recommendation set = the recommendation ids. Jaccard 1.00 means identical sets.

| Disk | 15 vs 20 % (seed 42): indicators, all | 15 vs 20 %: medium+ | 15 vs 20 %: rec ids | Across 5 seeds, 20 %: min pairwise, rec ids | Across 5 seeds, 15 %: min pairwise, rec ids | Across seeds, 20 %: min pairwise, medium+ indicators |
|---|---|---|---|---|---|---|
| img1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| img2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| img3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

Recommendation ids by seed at 20 %:

- img1 seed 42: document-access-traces, hacking-tools, removable-or-cloud, timestamp-inconsistency
- img1 seed 1337: document-access-traces, hacking-tools, removable-or-cloud, timestamp-inconsistency
- img1 seed 9999: document-access-traces, hacking-tools, removable-or-cloud, timestamp-inconsistency
- img1 seed 7: document-access-traces, hacking-tools, removable-or-cloud, timestamp-inconsistency
- img1 seed 2024: document-access-traces, hacking-tools, removable-or-cloud, timestamp-inconsistency
- img2 seed 42: anti-forensic-cleaner, document-access-traces, removable-or-cloud, timestamp-inconsistency
- img2 seed 1337: anti-forensic-cleaner, document-access-traces, removable-or-cloud, timestamp-inconsistency
- img2 seed 9999: anti-forensic-cleaner, document-access-traces, removable-or-cloud, timestamp-inconsistency
- img2 seed 7: anti-forensic-cleaner, document-access-traces, removable-or-cloud, timestamp-inconsistency
- img2 seed 2024: anti-forensic-cleaner, document-access-traces, removable-or-cloud, timestamp-inconsistency
- img3 seed 42: document-access-traces, removable-or-cloud, timestamp-inconsistency
- img3 seed 1337: document-access-traces, removable-or-cloud, timestamp-inconsistency
- img3 seed 9999: document-access-traces, removable-or-cloud, timestamp-inconsistency
- img3 seed 7: document-access-traces, removable-or-cloud, timestamp-inconsistency
- img3 seed 2024: document-access-traces, removable-or-cloud, timestamp-inconsistency

Confidence of each recommendation at seed 42, 15 % then 20 %:

- img1: document-access-traces: medium -> medium; hacking-tools: medium -> medium; removable-or-cloud: low -> low; timestamp-inconsistency: high -> high
- img2: anti-forensic-cleaner: high -> high; document-access-traces: medium -> medium; removable-or-cloud: high -> high; timestamp-inconsistency: low -> low
- img3: document-access-traces: medium -> medium; removable-or-cloud: high -> high; timestamp-inconsistency: low -> low

## 5. OS availability check (static)

Each command emitted for a disk is scanned for tools and syntax the detected OS lacks: XP = cmd.exe only (no PowerShell, no auditpol, no wevtutil, no netsh advfirewall); Win7 = PowerShell 2.0 (no later cmdlets or parameters, no simplified Where-Object syntax); Win10 = PowerShell 5.1. Commands the generator already left out for an OS are listed in the playbook and not counted.

| Disk | OS detected | Commands checked | Violations |
|---|---|---|---|
| img1 | Microsoft Windows XP (xp) | 44 | 0 |
| img2 | Windows 7 Ultimate (win7) | 42 | 0 |
| img3 | Windows 10 Education (win10) | 32 | 0 |

No violations found.

Scope of the check: it is a pattern scan, not an execution; it cannot prove a command works, only that it uses nothing known to be missing on that OS. Two XP commands carry edition notes in the playbook (`tasklist` and `eventquery.vbs` need XP Professional).
