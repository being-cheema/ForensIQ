# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: File creation times earlier than their filename-record time  [confidence: low]
# Source disk: Image 3: Win10 Lone Wolf; detected OS: Windows 10 Education (6.3, build 16299)
# Trigger: timestomp (creation < filename-record creation - 1 h) at Isolation Forest 19 features, 20% budget (33,222 files)
# Why this confidence: Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.77).
# Supporting flagged files (rank  path):
#         7  /Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll
#        91  /Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/adodb.dll
#       120  /Windows/System32/config/COMPONENTS
#       122  /Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/stdole.dll
#       129  /Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.stdformat.dll
#       130  /Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinEUDP_RoamUp.lex
#       131  /Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll
#       132  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll
#       138  /Windows/SysWOW64/opencl.dll
#       140  /Users/jcloudy/AppData/Roaming/Microsoft/InputMethod/Chs/ChsPinyinUDL_RoamUp.dat

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# Show the journal state of the system volume
# Note: Needs an elevated prompt.
fsutil usn queryjournal C:

# Read the visible timestamps of Microsoft.mshtml.dll
Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\Microsoft.mshtml.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of adodb.dll
Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\adodb.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of stdole.dll
Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\stdole.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Show the current file-system audit policy
auditpol /get /category:"Object Access"

