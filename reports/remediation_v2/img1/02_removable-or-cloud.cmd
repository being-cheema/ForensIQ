@echo off
REM ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
REM NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
REM Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
REM Recommendation: Device-install logs are present  [confidence: low]
REM Source disk: Image 1: XP Hacking (SCHARDT.001); detected OS: Microsoft Windows XP (5.1, build 2600)
REM Trigger: (c) removable-device or cloud-sync artifacts at Isolation Forest 23 features, 15% budget (1,766 files)
REM Why this confidence: The 1 flagged file(s) are only Windows' own setupapi / usbstor files, which exist on every install. They become evidence only if they list removable devices.
REM Supporting flagged files (rank  path):
REM       307  /WINDOWS/setupapi.log

if /i not "%FORENSIQ_LIVE_OK%"=="YES" (
  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.
  exit /b 1
)

REM List every USB storage device the host has seen (vendor, product, serial)
reg query HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR /s

REM List the volumes and drive letters Windows mapped to those devices
reg query HKLM\SYSTEM\MountedDevices

REM Read the device-install log for first-connection times of those serials
REM Note: XP keeps this in %SystemRoot%\setupapi.log; Vista and later in %SystemRoot%\inf\setupapi.dev.log.
findstr /i /c:"Disk&Ven" "%SystemRoot%\setupapi.log"

REM List local accounts
net user

