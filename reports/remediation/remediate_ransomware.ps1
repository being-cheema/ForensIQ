
vssadmin list shadows

Stop-Service LanmanServer -Force

Set-NetFirewallProfile `
-Profile Domain,Public,Private `
-Enabled True

Write-Host "Host isolated. Restore from backups if available."
