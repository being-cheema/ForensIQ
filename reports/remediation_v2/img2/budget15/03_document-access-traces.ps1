# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: Recently opened documents are recorded for informant, admin11  [confidence: medium]
# Source disk: Image 2: Win7 Data Leakage; detected OS: Windows 7 Ultimate (6.1, build 7601)
# Trigger: (b) shortcut / jump-list traces of documents at Isolation Forest 19 features, 15% budget (12,753 files)
# Why this confidence: 36 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
# Supporting flagged files (rank  path):
#       440  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/winter_whether_advisory.zip.lnk
#       509  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Resignation_Letter_(Iaman_Informant).docx.lnk
#       720  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/Resignation_Letter_(Iaman_Informant).docx.LNK
#       844  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/(secret_project)_pricing_decision.xlsx.LNK
#       936  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Koala.jpg.lnk
#       946  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/CD Drive.lnk
#       955  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/[secret_project]_proposal.lnk
#       979  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/Tulips.jpg.lnk
#      1049  /Users/informant/AppData/Roaming/Microsoft/Windows/Recent/secret.lnk
#      1181  /Users/informant/AppData/Roaming/Microsoft/Office/Recent/[secret_project]_proposal.LNK

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List the informant Recent-documents folder, newest first
Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize

# List the admin11 Recent-documents folder, newest first
Get-ChildItem -Force "C:\Users\admin11\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize

# List the informant Jump List stores
Get-ChildItem -Force "C:\Users\informant\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize

# Show account details and last logon for the profiles named in the paths
net user "informant"; net user "admin11"

