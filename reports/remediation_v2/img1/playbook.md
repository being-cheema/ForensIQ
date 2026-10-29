+--------------------------------------------------------------------------------------------------+
| ADVICE FOR THE LIVE ENVIRONMENT THIS DISK CAME FROM                                              |
| Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).    |
| Commands that change the system are commented out in the scripts and marked below.               |
+--------------------------------------------------------------------------------------------------+

# Containment playbook: Image 1: XP Hacking (SCHARDT.001)

- Detected OS: **Microsoft Windows XP** (version 5.1, build 2600)
- Detected by: SOFTWARE hive, Microsoft\Windows NT\CurrentVersion: ProductName, CurrentVersion, CurrentBuildNumber, CSDVersion. Path check: profiles under 'Documents and Settings' (1288 paths), none under 'Users'; system folder 'WINDOWS' (8721).
- Shell for the scripts: cmd.exe only (no PowerShell on this OS)
- Operating point: Isolation Forest, 23 features, 15% budget (recommended); the 20% budget is shown after it.

## 15% budget (1,766 flagged files) - recommended

### 1. Network-attack or password tools present: cain, ethereal, whois, netstumbler, anonymizer

- Technique: T1588.002 Obtain Capabilities: Tool
- Confidence: **high**. 152 flagged files name cain, ethereal, whois, netstumbler, anonymizer; 7 Prefetch records and 5 executables are among the listed ones.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 152 flagged files name cain, ethereal, whois, netstumbler, anonymizer.

Supporting flagged files (rank, path):

- 83  `/WINDOWS/Prefetch/CAIN.EXE-23D61279.pf`
- 85  `/Program Files/Ethereal/ethereal.exe`
- 91  `/WINDOWS/Prefetch/WHOIS.EXE-38443FF6.pf`
- 104  `/Program Files/Cain/Cain.exe`
- 115  `/WINDOWS/Prefetch/ETHEREAL-SETUP-0.10.6.EXE-1D932600.pf`
- 124  `/WINDOWS/Prefetch/WHOIS.EXE-3AFF2064.pf`
- 150  `/WINDOWS/Prefetch/CAIN25B45.EXE-056F3A6E.pf`
- 158  `/WINDOWS/Prefetch/NETSTUMBLER.EXE-0BFEE568.pf`
- 178  `/WINDOWS/Prefetch/ETHEREAL.EXE-1C148EEF.pf`
- 201  `/Program Files/Whois/whois.exe`

Actions:

1. Confirm with security staff whether cain, ethereal, whois, netstumbler, anonymizer are authorised on this machine; if a security team did not install them, treat as unauthorised.
2. Copy the tool folders, the Prefetch records and the event logs to external media before removing anything.
3. Packet-capture or sniffing tools can read passwords crossing the network segment: list the accounts that logged in on that segment after the install date and reset their passwords (approval required).
4. Password-cracking tools were present: assume the local account hashes (SAM) are exposed and reset the local passwords.
5. Review firewall and intrusion-detection logs for this host's address from the first Prefetch run time onward.
6. Quarantine rather than delete the tools once the copies are safe (approval required).

Commands:

