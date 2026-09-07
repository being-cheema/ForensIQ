
Get-NetTCPConnection |
Where {$_.State -eq "Established"}

New-NetFirewallRule `
-DisplayName "Block Suspicious IP" `
-Direction Outbound `
-RemoteAddress 0.0.0.0 `
-Action Block

Write-Host "Review outbound connections."
