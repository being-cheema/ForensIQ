
# Enable detailed file auditing

auditpol /set /subcategory:"File System" /success:enable /failure:enable

Write-Host "File auditing enabled."

# Replace account below if attacker identified

# Disable-LocalUser -Name "ATTACKER"
