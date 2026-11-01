# Autopsy 4.23.1 against ForensIQ, on one Apple M2 Pro (10 logical CPUs, 16 GB RAM)

All numbers here were measured on this laptop, one tool at a time, with nothing else running. Before every run about 28 GB of unrelated files were read so the image was not in the file cache (macOS has no cache purge without root).

## Setup
- Autopsy 4.23.1 (official zip, GPG signature verified), Sleuth Kit 4.15.0 built from source with Java bindings, BellSoft Liberica JDK 17, libewf. Install scripts: `tools/autopsy/install_*.sh`, `add_macos_jna.sh`.
- Command line: `autopsy --nosplash --createCase --addDataSource --runIngest --generateReports`, wrapper `tools/autopsy/run_ingest.sh NAME IMAGE`; sequences `run_mac_all.sh` (Image 1) and `run_mac_rest.sh` (Images 2 and 3; the first Image 2 run was disturbed by a compile, stopped and repeated clean).
- Default ingest modules. Keyword Search is off by default and no hash sets were configured. aLEAPP, iLEAPP, YARA and Embedded File Extractor do not run on macOS arm64; PhotoRec was not run. These omissions can only shorten Autopsy's time.
- Report generation fails headless (it needs a report configuration saved from the GUI), so all numbers come from the case databases (`autopsy.db`).
- On Image 3 the Autopsy process crashed (SIGSEGV in `__findenv_locked`) at exit, 3 s after the ingest job completed and after the case database was closed. The ingest result and time are not affected.
- Time = start of the command to the end of the ingest job (`ingest_jobs.end_date_time`).

## Results
| | Image 1 | Image 2 | Image 3 |
|---|---|---|---|
| Autopsy time (s) | 107 | 566 | 4651 |
| ForensIQ time (s), mean of 3 cold runs | 5.1 | 46.0 | 175.3 |
| File-system entries listed by Autopsy | 20,093 | 213,509 | 384,810 |
| Files with any artefact | 63 | 2407 | 471 |
| Files with a detection-type flag | 14 | 114 | 325 |
| Targets covered by detection flags | 0/7 | 4/19 | 0/34 |
| Targets covered by any artefact | 0/7 | 13/19 | 20/34 |
| Expected share of disk read for 100% (Autopsy order, simulated) | 71.7% | 81.2% | 91.4% |

Files: `mac/timing.jsonl` (ForensIQ stages per run), `mac/raw_img*.json` and `mac/analyze_img*.txt` (case-database analysis), `mac/budget_to_100pct.json` (`budget_to_100pct.py`, 20,000 repetitions), `time_e2e_mac.py` and `forensiq_cold_timing_mac.sh` (ForensIQ timing), `tools/autopsy/logs/` (Autopsy start, end and time files).
