# Remediation: Security Log Clearing & Anti-Forensics
Get-WinEvent -LogName Security | Where {$_.Id -eq 1102} | Select TimeCreated,Message | Export-Csv cleared_by.csv -NoTypeInformation
auditpol /set /subcategory:"Security System Extension" /success:enable
Write-Host "Audit policy reinforced for log tampering protection."
