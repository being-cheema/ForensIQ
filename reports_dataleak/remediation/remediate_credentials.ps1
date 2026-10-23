# Remediation: LSASS Credential Harvesting Containment
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" /v UseLogonCredential /t REG_DWORD /d 0 /f
Write-Host "LSA Protection (RunAsPPL) enabled. WDigest cleartext credentials disabled."
