#!/bin/bash
# Cold-read timing on macOS without root: before each run, read ~25 GB of unrelated image files so the system file cache
# no longer holds the image being timed (the Mac has 16 GB RAM). 3 runs per image, fresh process each time.
cd "$(dirname "$0")/../.." || exit 1
export FORENSIQ_FEATURE_SET=final
flush() { cat images/dataleak/cfreds_2015_data_leakage_pc.dd images/lonewolf/LoneWolf.E0[4-9] > /dev/null 2>&1; }
: > reports/autopsy_baseline/mac/timing.jsonl
for run in 1 2 3; do
  flush; .venv/bin/python reports/autopsy_baseline/time_e2e_mac.py img1 images/hacking/SCHARDT.dd $run
  flush; .venv/bin/python reports/autopsy_baseline/time_e2e_mac.py img2 images/dataleak/cfreds_2015_data_leakage_pc.dd $run
  flush; .venv/bin/python reports/autopsy_baseline/time_e2e_mac.py img3 images/lonewolf/LoneWolf.E01 $run
done
echo DONE
