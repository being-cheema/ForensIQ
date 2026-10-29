@echo off
REM ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
REM NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
REM Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
REM Recommendation: File creation times earlier than their filename-record time  [confidence: high]
REM Source disk: Image 1: XP Hacking (SCHARDT.001); detected OS: Microsoft Windows XP (5.1, build 2600)
REM Trigger: timestomp (creation < filename-record creation - 1 h) at Isolation Forest 19 features, 20% budget (2,355 files)
REM Why this confidence: 289 files with creation earlier than the filename-record time by over 1 h; enrichment 4.77 over the disk rate (Fisher p 5.6e-182).
REM Supporting flagged files (rank  path):
REM         2  /Documents and Settings/Mr. Evil/Local Settings/Temp/Temporary Directory 1 for powertoysetup.zip/PowerToySetup.exe
REM        56  /Program Files/Ethereal/ethereal.exe
REM        76  /Program Files/Look@LAN/LookAtHost.exe
REM        82  /Program Files/Look@LAN/LookAtLan.exe
REM        83  /Program Files/Common Files/Microsoft Shared/Web Folders/MSOWS409.DLL
REM        92  /Program Files/Network Stumbler/NetStumbler.exe
REM        98  /Program Files/Common Files/Microsoft Shared/Web Server Extensions/40/BIN/fp4autl.dll
REM        99  /Program Files/Common Files/Microsoft Shared/Web Server Extensions/40/BIN/1033/FPEXT.MSG
REM       108  /Program Files/Ethereal/libethereal.dll
REM       183  /Program Files/Ethereal/libgtk-win32-2.0-0.dll

if /i not "%FORENSIQ_LIVE_OK%"=="YES" (
  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.
  exit /b 1
)

REM Show the journal state of the system volume
REM Note: Needs an elevated prompt.
fsutil usn queryjournal C:

REM Read the visible timestamps of PowerToySetup.exe
dir /a /t:c "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe" & dir /a /t:w "C:\Documents and Settings\Mr. Evil\Local Settings\Temp\Temporary Directory 1 for powertoysetup.zip\PowerToySetup.exe"

REM Read the visible timestamps of ethereal.exe
dir /a /t:c "C:\Program Files\Ethereal\ethereal.exe" & dir /a /t:w "C:\Program Files\Ethereal\ethereal.exe"

REM Read the visible timestamps of LookAtHost.exe
dir /a /t:c "C:\Program Files\Look@LAN\LookAtHost.exe" & dir /a /t:w "C:\Program Files\Look@LAN\LookAtHost.exe"

REM Omitted because this OS lacks them:
REM   - Show the current file-system audit policy: auditpol.exe is not part of Windows XP (Resource Kit only); use Local Security Policy > Audit object access
REM   - Turn on file-system auditing (changes the system): auditpol.exe is not part of Windows XP; enable 'Audit object access' in Local Security Policy
