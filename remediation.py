# Classify breach type from anomaly patterns

import os
import pandas as pd
from config import FEAT_DIR, REPORT_DIR, OUT_DIR

# Load anomaly data
flagged = pd.read_csv(f"{FEAT_DIR}/flagged_anomalies.csv")
log_df = pd.read_csv(f"{FEAT_DIR}/log_gap_features.csv")

# Detect breach indicators
bulk_ts_change = (flagged["delta_mb"] < 60).sum() > 50 if "delta_mb" in flagged.columns else False
log_gaps = (log_df["gap"] == 1).sum() > 3 if "gap" in log_df.columns else False
usb_activity = ("usb_present" in flagged.columns and flagged["usb_present"].sum() > 0) or os.path.exists(f"{OUT_DIR}/usb/usb_devices.txt")

credential_dumping = ("credential_tool" in flagged.columns) and (flagged["credential_tool"].sum() > 0)
powershell_attack = ("powershell_exec" in flagged.columns) and (flagged["powershell_exec"].sum() > 0)
network_beaconing = ("sniffer_tool" in flagged.columns) and (flagged["sniffer_tool"].sum() > 0)
malware_detected = ("temp_path" in flagged.columns and "is_exe" in flagged.columns) and ((flagged["temp_path"] == 1) & (flagged["is_exe"] == 1)).sum() > 0
ransomware = ("is_archive" in flagged.columns) and (flagged["is_archive"].sum() > 20)
persistence = ("script_host" in flagged.columns) and (flagged["script_host"].sum() > 0)

breach_types = []

if bulk_ts_change:
    breach_types.append("timestamp_backdating")

if log_gaps:
    breach_types.append("log_clearing")

if usb_activity:
    breach_types.append("usb_exfiltration")
    
if credential_dumping:
    breach_types.append("credential_dumping")
    
if powershell_attack:
    breach_types.append("powershell_attack")
    
if network_beaconing:
    breach_types.append("network_beaconing")

if malware_detected:
    breach_types.append("malware_detected")
    
if ransomware:
    breach_types.append("ransomware")
    
if persistence:
    breach_types.append("persistence")

print(f"[+] Detected breach types: {breach_types}")


# Generate PowerShell containment scripts

def write_remediation(breach_types):

    rem_dir = os.path.join(REPORT_DIR, "remediation")
    os.makedirs(rem_dir, exist_ok=True)

    ###########################################
    # Log Clearing
    ###########################################
    if "log_clearing" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_log_clearing.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
# Find who cleared Security logs

Get-WinEvent -LogName Security |
Where {$_.Id -eq 1102} |
Select TimeCreated,Message |
Export-Csv cleared_by.csv -NoTypeInformation

auditpol /set /subcategory:"Security System Extension" /success:enable

Write-Host "Audit policy enabled."
''')

    ###########################################
    # USB Exfiltration
    ###########################################
    if "usb_exfiltration" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_usb.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
$reg="HKLM:\SYSTEM\CurrentControlSet\Services\USBSTOR"

Set-ItemProperty -Path $reg -Name Start -Value 4

gpupdate /force

Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR\*\*' |
Select PSChildName,FriendlyName |
Export-Csv usb_devices.csv -NoTypeInformation

Write-Host "USB storage disabled."
''')

    ###########################################
    # Timestamp Manipulation
    ###########################################
    if "timestamp_backdating" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_timestamp.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
# Enable detailed file auditing

auditpol /set /subcategory:"File System" /success:enable /failure:enable

Write-Host "File auditing enabled."

# Replace account below if attacker identified

# Disable-LocalUser -Name "ATTACKER"
''')

    ###########################################
    # Credential Dumping
    ###########################################
    if "credential_dumping" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_credentials.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Stop-Process -Name mimikatz -Force -ErrorAction SilentlyContinue

reg add HKLM\SYSTEM\CurrentControlSet\Control\Lsa ^
/v RunAsPPL /t REG_DWORD /d 1 /f

Write-Host "LSASS protection enabled."

gpupdate /force
''')

    ###########################################
    # PowerShell Abuse
    ###########################################
    if "powershell_attack" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_powershell.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Set-ExecutionPolicy RemoteSigned -Force

Enable-WindowsOptionalFeature -Online `
-FeatureName MicrosoftWindowsPowerShellV2Root `
-NoRestart

Write-Host "PowerShell policy updated."
''')

    ###########################################
    # Ransomware
    ###########################################
    if "ransomware" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_ransomware.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
vssadmin list shadows

Stop-Service LanmanServer -Force

Set-NetFirewallProfile `
-Profile Domain,Public,Private `
-Enabled True

Write-Host "Host isolated. Restore from backups if available."
''')

    ###########################################
    # Persistence
    ###########################################
    if "persistence" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_persistence.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Get-ScheduledTask |
Where {$_.TaskName -notmatch "Microsoft"} |
Export-Csv scheduled_tasks.csv -NoTypeInformation

Get-ItemProperty `
HKLM:\Software\Microsoft\Windows\CurrentVersion\Run

Write-Host "Review startup persistence."
''')

    ###########################################
    # Suspicious Services
    ###########################################
    if "malicious_service" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_services.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Get-Service |
Where {$_.Status -eq "Running"} |
Sort DisplayName

Write-Host "Review suspicious services."

# Stop-Service SERVICE_NAME
# Set-Service SERVICE_NAME -StartupType Disabled
''')

    ###########################################
    # Network Beaconing
    ###########################################
    if "network_beaconing" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_network.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Get-NetTCPConnection |
Where {$_.State -eq "Established"}

New-NetFirewallRule `
-DisplayName "Block Suspicious IP" `
-Direction Outbound `
-RemoteAddress 0.0.0.0 `
-Action Block

Write-Host "Review outbound connections."
''')

    ###########################################
    # Malware File Removal
    ###########################################
    if "malware_detected" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_malware.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Start-MpScan -ScanType FullScan

Update-MpSignature

Write-Host "Windows Defender scan initiated."
''')

    ###########################################
    # Account Lockdown
    ###########################################
    if "account_compromise" in breach_types:

        with open(os.path.join(rem_dir,
                "remediate_accounts.ps1"), "w",
                encoding="utf-8") as f:

            f.write(r'''
Get-LocalUser

Write-Host "Disable compromised account manually."

# Disable-LocalUser -Name USERNAME

net accounts /lockoutthreshold:5
''')

    print(f"[+] Generated remediation scripts in {rem_dir}")

if __name__ == "__main__":
    write_remediation(breach_types)