# Remediation: Network Sniffing & Covert Beaconing Containment
netsh advfirewall set allprofiles state on
netsh advfirewall firewall add rule name="Block Unauthorized Outbound" dir=out action=block protocol=TCP remoteport=4444,1337,8888
Write-Host "Host firewall enabled and suspicious egress ports blocked."
