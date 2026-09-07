
$reg="HKLM:\SYSTEM\CurrentControlSet\Services\USBSTOR"

Set-ItemProperty -Path $reg -Name Start -Value 4

gpupdate /force

Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR\*\*' |
Select PSChildName,FriendlyName |
Export-Csv usb_devices.csv -NoTypeInformation

Write-Host "USB storage disabled."
