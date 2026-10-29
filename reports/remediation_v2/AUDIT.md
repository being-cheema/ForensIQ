# Audit of the old remediation stage

Scope: `remediation.py` (unchanged, still used by `run_pipeline.py`) against what an earlier description said its scripts do, and against the three source operating systems. Checked by reading the code and re-running its trigger logic on `runs/img1`, `runs/img2`, `runs/img3`.

## 1. Claimed behaviour against actual code

| Script | The earlier description said | What the code does | Problem |
|---|---|---|---|
| `remediate_credentials.ps1` | Kills LSASS credential dumpers | Two `reg add` lines: LSA RunAsPPL=1 and WDigest UseLogonCredential=0. No process is listed or killed. | RunAsPPL needs Windows 8.1 or later and does nothing on XP; the WDigest value only matters on Win7/8 with KB2871997. XP cannot open a .ps1 file at all. |
| `remediate_credentials.ps1` | Resets passwords | No password is read or changed in any generated script. (A separate hand-kept remediate_account.ps1 that disables a hard-coded account is not produced by remediation.py.) | Claim has no code behind it. |
| `remediate_credentials.ps1` | Purges Kerberos tickets | No `klist purge` or equivalent anywhere. | Claim has no code behind it. |
| `remediate_network.ps1` | Disables promiscuous mode | `netsh advfirewall set allprofiles state on`, then a firewall rule blocking outbound TCP 4444, 1337, 8888. | Promiscuous mode is never touched. `netsh advfirewall` does not exist on XP (it uses `netsh firewall`). The three ports are a guess, not taken from any file. |
| `remediate_network.ps1` | Stops the npf (WinPcap) service | No `sc` or `Stop-Service` call. | Claim has no code behind it. |
| `remediate_timestamp.ps1` | Extracts $SI vs $FN timestamps | One line: `auditpol /set /subcategory:"File System" /success:enable /failure:enable`. | Extracts nothing. auditpol is not on XP, and the setting records nothing until audit entries are put on folders. |
| `remediate_usb.ps1` | USB storage disabled across the system | Sets USBSTOR Start=4 with Set-ItemProperty, runs gpupdate /force, exports USBSTOR names. | It changes the live system with no approval step and blocks legitimate devices. PowerShell does not exist on XP. |
| `remediate_log_clearing.ps1` | Audit policy reinforced for log-tampering protection | Reads event 1102 with Get-WinEvent and enables the 'Security System Extension' audit subcategory. | That subcategory logs security-package loading, not log clearing, and protects nothing. Get-WinEvent and auditpol do not exist on XP. |
| `remediate_ransomware.ps1` | VSS snapshot created and process mitigations enforced | `vssadmin create shadow /for=C:` and `Set-ProcessMitigation -System -Enable DEP`. | `vssadmin create shadow` works on Windows Server only; Set-ProcessMitigation needs Windows 10 and DEP is already on. |
| `remediate_malware.ps1` | Defender signatures updated and scan triggered | `Start-MpScan` and `Update-MpSignature`. | The Defender cmdlets are Windows 8+ only; XP and Win7 do not have them. |

## 2. Trigger faults

| Breach type | Rule in the code | Fault | Fired on |
|---|---|---|---|
| `timestamp_backdating` | delta_mb < 60 on more than 50 flagged files | A small modify-to-birth gap is the normal state of installed or copied files; it says nothing about $SI vs $FN, and it fires on any large flagged set. | Image 1 (226 of 589 flagged rows have delta_mb < 60); Image 2 (2,467 of 4,240 flagged rows have delta_mb < 60); Image 3 (1,754 of 8,306 flagged rows have delta_mb < 60) |
| `log_clearing` | more than 3 hours with no log events (log_gap) | Hours with no events are the norm on a workstation that is switched off or idle; it is not an event-log clearing record (event 1102). | Image 2 (17,428 no-event hours); Image 3 (80 no-event hours) |
| `usb_exfiltration` | usb_devices.txt exists, or any flagged row has usb_present | The extractor always writes usb_devices.txt and usb_present is set for every flagged row, so this fired on every disk whether or not a device was ever connected. | Image 1 (usb_devices.txt present; usb_present set on 589 of 589 flagged rows); Image 2 (usb_devices.txt present; usb_present set on 4,240 of 4,240 flagged rows); Image 3 (usb_devices.txt present; usb_present set on 8,306 of 8,306 flagged rows) |
| `credential_dumping` | any flagged row has credential_tool | credential_tool is a per-disk constant: either every flagged row has it or none does. It names no file. | Image 1 (credential_tool set on 589 of 589 flagged rows) |
| `powershell_attack` | any flagged row has powershell_exec | No file is named; never fired on these disks. | none of the three disks |
| `network_beaconing` | any flagged row has sniffer_tool | sniffer_tool is a per-disk constant, like credential_tool; no beaconing was measured. | Image 1 (sniffer_tool set on 589 of 589 flagged rows) |
| `malware_detected` | at least one flagged .exe in a temp path | One executable in a temp folder is routine (installers, updaters); this fires on every disk. | Image 1 (1 flagged executable(s) in temp paths); Image 2 (35 flagged executable(s) in temp paths); Image 3 (34 flagged executable(s) in temp paths) |
| `ransomware` | more than 20 flagged archives | Archives are not encryption. It fires on the XP hacking case, which contains no ransomware. | Image 1 (44 flagged archives) |
| `persistence` | any flagged row has script_host | No file is named; never fired on these disks. | none of the three disks |

## 3. The scripts cannot run on the source OS

- Image 1 is Windows XP (5.1, build 2600). XP has no PowerShell: every old script is a `.ps1` file.
- Cmdlets and tools used by the old scripts that XP lacks: `Get-WinEvent`, `Set-ItemProperty` (PowerShell), `auditpol`, `netsh advfirewall`, `Start-MpScan`.
- Win10-only or Server-only features: `Set-ProcessMitigation` (Windows 10), `vssadmin create shadow` (Windows Server), RunAsPPL (Windows 8.1+).
- Nothing in any old script is tied to a specific file. The new version cites the flagged files and their ranks for every recommendation.

## 4. What replaced it

`remediation_v2.py` takes only the fair indicators from `trust_eval.py` (Isolation Forest, 23 features, 15% and 20% budgets), detects the Windows version from the SOFTWARE hive, and writes advice that is read-only by default, OS-specific, tied to named files, and marked for human approval. See `reports/remediation_v2/<img>/playbook.md`.
