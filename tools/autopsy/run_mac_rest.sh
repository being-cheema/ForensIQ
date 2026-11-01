#!/bin/bash
# Clean re-run of Images 2 and 3 (the first Image 2 run was disturbed by a paper compile). Nothing else runs on the machine meanwhile.
T=/Users/cheema/ForensIQ/tools/autopsy; R=/Users/cheema/ForensIQ
flush() { cat $R/images/szechuan/DESKTOP-E01.zip $R/images/szechuan/DC01-E01.zip $R/images/lonewolf/LoneWolf.E0[4-9] > /dev/null 2>&1; }
flush; $T/run_ingest.sh img2 $R/images/dataleak/cfreds_2015_data_leakage_pc.dd
flush; $T/run_ingest.sh img3 $R/images/lonewolf/LoneWolf.E01
echo ALLDONE > $T/logs/mac_done