- List the install folder C:\Program Files\Ethereal [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Ethereal"
  ```

- List the install folder C:\Program Files\Cain [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Cain"
  ```

- List the install folder C:\Program Files\Whois [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Whois"
  ```

- List the install folder C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar [READ-ONLY]

  ```bat
  dir /a /s "C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar"
  ```

- List Prefetch records (proof of execution) for the named tools [READ-ONLY]

  ```bat
  dir "%SystemRoot%\Prefetch" /a /t:w | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"
  ```

- Check whether the WinPcap capture driver service is installed [READ-ONLY]

  ```bat
  sc query npf
  ```

- Show running processes that match the tool names [READ-ONLY]

  ```bat
  tasklist /v | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"
  ```

  Note: XP: tasklist is in XP Professional only.

- Show open network connections and owning process IDs [READ-ONLY]

  ```bat
  netstat -ano
  ```

- List administrators on the host [READ-ONLY]

  ```bat
  net localgroup administrators
  ```

- Stop and disable the capture driver (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  sc stop npf & sc config npf start= disabled
  ```

  Note: Only if the driver exists and the tool is confirmed unauthorised.

- Move C:\Program Files\Ethereal to a quarantine folder instead of deleting it (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  move "C:\Program Files\Ethereal" "D:\quarantine\Ethereal"
  ```

  Note: Keep the files: they are exhibits.

- Move C:\Program Files\Cain to a quarantine folder instead of deleting it (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  move "C:\Program Files\Cain" "D:\quarantine\Cain"
  ```

  Note: Keep the files: they are exhibits.

- Reset the password of Mr. Evil, the profile that holds the tools (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "Mr. Evil" *
  ```

  Note: Prompts for the new password.

### 2. Device-install logs are present

- Technique: none claimed
- Confidence: **low**. The 1 flagged file(s) are only Windows' own setupapi / usbstor files, which exist on every install. They become evidence only if they list removable devices.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 1 flagged files; 0 client-specific, 1 generic OS files among the 1 listed.

Supporting flagged files (rank, path):

- 307  `/WINDOWS/setupapi.log`  (generic OS file)

Actions:

1. Review the removable-device history for any device serials; the extractor found none on this disk, so start from the registry and setup log commands below.
2. No containment is advised: these are generic OS files. Only act if the setup log lists removable disks.

Commands:

- List every USB storage device the host has seen (vendor, product, serial) [READ-ONLY]

  ```bat
  reg query HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR /s
  ```

- List the volumes and drive letters Windows mapped to those devices [READ-ONLY]

  ```bat
  reg query HKLM\SYSTEM\MountedDevices
  ```

- Read the device-install log for first-connection times of those serials [READ-ONLY]

  ```bat
  findstr /i /c:"Disk&Ven" "%SystemRoot%\setupapi.log"
  ```

  Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

### 3. Recently opened documents are recorded for Mr. Evil

- Technique: none claimed
- Confidence: **medium**. 10 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 10 flagged .lnk or jump-list files under profile(s) Mr. Evil.

Supporting flagged files (rank, path):

- 248  `/Documents and Settings/Mr. Evil/Recent/keys.lnk`
- 313  `/Documents and Settings/Mr. Evil/Recent/GhostWare.lnk`
- 314  `/Documents and Settings/Mr. Evil/Recent/channels.lnk`
- 352  `/Documents and Settings/Mr. Evil/Recent/channels (2).lnk`
- 372  `/Documents and Settings/Mr. Evil/Recent/Anonyymizer.lnk`
- 397  `/Documents and Settings/Mr. Evil/Recent/Receipt.lnk`
- 407  `/Documents and Settings/All Users/Start Menu/Programs/mIRC/Readme.txt.lnk`
- 417  `/Documents and Settings/All Users/Start Menu/Programs/mIRC/Versions.txt.lnk`
- 446  `/Documents and Settings/Mr. Evil/Recent/Temp on m1200 (4.12.220.254).lnk`
- 491  `/Documents and Settings/Mr. Evil/Recent/yng13.lnk`

Actions:

1. Copy the Recent folder and Jump List stores of Mr. Evil to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the Mr. Evil Recent-documents folder, newest first [READ-ONLY]

  ```bat
  dir /a /o-d /t:w "C:\Documents and Settings\Mr. Evil\Recent"
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```bat
  net user "Mr. Evil"
  ```

### 4. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **high**. 128 files with creation earlier than the filename-record time by over 1 h; enrichment 2.76 over the disk rate (Fisher p 4.5e-30).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 128 flagged files; enrichment 2.76 over the disk rate (7.43% of flagged against 2.70% of the disk).

Supporting flagged files (rank, path):

- 23  `/Documents and Settings/Mr. Evil/Local Settings/Temp/Temporary Directory 1 for powertoysetup.zip/PowerToySetup.exe`
- 53  `/Program Files/Look@LAN/LookAtHost.exe`
- 59  `/Program Files/Look@LAN/LookAtLan.exe`
- 85  `/Program Files/Ethereal/ethereal.exe`
- 247  `/Program Files/Common Files/Microsoft Shared/Web Server Extensions/40/BIN/1033/FPEXT.MSG`
- 312  `/Program Files/Ethereal/iconv.dll`
- 345  `/Program Files/Network Stumbler/NetStumbler.exe`
- 375  `/WINDOWS/system32/config/system`
- 378  `/Program Files/Ethereal/libgtk-win32-2.0-0.dll`
- 386  `/Program Files/WinPcap/daemon_mgm.exe`

Actions:

1. Copy $MFT, $LogFile and $UsnJrnl:$J from an image of the volume, not from the live disk.
2. Offline, compare standard-information and filename-record times for the listed files with an MFT parser; a creation time earlier than the filename-record time is the pattern to confirm.
3. Cross-check against the $UsnJrnl and $LogFile: a file whose visible times predate its first journal entry was probably altered.
4. Turn on file-system auditing going forward if the audit policy shows it is off (approval required).

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of PowerToySetup.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe" & dir /a /t:w "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe"
  ```

- Read the visible timestamps of LookAtHost.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Program Files\Look@LAN\LookAtHost.exe" & dir /a /t:w "C:\Program Files\Look@LAN\LookAtHost.exe"
  ```

- Read the visible timestamps of LookAtLan.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Program Files\Look@LAN\LookAtLan.exe" & dir /a /t:w "C:\Program Files\Look@LAN\LookAtLan.exe"
  ```

Not applicable on this OS:

- Show the current file-system audit policy - auditpol.exe is not part of Windows XP (Resource Kit only); use Local Security Policy > Audit object access
- Turn on file-system auditing (changes the system) - auditpol.exe is not part of Windows XP; enable 'Audit object access' in Local Security Policy

Not triggered:

- Wiper or cleaner executed: 0 of the 1,766 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.

## 20% budget (2,355 flagged files)

### 1. Network-attack or password tools present: cain, ethereal, whois, netstumbler, anonymizer

- Technique: T1588.002 Obtain Capabilities: Tool
- Confidence: **high**. 256 flagged files name cain, ethereal, whois, netstumbler, anonymizer; 7 Prefetch records and 5 executables are among the listed ones.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 256 flagged files name cain, ethereal, whois, netstumbler, anonymizer.

Supporting flagged files (rank, path):

- 83  `/WINDOWS/Prefetch/CAIN.EXE-23D61279.pf`
- 85  `/Program Files/Ethereal/ethereal.exe`
- 91  `/WINDOWS/Prefetch/WHOIS.EXE-38443FF6.pf`
- 104  `/Program Files/Cain/Cain.exe`
- 115  `/WINDOWS/Prefetch/ETHEREAL-SETUP-0.10.6.EXE-1D932600.pf`
- 124  `/WINDOWS/Prefetch/WHOIS.EXE-3AFF2064.pf`
- 150  `/WINDOWS/Prefetch/CAIN25B45.EXE-056F3A6E.pf`
- 158  `/WINDOWS/Prefetch/NETSTUMBLER.EXE-0BFEE568.pf`
- 178  `/WINDOWS/Prefetch/ETHEREAL.EXE-1C148EEF.pf`
- 201  `/Program Files/Whois/whois.exe`

Actions:

1. Confirm with security staff whether cain, ethereal, whois, netstumbler, anonymizer are authorised on this machine; if a security team did not install them, treat as unauthorised.
2. Copy the tool folders, the Prefetch records and the event logs to external media before removing anything.
3. Packet-capture or sniffing tools can read passwords crossing the network segment: list the accounts that logged in on that segment after the install date and reset their passwords (approval required).
4. Password-cracking tools were present: assume the local account hashes (SAM) are exposed and reset the local passwords.
5. Review firewall and intrusion-detection logs for this host's address from the first Prefetch run time onward.
6. Quarantine rather than delete the tools once the copies are safe (approval required).

Commands:

- List the install folder C:\Program Files\Ethereal [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Ethereal"
  ```

- List the install folder C:\Program Files\Cain [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Cain"
  ```

- List the install folder C:\Program Files\Whois [READ-ONLY]

  ```bat
  dir /a /s "C:\Program Files\Whois"
  ```

- List the install folder C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar [READ-ONLY]

  ```bat
  dir /a /s "C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar"
  ```

- List Prefetch records (proof of execution) for the named tools [READ-ONLY]

  ```bat
  dir "%SystemRoot%\Prefetch" /a /t:w | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"
  ```

- Check whether the WinPcap capture driver service is installed [READ-ONLY]

  ```bat
  sc query npf
  ```

- Show running processes that match the tool names [READ-ONLY]

  ```bat
  tasklist /v | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"
  ```

  Note: XP: tasklist is in XP Professional only.

- Show open network connections and owning process IDs [READ-ONLY]

  ```bat
  netstat -ano
  ```

- List administrators on the host [READ-ONLY]

  ```bat
  net localgroup administrators
  ```

- Stop and disable the capture driver (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  sc stop npf & sc config npf start= disabled
  ```

  Note: Only if the driver exists and the tool is confirmed unauthorised.

- Move C:\Program Files\Ethereal to a quarantine folder instead of deleting it (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  move "C:\Program Files\Ethereal" "D:\quarantine\Ethereal"
  ```

  Note: Keep the files: they are exhibits.

- Move C:\Program Files\Cain to a quarantine folder instead of deleting it (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  move "C:\Program Files\Cain" "D:\quarantine\Cain"
  ```

  Note: Keep the files: they are exhibits.

- Reset the password of Mr. Evil, the profile that holds the tools (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "Mr. Evil" *
  ```

  Note: Prompts for the new password.

### 2. Device-install logs are present

- Technique: none claimed
- Confidence: **low**. The 1 flagged file(s) are only Windows' own setupapi / usbstor files, which exist on every install. They become evidence only if they list removable devices.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 1 flagged files; 0 client-specific, 1 generic OS files among the 1 listed.

Supporting flagged files (rank, path):

- 307  `/WINDOWS/setupapi.log`  (generic OS file)

Actions:

1. Review the removable-device history for any device serials; the extractor found none on this disk, so start from the registry and setup log commands below.
2. No containment is advised: these are generic OS files. Only act if the setup log lists removable disks.

Commands:

- List every USB storage device the host has seen (vendor, product, serial) [READ-ONLY]

  ```bat
  reg query HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR /s
  ```

- List the volumes and drive letters Windows mapped to those devices [READ-ONLY]

  ```bat
  reg query HKLM\SYSTEM\MountedDevices
  ```

- Read the device-install log for first-connection times of those serials [READ-ONLY]

  ```bat
  findstr /i /c:"Disk&Ven" "%SystemRoot%\setupapi.log"
  ```

  Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

### 3. Recently opened documents are recorded for Mr. Evil

- Technique: none claimed
- Confidence: **medium**. 10 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 10 flagged .lnk or jump-list files under profile(s) Mr. Evil.

Supporting flagged files (rank, path):

- 248  `/Documents and Settings/Mr. Evil/Recent/keys.lnk`
- 313  `/Documents and Settings/Mr. Evil/Recent/GhostWare.lnk`
- 314  `/Documents and Settings/Mr. Evil/Recent/channels.lnk`
- 352  `/Documents and Settings/Mr. Evil/Recent/channels (2).lnk`
- 372  `/Documents and Settings/Mr. Evil/Recent/Anonyymizer.lnk`
- 397  `/Documents and Settings/Mr. Evil/Recent/Receipt.lnk`
- 407  `/Documents and Settings/All Users/Start Menu/Programs/mIRC/Readme.txt.lnk`
- 417  `/Documents and Settings/All Users/Start Menu/Programs/mIRC/Versions.txt.lnk`
- 446  `/Documents and Settings/Mr. Evil/Recent/Temp on m1200 (4.12.220.254).lnk`
- 491  `/Documents and Settings/Mr. Evil/Recent/yng13.lnk`

Actions:

1. Copy the Recent folder and Jump List stores of Mr. Evil to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the Mr. Evil Recent-documents folder, newest first [READ-ONLY]

  ```bat
  dir /a /o-d /t:w "C:\Documents and Settings\Mr. Evil\Recent"
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```bat
  net user "Mr. Evil"
  ```

### 4. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **high**. 227 files with creation earlier than the filename-record time by over 1 h; enrichment 3.86 over the disk rate (Fisher p 7.1e-99).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 227 flagged files; enrichment 3.86 over the disk rate (10.41% of flagged against 2.70% of the disk).

Supporting flagged files (rank, path):

- 23  `/Documents and Settings/Mr. Evil/Local Settings/Temp/Temporary Directory 1 for powertoysetup.zip/PowerToySetup.exe`
- 53  `/Program Files/Look@LAN/LookAtHost.exe`
- 59  `/Program Files/Look@LAN/LookAtLan.exe`
- 85  `/Program Files/Ethereal/ethereal.exe`
- 247  `/Program Files/Common Files/Microsoft Shared/Web Server Extensions/40/BIN/1033/FPEXT.MSG`
- 312  `/Program Files/Ethereal/iconv.dll`
- 345  `/Program Files/Network Stumbler/NetStumbler.exe`
- 375  `/WINDOWS/system32/config/system`
- 378  `/Program Files/Ethereal/libgtk-win32-2.0-0.dll`
- 386  `/Program Files/WinPcap/daemon_mgm.exe`

Actions:

1. Copy $MFT, $LogFile and $UsnJrnl:$J from an image of the volume, not from the live disk.
2. Offline, compare standard-information and filename-record times for the listed files with an MFT parser; a creation time earlier than the filename-record time is the pattern to confirm.
3. Cross-check against the $UsnJrnl and $LogFile: a file whose visible times predate its first journal entry was probably altered.
4. Turn on file-system auditing going forward if the audit policy shows it is off (approval required).

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of PowerToySetup.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe" & dir /a /t:w "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe"
  ```

- Read the visible timestamps of LookAtHost.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Program Files\Look@LAN\LookAtHost.exe" & dir /a /t:w "C:\Program Files\Look@LAN\LookAtHost.exe"
  ```

- Read the visible timestamps of LookAtLan.exe [READ-ONLY]

  ```bat
  dir /a /t:c "C:\Program Files\Look@LAN\LookAtLan.exe" & dir /a /t:w "C:\Program Files\Look@LAN\LookAtLan.exe"
  ```

Not applicable on this OS:

- Show the current file-system audit policy - auditpol.exe is not part of Windows XP (Resource Kit only); use Local Security Policy > Audit object access
- Turn on file-system auditing (changes the system) - auditpol.exe is not part of Windows XP; enable 'Audit object access' in Local Security Policy

Not triggered:

- Wiper or cleaner executed: 0 of the 2,355 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.
