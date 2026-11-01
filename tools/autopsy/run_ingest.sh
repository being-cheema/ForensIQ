#!/bin/bash
# usage: run_ingest.sh name imagepath
T=/Users/cheema/ForensIQ/tools/autopsy
export TSK_JAVA_LIB_PATH=$T/tsk/share/java
export DYLD_FALLBACK_LIBRARY_PATH=$T/tsk/lib:/opt/homebrew/lib
mkdir -p $T/autopsy_cases $T/logs $T/userdir_$1/config/ModuleConfig/IngestSettings
cat > $T/userdir_$1/config/ModuleConfig/IngestSettings/CommandLineModeContext.properties <<EOP
Enabled_Ingest_Modules=Central Repository, Data Source Integrity, Virtual Machine Extractor, Extension Mismatch Detector, Hash Lookup, Encryption Detection, GPX Parser, DJI Drone Analyzer, Picture Analyzer, Recent Activity, File Type Identification, Email Parser, Interesting Files Identifier, Android Analyzer
Disabled_Ingest_Modules=PhotoRec Carver, Plaso, Keyword Search, Android Analyzer (aLEAPP), iOS Analyzer (iLEAPP), Embedded File Extractor, YARA Analyzer
EOP
date +%s > $T/logs/$1.start
/usr/bin/time -l $T/app/autopsy-4.23.1/bin/autopsy --nosplash --userdir $T/userdir_$1 --createCase --caseName=$1 --caseBaseDir=$T/autopsy_cases --addDataSource --dataSourcePath="$2" --runIngest --generateReports > $T/logs/$1.out 2> $T/logs/$1.time
date +%s > $T/logs/$1.end
