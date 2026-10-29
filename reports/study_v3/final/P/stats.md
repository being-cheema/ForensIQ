# Paper statistics (final feature set, 19 features)

Produced by `study_v3_paper_stats.py`. Seeds 42, 1337, 9999, 7, 2024 (LOF is deterministic: one fit). K = round(budget x N). Recall is target-level; precision, false alarms are file-level (target files = every file matching a target pattern). Wilson 95% intervals use n = number of targets (7 / 19 / 34 / 60 pooled); for the seed-mean the mean caught count is used as k.

## (a) Error rates

### Budget 15%

| disk | model | K | recall (seed-mean) | Wilson 95% | recall (worst seed) | Wilson 95% | miss rate | file precision | false alarms | false-alarm rate |
|---|---|---|---|---|---|---|---|---|---|---|
| img1 | IF | 1766 | 100.0% (7.0/7) | 64.6-100.0 | 100.0% | 64.6-100.0 | 0.0% | 0.79% | 1752 | 14.90% |
| img1 | LOF | 1766 | 57.1% (4.0/7) | 25.0-84.2 | 57.1% | 25.0-84.2 | 42.9% | 0.28% | 1761 | 14.98% |
| img1 | OC-SVM | 1766 | 85.7% (6.0/7) | 48.7-97.4 | 85.7% | 48.7-97.4 | 14.3% | 0.46% | 1758 | 14.95% |
| img2 | IF | 12753 | 100.0% (19.0/19) | 83.2-100.0 | 100.0% | 83.2-100.0 | 0.0% | 0.30% | 12715 | 14.96% |
| img2 | LOF | 12753 | 26.3% (5.0/19) | 11.8-48.8 | 26.3% | 11.8-48.8 | 73.7% | 0.04% | 12748 | 15.00% |
| img2 | OC-SVM | 12753 | 100.0% (19.0/19) | 83.2-100.0 | 100.0% | 83.2-100.0 | 0.0% | 0.29% | 12717 | 14.96% |
| img3 | IF | 24916 | 95.3% (32.4/34) | 82.5-98.9 | 85.3% | 69.9-93.6 | 4.7% | 0.32% | 24836 | 14.96% |
| img3 | LOF | 24916 | 44.1% (15.0/34) | 28.9-60.5 | 44.1% | 28.9-60.5 | 55.9% | 0.07% | 24899 | 15.00% |
| img3 | OC-SVM | 24916 | 64.7% (22.0/34) | 47.9-78.5 | 52.9% | 36.7-68.5 | 35.3% | 0.22% | 24862 | 14.97% |
| pooled (60) | IF | 39435 | 97.3% | 89.6-99.4 | 91.7% | 81.9-96.4 | 2.7% | 0.33% | 39303 | 14.96% |
| pooled (60) | LOF | 39435 | 40.0% | 28.6-52.6 | 40.0% | 28.6-52.6 | 60.0% | 0.07% | 39408 | 15.00% |
| pooled (60) | OC-SVM | 39435 | 78.3% | 66.4-86.9 | 71.7% | 59.2-81.5 | 21.7% | 0.25% | 39336 | 14.97% |

### Budget 20%

