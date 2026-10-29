# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: Removable-device and cloud-sync artifacts  [confidence: high]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: (c) removable-device or cloud-sync artifacts at Isolation Forest 23 features, 15% budget (12,753 files)
# Why this confidence: 15 client-specific files from Google Drive, iCloud are in the flagged set (36 flagged files in all).
# Supporting flagged files (rank  path):
#        54  /Program Files (x86)/Google/Drive/googledrivesync.exe
#       238  /Users/informant/Downloads/icloudsetup.exe
#       264  /Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log
#       564  /Windows/Prefetch/GOOGLEDRIVESYNC.EXE-841A0D94.pf
#       645  /Users/informant/Downloads/googledrivesync.exe
#       732  /Users/informant/AppData/Local/Temp/icloudsetupE88.log
#       875  /Users/informant/AppData/Local/Google/Drive/user_default/cloud_graph/dict_2.db
#      1626  /Users/informant/AppData/Local/Google/Drive/user_default/sync_config.db
#      1742  /Users/informant/AppData/Local/Google/Drive/user_default/snapshot.db
#      1823  /Users/informant/AppData/Local/Google/Drive/user_default/sync_log.log

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List every USB storage device the host has seen (vendor, product, serial)
reg query HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR /s

# List the volumes and drive letters Windows mapped to those devices
reg query HKLM\SYSTEM\MountedDevices

# Read the device-install log for first-connection times of those serials
# Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.
Select-String -Path "$env:SystemRoot\inf\setupapi.dev.log" -Pattern 'Disk&Ven' | Select-Object -First 100 LineNumber, Line | Format-List

# Show the Drive sync client folder and its logs
Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Google\Drive" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime

# Show the Downloads sync client folder and its logs
Get-ChildItem -Force -Recurse "C:\Users\informant\Downloads" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime

# List local accounts
net user

# Block new USB storage devices (changes the system)  -- CHANGES SYSTEM (requires approval)
# Note: Stops all USB mass storage, including legitimate devices; set Start back to 3 to undo. Needs a policy decision.
# [CHANGES SYSTEM] reg add HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR /v Start /t REG_DWORD /d 4 /f

# Reset the password of informant, whose profile holds the flagged files (changes the system)  -- CHANGES SYSTEM (requires approval)
# Note: Prompts for the new password; do not put it in the script.
# [CHANGES SYSTEM] net user "informant" *

