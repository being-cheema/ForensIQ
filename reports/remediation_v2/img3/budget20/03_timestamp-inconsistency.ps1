# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: File creation times earlier than their filename-record time  [confidence: low]
# Source disk: Image 3: Win10 Lone Wolf; detected OS: Windows 10 Education (6.3, build 16299)
# Trigger: timestomp (creation < filename-record creation - 1 h) at Isolation Forest 23 features, 20% budget (33,222 files)
# Why this confidence: Low: not enriched, likely normal. The flagged set has a lower timestamp-gap rate than the whole disk (enrichment 0.72).
# Supporting flagged files (rank  path):
#         4  /Program Files (x86)/Microsoft.NET/Primary Interop Assemblies/Microsoft.mshtml.dll
#        19  /Program Files (x86)/Common Files/microsoft shared/VSTO/10.0/VSTOLoader.dll
#        21  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll
#        22  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.Word.HostAdapter.v10.0.dll
#        23  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/HostSideAdapters/Microsoft.VisualStudio.Tools.Office.HostAdapter.v10.0.dll
#        24  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInViews/Microsoft.Office.Tools.v9.0.dll
#        29  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/Contracts/Microsoft.VisualStudio.Tools.Office.Contract.v9.0.dll
#        37  /Program Files (x86)/Common Files/microsoft shared/VSTA/AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument/Microsoft.VisualStudio.Tools.Office.AppInfoDocument.v9.0.dll
#        41  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v10.0.dll
#        42  /Program Files (x86)/Common Files/microsoft shared/VSTA/Pipeline.v10.0/AddInSideAdapters/Microsoft.VisualStudio.Tools.Applications.AddInAdapter.v9.0.dll

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# Show the journal state of the system volume
# Note: Needs an elevated prompt.
fsutil usn queryjournal C:

# Read the visible timestamps of Microsoft.mshtml.dll
Get-Item -Force "C:\Program Files (x86)\Microsoft.NET\Primary Interop Assemblies\Microsoft.mshtml.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of VSTOLoader.dll
Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTO\10.0\VSTOLoader.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Read the visible timestamps of Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll
Get-Item -Force "C:\Program Files (x86)\Common Files\microsoft shared\VSTA\Pipeline.v10.0\AddInViews\Microsoft.VisualStudio.Tools.Applications.Runtime.v9.0.dll" | Select-Object FullName, CreationTime, LastWriteTime, LastAccessTime | Format-List

# Show the current file-system audit policy
auditpol /get /category:"Object Access"