| disk | model | K | recall (seed-mean) | Wilson 95% | recall (worst seed) | Wilson 95% | miss rate | file precision | false alarms | false-alarm rate |
|---|---|---|---|---|---|---|---|---|---|---|
| img1 | IF | 2355 | 100.0% (7.0/7) | 64.6-100.0 | 100.0% | 64.6-100.0 | 0.0% | 0.62% | 2340 | 19.90% |
| img1 | LOF | 2355 | 71.4% (5.0/7) | 35.9-91.8 | 71.4% | 35.9-91.8 | 28.6% | 0.34% | 2347 | 19.96% |
| img1 | OC-SVM | 2355 | 85.7% (6.0/7) | 48.7-97.4 | 85.7% | 48.7-97.4 | 14.3% | 0.42% | 2345 | 19.94% |
| img2 | IF | 17003 | 100.0% (19.0/19) | 83.2-100.0 | 100.0% | 83.2-100.0 | 0.0% | 0.22% | 16965 | 19.96% |
| img2 | LOF | 17003 | 42.1% (8.0/19) | 23.1-63.7 | 42.1% | 23.1-63.7 | 57.9% | 0.05% | 16995 | 20.00% |
| img2 | OC-SVM | 17003 | 100.0% (19.0/19) | 83.2-100.0 | 100.0% | 83.2-100.0 | 0.0% | 0.22% | 16966 | 19.96% |
| img3 | IF | 33222 | 100.0% (34.0/34) | 89.8-100.0 | 100.0% | 89.8-100.0 | 0.0% | 0.26% | 33137 | 19.96% |
| img3 | LOF | 33222 | 55.9% (19.0/34) | 39.5-71.1 | 55.9% | 39.5-71.1 | 44.1% | 0.09% | 33193 | 19.99% |
| img3 | OC-SVM | 33222 | 68.8% (23.4/34) | 52.0-81.8 | 61.8% | 45.0-76.1 | 31.2% | 0.18% | 33164 | 19.98% |
| pooled (60) | IF | 52580 | 100.0% | 94.0-100.0 | 100.0% | 94.0-100.0 | 0.0% | 0.26% | 52442 | 19.96% |
| pooled (60) | LOF | 52580 | 53.3% | 40.9-65.4 | 53.3% | 40.9-65.4 | 46.7% | 0.09% | 52535 | 19.99% |
| pooled (60) | OC-SVM | 52580 | 80.7% | 69.0-88.7 | 76.7% | 64.6-85.6 | 19.3% | 0.20% | 52475 | 19.97% |

### Per-target best rank, Isolation Forest (seed-mean over 5 seeds)

Percentile = best rank / N. `outside 20%` marks targets whose seed-mean best rank is beyond the 20% review budget; `hard` = one of the 10 largest percentiles of the 60 targets.

