@echo off
REM ForensIQ remediation v2 - advice for the LIVE environment this disk came from.
REM NEVER run against seized evidence (ISO/IEC 27037). Human approval is required for any change.
REM Lines marked CHANGES SYSTEM are commented out. Un-commenting one is an approved action, not a default.
REM Recommendation: Recently opened documents are recorded for Mr. Evil  [confidence: medium]
REM Source disk: Image 1: XP Hacking (SCHARDT.001); detected OS: Microsoft Windows XP (5.1, build 2600)
REM Trigger: (b) shortcut / jump-list traces of documents at Isolation Forest 23 features, 20% budget (2,355 files)
REM Why this confidence: 10 flagged shortcut / jump-list traces. Recent-file shortcuts exist on every used profile, so this shows access, not copying or removal; it is never rated higher than medium.
REM Supporting flagged files (rank  path):
REM       248  /Documents and Settings/Mr. Evil/Recent/keys.lnk
REM       313  /Documents and Settings/Mr. Evil/Recent/GhostWare.lnk
REM       314  /Documents and Settings/Mr. Evil/Recent/channels.lnk
REM       352  /Documents and Settings/Mr. Evil/Recent/channels (2).lnk
REM       372  /Documents and Settings/Mr. Evil/Recent/Anonyymizer.lnk
REM       397  /Documents and Settings/Mr. Evil/Recent/Receipt.lnk
REM       407  /Documents and Settings/All Users/Start Menu/Programs/mIRC/Readme.txt.lnk
REM       417  /Documents and Settings/All Users/Start Menu/Programs/mIRC/Versions.txt.lnk
REM       446  /Documents and Settings/Mr. Evil/Recent/Temp on m1200 (4.12.220.254).lnk
REM       491  /Documents and Settings/Mr. Evil/Recent/yng13.lnk

if /i not "%FORENSIQ_LIVE_OK%"=="YES" (
  echo Set FORENSIQ_LIVE_OK=YES only on the live machine, with approval. Never on evidence.
  exit /b 1
)

REM List the Mr. Evil Recent-documents folder, newest first
dir /a /o-d /t:w "C:\Documents and Settings\Mr. Evil\Recent"

REM Show account details and last logon for the profiles named in the paths
net user "Mr. Evil"

