+--------------------------------------------------------------------------------------------------+
| ADVICE FOR THE LIVE ENVIRONMENT THIS DISK CAME FROM                                              |
| Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).    |
| Commands that change the system are commented out in the scripts and marked below.               |
+--------------------------------------------------------------------------------------------------+

# Containment playbook: Image 3: Win10 Lone Wolf

- Detected OS: **Windows 10 Education** (version 6.3, build 16299)
- Detected by: SOFTWARE hive, Microsoft\Windows NT\CurrentVersion: ProductName, CurrentVersion, CurrentBuildNumber, CSDVersion. Path check: profiles under 'Users' (14191 paths); system folder 'Windows' (128505).
- Shell for the scripts: Windows PowerShell 5.1
- Operating point: Isolation Forest, 19 features, seed 42; the 20% budget is the headline, the 15% budget is shown for comparison.

## 15% budget (24,916 flagged files)

### 1. Removable-device and cloud-sync artifacts

- Technique: T1567.002 Exfiltration Over Web Service: Exfiltration to Cloud Storage
- Confidence: **high**. 23 client-specific files from Box Sync, Google Drive, Dropbox are in the flagged set (1030 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 1030 flagged files; 23 client-specific, 2 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 74  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/Update/OneDriveSetup.exe`
- 209  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/18.044.0301.0006/OneDriveSetup.exe`
- 212  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7900.log`
- 235  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/sync_log.log`
- 313  `/Program Files (x86)/Dropbox/Update/Download/{CC46080E-4C33-4981-859A-BBA2F780F31E}/46.4.65/DropboxClient_46.4.65.exe`
- 462  `/Program Files/Google/Drive/googledrivesync.exe`
- 480  `/Program Files/Box/Box Sync/cacert.pem`
- 490  `/Program Files (x86)/Dropbox/Client/Qt5WebEngineCore.dll`
- 496  `/Program Files/Box/Box Sync/BoxSync.exe`
- 508  `/Program Files (x86)/Dropbox/Client/icudt56.dll`

Actions:

1. Review the removable-device history. The extracted list names: USB Device: Disk&Ven_SanDisk&Prod_Extreme&Rev_0001; USB Device: Disk&Ven_Samsung&Prod_SSD_850_PRO_512G; Device Serial Signature: AA010603160707470215; Device Serial Signature: AA010215170355310594. Match each serial to an owner and to the incident window.
2. A sync client is present: Box Sync, Google Drive, Dropbox. Identify the signed-in account from its config database or logs and ask the provider (or tenant admin) for sharing, link and download audit logs.
3. If the device or account is not authorised, sign the cloud account out and revoke its sessions at the provider (not a local command).
4. Consider resetting the passwords of jcloudy (approval required).

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

- Show the user_default sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\jcloudy\AppData\Local\Google\Drive\user_default" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Dropbox sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Dropbox" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Box Sync sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\jcloudy\AppData\Local\Box Sync" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

- Reset the password of jcloudy, whose profile holds the flagged files (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "jcloudy" *
  ```

  Note: Prompts for the new password; do not put it in the script.

### 2. Recently opened documents are recorded for jcloudy

- Technique: none claimed
- Confidence: **medium**. 62 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 62 flagged .lnk or jump-list files under profile(s) jcloudy.

Supporting flagged files (rank, path):

- 1,308  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Downloads.lnk`
- 3,016  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/OneDrive.lnk`
- 3,406  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Planning.LNK`
- 3,904  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Sheep.lnk`
- 4,054  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DemGun.lnk`
- 4,243  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Planning.lnk`
- 4,328  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Desktop.LNK`
- 4,568  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DeathToll.lnk`
- 4,930  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/AIRPORT INFORMATION.lnk`
- 5,104  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Templates.LNK`

Actions:

1. Copy the Recent folder and Jump List stores of jcloudy to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the jcloudy Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the jcloudy Jump List stores [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```powershell
  net user "jcloudy"
  ```

### 3. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **low**. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.82).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 10838 flagged files; enrichment 0.82 over the disk rate (46.59% of flagged against 56.62% of the disk).

Supporting flagged files (rank, path):

- 7  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll`
- 91  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/adodb.dll`
- 120  `/Windows/System32/config/COMPONENTS`
- 122  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/stdole.dll`
- 129  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.stdformat.dll`
- 130  `/Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinEUDP_RoamUp.lex`
- 131  `/Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll`
- 132  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll`
- 138  `/Windows/SysWOW64/opencl.dll`
- 140  `/Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinUDL_RoamUp.dat`

Actions:

1. No containment. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.82).
2. Visible timestamps cannot show this; only an offline comparison of the two time sets in the MFT can. The MFT export keeps whole seconds, so the sub-second test cannot run.
3. Do not act on this indicator unless another recommendation here also fires.

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of Microsoft.mshtml.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\Microsoft.mshtml.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of adodb.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\adodb.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of stdole.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\stdole.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Wiper or cleaner executed: 0 of the 24,916 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.
- Hacking tools: 0 of the 24,916 flagged files matched: (d) no hacking-tool name among the flagged files.

## 20% budget (33,222 flagged files) - headline

### 1. Removable-device and cloud-sync artifacts

- Technique: T1567.002 Exfiltration Over Web Service: Exfiltration to Cloud Storage
- Confidence: **high**. 23 client-specific files from Box Sync, Google Drive, Dropbox are in the flagged set (1442 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 1442 flagged files; 23 client-specific, 2 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 74  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/Update/OneDriveSetup.exe`
- 209  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/18.044.0301.0006/OneDriveSetup.exe`
- 212  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7900.log`
- 235  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/sync_log.log`
- 313  `/Program Files (x86)/Dropbox/Update/Download/{CC46080E-4C33-4981-859A-BBA2F780F31E}/46.4.65/DropboxClient_46.4.65.exe`
- 462  `/Program Files/Google/Drive/googledrivesync.exe`
- 480  `/Program Files/Box/Box Sync/cacert.pem`
- 490  `/Program Files (x86)/Dropbox/Client/Qt5WebEngineCore.dll`
- 496  `/Program Files/Box/Box Sync/BoxSync.exe`
- 508  `/Program Files (x86)/Dropbox/Client/icudt56.dll`

Actions:

1. Review the removable-device history. The extracted list names: USB Device: Disk&Ven_SanDisk&Prod_Extreme&Rev_0001; USB Device: Disk&Ven_Samsung&Prod_SSD_850_PRO_512G; Device Serial Signature: AA010603160707470215; Device Serial Signature: AA010215170355310594. Match each serial to an owner and to the incident window.
2. A sync client is present: Box Sync, Google Drive, Dropbox. Identify the signed-in account from its config database or logs and ask the provider (or tenant admin) for sharing, link and download audit logs.
3. If the device or account is not authorised, sign the cloud account out and revoke its sessions at the provider (not a local command).
4. Consider resetting the passwords of jcloudy (approval required).

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

- Show the user_default sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\jcloudy\AppData\Local\Google\Drive\user_default" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Dropbox sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Dropbox" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- Show the Box Sync sync client folder and its logs [READ-ONLY]

  ```powershell
  Get-ChildItem -Force -Recurse "C:\Users\jcloudy\AppData\Local\Box Sync" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
  ```

- List local accounts [READ-ONLY]

  ```bat
  net user
  ```

- Reset the password of jcloudy, whose profile holds the flagged files (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "jcloudy" *
  ```

  Note: Prompts for the new password; do not put it in the script.

### 2. Recently opened documents are recorded for jcloudy

- Technique: none claimed
- Confidence: **medium**. 65 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 65 flagged .lnk or jump-list files under profile(s) jcloudy.

Supporting flagged files (rank, path):

- 1,308  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Downloads.lnk`
- 3,016  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/OneDrive.lnk`
- 3,406  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Planning.LNK`
- 3,904  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Sheep.lnk`
- 4,054  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DemGun.lnk`
- 4,243  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Planning.lnk`
- 4,328  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Desktop.LNK`
- 4,568  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DeathToll.lnk`
- 4,930  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/AIRPORT INFORMATION.lnk`
- 5,104  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Templates.LNK`

Actions:

1. Copy the Recent folder and Jump List stores of jcloudy to external media.
2. Open the shortcuts offline (on a copy, with an LNK parser) to read the target path, volume serial and target timestamps; drive type 'removable' or a network path is the signal that matters.
3. Compare the document names with what the data-handling policy treats as confidential, and with the cloud and removable-device findings.
4. No containment is advised from this indicator alone.

Commands:

- List the jcloudy Recent-documents folder, newest first [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize
  ```

- List the jcloudy Jump List stores [READ-ONLY]

  ```powershell
  Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize
  ```

- Show account details and last logon for the profiles named in the paths [READ-ONLY]

  ```powershell
  net user "jcloudy"
  ```

### 3. File creation times earlier than their filename-record time

- Technique: T1070.006 Indicator Removal: Timestomp
- Confidence: **low**. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.77).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 12509 flagged files; enrichment 0.77 over the disk rate (43.32% of flagged against 56.62% of the disk).

Supporting flagged files (rank, path):

- 7  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll`
- 91  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/adodb.dll`
- 120  `/Windows/System32/config/COMPONENTS`
- 122  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/stdole.dll`
- 129  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.stdformat.dll`
- 130  `/Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinEUDP_RoamUp.lex`
- 131  `/Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll`
- 132  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll`
- 138  `/Windows/SysWOW64/opencl.dll`
- 140  `/Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinUDL_RoamUp.dat`

Actions:

1. No containment. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.77).
2. Visible timestamps cannot show this; only an offline comparison of the two time sets in the MFT can. The MFT export keeps whole seconds, so the sub-second test cannot run.
3. Do not act on this indicator unless another recommendation here also fires.

Commands:

- Show the journal state of the system volume [READ-ONLY]

  ```bat
  fsutil usn queryjournal C:
  ```

  Note: Needs an elevated prompt.

- Read the visible timestamps of Microsoft.mshtml.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\Microsoft.mshtml.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of adodb.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\adodb.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of stdole.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\stdole.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Wiper or cleaner executed: 0 of the 33,222 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.
- Hacking tools: 0 of the 33,222 flagged files matched: (d) no hacking-tool name among the flagged files.
