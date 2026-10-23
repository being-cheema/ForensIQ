# Remediation: Rapid Encryption & Staging Containment
vssadmin create shadow /for=C:
Set-ProcessMitigation -System -Enable DEP
Write-Host "VSS snapshot created and system process mitigations enforced."
