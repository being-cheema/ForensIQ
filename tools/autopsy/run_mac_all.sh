#!/bin/bash
# Autopsy 4.23.1 (default ingest modules) on the three images, on this Mac, one at a time, file cache flushed before each run.
T=/Users/cheema/ForensIQ/tools/autopsy; R=/Users/cheema/ForensIQ
flush() { cat $R/images/szechuan/DESKTOP-E01.zip $R/images/szechuan/DC01-E01.zip $R/images/lonewolf/LoneWolf.E0[4-9] > /dev/null 2>&1; }
rm -rf $T/autopsy_cases/img1 $T/autopsy_cases/img2 $T/autopsy_cases/img3
flush; $T/run_ingest.sh img1 $R/images/hacking/SCHARDT.dd
flush; $T/run_ingest.sh img2 $R/images/dataleak/cfreds_2015_data_leakage_pc.dd
flush; $T/run_ingest.sh img3 $R/images/lonewolf/LoneWolf.E01
echo ALLDONE > $T/logs/mac_done
