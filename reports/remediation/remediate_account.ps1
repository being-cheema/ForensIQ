
Disable-LocalUser -Name "Mr. Evil"   # Replace with identified account

auditpol /set /subcategory:"File System" `
    /success:enable `
    /failure:enable
