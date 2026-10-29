# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: Removable-device and cloud-sync artifacts  [confidence: high]
# Source disk: Image 3: Win10 Lone Wolf; detected OS: Windows 10 Education (6.3, build 16299)
# Trigger: (c) removable-device or cloud-sync artifacts at Isolation Forest 23 features, 20% budget (33,222 files)
# Why this confidence: 22 client-specific files from Box Sync, Google Drive, Dropbox are in the flagged set (1317 flagged files in all).
# Supporting flagged files (rank  path):
#        20  /Users/jcloudy/AppData/Local/Microsoft/OneDrive/Update/OneDriveSetup.exe
#       130  /Program Files/Box/Box Sync/cacert.pem
#       144  /Users/jcloudy/AppData/Local/Microsoft/OneDrive/18.044.0301.0006/OneDriveSetup.exe
#       202  /Users/jcloudy/AppData/Local/Google/Drive/user_default/sync_log.log
#       215  /Program Files/Google/Drive/googledrivesync.exe
#       238  /Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7900.log
#       248  /Program Files/Box/Box Sync/BoxSync.exe
#       266  /Users/jcloudy/AppData/Local/Microsoft/OneDrive/OneDrive.exe
#       479  /Users/jcloudy/AppData/Local/Box Sync/Logs/Box Sync-4.0.7886.log
#       701  /Users/jcloudy/AppData/Local/Google/Drive/user_default/cloud_graph/cloud_graph.db

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List every USB storage device the host has seen (vendor, product, serial)
reg query HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR /s

# List the volumes and drive letters Windows mapped to those devices
reg query HKLM\SYSTEM\MountedDevices

# Read the device-install log for first-connection times of those serials
# Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.
Select-String -Path "$env:SystemRoot\inf\setupapi.dev.log" -Pattern 'Disk&Ven' | Select-Object -First 100 LineNumber, Line | Format-List

# Show the user_default sync client folder and its logs
Get-ChildItem -Force -Recurse "C:\Users\jcloudy\AppData\Local\Google\Drive\user_default" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime

# Show the Dropbox sync client folder and its logs
Get-ChildItem -Force -Recurse "C:\Program Files (x86)\Dropbox" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime

# Show the Box Sync sync client folder and its logs
Get-ChildItem -Force -Recurse "C:\Program Files\Box\Box Sync" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(log|db)$" } | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime

# List local accounts
net user

# Block new USB storage devices (changes the system)  -- CHANGES SYSTEM (requires approval)
# Note: Stops all USB mass storage, including legitimate devices; set Start back to 3 to undo. Needs a policy decision.
# [CHANGES SYSTEM] reg add HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR /v Start /t REG_DWORD /d 4 /f

# Reset the password of jcloudy, whose profile holds the flagged files (changes the system)  -- CHANGES SYSTEM (requires approval)
# Note: Prompts for the new password; do not put it in the script.
# [CHANGES SYSTEM] net user "jcloudy" *

