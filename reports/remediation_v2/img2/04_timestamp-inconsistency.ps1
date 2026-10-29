# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: File creation times earlier than their filename-record time  [confidence: low]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: timestomp (creation < filename-record creation - 1 h) at Isolation Forest 19 features, 20% budget (17,003 files)
# Why this confidence: Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.62).
# Supporting flagged files (rank  path):
#         5  /Windows/System32/config/SYSTEM
#         6  /Windows/System32/config/COMPONENTS
#         7  /Windows/System32/Msdtc/MSDTC.LOG
#         9  /Windows/System32/config/SOFTWARE
#        12  /Windows/System32/SMI/Store/Machine/SCHEMA.DAT
#        13  /Windows/System32/catroot2/edb.log
#        41  /Windows/System32/catroot2/{F750E6C3-38EE-11D1-85E5-00C04FC295EE}/catdb
#        42  /Users/Default/NTUSER.DAT
#        84  /Windows/setupact.log
#        90  /Windows/System32/wbem/Repository/OBJECTS.DATA

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# Show the journal state of the system volume
# Note: Needs an elevated prompt.
fsutil usn queryjournal C:

# Read the visible timestamps of MSDTC.LOG
Get-Item -Force "C:\Windows\System32\Msdtc\MSDTC.LOG" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of SCHEMA.DAT
Get-Item -Force "C:\Windows\System32\SMI\Store\Machine\SCHEMA.DAT" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of edb.log
Get-Item -Force "C:\Windows\System32\catroot2\edb.log" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Show the current file-system audit policy
auditpol /get /category:"Object Access"

