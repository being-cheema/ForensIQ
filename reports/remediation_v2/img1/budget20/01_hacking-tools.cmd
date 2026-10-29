@echo off
REM ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
REM NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
REM Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
REM Recommendation: Network-attack or password tools present: cain, ethereal, whois, netstumbler, anonymizer  [confidence: high]
REM Source disk: Image 1: XP Hacking (SCHARDT.001); detected OS: Microsoft Windows XP (5.1, build 2600)
REM Trigger: (d) hacking-tool names at Isolation Forest 23 features, 20% budget (2,355 files)
REM Why this confidence: 256 flagged files name cain, ethereal, whois, netstumbler, anonymizer; 7 Prefetch records and 5 executables are among the listed ones.
REM Supporting flagged files (rank  path):
REM        83  /WINDOWS/Prefetch/CAIN.EXE-23D61279.pf
REM        85  /Program Files/Ethereal/ethereal.exe
REM        91  /WINDOWS/Prefetch/WHOIS.EXE-38443FF6.pf
REM       104  /Program Files/Cain/Cain.exe
REM       115  /WINDOWS/Prefetch/ETHEREAL-SETUP-0.10.6.EXE-1D932600.pf
REM       124  /WINDOWS/Prefetch/WHOIS.EXE-3AFF2064.pf
REM       150  /WINDOWS/Prefetch/CAIN25B45.EXE-056F3A6E.pf
REM       158  /WINDOWS/Prefetch/NETSTUMBLER.EXE-0BFEE568.pf
REM       178  /WINDOWS/Prefetch/ETHEREAL.EXE-1C148EEF.pf
REM       201  /Program Files/Whois/whois.exe

if /i not "%FORENSIQ_LIVE_OK%"=="YES" (
  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.
  exit /b 1
)

REM List the install folder C:\Program Files\Ethereal
dir /a /s "C:\Program Files\Ethereal"

REM List the install folder C:\Program Files\Cain
dir /a /s "C:\Program Files\Cain"

REM List the install folder C:\Program Files\Whois
dir /a /s "C:\Program Files\Whois"

REM List the install folder C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar
dir /a /s "C:\Documents and Settings\Mr. Evil\Start Menu\Programs\Anonymizer Toolbar"

REM List Prefetch records (proof of execution) for the named tools
dir "%SystemRoot%\Prefetch" /a /t:w | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"

REM Check whether the WinPcap capture driver service is installed
sc query npf

REM Show running processes that match the tool names
REM Note: XP: tasklist is in XP Professional only.
tasklist /v | findstr /i "CAIN ETHEREAL WHOIS NETSTUMBLER ANONYMIZER"

REM Show open network connections and owning process IDs
netstat -ano

REM List administrators on the host
net localgroup administrators

REM Stop and disable the capture driver (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Only if the driver exists and the tool is confirmed unauthorised.
REM [CHANGES SYSTEM] sc stop npf & sc config npf start= disabled

REM Move C:\Program Files\Ethereal to a quarantine folder instead of deleting it (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Keep the files: they are exhibits.
REM [CHANGES SYSTEM] move "C:\Program Files\Ethereal" "D:\quarantine\Ethereal"

REM Move C:\Program Files\Cain to a quarantine folder instead of deleting it (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Keep the files: they are exhibits.
REM [CHANGES SYSTEM] move "C:\Program Files\Cain" "D:\quarantine\Cain"

REM Reset the password of Mr. Evil, the profile that holds the tools (changes the system)  -- CHANGES SYSTEM (requires approval)
REM Note: Prompts for the new password.
REM [CHANGES SYSTEM] net user "Mr. Evil" *