| disk | target | files | best rank (mean) | sd | worst seed | percentile (mean) | percentile (worst seed) | outside 15% | outside 20% | hard |
|---|---|---|---|---|---|---|---|---|---|---|
| img1 | 123WASP (UNWISE.EXE, 123wasp.exe) | 2 | 1462.8 | 187.4 | 1742 | 12.43% | 14.80% |  |  | hard |
| img1 | defrag.exe / Anonymizer | 4 | 308.4 | 27.1 | 353 | 2.62% | 3.00% |  |  |  |
| img1 | NetStumbler | 1 | 124.8 | 63.3 | 234 | 1.06% | 1.99% |  |  |  |
| img1 | Ethereal / WinPcap | 2 | 67.8 | 28.4 | 118 | 0.58% | 1.00% |  |  |  |
| img1 | Cain & Abel (Cain.exe) | 2 | 35.6 | 30.0 | 75 | 0.30% | 0.64% |  |  |  |
| img1 | NMEM/NGETTIME (timestomped Novell tools) | 2 | 26.6 | 21.4 | 46 | 0.23% | 0.39% |  |  |  |
| img1 | Password wordlists (ZIP) | 2 | 19.0 | 15.4 | 38 | 0.16% | 0.32% |  |  |  |
| img2 | happy_holiday.jpg (Confidential Pricing) | 1 | 10840.0 | 636.2 | 11815 | 12.75% | 13.90% |  |  | hard |
| img2 | Chrysanthemum.jpg (Wiped via Eraser) | 1 | 8523.0 | 2354.2 | 11230 | 10.03% | 13.21% |  |  | hard |
| img2 | CCleaner64.exe (CCleaner Prefetch) | 1 | 3853.2 | 1175.5 | 5307 | 4.53% | 6.24% |  |  |  |
| img2 | Penguins.jpg (Decoy burned to CD-R) | 2 | 2073.0 | 974.9 | 3620 | 2.44% | 4.26% |  |  |  |
| img2 | Tulips.jpg (Decoy burned to CD-R) | 2 | 1660.0 | 652.8 | 2617 | 1.95% | 3.08% |  |  |  |
| img2 | [secret_project]_design_concept.ppt (LNK) | 2 | 1650.6 | 713.4 | 2876 | 1.94% | 3.38% |  |  |  |
| img2 | System.evtx (Removable Drive Events) | 1 | 1643.2 | 1070.1 | 3496 | 1.93% | 4.11% |  |  |  |
| img2 | [secret_project]_final_meeting.pptx (LNK) | 2 | 1633.8 | 857.8 | 3132 | 1.92% | 3.68% |  |  |  |
| img2 | (secret_project)_pricing_decision.xlsx (LNK) | 2 | 1401.2 | 761.7 | 2707 | 1.65% | 3.18% |  |  |  |
| img2 | Koala.jpg (Decoy burned to CD-R) | 2 | 1380.6 | 571.9 | 2332 | 1.62% | 2.74% |  |  |  |
| img2 | [secret_project]_proposal.docx (LNK) | 2 | 1274.2 | 421.6 | 1999 | 1.50% | 2.35% |  |  |  |
| img2 | sync_config.db / snapshot.db (GDrive DBs) | 6 | 1132.8 | 309.4 | 1620 | 1.33% | 1.91% |  |  |  |
| img2 | ccsetup504.exe (Downloaded CCleaner) | 2 | 1087.8 | 503.8 | 1851 | 1.28% | 2.18% |  |  |  |
| img2 | Eraser 6.2.0.2962.exe (Downloaded Installer) | 2 | 1069.4 | 468.7 | 1758 | 1.26% | 2.07% |  |  |  |
| img2 | Resignation_Letter_(Iaman_Informant).docx / .xps | 5 | 844.4 | 245.1 | 1119 | 0.99% | 1.32% |  |  |  |
| img2 | winter_whether_advisory.zip (Masqueraded Design) | 1 | 742.2 | 243.0 | 1101 | 0.87% | 1.30% |  |  |  |
| img2 | Eraser.exe (Installed Wiping Tool) | 1 | 460.6 | 242.2 | 880 | 0.54% | 1.04% |  |  |  |
| img2 | sync_log.log (Google Drive Sync Log) | 2 | 300.0 | 55.3 | 389 | 0.35% | 0.46% |  |  |  |
| img2 | setupapi.dev.log (USB Connection Log) | 1 | 111.6 | 40.8 | 159 | 0.13% | 0.19% |  |  |  |
| img3 | Cloudy thoughts (4apr).docx | 1 | 26898.2 | 2497.0 | 30300 | 16.19% | 18.24% | yes |  | hard |
| img3 | rootkey.csv | 1 | 23635.4 | 2294.1 | 27583 | 14.23% | 16.61% |  |  | hard |
| img3 | 2018-04-04 (2).png | 1 | 22368.4 | 2895.3 | 26094 | 13.47% | 15.71% |  |  | hard |
| img3 | 2018-04-04 (3).png | 1 | 22038.0 | 2774.5 | 25253 | 13.27% | 15.20% |  |  | hard |
| img3 | 2018-04-03.png | 1 | 21172.0 | 2681.0 | 25340 | 12.75% | 15.25% |  |  | hard |
| img3 | SelfDefenseisMurder.pdf | 1 | 18346.8 | 1770.6 | 20397 | 11.04% | 12.28% |  |  | hard |
| img3 | AMEN.pdf | 1 | 17892.2 | 2044.3 | 20572 | 10.77% | 12.38% |  |  | hard |
| img3 | Chrome Login Data database | 2 | 16435.6 | 1315.7 | 17721 | 9.89% | 10.67% |  |  |  |
| img3 | 2018-04-04 (4).png | 1 | 16427.8 | 1301.8 | 18404 | 9.89% | 11.08% |  |  |  |
| img3 | 2018-04-03 (1).png | 1 | 15308.2 | 1292.0 | 16568 | 9.22% | 9.97% |  |  |  |
| img3 | UKknifeBan.pdf | 1 | 13770.2 | 2802.6 | 15746 | 8.29% | 9.48% |  |  |  |
| img3 | CachedImage_1366_768_POS4.jpg | 1 | 12072.0 | 2262.8 | 14937 | 7.27% | 8.99% |  |  |  |
| img3 | LeftUsesBoycotts.pdf | 1 | 11175.8 | 2462.7 | 13405 | 6.73% | 8.07% |  |  |  |
| img3 | Planning.docx | 5 | 10959.8 | 735.3 | 12049 | 6.60% | 7.25% |  |  |  |
| img3 | Brother Chat.gdoc | 1 | 10091.0 | 2159.1 | 13056 | 6.07% | 7.86% |  |  |  |
| img3 | DeathToll.jpg | 4 | 9464.2 | 465.3 | 10174 | 5.70% | 6.12% |  |  |  |
| img3 | HoldMyTidePod.jpg | 4 | 9448.0 | 776.6 | 10404 | 5.69% | 6.26% |  |  |  |
| img3 | DemLogic.jpg | 4 | 9305.6 | 907.8 | 10221 | 5.60% | 6.15% |  |  |  |
| img3 | Jim's Notebook.url | 1 | 8582.2 | 2316.9 | 11382 | 5.17% | 6.85% |  |  |  |
| img3 | 2018-04-04.png | 1 | 8568.8 | 2631.3 | 12132 | 5.16% | 7.30% |  |  |  |
| img3 | RedGuns.jpg | 4 | 8295.6 | 634.8 | 9090 | 4.99% | 5.47% |  |  |  |
| img3 | AIRPORT INFORMATION.docx | 4 | 7817.4 | 575.1 | 8499 | 4.71% | 5.12% |  |  |  |
| img3 | CubaDearmed.jpg | 4 | 7572.4 | 1020.0 | 9315 | 4.56% | 5.61% |  |  |  |
| img3 | 2018-04-03 (3).png | 1 | 7384.6 | 2265.7 | 10259 | 4.45% | 6.18% |  |  |  |
| img3 | MyTiredHead.jpg | 4 | 7347.8 | 847.0 | 8774 | 4.42% | 5.28% |  |  |  |
| img3 | BladeofGrass.jpg | 4 | 7133.8 | 437.1 | 7786 | 4.29% | 4.69% |  |  |  |
| img3 | Huckleberry.png | 4 | 6655.8 | 557.3 | 7299 | 4.01% | 4.39% |  |  |  |
| img3 | Sheep.jpg | 4 | 6080.0 | 1048.0 | 6930 | 3.66% | 4.17% |  |  |  |
| img3 | DarkWolf.png | 4 | 4751.8 | 538.4 | 5633 | 2.86% | 3.39% |  |  |  |
| img3 | The Cloudy Manifesto.docx | 6 | 3089.0 | 937.5 | 4311 | 1.86% | 2.60% |  |  |  |
| img3 | Google Drive.lnk | 3 | 1986.6 | 805.4 | 3196 | 1.20% | 1.92% |  |  |  |
| img3 | Box Sync.lnk | 2 | 1902.4 | 742.1 | 3069 | 1.15% | 1.85% |  |  |  |
| img3 | Dropbox.lnk | 2 | 1844.6 | 626.5 | 2761 | 1.11% | 1.66% |  |  |  |
| img3 | Operation 2nd Hand Smoke.pptx | 5 | 1685.2 | 912.8 | 2862 | 1.01% | 1.72% |  |  |  |

