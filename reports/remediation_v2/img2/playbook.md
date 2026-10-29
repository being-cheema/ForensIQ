+--------------------------------------------------------------------------------------------------+
| ADVICE FOR THE LIVE ENVIRONMENT THIS DISK CAME FROM                                              |
| Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).    |
| Commands that change the system are commented out in the scripts and marked below.               |
+--------------------------------------------------------------------------------------------------+

# Containment playbook: Image 2: Win7 Data Leakage

- Detected OS: **Windows 7 Ultimate** (version 6.1, build 7601, Service Pack 1)
- Detected by: SOFTWARE hive, Microsoft\Windows NT\CurrentVersion: ProductName, CurrentVersion, CurrentBuildNumber, CSDVersion. Path check: profiles under 'Users' (5786 paths); system folder 'Windows' (72059).
- Shell for the scripts: Windows PowerShell 2.0-compatible cmdlets only
- Operating point: Isolation Forest, 23 features, 15% budget (recommended); the 20% budget is shown after it.

## 15% budget (12,753 flagged files) - recommended

### 1. A data-wiping or cleaning tool was installed and has run

- Technique: T1070.004 Indicator Removal: File Deletion
- Confidence: **high**. 8 flagged files name a wiper/cleaner; 4 are Prefetch entries, which prove the program ran.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 8 of the flagged files name a cleaner (eraser, ccleaner); 4 Prefetch records.

Supporting flagged files (rank, path):

- 349  `/Program Files/Eraser/Eraser.exe`
- 657  `/Windows/Prefetch/CCLEANER64.EXE-779BD542.pf`
- 724  `/Windows/Prefetch/ERASER.EXE-CE61944A.pf`
- 889  `/Windows/Prefetch/CCSETUP504.EXE-6BA2F6A1.pf`
- 928  `/Windows/Prefetch/ERASER 6.2.0.2962.EXE-BE552234.pf`
- 1,333  `/Users/informant/Desktop/Download/Eraser 6.2.0.2962.exe`
- 1,386  `/Users/informant/Desktop/Download/ccsetup504.exe`
- 1,432  `/Windows/Installer/{C6E287F1-2E47-45F0-BB51-94F815CFFB48}/Eraser.exe`  (generic OS file)

Actions:

1. Treat this as evidence of an attempt to destroy data: the flagged files name eraser, ccleaner.
2. Copy the Prefetch folder, the event logs and the scheduled-task list to write-protected external media before anything else is touched.
3. From the Prefetch records, establish when the tool last ran and how many times; compare with the incident window.
4. Ask the account owner and their manager whether the tool was authorised for this machine.
5. Check the same user's other machines and any file shares for the same tool.
6. Do not launch the tool. Removal is optional, and only after the logs above are safely copied (approval required).

Commands:

- List Prefetch records (proof of execution and last run) for the named tools [READ-ONLY]

  ```powershell
  Get-ChildItem "$env:SystemRoot\Prefetch" | Where-Object { $_.Name -match 'eraser|ccleaner' } | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize
  ```

- Look for scheduled wipe tasks [READ-ONLY]

  ```bat
  schtasks /query /fo LIST /v | findstr /i "ERASER CCLEANER TASKNAME"
  ```

- Find the installed program entries to learn the exact name and version [READ-ONLY]

  ```bat
  reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s | findstr /i "DisplayName" | findstr /i "ERASER CCLEANER"
  ```

- Copy the Security event log to external media before anything else changes [READ-ONLY]

  ```bat
  wevtutil epl Security Security.evtx
  ```

  Note: Writes a copy to the current folder: run it from removable media you control, not the host disk. XP: eventquery.vbs ships with XP Professional only; otherwise take a forensic image.

- Remove the installed cleaner (changes the system) [CHANGES SYSTEM - requires approval]

  ```powershell
  (Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like 'eraser*' }).Uninstall()
  ```

  Note: Only after the owner and legal sign off; uninstalling destroys the tool's own logs and schedule.

### 2. Removable-device and cloud-sync artifacts

