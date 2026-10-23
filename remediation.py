"""
remediation.py
==============
ForensIQ Automated Incident Response & Remediation Script Generator
Classifies breach types based on detected forensic anomalies and generates
targeted PowerShell containment and remediation scripts.
"""

import os
import pandas as pd
from config import FEAT_DIR, REPORT_DIR, OUT_DIR


def detect_breach_types():
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    log_gap_path = os.path.join(FEAT_DIR, "log_gap_features.csv")

    flagged = pd.read_csv(flagged_path) if os.path.exists(flagged_path) else pd.DataFrame()
    log_df = pd.read_csv(log_gap_path) if os.path.exists(log_gap_path) else pd.DataFrame()

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

    return breach_types


def write_remediation(breach_types=None):
    if breach_types is None:
        breach_types = detect_breach_types()

    print(f"[+] Detected breach patterns: {breach_types}")
    rem_dir = os.path.join(REPORT_DIR, "remediation")
    os.makedirs(rem_dir, exist_ok=True)

    if "log_clearing" in breach_types:
        with open(os.path.join(rem_dir, "remediate_log_clearing.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: Security Log Clearing & Anti-Forensics
Get-WinEvent -LogName Security | Where {$_.Id -eq 1102} | Select TimeCreated,Message | Export-Csv cleared_by.csv -NoTypeInformation
auditpol /set /subcategory:"Security System Extension" /success:enable
Write-Host "Audit policy reinforced for log tampering protection."
''')

    if "usb_exfiltration" in breach_types:
        with open(os.path.join(rem_dir, "remediate_usb.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: USB Exfiltration Containment
$reg = "HKLM:\SYSTEM\CurrentControlSet\Services\USBSTOR"
Set-ItemProperty -Path $reg -Name Start -Value 4
gpupdate /force
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR\*\*' | Select PSChildName,FriendlyName | Export-Csv usb_devices.csv -NoTypeInformation
Write-Host "USB storage disabled across the system."
''')

    if "timestamp_backdating" in breach_types:
        with open(os.path.join(rem_dir, "remediate_timestamp.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: File System Auditing for Timestomp Tampering
auditpol /set /subcategory:"File System" /success:enable /failure:enable
Write-Host "File system auditing enabled for timestamp monitoring."
''')

    if "credential_dumping" in breach_types:
        with open(os.path.join(rem_dir, "remediate_credentials.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: LSASS Credential Harvesting Containment
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" /v UseLogonCredential /t REG_DWORD /d 0 /f
Write-Host "LSA Protection (RunAsPPL) enabled. WDigest cleartext credentials disabled."
''')

    if "network_beaconing" in breach_types:
        with open(os.path.join(rem_dir, "remediate_network.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: Network Sniffing & Covert Beaconing Containment
netsh advfirewall set allprofiles state on
netsh advfirewall firewall add rule name="Block Unauthorized Outbound" dir=out action=block protocol=TCP remoteport=4444,1337,8888
Write-Host "Host firewall enabled and suspicious egress ports blocked."
''')

    if "ransomware" in breach_types:
        with open(os.path.join(rem_dir, "remediate_ransomware.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: Rapid Encryption & Staging Containment
vssadmin create shadow /for=C:
Set-ProcessMitigation -System -Enable DEP
Write-Host "VSS snapshot created and system process mitigations enforced."
''')

    if "malware_detected" in breach_types:
        with open(os.path.join(rem_dir, "remediate_malware.ps1"), "w", encoding="utf-8") as f:
            f.write(r'''# Remediation: Malware Staging Clean-up
Start-MpScan -ScanType FullScan
Update-MpSignature
Write-Host "Windows Defender antimalware signature updated and scan triggered."
''')

    print(f"[+] Remediation PowerShell scripts generated in: {rem_dir}")
    return rem_dir


def main():
    write_remediation()


if __name__ == "__main__":
    main()