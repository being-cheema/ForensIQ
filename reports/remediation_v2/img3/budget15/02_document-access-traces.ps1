# ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
# NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
# Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
# Recommendation: Recently opened documents are recorded for jcloudy  [confidence: medium]
# Source disk: Image 3: Win10 Lone Wolf; detected OS: Windows 10 Education (6.3, build 16299)
# Trigger: (b) shortcut / jump-list traces of documents at Isolation Forest 19 features, 15% budget (24,916 files)
# Why this confidence: 62 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
# Supporting flagged files (rank  path):
#      1308  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Downloads.lnk
#      3016  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/OneDrive.lnk
#      3406  /Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Planning.LNK
#      3904  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Sheep.lnk
#      4054  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DemGun.lnk
#      4243  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/Planning.lnk
#      4328  /Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Desktop.LNK
#      4568  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/DeathToll.lnk
#      4930  /Users/jcloudy/AppData/Roaming/Microsoft/Windows/Recent/AIRPORT INFORMATION.lnk
#      5104  /Users/jcloudy/AppData/Roaming/Microsoft/Office/Recent/Templates.LNK

if ($env:FORENSIQ_LIVE_OK -ne 'YES') { Write-Host 'Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.'; exit 1 }

# List the jcloudy Recent-documents folder, newest first
Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent" | Sort-Object LastWriteTime -Descending | Select-Object -First 50 Name, LastWriteTime | Format-Table -AutoSize

# List the jcloudy Jump List stores
Get-ChildItem -Force "C:\Users\jcloudy\AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations" | Select-Object Name, LastWriteTime | Format-Table -AutoSize

# Show account details and last logon for the profiles named in the paths
net user "jcloudy"