## (b) Rank-based metrics (file level, mean ± sd over seeds)

| disk | model | target files | AUC-ROC | average precision | R-precision |
|---|---|---|---|---|---|
| img1 | IF | 15 | 0.9439 ± 0.0013 | 0.0730 ± 0.0276 | 0.0933 ± 0.0596 |
| img1 | LOF | 15 | 0.7067 ± 0.0000 | 0.0028 ± 0.0000 | 0.0000 ± 0.0000 |
| img1 | OC-SVM | 15 | 0.8165 ± 0.0126 | 0.0443 ± 0.0134 | 0.0667 ± 0.0000 |
| img2 | IF | 38 | 0.9563 ± 0.0064 | 0.0079 ± 0.0019 | 0.0000 ± 0.0000 |
| img2 | LOF | 38 | 0.4929 ± 0.0000 | 0.0004 ± 0.0000 | 0.0000 ± 0.0000 |
| img2 | OC-SVM | 38 | 0.9714 ± 0.0049 | 0.0132 ± 0.0015 | 0.0000 ± 0.0000 |
| img3 | IF | 85 | 0.9251 ± 0.0073 | 0.0033 ± 0.0003 | 0.0000 ± 0.0000 |
| img3 | LOF | 85 | 0.5938 ± 0.0000 | 0.0007 ± 0.0000 | 0.0000 ± 0.0000 |
| img3 | OC-SVM | 85 | 0.8216 ± 0.0354 | 0.0029 ± 0.0005 | 0.0000 ± 0.0000 |

