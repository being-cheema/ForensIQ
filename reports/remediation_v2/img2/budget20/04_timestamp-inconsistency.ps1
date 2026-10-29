# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: File creation times earlier than their filename-record time  [confidence: low]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: timestomp (creation < filename-record creation - 1 h) at Isolation Forest 23 features, 20% budget (17,003 files)
# Why this confidence: Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.46).
# Supporting flagged files (rank  path):
#         3  /Windows/System32/config/SYSTEM
#         4  /Windows/System32/SMI/Store/Machine/SCHEMA.DAT
#         5  /Windows/System32/config/SOFTWARE
#         6  /Windows/System32/config/COMPONENTS
#        10  /Windows/System32/catroot2/edb.log
#        12  /Windows/Microsoft.NET/Framework/v4.0.30319/clr.dll
#        17  /Windows/System32/Msdtc/MSDTC.LOG
#        21  /Windows/System32/config/SAM
#        46  /Windows/Microsoft.NET/Framework/v4.0.30319/ngen.exe
#        47  /Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# Show the journal state of the system volume
# Note: Needs an elevated prompt.
fsutil usn queryjournal C:

# Read the visible timestamps of SCHEMA.DAT
Get-Item -Force "C:\Windows\System32\SMI\Store\Machine\SCHEMA.DAT" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of edb.log
Get-Item -Force "C:\Windows\System32\catroot2\edb.log" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of clr.dll
Get-Item -Force "C:\Windows\Microsoft.NET\Framework\v4.0.30319\clr.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Show the current file-system audit policy
auditpol /get /category:"Object Access"

