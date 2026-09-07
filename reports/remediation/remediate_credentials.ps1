
Stop-Process -Name mimikatz -Force -ErrorAction SilentlyContinue

reg add HKLM\SYSTEM\CurrentControlSet\Control\Lsa ^
/v RunAsPPL /t REG_DWORD /d 1 /f

Write-Host "LSASS protection enabled."

gpupdate /force
