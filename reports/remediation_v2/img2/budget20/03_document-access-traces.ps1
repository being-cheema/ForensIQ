# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: Recently opened documents are recorded for informant, admin11  [confidence: medium]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: (b) shortcut / jump-list traces of documents at Isolation Forest 23 features, 20% budget (17,003 files)
# Why this confidence: 49 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
# Supporting flagged files (rank  path):
#       546  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/Resignation_Letter_(Iaman_Informant).docx.LNK
#       651  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Resignation_Letter_(Iaman_Informant).docx.lnk
#       874  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/winter_whether_advisory.zip.lnk
#       918  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/(secret_project)_pricing_decision.xlsx.LNK
#       970  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/[secret_project]_final_meeting.pptx.LNK
#       979  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_final_meeting.pptx.lnk
#       980  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/(secret_project)_pricing_decision.xlsx.lnk
#      1008  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_design_concept.lnk
#      1033  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/final.lnk
#      1046  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_proposal.lnk

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List the informant Recent-documents folder, newest first
Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize

# List the admin11 Recent-documents folder, newest first
Get-ChildItem -Force "C:\Users\admin11\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize

# List the informant Jump List stores
Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize

# Show account details and last logon for the profiles named in the paths
net user "informant"; net user "admin11"

