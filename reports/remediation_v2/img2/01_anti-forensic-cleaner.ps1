# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: A data-wiping or cleaning tool was installed and has run  [confidence: high]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: (a) wiper / cleaner executable or Prefetch record at Isolation Forest 19 features, 20% budget (17,003 files)
# Why this confidence: 8 flagged files name a wiper/cleaner; 4 are Prefetch entries, which prove the program ran.
# Supporting flagged files (rank  path):
#       358  /Program Files/Eraser/Eraser.exe
#       779  /Users/informant/Desktop/Download/Eraser 6.2.0.2962.exe
#       810  /Users/informant/Desktop/Download/ccsetup504.exe
#      3391  /Windows/Prefetch/ERASER.EXE-CE61944A.pf
#      3894  /Windows/Prefetch/CCSETUP504.EXE-6BA2F6A1.pf
#      4927  /Windows/Prefetch/CCLEANER64.EXE-779BD542.pf
#      6392  /Windows/Prefetch/ERASER 6.2.0.2962.EXE-BE552234.pf
#      2561  /Windows/Installer/{C6E287F1-2E47-45F0-BB51-94F815CFFB48}/Eraser.exe

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List Prefetch records (proof of execution and last run) for the named tools
Get-ChildItem "$env:SystemRoot\Prefetch" | Where-Object { $_.Name -match 'eraser|ccleaner' } | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize

# Look for scheduled wipe tasks
schtasks /query /fo LIST /v | findstr /i "ERASER CCLEANER TASKNAME"

# Find the installed program entries to learn the exact name and version
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s | findstr /i "DisplayName" | findstr /i "ERASER CCLEANER"

# Copy the Security event log to external media before anything else changes
# Note: Writes a copy to the current folder: run it from removable media you control, not the host disk. XP: eventquery.vbs ships with XP Professional only; otherwise take a forensic image.
wevtutil epl Security Security.evtx

# Remove the installed cleaner (changes the system)  -- CHANGES SYSTEM (requires approval)
# Note: Only after the owner and legal sign off; uninstalling destroys the tool's own logs and schedule.
# [CHANGES SYSTEM] (Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like 'eraser*' }).Uninstall()