file-level; positives = all files matching a target pattern; LOF is deterministic so its sd is 0; R-precision = share of positives in the top R (R = #positives).

## (c) Model comparison

Target-level paired test, 60 targets pooled over disks. For each target the seed-mean best-rank percentile is compared.

| comparison | n | non-zero pairs | W | one-sided p | median pct IF | median pct other | IF better / other better / ties |
|---|---|---|---|---|---|---|---|
| IF vs OC-SVM | 60 | 60 | 858.0 | 0.337 | 4.15 | 3.12 | 27 / 33 / 0 |
| IF vs LOF | 60 | 60 | 32.0 | 4.01e-11 | 4.15 | 18.95 | 53 / 7 / 0 |

Per disk (same test):

| comparison | disk | n | W | p |
|---|---|---|---|---|
| IF vs OC-SVM | img1 | 7 | 7.0 | 0.148 |
| IF vs OC-SVM | img2 | 19 | 161.0 | 0.997 |
| IF vs OC-SVM | img3 | 34 | 195.0 | 0.0406 |
| IF vs LOF | img1 | 7 | 0.0 | 0.00781 |
| IF vs LOF | img2 | 19 | 1.0 | 3.81e-06 |
| IF vs LOF | img3 | 34 | 23.0 | 3.73e-08 |

Bootstrap (2,000 resamples of targets) 95% CI of recall at 20%:

| model | pooled | img1 | img2 | img3 |
|---|---|---|---|---|
| IF | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] |
| LOF | 53.3% [40.0, 65.0] | 71.4% [28.6, 100.0] | 42.1% [21.1, 63.2] | 55.9% [38.2, 73.5] |
| OC-SVM | 80.7% [71.0, 89.7] | 85.7% [57.1, 100.0] | 100.0% [100.0, 100.0] | 68.8% [54.1, 82.9] |

percentile = seed-mean best rank / N; the 60 targets are pooled across disks, so disk difficulty is shared; targets within a disk are not independent of each other (same model fit).

## (d) Runtime and data volume

Machine: Apple M2 Pro, 10 logical CPUs, 16.0 GB RAM, macOS-27.2-arm64-arm-64bit-Mach-O, Python 3.13.5, scikit-learn 1.9.1, shap 0.54.1. Mean of 3 runs.

| disk | files | flagged (20%) | feature build (s) | IF fit+score (s) | TreeSHAP per 1,000 flagged (s) | MFT records (files / all) | prefetch .pf | event logs | registry hives |
|---|---|---|---|---|---|---|---|---|---|
| img1 | 11773 | 2355 | 0.3 ± 0.1 | 0.33 ± 0.01 | 1.44 ± 0.01 | 11773 / 12541 | 81 | 3 | 5 |
| img2 | 85017 | 17003 | 2.3 ± 0.0 | 1.09 ± 0.00 | 1.58 ± 0.01 | 85017 / 104034 | 95 | 9 | 5 |
| img3 | 166110 | 33222 | 4.8 ± 0.0 | 1.76 ± 0.03 | 1.46 ± 0.00 | 166110 / 197058 | 161 | 20 | 5 |

feature building = multimodel_eval.build_features (final set incl. burst) from runs/imgN/artifacts, JSON already extracted; IF = standardise + fit (200 trees, sample 256, n_jobs=-1) + score all rows; SHAP = TreeSHAP on 1000 random flagged files (top 20%).

Parsed event records: img1 0, img2 4076, img3 8614.
