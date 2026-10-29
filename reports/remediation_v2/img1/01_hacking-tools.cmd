@echo off
REM ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
REM NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
REM Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
REM Recommendation: Network-attack or password tools present: cain, ethereal, netstumbler, whois, anonymizer  [confidence: medium]
REM Source disk: Image 1: XP Hacking (SCHARDT.001); detected OS: Microsoft Windows XP (5.1, build 2600)
REM Trigger: (d) hacking-tool names at Isolation Forest 19 features, 20% budget (2,355 files)
REM Why this confidence: 293 flagged files name cain, ethereal, netstumbler, whois, anonymizer; 0 Prefetch records and 7 executables are among the listed ones.
REM Supporting flagged files (rank  path):
REM        49  /Program Files/Cain/Cain.exe
REM        56  /Program Files/Ethereal/ethereal.exe
REM        92  /Program Files/Network Stumbler/NetStumbler.exe
REM       108  /Program Files/Ethereal/libethereal.dll
REM       183  /Program Files/Ethereal/libgtk-win32-2.0-0.dll
REM       210  /Program Files/Whois/whois.exe
REM       289  /Program Files/Anonymizer/Toolbar/AnonymizerBar.dll
REM       300  /Program Files/Anonymizer/Core/Anonymizer.dll
REM       324  /Program Files/Ethereal/lib/gtk-2.0/2.4.0/immodules/im-thai-broken.dll
REM       377  /Program Files/Whois/whoisi.exe

if /i not "%FORENSIQ_LIVE_OK%"=="YES" (
  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.
  exit /b 1
)

REM List the install folder C:\Program Files\Cain
dir /a /s "C:\Program Files\Cain"

REM List the install folder C:\Program Files\Ethereal
dir /a /s "C:\Program Files\Ethereal"

REM List the install folder C:\Program Files\Network Stumbler
dir /a /s "C:\Program Files\Network Stumbler"

REM List the install folder C:\Program Files\Whois
dir /a /s "C:\Program Files\Whois"

REM List Prefetch records (proof of execution) for the named tools
dir "%SystemRoot%\Prefetch" /a /t:w | findstr /i "CAIN ETHEREAL NETSTUMBLER WHOIS ANONYMIZER"

REM Check whether the WinPcap capture driver service is installed
sc query npf

REM Show running processes that match the tool names
REM Note: XP: tasklist is in XP Professional only.
tasklist /v | findstr /i "CAIN ETHEREAL NETSTUMBLER WHOIS ANONYMIZER"

REM Show open network connections and owning process IDs
netstat -ano

REM List administrators on the host
net localgroup administrators

REM Stop and disable the capture driver (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Only if the driver exists and the tool is confirmed unauthorised.
REM [CHANGES SYSTEM] sc stop npf & sc config npf start= disabled

REM Move C:\Program Files\Cain to a quarantine folder instead of deleting it (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Keep the files: they are exhibits.
REM [CHANGES SYSTEM] move "C:\Program Files\Cain" "D:\quarantine\Cain"

REM Move C:\Program Files\Ethereal to a quarantine folder instead of deleting it (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Keep the files: they are exhibits.
REM [CHANGES SYSTEM] move "C:\Program Files\Ethereal" "D:\quarantine\Ethereal"