- Technique: T1052.001 Exfiltration Over Physical Medium: Exfiltration over USB
- Confidence: **high**. 15 client-specific files from Google Drive, iCloud are in the flagged set (36 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 36 flagged files; 15 client-specific, 10 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 54  `/Program Files (x86)/Google/Drive/googledrivesync.exe`
- 238  `/Users/informant/Downloads/icloudsetup.exe`
- 264  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log`
- 564  `/Windows/Prefetch/GOOGLEDRIVESYNC.EXE-841A0D94.pf`
- 645  `/Users/informant/Downloads/googledrivesync.exe`
- 732  `/Users/informant/AppData/Local/Temp/icloudsetupE88.log`
- 875  `/Users/informant/AppData/Local/Google/Drive/user_default/cloud_graph/dict_2.db`
- 1,626  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_config.db`
- 1,742  `/Users/informant/AppData/Local/Google/Drive/user_default/snapshot.db`
- 1,823  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log`

Actions:

1. Review the removable-device history. The extracted list names: USB Device: Disk&Ven_VMware_&Prod_VMware_Virtual_S; USB Device: Disk&Ven_SanDisk&Prod_Cruzer_Fit&Rev_2.01; USB Device: Disk&Ven_Dell&Prod_VIRTUAL_DISK; Device Serial Signature: 4C530012450531101593; Device Serial Signature: 4C530012550531106501. Match each serial to an owner and to the incident window.
2. A sync client is present: Google Drive, iCloud. Identify the signed-in account from its config database or logs and ask the provider (or tenant admin) for sharing, link and download audit logs.
3. If the device or account is not authorised, sign the cloud account out and revoke its sessions at the provider (not a local command).
4. Consider resetting the passwords of informant (approval required).

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

  ```powershell
  Select-String -Path "$env:SystemRoot\inf\setupapi.dev.log" -Pattern 'Disk&Ven' | Select-Object -First 100 LineNumber, Line | Format-List
  ```

  Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.

- Show the Drive sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Google\Drive" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Downloads sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\informant\Downloads" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

- Block new USB storage devices (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  reg add HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR /v Start /t REG_DWORD /d 4 /f
  ```

  Note: Stops all USB mass storage, including legitimate devices; set Start back to 3 to undo. Needs a policy decision.

- Reset the password of informant, whose profile holds the flagged files (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "informant" *
  ```

  Note: Prompts for the new password; do not put it in the script.

### 3. Recently opened documents are recorded for informant, admin11

- Technique: none claimed
- Confidence: **medium**. 49 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 49 flagged .lnk or jump-list files under profile(s) informant, admin11.

Supporting flagged files (rank, path):

- 546  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/Resignation_Letter_(Iaman_Informant).docx.LNK`
- 651  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Resignation_Letter_(Iaman_Informant).docx.lnk`
- 874  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/winter_whether_advisory.zip.lnk`
- 918  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/(secret_project)_pricing_decision.xlsx.LNK`
- 970  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/[secret_project]_final_meeting.pptx.LNK`
- 979  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_final_meeting.pptx.lnk`
- 980  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/(secret_project)_pricing_decision.xlsx.lnk`
- 1,008  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_design_concept.lnk`
- 1,033  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/final.lnk`
- 1,046  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_proposal.lnk`

Actions:

1. Copy the Recent folder and Jump List stores of informant, admin11 to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the informant Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the admin11 Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\admin11\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the informant Jump List stores [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```powershell
  net user "informant"; net user "admin11"
  ```

### 4. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **low**. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.44).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 4641 flagged files; enrichment 0.44 over the disk rate (37.64% of flagged against 84.98% of the disk).

Supporting flagged files (rank, path):

- 3  `/Windows/System32/config/SYSTEM`
- 4  `/Windows/System32/SMI/Store/Machine/SCHEMA.DAT`
- 5  `/Windows/System32/config/SOFTWARE`
- 6  `/Windows/System32/config/COMPONENTS`
- 10  `/Windows/System32/catroot2/edb.log`
- 12  `/Windows/Microsoft.NET/Framework/v4.0.30319/clr.dll`
- 17  `/Windows/System32/Msdtc/MSDTC.LOG`
- 21  `/Windows/System32/config/SAM`
- 46  `/Windows/Microsoft.NET/Framework/v4.0.30319/ngen.exe`
- 47  `/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe`

Actions:

1. No containment. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.44).
2. Visible timestamps cannot show this; only an offline comparison of the two time sets in the MFT can. The MFT export keeps whole seconds, so the sub-second test cannot run.
3. Do not act on this indicator unless another recommendation here also fires.

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of SCHEMA.DAT [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\System32\SMI\Store\Machine\SCHEMA.DAT" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of edb.log [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\System32\catroot2\edb.log" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of clr.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\Microsoft.NET\Framework\v4.0.30319\clr.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Hacking tools: 0 of the 12,753 flagged files matched: (d) no hacking-tool name among the flagged files.

## 20% budget (17,003 flagged files)

### 1. A data-wiping or cleaning tool was installed and has run

- Technique: T1070.004 Indicator Removal: File Deletion
- Confidence: **high**. 8 flagged files name a wiper/cleaner; 4 are Prefetch entries, which prove the program ran.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 8 of the flagged files name a cleaner (eraser, ccleaner); 4 Prefetch records.

Supporting flagged files (rank, path):

- 349  `/Program Files/Eraser/Eraser.exe`
- 657  `/Windows/Prefetch/CCLEANER64.EXE-779BD542.pf`
- 724  `/Windows/Prefetch/ERASER.EXE-CE61944A.pf`
- 889  `/Windows/Prefetch/CCSETUP504.EXE-6BA2F6A1.pf`
- 928  `/Windows/Prefetch/ERASER 6.2.0.2962.EXE-BE552234.pf`
- 1,333  `/Users/informant/Desktop/Download/Eraser 6.2.0.2962.exe`
- 1,386  `/Users/informant/Desktop/Download/ccsetup504.exe`
- 1,432  `/Windows/Installer/{C6E287F1-2E47-45F0-BB51-94F815CFFB48}/Eraser.exe`  (generic OS file)

Actions:

1. Treat this as evidence of an attempt to destroy data: the flagged files name eraser, ccleaner.
2. Copy the Prefetch folder, the event logs and the scheduled-task list to write-protected external media before anything else is touched.
3. From the Prefetch records, establish when the tool last ran and how many times; compare with the incident window.
4. Ask the account owner and their manager whether the tool was authorised for this machine.
5. Check the same user's other machines and any file shares for the same tool.
6. Do not launch the tool. Removal is optional, and only after the logs above are safely copied (approval required).

Commands:

- List Prefetch records (proof of execution and last run) for the named tools [READ-ONLY]

  ```powershell
  Get-ChildItem "$env:SystemRoot\Prefetch" | Where-Object { $_.Name -match 'eraser|ccleaner' } | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize
  ```

- Look for scheduled wipe tasks [READ-ONLY]

  ```bat
  schtasks /query /fo LIST /v | findstr /i "ERASER CCLEANER TASKNAME"
  ```

- Find the installed program entries to learn the exact name and version [READ-ONLY]

  ```bat
  reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s | findstr /i "DisplayName" | findstr /i "ERASER CCLEANER"
  ```

- Copy the Security event log to external media before anything else changes [READ-ONLY]

  ```bat
  wevtutil epl Security Security.evtx
  ```

  Note: Writes a copy to the current folder: run it from removable media you control, not the host disk. XP: eventquery.vbs ships with XP Professional only; otherwise take a forensic image.

- Remove the installed cleaner (changes the system) [CHANGES SYSTEM - requires approval]

  ```powershell
  (Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like 'eraser*' }).Uninstall()
  ```

  Note: Only after the owner and legal sign off; uninstalling destroys the tool's own logs and schedule.

### 2. Removable-device and cloud-sync artifacts

- Technique: T1052.001 Exfiltration Over Physical Medium: Exfiltration over USB
- Confidence: **high**. 15 client-specific files from Google Drive, iCloud are in the flagged set (105 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 105 flagged files; 15 client-specific, 10 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 54  `/Program Files (x86)/Google/Drive/googledrivesync.exe`
- 238  `/Users/informant/Downloads/icloudsetup.exe`
- 264  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log`
- 564  `/Windows/Prefetch/GOOGLEDRIVESYNC.EXE-841A0D94.pf`
- 645  `/Users/informant/Downloads/googledrivesync.exe`
- 732  `/Users/informant/AppData/Local/Temp/icloudsetupE88.log`
- 875  `/Users/informant/AppData/Local/Google/Drive/user_default/cloud_graph/dict_2.db`
- 1,626  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_config.db`
- 1,742  `/Users/informant/AppData/Local/Google/Drive/user_default/snapshot.db`
- 1,823  `/Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log`

Actions:

1. Review the removable-device history. The extracted list names: USB Device: Disk&Ven_VMware_&Prod_VMware_Virtual_S; USB Device: Disk&Ven_SanDisk&Prod_Cruzer_Fit&Rev_2.01; USB Device: Disk&Ven_Dell&Prod_VIRTUAL_DISK; Device Serial Signature: 4C530012450531101593; Device Serial Signature: 4C530012550531106501. Match each serial to an owner and to the incident window.
2. A sync client is present: Google Drive, iCloud. Identify the signed-in account from its config database or logs and ask the provider (or tenant admin) for sharing, link and download audit logs.
3. If the device or account is not authorised, sign the cloud account out and revoke its sessions at the provider (not a local command).
4. Consider resetting the passwords of informant (approval required).

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

  ```powershell
  Select-String -Path "$env:SystemRoot\inf\setupapi.dev.log" -Pattern 'Disk&Ven' | Select-Object -First 100 LineNumber, Line | Format-List
  ```

  Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.

- Show the Drive sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Google\Drive" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Downloads sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\informant\Downloads" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

- Block new USB storage devices (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  reg add HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR /v Start /t REG_DWORD /d 4 /f
  ```

  Note: Stops all USB mass storage, including legitimate devices; set Start back to 3 to undo. Needs a policy decision.

- Reset the password of informant, whose profile holds the flagged files (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "informant" *
  ```

  Note: Prompts for the new password; do not put it in the script.

### 3. Recently opened documents are recorded for informant, admin11

- Technique: none claimed
- Confidence: **medium**. 49 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 49 flagged .lnk or jump-list files under profile(s) informant, admin11.

Supporting flagged files (rank, path):

- 546  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/Resignation_Letter_(Iaman_Informant).docx.LNK`
- 651  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Resignation_Letter_(Iaman_Informant).docx.lnk`
- 874  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/winter_whether_advisory.zip.lnk`
- 918  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/(secret_project)_pricing_decision.xlsx.LNK`
- 970  `/Users/informant/AppData/Roaming/Microsoft/Office/Recent/[secret_project]_final_meeting.pptx.LNK`
- 979  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_final_meeting.pptx.lnk`
- 980  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/(secret_project)_pricing_decision.xlsx.lnk`
- 1,008  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_design_concept.lnk`
- 1,033  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/final.lnk`
- 1,046  `/Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_proposal.lnk`

Actions:

1. Copy the Recent folder and Jump List stores of informant, admin11 to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the informant Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the admin11 Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\admin11\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the informant Jump List stores [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```powershell
  net user "informant"; net user "admin11"
  ```

### 4. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **low**. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.46).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 6310 flagged files; enrichment 0.46 over the disk rate (39.22% of flagged against 84.98% of the disk).

Supporting flagged files (rank, path):

- 3  `/Windows/System32/config/SYSTEM`
- 4  `/Windows/System32/SMI/Store/Machine/SCHEMA.DAT`
- 5  `/Windows/System32/config/SOFTWARE`
- 6  `/Windows/System32/config/COMPONENTS`
- 10  `/Windows/System32/catroot2/edb.log`
- 12  `/Windows/Microsoft.NET/Framework/v4.0.30319/clr.dll`
- 17  `/Windows/System32/Msdtc/MSDTC.LOG`
- 21  `/Windows/System32/config/SAM`
- 46  `/Windows/Microsoft.NET/Framework/v4.0.30319/ngen.exe`
- 47  `/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe`

Actions:

1. No containment. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.46).
2. Visible timestamps cannot show this; only an offline comparison of the two time sets in the MFT can. The MFT export keeps whole seconds, so the sub-second test cannot run.
3. Do not act on this indicator unless another recommendation here also fires.

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of SCHEMA.DAT [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\System32\SMI\Store\Machine\SCHEMA.DAT" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of edb.log [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\System32\catroot2\edb.log" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of clr.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Windows\Microsoft.NET\Framework\v4.0.30319\clr.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Hacking tools: 0 of the 17,003 flagged files matched: (d) no hacking-tool name among the flagged files.
