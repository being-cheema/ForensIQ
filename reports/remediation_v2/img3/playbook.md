+--------------------------------------------------------------------------------------------------+
| ADVICE FOR THE LIVE ENVIRONMENT THIS DISK CAME FROM                                              |
| Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).    |
| Commands that change the system are commented out in the scripts and marked below.               |
+--------------------------------------------------------------------------------------------------+

# Containment playbook: Image 3: Win10 Lone Wolf

- Detected OS: **Windows 10 Education** (version 6.3, build 16299)
- Detected by: SOFTWARE hive, Microsoft\Windows NT\CurrentVersion: ProductName, CurrentVersion, CurrentBuildNumber, CSDVersion. Path check: profiles under 'Users' (14191 paths); system folder 'Windows' (128505).
- Shell for the scripts: Windows PowerShell 5.1
- Operating point: Isolation Forest, 23 features, 15% budget (recommended); the 20% budget is shown after it.

## 15% budget (24,916 flagged files) - recommended

### 1. Removable-device and cloud-sync artifacts

- Technique: T1052.001 Exfiltration Over Physical Medium: Exfiltration over USB
- Confidence: **high**. 22 client-specific files from Box Sync, Google Drive, Dropbox are in the flagged set (963 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 963 flagged files; 22 client-specific, 3 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 20  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/Update/OneDriveSetup.exe`
- 130  `/Program Files/Box/Box Sync/cacert.pem`
- 144  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/18.044.0301.0006/OneDriveSetup.exe`
- 202  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/sync_log.log`
- 215  `/Program Files/Google/Drive/googledrivesync.exe`
- 238  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7900.log`
- 248  `/Program Files/Box/Box Sync/BoxSync.exe`
- 266  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/OneDrive.exe`
- 479  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7886.log`
- 701  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/cloud_graph/cloud_graph.db`

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
  Get-ChildItem -Force -Recurse "C:\Program Files\Box\Box Sync" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
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

- 2,084  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Downloads.lnk`
- 2,232  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DemGun.lnk`
- 2,471  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/OneDrive.lnk`
- 2,698  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Planning.LNK`
- 2,700  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Planning.lnk`
- 2,807  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Desktop.LNK`
- 2,915  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/AIRPORT INFORMATION.lnk`
- 2,950  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/AIRPORT INFORMATION.LNK`
- 2,951  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Templates.LNK`
- 3,167  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Sheep.lnk`

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
- Trigger: 11185 flagged files; enrichment 0.82 over the disk rate (46.19% of flagged against 56.62% of the disk).

Supporting flagged files (rank, path):

- 4  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll`
- 19  `/Program Files (x86)/Common Files/microsoft shared/VSTO/10.0/VSTOLoader.dll`
- 21  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll`
- 22  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.Word.HostAdapter.v10.0.dll`
- 23  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.HostAdapter.v10.0.dll`
- 24  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.Office.Tools.v9.0.dll`
- 29  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/Contracts/Microsoft.VisualStudio.Tools.Office.Contract.v9.0.dll`
- 37  `/Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll`
- 41  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v10.0.dll`
- 42  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v9.0.dll`

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

- Read the visible timestamps of VSTOLoader.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTO\10.0\VSTOLoader.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTA\Pipeline.v10.0\AddInViews\Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Wiper or cleaner executed: 0 of the 24,916 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.
- Hacking tools: 0 of the 24,916 flagged files matched: (d) no hacking-tool name among the flagged files.

## 20% budget (33,222 flagged files)

### 1. Removable-device and cloud-sync artifacts

- Technique: T1052.001 Exfiltration Over Physical Medium: Exfiltration over USB
- Confidence: **high**. 22 client-specific files from Box Sync, Google Drive, Dropbox are in the flagged set (1317 flagged files in all).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: yes, it contains system-changing commands
- Trigger: 1317 flagged files; 22 client-specific, 3 generic OS files among the 25 listed.

Supporting flagged files (rank, path):

- 20  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/Update/OneDriveSetup.exe`
- 130  `/Program Files/Box/Box Sync/cacert.pem`
- 144  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/18.044.0301.0006/OneDriveSetup.exe`
- 202  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/sync_log.log`
- 215  `/Program Files/Google/Drive/googledrivesync.exe`
- 238  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7900.log`
- 248  `/Program Files/Box/Box Sync/BoxSync.exe`
- 266  `/Users/jcloudy/AppData/Local/Microsoft/OneDrive/OneDrive.exe`
- 479  `/Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7886.log`
- 701  `/Users/jcloudy/AppData/Local/Google/Drive/user_default/cloud_graph/cloud_graph.db`

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
  Get-ChildItem -Force -Recurse "C:\Program Files\Box\Box Sync" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
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

- Reset the password of jcloudy, whose profile holds the flagged files (changes the system) [CHANGES SYSTEM - requires approval]

  ```bat
  net user "jcloudy" *
  ```

  Note: Prompts for the new password; do not put it in the script.

### 2. Recently opened documents are recorded for jcloudy

- Technique: none claimed
- Confidence: **medium**. 64 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 64 flagged .lnk or jump-list files under profile(s) jcloudy.

Supporting flagged files (rank, path):

- 2,084  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Downloads.lnk`
- 2,232  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DemGun.lnk`
- 2,471  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/OneDrive.lnk`
- 2,698  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Planning.LNK`
- 2,700  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Planning.lnk`
- 2,807  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Desktop.LNK`
- 2,915  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/AIRPORT INFORMATION.lnk`
- 2,950  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/AIRPORT INFORMATION.LNK`
- 2,951  `/Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Templates.LNK`
- 3,167  `/Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Sheep.lnk`

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
- Confidence: **low**. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.72).
- Scope: live environment the disk came from - never run on the evidence
- Requires approval: no system-changing command is offered
- Trigger: 12650 flagged files; enrichment 0.72 over the disk rate (40.83% of flagged against 56.62% of the disk).

Supporting flagged files (rank, path):

- 4  `/Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll`
- 19  `/Program Files (x86)/Common Files/microsoft shared/VSTO/10.0/VSTOLoader.dll`
- 21  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll`
- 22  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.Word.HostAdapter.v10.0.dll`
- 23  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.HostAdapter.v10.0.dll`
- 24  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.Office.Tools.v9.0.dll`
- 29  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/Contracts/Microsoft.VisualStudio.Tools.Office.Contract.v9.0.dll`
- 37  `/Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll`
- 41  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v10.0.dll`
- 42  `/Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v9.0.dll`

Actions:

1. No containment. Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.72).
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

- Read the visible timestamps of VSTOLoader.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTO\10.0\VSTOLoader.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Read the visible timestamps of Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll [READ-ONLY]

  ```powershell
  Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTA\Pipeline.v10.0\AddInViews\Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List
  ```

- Show the current file-system audit policy [READ-ONLY]

  ```bat
  auditpol /get /category:"Object Access"
  ```

Not triggered:

- Wiper or cleaner executed: 0 of the 33,222 flagged files matched: (a) no wiper, cleaner or shredder executable or Prefetch record among the flagged files.
- Hacking tools: 0 of the 33,222 flagged files matched: (d) no hacking-tool name among the flagged files.
